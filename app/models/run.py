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
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SAEnum

from app.models.base import Base


class RunTier(str, enum.Enum):
    quick = "quick"
    deep = "deep"


class RunStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    hand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("hands.id"), nullable=False
    )
    activation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("activations.id"), nullable=True
    )
    tier: Mapped[RunTier] = mapped_column(
        SAEnum(RunTier, name="run_tier_enum"),
        default=RunTier.quick,
        server_default="quick",
    )
    status: Mapped[RunStatus] = mapped_column(
        SAEnum(RunStatus, name="run_status_enum"),
        default=RunStatus.queued,
        server_default="queued",
    )
    config: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default="{}"
    )
    delivery_channel: Mapped[str] = mapped_column(
        String(50), default="dashboard", server_default="dashboard"
    )
    delivery_target: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    openfang_run_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    openfang_agent_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    output_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_preview: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    payment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payments.id"), nullable=True
    )
    lamports_charged: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )
    fgh_used: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    discount_pct: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0"
    )
    queued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), server_default=func.now()
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), server_default=func.now()
    )

    # Relationships
    user = relationship("User", back_populates="runs", lazy="selectin")
    hand = relationship("Hand", lazy="selectin")
    activation = relationship("Activation", lazy="selectin")
