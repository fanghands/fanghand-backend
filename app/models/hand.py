import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    BigInteger,
    DateTime,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SAEnum, ForeignKey

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class HandType(str, enum.Enum):
    official = "official"
    community = "community"


class HandStatus(str, enum.Enum):
    draft = "draft"
    review = "review"
    approved = "approved"
    live = "live"
    suspended = "suspended"
    deprecated = "deprecated"


class HandCategory(str, enum.Enum):
    intelligence = "intelligence"
    research = "research"
    growth = "growth"
    social = "social"
    content = "content"
    automation = "automation"
    finance = "finance"
    custom = "custom"


class Hand(TimestampMixin, Base):
    __tablename__ = "hands"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    slug: Mapped[str] = mapped_column(
        String(80), unique=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    long_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    type: Mapped[HandType] = mapped_column(
        SAEnum(HandType, name="hand_type_enum"),
        default=HandType.community,
        server_default="community",
    )
    status: Mapped[HandStatus] = mapped_column(
        SAEnum(HandStatus, name="hand_status_enum"),
        default=HandStatus.draft,
        server_default="draft",
    )
    category: Mapped[HandCategory] = mapped_column(
        SAEnum(HandCategory, name="hand_category_enum"),
        nullable=False,
    )
    tags: Mapped[list] = mapped_column(
        ARRAY(String), default=list, server_default="{}"
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    price_monthly_cents: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    price_quick_lamports: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )
    price_deep_lamports: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )
    free_trial_runs: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0"
    )
    stripe_price_monthly: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )
    openfang_hand_slug: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    hand_toml_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    skill_md_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    system_prompt_url: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    min_openfang_version: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )
    total_activations: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0"
    )
    total_runs: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0"
    )
    avg_rating: Mapped[float] = mapped_column(
        Numeric(3, 2), default=0, server_default="0"
    )
    review_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0"
    )
    icon_emoji: Mapped[str | None] = mapped_column(
        String(10), nullable=True
    )
    cover_image_url: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    demo_video_url: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    version: Mapped[str] = mapped_column(
        String(20), default="0.1.0", server_default="0.1.0"
    )
    changelog: Mapped[dict] = mapped_column(
        JSONB, default=list, server_default="[]"
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    author: Mapped["User"] = relationship(lazy="selectin")
