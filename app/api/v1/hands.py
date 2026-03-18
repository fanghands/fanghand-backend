"""Hand catalogue routes: listing, detail, user reviews."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.hand import Hand, HandCategory, HandStatus, HandType
from app.models.user import User
from app.schemas.common import CursorPage
from app.schemas.hand import (
    HandDetail,
    HandListItem,
    UserReviewCreate,
    UserReviewResponse,
)

router = APIRouter(prefix="/hands", tags=["hands"])

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SORT_MAP = {
    "popular": Hand.total_activations.desc(),
    "new": Hand.published_at.desc().nulls_last(),
    "price_asc": Hand.price_monthly_cents.asc().nulls_last(),
    "price_desc": Hand.price_monthly_cents.desc().nulls_last(),
    "rating": Hand.avg_rating.desc(),
}


def _apply_cursor(stmt, cursor: str | None):
    """Apply cursor-based pagination (by UUID pk ordering)."""
    if cursor:
        try:
            cursor_id = uuid.UUID(cursor)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid cursor",
            )
        stmt = stmt.where(Hand.id < cursor_id)
    return stmt


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/official", response_model=CursorPage[HandListItem])
async def list_official_hands(
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> CursorPage[HandListItem]:
    """List only official hands."""
    stmt = (
        select(Hand)
        .where(Hand.type == HandType.official, Hand.status == HandStatus.live)
        .order_by(Hand.total_activations.desc(), Hand.id.desc())
    )
    stmt = _apply_cursor(stmt, cursor)
    stmt = stmt.limit(limit + 1)

    result = await db.execute(stmt)
    rows = list(result.scalars().all())
    has_more = len(rows) > limit
    items = rows[:limit]

    return CursorPage(
        items=[HandListItem.model_validate(h) for h in items],
        next_cursor=str(items[-1].id) if has_more and items else None,
        has_more=has_more,
    )


@router.get("/community", response_model=CursorPage[HandListItem])
async def list_community_hands(
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> CursorPage[HandListItem]:
    """List only community hands."""
    stmt = (
        select(Hand)
        .where(Hand.type == HandType.community, Hand.status == HandStatus.live)
        .order_by(Hand.total_activations.desc(), Hand.id.desc())
    )
    stmt = _apply_cursor(stmt, cursor)
    stmt = stmt.limit(limit + 1)

    result = await db.execute(stmt)
    rows = list(result.scalars().all())
    has_more = len(rows) > limit
    items = rows[:limit]

    return CursorPage(
        items=[HandListItem.model_validate(h) for h in items],
        next_cursor=str(items[-1].id) if has_more and items else None,
        has_more=has_more,
    )


@router.get("/{slug}", response_model=HandDetail)
async def get_hand(
    slug: str,
    db: AsyncSession = Depends(get_db),
) -> HandDetail:
    """Get hand detail by slug."""
    result = await db.execute(select(Hand).where(Hand.slug == slug))
    hand = result.scalar_one_or_none()
    if hand is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hand not found",
        )
    return HandDetail.model_validate(hand)


@router.get("/{slug}/reviews", response_model=CursorPage[UserReviewResponse])
async def get_hand_reviews(
    slug: str,
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> CursorPage[UserReviewResponse]:
    """List user reviews for a hand."""
    hand_result = await db.execute(select(Hand).where(Hand.slug == slug))
    hand = hand_result.scalar_one_or_none()
    if hand is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hand not found",
        )

    # TODO: query UserReview model once it is created
    # There is currently no user review model; return empty for now.
    return CursorPage(items=[], next_cursor=None, has_more=False)


@router.post(
    "/{slug}/review",
    response_model=UserReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_review(
    slug: str,
    body: UserReviewCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserReviewResponse:
    """Submit a user review for a hand."""
    hand_result = await db.execute(select(Hand).where(Hand.slug == slug))
    hand = hand_result.scalar_one_or_none()
    if hand is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hand not found",
        )

    # TODO: persist to UserReview table once model exists
    # TODO: check if user already reviewed (return 409)

    # Update hand aggregate stats
    new_count = hand.review_count + 1
    new_avg = ((float(hand.avg_rating) * hand.review_count) + body.rating) / new_count
    hand.review_count = new_count
    hand.avg_rating = round(new_avg, 2)
    await db.flush()

    return UserReviewResponse(
        id=uuid.uuid4(),
        user_address=user.wallet_address,
        rating=body.rating,
        comment=body.comment,
        created_at=datetime.now(timezone.utc),
    )


@router.get("", response_model=CursorPage[HandListItem])
async def list_hands(
    type: str | None = Query(None, pattern="^(all|official|community)$"),
    category: str | None = Query(None),
    hand_status: str = Query("live", alias="status"),
    sort: str = Query("popular", pattern="^(popular|new|price_asc|price_desc|rating)$"),
    search: str | None = Query(None, max_length=200),
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> CursorPage[HandListItem]:
    """List hands with filtering, search, and cursor pagination."""
    stmt = select(Hand)

    # Type filter
    if type and type != "all":
        stmt = stmt.where(Hand.type == type)

    # Status filter
    try:
        status_enum = HandStatus(hand_status)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status: {hand_status}",
        )
    stmt = stmt.where(Hand.status == status_enum)

    # Category filter
    if category:
        try:
            cat_enum = HandCategory(category)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category: {category}",
            )
        stmt = stmt.where(Hand.category == cat_enum)

    # Full-text search (ILIKE on name + description)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                Hand.name.ilike(pattern),
                Hand.description.ilike(pattern),
            )
        )

    # Sort
    order_clause = SORT_MAP.get(sort, Hand.total_activations.desc())
    stmt = stmt.order_by(order_clause, Hand.id.desc())

    # Cursor pagination
    stmt = _apply_cursor(stmt, cursor)
    stmt = stmt.limit(limit + 1)

    result = await db.execute(stmt)
    rows = list(result.scalars().all())
    has_more = len(rows) > limit
    items = rows[:limit]

    return CursorPage(
        items=[HandListItem.model_validate(h) for h in items],
        next_cursor=str(items[-1].id) if has_more and items else None,
        has_more=has_more,
    )
