import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class FghBurn(Base):
    __tablename__ = "fgh_burns"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    trigger_type: Mapped[str] = mapped_column(String(50), nullable=False)
    payment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payments.id"), nullable=True
    )
    stake_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("builder_stakes.id"), nullable=True
    )
    fgh_burned: Mapped[int] = mapped_column(BigInteger, nullable=False)
    usd_equivalent: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    tx_signature: Mapped[str] = mapped_column(String(90), nullable=False)
    confirmed_slot: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )
    burned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), server_default=func.now()
    )

    # Relationships
    payment = relationship("Payment", lazy="selectin")
    stake = relationship("BuilderStake", lazy="selectin")
