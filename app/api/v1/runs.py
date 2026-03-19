"""Run routes: trigger pay-per-run, status, output stream, history."""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.hand import Hand
from app.models.run import Run, RunStatus, RunTier
from app.models.user import User
from app.schemas.common import CursorPage
from app.schemas.run import RunCreate, RunOutput, RunResponse

try:
    from sse_starlette.sse import EventSourceResponse
except ImportError:
    EventSourceResponse = None  # type: ignore[assignment, misc]

router = APIRouter(prefix="/runs", tags=["runs"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _to_response(run: Run) -> RunResponse:
    return RunResponse(
        id=run.id,
        hand_name=run.hand.name if run.hand else "Unknown",
        status=run.status.value,
        tier=run.tier.value,
        output_preview=run.output_preview,
        token_count=run.token_count,
        duration_ms=run.duration_ms,
        error_message=run.error_message,
        lamports_charged=run.lamports_charged,
        queued_at=run.queued_at,
        started_at=run.started_at,
        completed_at=run.completed_at,
    )


async def _get_user_run(
    run_id: uuid.UUID, user: User, db: AsyncSession
) -> Run:
    result = await db.execute(
        select(Run).where(Run.id == run_id, Run.user_id == user.id)
    )
    run = result.scalar_one_or_none()
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )
    return run


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/history", response_model=CursorPage[RunResponse])
async def run_history(
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CursorPage[RunResponse]:
    """Paginated run history for the current user."""
    stmt = (
        select(Run)
        .where(Run.user_id == user.id)
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
        data=[_to_response(r) for r in items],
        next_cursor=str(items[-1].id) if has_more and items else None,
        total=len(items),
    )


@router.post("", response_model=RunResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_run(
    body: RunCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RunResponse:
    """Trigger a pay-per-run execution."""
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

    # Determine cost based on tier
    try:
        tier = RunTier(body.tier)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tier: {body.tier}",
        )

    cost = hand.price_quick_lamports or 0
    if tier == RunTier.deep:
        cost = hand.price_deep_lamports or 0

    # Verify payment
    if body.payment_method == "credits":
        if user.credit_balance_lamports < cost:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient credit balance",
            )
        user.credit_balance_lamports -= cost
    elif body.payment_method in ("sol", "fgh", "usdc"):
        if not body.solana_tx_signature:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="solana_tx_signature required for on-chain payment",
            )
        # TODO: implement real Solana transaction verification
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid payment method: {body.payment_method}",
        )

    now = datetime.now(timezone.utc)
    run = Run(
        id=uuid.uuid4(),
        user_id=user.id,
        hand_id=hand.id,
        tier=tier,
        status=RunStatus.queued,
        config=body.config,
        delivery_channel=body.delivery_channel or "dashboard",
        delivery_target=body.delivery_target,
        lamports_charged=cost,
        fgh_used=(body.payment_method == "fgh"),
        queued_at=now,
    )
    db.add(run)

    # Update hand stats
    hand.total_runs = hand.total_runs + 1
    await db.flush()
    await db.refresh(run)

    # TODO: dispatch Celery task
    # from app.workers.tasks.hand_tasks import execute_run
    # execute_run.delay(str(run.id))

    return _to_response(run)


@router.get("/{run_id}", response_model=RunResponse)
async def get_run(
    run_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RunResponse:
    """Get run status and output."""
    run = await _get_user_run(run_id, user, db)
    return _to_response(run)


@router.get("/{run_id}/output")
async def stream_run_output(
    run_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """SSE stream of run output."""
    run = await _get_user_run(run_id, user, db)

    async def event_generator():
        # TODO: connect to OpenFang run output stream
        lines = [
            "Initializing agent...",
            "Loading hand configuration...",
            "Executing task...",
            "Processing results...",
            "Run completed successfully.",
        ]
        for i, line in enumerate(lines):
            data = json.dumps({
                "type": "stdout",
                "content": line,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            yield {"event": "output", "data": data}
            await asyncio.sleep(1)
        yield {
            "event": "done",
            "data": json.dumps({"run_id": str(run.id)}),
        }

    if EventSourceResponse is not None:
        return EventSourceResponse(event_generator())

    async def sse_fallback():
        async for event in event_generator():
            yield f"event: {event['event']}\ndata: {event['data']}\n\n"

    return StreamingResponse(sse_fallback(), media_type="text/event-stream")


@router.delete("/{run_id}")
async def cancel_run(
    run_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Cancel a queued run."""
    run = await _get_user_run(run_id, user, db)
    if run.status != RunStatus.queued:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only queued runs can be cancelled",
        )
    run.status = RunStatus.cancelled
    await db.flush()
    # TODO: revoke Celery task
    return {"detail": "Run cancelled"}
