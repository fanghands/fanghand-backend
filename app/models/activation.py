import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SAEnum, func

from app.models.base import Base, TimestampMixin


class ActivationStatus(str, enum.Enum):
    active = "active"
    paused = "paused"
    cancelled = "cancelled"
    expired = "expired"


class PaymentCurrency(str, enum.Enum):
    usd = "usd"
    usdc = "usdc"
    sol = "sol"
    fgh = "fgh"


class Activation(TimestampMixin, Base):
    __tablename__ = "activations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    hand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("hands.id"), nullable=False
    )
    status: Mapped[ActivationStatus] = mapped_column(
        SAEnum(ActivationStatus, name="activation_status_enum"),
        default=ActivationStatus.active,
        server_default="active",
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
    openfang_agent_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    payment_currency: Mapped[PaymentCurrency] = mapped_column(
        SAEnum(PaymentCurrency, name="payment_currency_enum"),
        default=PaymentCurrency.usd,
        server_default="usd",
    )
    stripe_subscription_id: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )
    current_period_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    discount_pct: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0"
    )
    activated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), server_default=func.now()
    )
    paused_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    user = relationship("User", back_populates="activations", lazy="selectin")
    hand = relationship("Hand", lazy="selectin")
