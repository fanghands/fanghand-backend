"""Hand catalogue routes: listing, detail, user reviews."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
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


async def _paginated_hands(db, stmt, cursor, limit) -> CursorPage[HandListItem]:
    """Execute a query and return a CursorPage with frontend-compatible items."""
    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = _apply_cursor(stmt, cursor)
    stmt = stmt.limit(limit + 1)

    result = await db.execute(stmt)
    rows = list(result.scalars().all())
    has_more = len(rows) > limit
    items = rows[:limit]

    return CursorPage(
        data=[HandListItem.from_hand(h) for h in items],
        next_cursor=str(items[-1].id) if has_more and items else None,
        total=total,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/official")
async def list_official_hands(
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List only official hands."""
    stmt = (
        select(Hand)
        .where(Hand.type == HandType.official, Hand.status == HandStatus.live)
        .order_by(Hand.total_activations.desc(), Hand.id.desc())
    )
    return await _paginated_hands(db, stmt, cursor, limit)


@router.get("/community")
async def list_community_hands(
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List only community hands."""
    stmt = (
        select(Hand)
        .where(Hand.type == HandType.community, Hand.status == HandStatus.live)
        .order_by(Hand.total_activations.desc(), Hand.id.desc())
    )
    return await _paginated_hands(db, stmt, cursor, limit)


@router.get("/{slug}")
async def get_hand(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    """Get hand detail by slug."""
    result = await db.execute(select(Hand).where(Hand.slug == slug))
    hand = result.scalar_one_or_none()
    if hand is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hand not found",
        )
    return HandDetail.from_hand(hand)


@router.get("/{slug}/reviews")
async def get_hand_reviews(
    slug: str,
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List user reviews for a hand."""
    hand_result = await db.execute(select(Hand).where(Hand.slug == slug))
    hand = hand_result.scalar_one_or_none()
    if hand is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hand not found",
        )
    return CursorPage(data=[], next_cursor=None, total=0)


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


@router.get("")
async def list_hands(
    type: str | None = Query(None, pattern="^(all|official|community)$"),
    category: str | None = Query(None),
    hand_status: str = Query("live", alias="status"),
    sort: str = Query("popular", pattern="^(popular|new|price_asc|price_desc|rating)$"),
    search: str | None = Query(None, max_length=200),
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List hands with filtering, search, and cursor pagination."""
    stmt = select(Hand)

    # Type filter
    if type and type != "all":
        stmt = stmt.where(Hand.type == type)

    # Status filter — accept "all" to skip, accept frontend values
    status_map = {"active": "live", "pending": "review", "deprecated": "deprecated"}
    resolved_status = status_map.get(hand_status, hand_status)
    if resolved_status != "all":
        try:
            status_enum = HandStatus(resolved_status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {hand_status}",
            )
        stmt = stmt.where(Hand.status == status_enum)

    # Category filter — accept "all", "official", "community" as special values
    if category and category not in ("all", "official", "community", "free"):
        try:
            cat_enum = HandCategory(category)
            stmt = stmt.where(Hand.category == cat_enum)
        except ValueError:
            pass  # ignore unknown categories gracefully
    elif category == "official":
        stmt = stmt.where(Hand.type == HandType.official)
    elif category == "community":
        stmt = stmt.where(Hand.type == HandType.community)
    elif category == "free":
        stmt = stmt.where(Hand.price_monthly_cents.is_(None))

    # Full-text search
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

    return await _paginated_hands(db, stmt, cursor, limit)
