"""Builder routes: registration, hand submission, earnings, payouts."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_builder
from app.models.builder import Builder
from app.models.hand import Hand, HandCategory, HandStatus, HandType
from app.models.hand_review import HandReview, ReviewStatus
from app.models.payment import Payment
from app.models.user import User
from app.schemas.builder import (
    BuilderRegister,
    BuilderResponse,
    EarningsResponse,
    HandSubmit,
)
from app.schemas.common import CursorPage
from app.schemas.hand import HandDetail

router = APIRouter(prefix="/builders", tags=["builders"])

# ---------------------------------------------------------------------------
# Extra schemas
# ---------------------------------------------------------------------------


class HandUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=100)
    description: str | None = Field(None, min_length=10)
    category: str | None = None
    price_monthly_cents: int | None = Field(None, ge=0)
    hand_toml: str | None = None
    skill_md: str | None = None
    system_prompt: str | None = None
    icon_emoji: str | None = None


class ReviewStatusResponse(BaseModel):
    hand_id: uuid.UUID
    review_id: uuid.UUID | None = None
    status: str
    submitted_at: datetime
    reviewed_at: datetime | None = None
    reviewer_feedback: str | None = None


class PayoutRequest(BaseModel):
    amount_cents: int = Field(..., gt=0)
    payout_usdc_address: str = Field(..., min_length=32, max_length=44)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/register",
    response_model=BuilderResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_builder(
    body: BuilderRegister,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BuilderResponse:
    """Register the current user as a builder."""
    if user.is_builder:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a builder",
        )

    user.is_builder = True

    builder = Builder(
        id=user.id,
        bio=body.bio,
        twitter_handle=body.twitter_handle,
        github_handle=body.github_handle,
        payout_usdc_address=body.payout_usdc_address,
    )
    db.add(builder)
    await db.flush()
    await db.refresh(builder)

    return BuilderResponse.model_validate(builder)


@router.get("/me", response_model=BuilderResponse)
async def get_builder_profile(
    builder: Builder = Depends(require_builder),
) -> BuilderResponse:
    """Get the current builder's profile and stats."""
    return BuilderResponse.model_validate(builder)


@router.get("/me/hands", response_model=CursorPage[HandDetail])
async def list_my_hands(
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    builder: Builder = Depends(require_builder),
    db: AsyncSession = Depends(get_db),
) -> CursorPage[HandDetail]:
    """List hands submitted by the current builder."""
    stmt = (
        select(Hand)
        .where(Hand.author_id == builder.id)
        .order_by(Hand.created_at.desc(), Hand.id.desc())
    )
    if cursor:
        try:
            cursor_id = uuid.UUID(cursor)
            stmt = stmt.where(Hand.id < cursor_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid cursor")

    stmt = stmt.limit(limit + 1)
    result = await db.execute(stmt)
    rows = list(result.scalars().all())
    has_more = len(rows) > limit
    items = rows[:limit]

    return CursorPage(
        items=[HandDetail.model_validate(h) for h in items],
        next_cursor=str(items[-1].id) if has_more and items else None,
        has_more=has_more,
    )


@router.post(
    "/hands/submit",
    response_model=HandDetail,
    status_code=status.HTTP_201_CREATED,
)
async def submit_hand(
    body: HandSubmit,
    builder: Builder = Depends(require_builder),
    db: AsyncSession = Depends(get_db),
) -> HandDetail:
    """Submit a new hand for review."""
    # Generate slug from name
    slug = body.name.lower().replace(" ", "-")
    # Remove non-alphanumeric chars except hyphens
    slug = "".join(c for c in slug if c.isalnum() or c == "-")
    slug = slug.strip("-")

    # Check slug uniqueness
    existing = await db.execute(select(Hand).where(Hand.slug == slug))
    if existing.scalar_one_or_none() is not None:
        # Append random suffix
        slug = f"{slug}-{uuid.uuid4().hex[:6]}"

    # Validate category
    try:
        cat_enum = HandCategory(body.category)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid category: {body.category}",
        )

    hand = Hand(
        id=uuid.uuid4(),
        slug=slug,
        name=body.name,
        description=body.description,
        type=HandType.community,
        status=HandStatus.review,
        category=cat_enum,
        author_id=builder.id,
        price_monthly_cents=body.price_monthly_cents,
        hand_toml_url=body.hand_toml,  # store as URL/content
        skill_md_url=body.skill_md,
        system_prompt_url=body.system_prompt,
        icon_emoji=body.icon_emoji,
    )
    db.add(hand)

    # Create a review record
    review = HandReview(
        id=uuid.uuid4(),
        hand_id=hand.id,
        builder_id=builder.id,
        status=ReviewStatus.pending,
        version=hand.version,
    )
    db.add(review)

    # Increment builder hand count
    builder.total_hands = builder.total_hands + 1

    await db.flush()
    await db.refresh(hand)
    return HandDetail.model_validate(hand)


@router.patch("/hands/{hand_id}", response_model=HandDetail)
async def update_hand(
    hand_id: uuid.UUID,
    body: HandUpdate,
    builder: Builder = Depends(require_builder),
    db: AsyncSession = Depends(get_db),
) -> HandDetail:
    """Update a hand (triggers re-review for content changes)."""
    result = await db.execute(
        select(Hand).where(Hand.id == hand_id, Hand.author_id == builder.id)
    )
    hand = result.scalar_one_or_none()
    if hand is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hand not found or not owned by you",
        )

    update_data = body.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No fields to update",
        )

    # Map schema fields to model fields where names differ
    field_mapping = {
        "hand_toml": "hand_toml_url",
        "skill_md": "skill_md_url",
        "system_prompt": "system_prompt_url",
    }
    for schema_field, model_field in field_mapping.items():
        if schema_field in update_data:
            update_data[model_field] = update_data.pop(schema_field)

    # Validate category if changing
    if "category" in update_data:
        try:
            update_data["category"] = HandCategory(update_data["category"])
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category: {update_data['category']}",
            )

    for field, value in update_data.items():
        setattr(hand, field, value)

    # Trigger re-review for content changes
    content_fields = {"name", "description", "hand_toml_url", "skill_md_url", "system_prompt_url"}
    if content_fields & set(update_data.keys()):
        hand.status = HandStatus.review
        # Create new review record
        review = HandReview(
            id=uuid.uuid4(),
            hand_id=hand.id,
            builder_id=builder.id,
            status=ReviewStatus.pending,
            version=hand.version,
        )
        db.add(review)

    await db.flush()
    await db.refresh(hand)
    return HandDetail.model_validate(hand)


@router.post("/hands/{hand_id}/stake")
async def stake_fgh(
    hand_id: uuid.UUID,
    builder: Builder = Depends(require_builder),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Lock FGH stake for a hand."""
    result = await db.execute(
        select(Hand).where(Hand.id == hand_id, Hand.author_id == builder.id)
    )
    hand = result.scalar_one_or_none()
    if hand is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hand not found or not owned by you",
        )

    # TODO: implement real FGH staking via Solana program
    return {
        "hand_id": str(hand.id),
        "status": "staked",
        "message": "FGH stake locked successfully (stub)",
    }


@router.get("/hands/{hand_id}/review", response_model=ReviewStatusResponse)
async def get_review_status(
    hand_id: uuid.UUID,
    builder: Builder = Depends(require_builder),
    db: AsyncSession = Depends(get_db),
) -> ReviewStatusResponse:
    """Get the review status and feedback for a hand."""
    result = await db.execute(
        select(Hand).where(Hand.id == hand_id, Hand.author_id == builder.id)
    )
    hand = result.scalar_one_or_none()
    if hand is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hand not found or not owned by you",
        )

    # Get latest review
    review_result = await db.execute(
        select(HandReview)
        .where(HandReview.hand_id == hand.id)
        .order_by(HandReview.submitted_at.desc())
        .limit(1)
    )
    review = review_result.scalar_one_or_none()

    if review:
        return ReviewStatusResponse(
            hand_id=hand.id,
            review_id=review.id,
            status=review.status.value,
            submitted_at=review.submitted_at,
            reviewed_at=review.reviewed_at,
            reviewer_feedback=review.review_notes or review.rejection_reason,
        )

    return ReviewStatusResponse(
        hand_id=hand.id,
        status=hand.status.value,
        submitted_at=hand.created_at,
    )


@router.get("/me/earnings", response_model=EarningsResponse)
async def get_earnings(
    builder: Builder = Depends(require_builder),
    db: AsyncSession = Depends(get_db),
) -> EarningsResponse:
    """Get revenue and payout history."""
    # Total earnings
    total = await db.scalar(
        select(func.coalesce(func.sum(Payment.builder_amount_cents), 0)).where(
            Payment.builder_id == builder.id,
            Payment.status == "confirmed",
        )
    ) or 0

    # Paid out
    paid = await db.scalar(
        select(func.coalesce(func.sum(Payment.builder_amount_cents), 0)).where(
            Payment.builder_id == builder.id,
            Payment.payout_status == "paid",
        )
    ) or 0

    pending = total - paid

    return EarningsResponse(
        total_cents=total,
        pending_cents=pending,
        paid_cents=paid,
        monthly=[],  # TODO: aggregate monthly breakdown
    )


@router.post("/me/payout")
async def request_payout(
    body: PayoutRequest,
    builder: Builder = Depends(require_builder),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Request a manual payout to a USDC wallet."""
    # TODO: implement real payout logic
    # - Check pending balance >= amount
    # - Create payout record
    # - Queue USDC transfer
    return {
        "status": "pending",
        "amount_cents": body.amount_cents,
        "payout_usdc_address": body.payout_usdc_address,
        "message": "Payout request submitted (stub)",
    }
