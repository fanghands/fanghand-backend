import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    String,
    Text,
    ForeignKey,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SAEnum

from app.models.base import Base


class PaymentType(str, enum.Enum):
    subscription = "subscription"
    pay_per_run = "pay_per_run"
    builder_stake = "builder_stake"
    refund = "refund"


class PaymentStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    failed = "failed"
    refunded = "refunded"


class PaymentCurrencyType(str, enum.Enum):
    usd = "usd"
    usdc = "usdc"
    sol = "sol"
    fgh = "fgh"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    type: Mapped[PaymentType] = mapped_column(
        SAEnum(PaymentType, name="payment_type_enum"), nullable=False
    )
    status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(PaymentStatus, name="payment_status_enum"),
        default=PaymentStatus.pending,
        server_default="pending",
    )
    currency: Mapped[PaymentCurrencyType] = mapped_column(
        SAEnum(PaymentCurrencyType, name="payment_currency_type_enum"),
        nullable=False,
    )
    amount_cents: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )
    amount_lamports: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )
    amount_fgh: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )
    usd_equivalent_cents: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )
    hand_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("hands.id"), nullable=True
    )
    activation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("activations.id"), nullable=True
    )
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("runs.id"), nullable=True
    )
    stripe_payment_intent_id: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )
    stripe_subscription_id: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )
    stripe_invoice_id: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )
    solana_tx_signature: Mapped[str | None] = mapped_column(
        String(90), nullable=True
    )
    solana_confirmed_slot: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )
    fgh_burned_amount: Mapped[int] = mapped_column(
        BigInteger, default=0, server_default="0"
    )
    burn_tx_signature: Mapped[str | None] = mapped_column(
        String(90), nullable=True
    )
    builder_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    builder_amount_cents: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )
    platform_amount_cents: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )
    payout_status: Mapped[str] = mapped_column(
        String(20), default="pending", server_default="pending"
    )
    payout_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONB, default=dict, server_default="{}"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), server_default=func.now()
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    user = relationship(
        "User",
        back_populates="payments",
        foreign_keys=[user_id],
        lazy="selectin",
    )
    hand = relationship("Hand", lazy="selectin")
