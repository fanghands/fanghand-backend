"""Dashboard routes: overview stats, recent runs, approval queue."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.activation import Activation, ActivationStatus
from app.models.payment import Payment
from app.models.run import Run
from app.models.user import User
from app.schemas.run import RunResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class DashboardOverview(BaseModel):
    active_hands_count: int
    total_runs: int
    total_spent_cents: int
    fgh_balance: int


class ApprovalItem(BaseModel):
    id: uuid.UUID
    type: str
    title: str
    status: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/overview", response_model=DashboardOverview)
async def dashboard_overview(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DashboardOverview:
    """Aggregate dashboard statistics for the current user."""
    active_count = await db.scalar(
        select(func.count())
        .select_from(Activation)
        .where(
            Activation.user_id == user.id,
            Activation.status == ActivationStatus.active,
        )
    ) or 0

    total_runs = await db.scalar(
        select(func.count()).select_from(Run).where(Run.user_id == user.id)
    ) or 0

    total_spent = await db.scalar(
        select(func.coalesce(func.sum(Payment.usd_equivalent_cents), 0)).where(
            Payment.user_id == user.id,
            Payment.status == "confirmed",
        )
    ) or 0

    return DashboardOverview(
        active_hands_count=active_count,
        total_runs=total_runs,
        total_spent_cents=total_spent,
        fgh_balance=user.fgh_balance_cache,
    )


@router.get("/recent-runs", response_model=list[RunResponse])
async def recent_runs(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[RunResponse]:
    """Get the last 10 runs for the current user."""
    result = await db.execute(
        select(Run)
        .where(Run.user_id == user.id)
        .order_by(Run.queued_at.desc())
        .limit(10)
    )
    runs = result.scalars().all()

    return [
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
        for r in runs
    ]


@router.get("/approval-queue", response_model=list[ApprovalItem])
async def approval_queue(
    user: User = Depends(get_current_user),
) -> list[ApprovalItem]:
    """Get pending approval actions for the user (mock)."""
    # TODO: implement real approval queue
    return []
