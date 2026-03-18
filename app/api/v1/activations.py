"""Activation routes: create, manage, monitor agent activations."""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.activation import Activation, ActivationStatus
from app.models.hand import Hand
from app.models.run import Run
from app.models.user import User
from app.schemas.activation import (
    ActivationConfigUpdate,
    ActivationCreate,
    ActivationResponse,
    StatusEvent,
)
from app.schemas.common import CursorPage
from app.schemas.run import RunResponse

try:
    from sse_starlette.sse import EventSourceResponse
except ImportError:
    EventSourceResponse = None  # type: ignore[assignment, misc]

router = APIRouter(prefix="/activations", tags=["activations"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _to_response(act: Activation) -> ActivationResponse:
    """Map an Activation ORM instance to its response schema."""
    return ActivationResponse(
        id=act.id,
        hand_id=act.hand_id,
        hand_name=act.hand.name if act.hand else "Unknown",
        status=act.status.value,
        config=act.config,
        delivery_channel=act.delivery_channel,
        openfang_agent_id=act.openfang_agent_id,
        payment_currency=act.payment_currency.value,
        discount_pct=act.discount_pct,
        activated_at=act.activated_at,
        paused_at=act.paused_at,
        created_at=act.created_at,
    )


async def _get_user_activation(
    activation_id: uuid.UUID,
    user: User,
    db: AsyncSession,
) -> Activation:
    result = await db.execute(
        select(Activation).where(
            Activation.id == activation_id,
            Activation.user_id == user.id,
        )
    )
    act = result.scalar_one_or_none()
    if act is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activation not found",
        )
    return act


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=CursorPage[ActivationResponse])
async def list_activations(
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CursorPage[ActivationResponse]:
    """List the current user's activations."""
    stmt = (
        select(Activation)
        .where(Activation.user_id == user.id)
        .order_by(Activation.created_at.desc(), Activation.id.desc())
    )
    if cursor:
        try:
            cursor_id = uuid.UUID(cursor)
            stmt = stmt.where(Activation.id < cursor_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid cursor")

    stmt = stmt.limit(limit + 1)
    result = await db.execute(stmt)
    rows = list(result.scalars().all())
    has_more = len(rows) > limit
    items = rows[:limit]

    return CursorPage(
        items=[_to_response(a) for a in items],
        next_cursor=str(items[-1].id) if has_more and items else None,
        has_more=has_more,
    )


@router.post("", response_model=ActivationResponse, status_code=status.HTTP_201_CREATED)
async def create_activation(
    body: ActivationCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ActivationResponse:
    """Create a new hand activation after verifying payment."""
    # Verify hand exists and is live
    result = await db.execute(select(Hand).where(Hand.id == body.hand_id))
    hand = result.scalar_one_or_none()
    if hand is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hand not found",
        )
    if hand.status.value != "live":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hand is not currently available",
        )

    # Verify payment
    if body.payment_method == "stripe":
        if not body.stripe_payment_method_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="stripe_payment_method_id required for Stripe payment",
            )
        # TODO: implement real Stripe payment verification
    elif body.solana_tx_signature:
        # TODO: implement real Solana transaction verification
        pass

    # TODO: call OpenFang client to spawn the agent
    # openfang_agent_id = await openfang_client.spawn(hand.openfang_hand_slug, body.config)

    activation = Activation(
        id=uuid.uuid4(),
        user_id=user.id,
        hand_id=hand.id,
        status=ActivationStatus.active,
        config=body.config,
        delivery_channel=body.delivery_channel,
        delivery_target=body.delivery_target,
        payment_currency=body.payment_currency,
        discount_pct=body.discount_applied_pct or 0,
    )
    db.add(activation)

    # Update hand stats
    hand.total_activations = hand.total_activations + 1
    await db.flush()
    await db.refresh(activation)

    return _to_response(activation)


@router.get("/{activation_id}", response_model=ActivationResponse)
async def get_activation(
    activation_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ActivationResponse:
    """Get activation detail with current OpenFang status."""
    act = await _get_user_activation(activation_id, user, db)
    # TODO: fetch live status from OpenFang
    return _to_response(act)


@router.patch("/{activation_id}/config", response_model=ActivationResponse)
async def update_activation_config(
    activation_id: uuid.UUID,
    body: ActivationConfigUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ActivationResponse:
    """Update an activation's configuration."""
    act = await _get_user_activation(activation_id, user, db)
    if act.status not in (ActivationStatus.active, ActivationStatus.paused):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update config for this activation status",
        )
    act.config = body.config
    await db.flush()
    await db.refresh(act)
    return _to_response(act)


@router.post("/{activation_id}/pause", response_model=ActivationResponse)
async def pause_activation(
    activation_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ActivationResponse:
    """Pause a running activation."""
    act = await _get_user_activation(activation_id, user, db)
    if act.status != ActivationStatus.active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only active activations can be paused",
        )
    act.status = ActivationStatus.paused
    act.paused_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(act)
    # TODO: call OpenFang to pause the agent
    return _to_response(act)


@router.post("/{activation_id}/resume", response_model=ActivationResponse)
async def resume_activation(
    activation_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ActivationResponse:
    """Resume a paused activation."""
    act = await _get_user_activation(activation_id, user, db)
    if act.status != ActivationStatus.paused:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only paused activations can be resumed",
        )
    act.status = ActivationStatus.active
    act.paused_at = None
    await db.flush()
    await db.refresh(act)
    # TODO: call OpenFang to resume the agent
    return _to_response(act)


@router.delete("/{activation_id}")
async def cancel_activation(
    activation_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Cancel an activation."""
    act = await _get_user_activation(activation_id, user, db)
    if act.status == ActivationStatus.cancelled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Activation already cancelled",
        )
    act.status = ActivationStatus.cancelled
    act.cancelled_at = datetime.now(timezone.utc)
    await db.flush()
    # TODO: call OpenFang to stop the agent
    return {"detail": "Activation cancelled"}


@router.get("/{activation_id}/metrics")
async def get_activation_metrics(
    activation_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get dashboard metrics for an activation."""
    act = await _get_user_activation(activation_id, user, db)

    # Aggregate run stats
    total_runs = await db.scalar(
        select(func.count()).select_from(Run).where(Run.activation_id == act.id)
    ) or 0
    successful_runs = await db.scalar(
        select(func.count())
        .select_from(Run)
        .where(Run.activation_id == act.id, Run.status == "completed")
    ) or 0
    failed_runs = await db.scalar(
        select(func.count())
        .select_from(Run)
        .where(Run.activation_id == act.id, Run.status == "failed")
    ) or 0

    last_run_result = await db.execute(
        select(Run.completed_at)
        .where(Run.activation_id == act.id)
        .order_by(Run.completed_at.desc().nulls_last())
        .limit(1)
    )
    last_run_at = last_run_result.scalar_one_or_none()

    uptime = 0
    if act.status == ActivationStatus.active:
        uptime = int((datetime.now(timezone.utc) - act.activated_at).total_seconds())

    return {
        "activation_id": str(act.id),
        "status": act.status.value,
        "uptime_seconds": uptime,
        "total_runs": total_runs,
        "successful_runs": successful_runs,
        "failed_runs": failed_runs,
        "last_run_at": last_run_at.isoformat() if last_run_at else None,
    }


@router.get("/{activation_id}/status/stream")
async def stream_activation_status(
    activation_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """SSE live status stream for an activation."""
    act = await _get_user_activation(activation_id, user, db)

    async def event_generator():
        # TODO: connect to OpenFang status stream
        counter = 0
        while True:
            counter += 1
            data = json.dumps({
                "activation_id": str(act.id),
                "status": act.status.value,
                "tick": counter,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            yield {"event": "status", "data": data}
            await asyncio.sleep(5)

    if EventSourceResponse is not None:
        return EventSourceResponse(event_generator())

    async def sse_fallback():
        async for event in event_generator():
            yield f"event: {event['event']}\ndata: {event['data']}\n\n"

    return StreamingResponse(sse_fallback(), media_type="text/event-stream")


@router.get("/{activation_id}/logs", response_model=CursorPage[RunResponse])
async def get_activation_logs(
    activation_id: uuid.UUID,
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CursorPage[RunResponse]:
    """List run history for this activation."""
    act = await _get_user_activation(activation_id, user, db)

    stmt = (
        select(Run)
        .where(Run.activation_id == act.id)
        .order_by(Run.queued_at.desc(), Run.id.desc())
    )
    if cursor:
        try:
            cursor_id = uuid.UUID(cursor)
            stmt = stmt.where(Run.id < cursor_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid cursor")

    stmt = stmt.limit(limit + 1)
    result = await db.execute(stmt)
    rows = list(result.scalars().all())
    has_more = len(rows) > limit
    items = rows[:limit]

    return CursorPage(
        items=[
            RunResponse(
                id=r.id,
                hand_name=r.hand.name if r.hand else "Unknown",
                status=r.status.value,
                tier=r.tier.value,
                output_preview=r.output_preview,
                token_count=r.token_count,
                duration_ms=r.duration_ms,
                error_message=r.error_message,
                lamports_charged=r.lamports_charged,
                queued_at=r.queued_at,
                started_at=r.started_at,
                completed_at=r.completed_at,
            )
            for r in items
        ],
        next_cursor=str(items[-1].id) if has_more and items else None,
        has_more=has_more,
    )
