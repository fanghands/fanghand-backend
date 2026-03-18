"""Payment routes: Stripe checkout, credit wallet, burn stats, history."""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.api.deps import get_current_user, get_db
from app.models.credit_transaction import CreditTransaction
from app.models.fgh_burn import FghBurn
from app.models.payment import Payment
from app.models.user import User
from app.schemas.common import CursorPage
from app.schemas.payment import (
    BurnEvent,
    BurnStats,
    CheckoutCreate,
    CreditBalanceResponse,
    CreditDeposit,
    PaymentHistoryItem,
)

try:
    from sse_starlette.sse import EventSourceResponse
except ImportError:
    EventSourceResponse = None  # type: ignore[assignment, misc]

router = APIRouter(prefix="/payments", tags=["payments"])

# ---------------------------------------------------------------------------
# Inline response schemas
# ---------------------------------------------------------------------------

from pydantic import BaseModel as _BM  # noqa: E402


class _CheckoutResp(_BM):
    session_id: str
    url: str


class _PortalResp(_BM):
    url: str


@router.post("/stripe/create-session", response_model=_CheckoutResp)
async def create_stripe_session(
    body: CheckoutCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> _CheckoutResp:
    """Create a Stripe Checkout session for hand subscription."""
    # TODO: implement real Stripe integration
    # import stripe
    # stripe.api_key = settings.STRIPE_SECRET_KEY
    # session = stripe.checkout.Session.create(
    #     customer=user.stripe_customer_id or stripe.Customer.create(
    #         metadata={"user_id": str(user.id)}
    #     ).id,
    #     mode="subscription",
    #     line_items=[{"price": body.price_id, "quantity": 1}],
    #     success_url=body.success_url,
    #     cancel_url=body.cancel_url,
    #     metadata={"hand_id": str(body.hand_id), "user_id": str(user.id)},
    # )
    mock_session_id = f"cs_mock_{uuid.uuid4().hex[:16]}"
    return _CheckoutResp(
        session_id=mock_session_id,
        url=f"https://checkout.stripe.com/c/pay/{mock_session_id}",
    )


@router.get("/stripe/portal", response_model=_PortalResp)
async def get_stripe_portal(
    user: User = Depends(get_current_user),
) -> _PortalResp:
    """Get Stripe Customer Portal URL for managing subscriptions."""
    if not user.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Stripe customer record found. Make a purchase first.",
        )
    # TODO: implement real Stripe portal session
    return _PortalResp(
        url=f"https://billing.stripe.com/p/session/mock_{user.stripe_customer_id}"
    )


# ---------------------------------------------------------------------------
# Credit wallet
# ---------------------------------------------------------------------------


@router.post("/credit/deposit", response_model=CreditBalanceResponse)
async def deposit_credit(
    body: CreditDeposit,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CreditBalanceResponse:
    """Verify a SOL deposit and credit the user's account."""
    if body.lamports < settings.CREDIT_DEPOSIT_MIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Minimum deposit is {settings.CREDIT_DEPOSIT_MIN} lamports",
        )

    # TODO: implement real Solana transaction verification
    # Verify tx_signature on-chain: correct recipient, amount, finality

    user.credit_balance_lamports += body.lamports
    new_balance = user.credit_balance_lamports

    # Record the credit transaction
    ct = CreditTransaction(
        id=uuid.uuid4(),
        user_id=user.id,
        type="deposit",
        lamports=body.lamports,
        balance_after=new_balance,
        tx_signature=body.tx_signature,
        description="SOL deposit",
    )
    db.add(ct)
    await db.flush()

    # Approximate USD equivalent (rough SOL price placeholder)
    usd_equiv = round(new_balance / 1_000_000_000 * 150, 2)  # TODO: use real price feed

    return CreditBalanceResponse(
        lamports=new_balance,
        usd_equivalent=usd_equiv,
    )


@router.get("/credit/balance", response_model=CreditBalanceResponse)
async def get_credit_balance(
    user: User = Depends(get_current_user),
) -> CreditBalanceResponse:
    """Get the current user's credit wallet balance."""
    usd_equiv = round(user.credit_balance_lamports / 1_000_000_000 * 150, 2)
    return CreditBalanceResponse(
        lamports=user.credit_balance_lamports,
        usd_equivalent=usd_equiv,
    )


# ---------------------------------------------------------------------------
# Payment history
# ---------------------------------------------------------------------------


@router.get("/history", response_model=CursorPage[PaymentHistoryItem])
async def payment_history(
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CursorPage[PaymentHistoryItem]:
    """Paginated payment history for the current user."""
    stmt = (
        select(Payment)
        .where(Payment.user_id == user.id)
        .order_by(Payment.created_at.desc(), Payment.id.desc())
    )
    if cursor:
        try:
            cursor_id = uuid.UUID(cursor)
            stmt = stmt.where(Payment.id < cursor_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid cursor")

    stmt = stmt.limit(limit + 1)
    result = await db.execute(stmt)
    rows = list(result.scalars().all())
    has_more = len(rows) > limit
    items = rows[:limit]

    return CursorPage(
        items=[
            PaymentHistoryItem(
                id=p.id,
                type=p.type.value,
                status=p.status.value,
                currency=p.currency.value,
                amount_cents=p.amount_cents,
                amount_lamports=p.amount_lamports,
                hand_id=p.hand_id,
                created_at=p.created_at,
            )
            for p in items
        ],
        next_cursor=str(items[-1].id) if has_more and items else None,
        has_more=has_more,
    )


# ---------------------------------------------------------------------------
# FGH Burns (public)
# ---------------------------------------------------------------------------


@router.get("/burns", response_model=CursorPage[BurnEvent])
async def list_burns(
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> CursorPage[BurnEvent]:
    """Public paginated list of FGH burn events."""
    stmt = select(FghBurn).order_by(FghBurn.burned_at.desc(), FghBurn.id.desc())
    if cursor:
        try:
            cursor_id = uuid.UUID(cursor)
            stmt = stmt.where(FghBurn.id < cursor_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid cursor")

    stmt = stmt.limit(limit + 1)
    result = await db.execute(stmt)
    rows = list(result.scalars().all())
    has_more = len(rows) > limit
    items = rows[:limit]

    return CursorPage(
        items=[
            BurnEvent(
                id=b.id,
                fgh_burned=b.fgh_burned,
                tx_signature=b.tx_signature,
                trigger_type=b.trigger_type,
                burned_at=b.burned_at,
            )
            for b in items
        ],
        next_cursor=str(items[-1].id) if has_more and items else None,
        has_more=has_more,
    )


@router.get("/burns/stats", response_model=BurnStats)
async def burn_stats(
    db: AsyncSession = Depends(get_db),
) -> BurnStats:
    """Aggregate FGH burn statistics."""
    total_burned = await db.scalar(
        select(func.coalesce(func.sum(FghBurn.fgh_burned), 0))
    ) or 0
    total_events = await db.scalar(
        select(func.count()).select_from(FghBurn)
    ) or 0

    last_burn_result = await db.execute(
        select(FghBurn.burned_at)
        .order_by(FghBurn.burned_at.desc())
        .limit(1)
    )
    last_burn_at = last_burn_result.scalar_one_or_none()

    return BurnStats(
        total_burned=total_burned,
        total_events=total_events,
        last_burn_at=last_burn_at,
    )


@router.get("/burns/stream")
async def burn_stream():
    """SSE live burn ticker (public)."""
    async def event_generator():
        # TODO: connect to real burn event stream / Redis pub-sub
        counter = 0
        cumulative = 0
        while True:
            counter += 1
            cumulative += 1_000_000  # Mock: 1M FGH units burned per tick
            data = json.dumps({
                "event_id": counter,
                "amount_burned": 1_000_000,
                "cumulative_burned": cumulative,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            yield {"event": "burn", "data": data}
            await asyncio.sleep(3)

    if EventSourceResponse is not None:
        return EventSourceResponse(event_generator())

    async def sse_fallback():
        async for event in event_generator():
            yield f"event: {event['event']}\ndata: {event['data']}\n\n"

    return StreamingResponse(sse_fallback(), media_type="text/event-stream")
