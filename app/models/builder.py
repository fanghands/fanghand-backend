import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Integer,
    String,
    Text,
    ForeignKey,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SAEnum

from app.models.base import Base


class BuilderTier(str, enum.Enum):
    standard = "standard"
    verified = "verified"
    elite = "elite"


class Builder(Base):
    __tablename__ = "builders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        primary_key=True,
    )
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    twitter_handle: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )
    github_handle: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )
    tier: Mapped[BuilderTier] = mapped_column(
        SAEnum(BuilderTier, name="builder_tier_enum"),
        default=BuilderTier.standard,
        server_default="standard",
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    total_hands: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0"
    )
    total_activations: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0"
    )
    total_revenue_cents: Mapped[int] = mapped_column(
        BigInteger, default=0, server_default="0"
    )
    revenue_share_pct: Mapped[int] = mapped_column(
        Integer, default=80, server_default="80"
    )
    first_cohort: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    first_cohort_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    payout_usdc_address: Mapped[str | None] = mapped_column(
        String(44), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), server_default=func.now()
    )

    # Relationships
    user = relationship("User", lazy="selectin")
