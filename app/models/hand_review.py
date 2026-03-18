import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SAEnum

from app.models.base import Base


class ReviewStatus(str, enum.Enum):
    pending = "pending"
    in_review = "in_review"
    approved = "approved"
    rejected = "rejected"
    revision_requested = "revision_requested"


class HandReview(Base):
    __tablename__ = "hand_reviews"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    hand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("hands.id"), nullable=False
    )
    builder_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("builders.id"), nullable=False
    )
    status: Mapped[ReviewStatus] = mapped_column(
        SAEnum(ReviewStatus, name="review_status_enum"),
        default=ReviewStatus.pending,
        server_default="pending",
    )
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    submission_notes: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    auto_passed: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True
    )
    auto_errors: Mapped[dict] = mapped_column(
        JSONB, default=list, server_default="[]"
    )
    security_passed: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True
    )
    functional_passed: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), server_default=func.now()
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    hand = relationship("Hand", lazy="selectin")
    builder = relationship("Builder", lazy="selectin")
    reviewer = relationship("User", lazy="selectin")
