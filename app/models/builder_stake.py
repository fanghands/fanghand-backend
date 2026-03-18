import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
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


class StakeStatus(str, enum.Enum):
    locked = "locked"
    released = "released"
    slashed = "slashed"


class BuilderStake(Base):
    __tablename__ = "builder_stakes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    builder_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("builders.id"), nullable=False
    )
    hand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("hands.id"), nullable=False
    )
    status: Mapped[StakeStatus] = mapped_column(
        SAEnum(StakeStatus, name="stake_status_enum"),
        default=StakeStatus.locked,
        server_default="locked",
    )
    fgh_amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    usd_value_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    lock_tx_signature: Mapped[str | None] = mapped_column(
        String(90), nullable=True
    )
    release_tx_signature: Mapped[str | None] = mapped_column(
        String(90), nullable=True
    )
    slash_pct: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0"
    )
    slash_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    locked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), server_default=func.now()
    )
    release_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    released_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    slashed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    builder = relationship("Builder", lazy="selectin")
    hand = relationship("Hand", lazy="selectin")
