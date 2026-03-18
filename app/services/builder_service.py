import uuid

from fastapi import HTTPException, status
from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hand import Hand, HandStatus
from app.models.payment import Payment, PaymentStatus
from app.models.user import User


class BuilderService:
    """Manages builder registration, hand submissions, and earnings."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def register(self, user: User, data: dict) -> dict:
        """Register a user as a builder.

        Args:
            user: The user to register.
            data: Dict with builder profile fields (e.g. display_name, bio,
                  website, github_url, specializations).

        Returns:
            Builder info dict.

        Raises:
            HTTPException 409: If user is already a builder.
        """
        if user.is_builder:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already registered as a builder.",
            )

        user.is_builder = True

        # TODO: Create Builder record once the model is available
        # The Builder model should track:
        #   - id, user_id, display_name, bio, website, github_url,
        #   - specializations, revenue_share_pct, total_hands,
        #   - total_earnings_cents, verified, created_at
        #
        # from app.models.builder import Builder
        # builder = Builder(
        #     user_id=user.id,
        #     display_name=data.get("display_name", user.display_name),
        #     bio=data.get("bio", ""),
        #     website=data.get("website"),
        #     github_url=data.get("github_url"),
        #     specializations=data.get("specializations", []),
        # )
        # self.db.add(builder)

        await self.db.flush()
        await self.db.refresh(user)

        logger.info("Builder registered: user={}", user.id)
        return {
            "user_id": str(user.id),
            "is_builder": True,
            "display_name": data.get("display_name", user.display_name),
        }

    async def submit_hand(self, user: User, data: dict) -> Hand:
        """Submit a new Hand for review.

        Args:
            user: The builder submitting the hand.
            data: Dict with hand fields (name, slug, description, category,
                  tags, openfang_hand_slug, etc.).

        Returns:
            The newly created Hand in 'review' status.

        Raises:
            HTTPException 403: If user is not a builder.
            HTTPException 409: If slug is already taken.
        """
        if not user.is_builder:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be a registered builder to submit Hands.",
            )

        # Check slug uniqueness
        slug = data["slug"]
        existing = await self.db.execute(
            select(Hand).where(Hand.slug == slug)
        )
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Hand slug '{slug}' is already taken.",
            )

        hand = Hand(
            slug=slug,
            name=data["name"],
            description=data["description"],
            long_description=data.get("long_description"),
            type=data.get("type", "community"),
            status=HandStatus.review,
            category=data["category"],
            tags=data.get("tags", []),
            author_id=user.id,
            price_monthly_cents=data.get("price_monthly_cents"),
            price_quick_lamports=data.get("price_quick_lamports"),
            price_deep_lamports=data.get("price_deep_lamports"),
            openfang_hand_slug=data.get("openfang_hand_slug", slug),
            hand_toml_url=data.get("hand_toml_url"),
            skill_md_url=data.get("skill_md_url"),
            system_prompt_url=data.get("system_prompt_url"),
            min_openfang_version=data.get("min_openfang_version"),
            icon_emoji=data.get("icon_emoji"),
            cover_image_url=data.get("cover_image_url"),
            demo_video_url=data.get("demo_video_url"),
        )
        self.db.add(hand)

        # TODO: Increment builder.total_hands once Builder model exists
        # builder.total_hands = (builder.total_hands or 0) + 1

        await self.db.flush()
        await self.db.refresh(hand)

        logger.info(
            "Hand submitted: id={} slug={} by user={}",
            hand.id,
            hand.slug,
            user.id,
        )
        return hand

    async def get_earnings(self, builder_id: uuid.UUID) -> dict:
        """Get earnings summary for a builder.

        Args:
            builder_id: The builder's user ID.

        Returns:
            Dict with total, pending, and paid amounts.
        """
        # Query payments where builder_id matches
        result = await self.db.execute(
            select(
                func.coalesce(func.sum(Payment.builder_amount_cents), 0).label("total"),
                func.coalesce(
                    func.sum(
                        Payment.builder_amount_cents
                    ).filter(Payment.payout_status == "pending"),
                    0,
                ).label("pending"),
                func.coalesce(
                    func.sum(
                        Payment.builder_amount_cents
                    ).filter(Payment.payout_status == "paid"),
                    0,
                ).label("paid"),
            ).where(
                Payment.builder_id == builder_id,
                Payment.status == PaymentStatus.confirmed,
            )
        )
        row = result.one()

        earnings = {
            "builder_id": str(builder_id),
            "total_cents": row.total,
            "pending_cents": row.pending,
            "paid_cents": row.paid,
        }
        logger.debug("Builder earnings: {}", earnings)
        return earnings

    async def calculate_payout(self, builder_id: uuid.UUID) -> dict:
        """Calculate pending payout for a builder.

        Args:
            builder_id: The builder's user ID.

        Returns:
            Payout info dict.
        """
        # TODO: real payout calculation based on revenue share percentage
        # from the Builder model
        earnings = await self.get_earnings(builder_id)
        pending = earnings["pending_cents"]

        payout_info = {
            "builder_id": str(builder_id),
            "pending_amount_cents": pending,
            "revenue_share_pct": 70,  # TODO: read from Builder model
            "estimated_payout_cents": pending,  # Already builder's share
            "payout_ready": pending > 0,
        }
        logger.debug("Builder payout calculated: {}", payout_info)
        return payout_info
