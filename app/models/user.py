import uuid
from typing import TYPE_CHECKING, List

from sqlalchemy import BigInteger, Boolean, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.activation import Activation
    from app.models.payment import Payment
    from app.models.run import Run


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    username: Mapped[str | None] = mapped_column(
        String(50), unique=True, nullable=True
    )
    display_name: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    wallet_address: Mapped[str] = mapped_column(
        String(44), unique=True, nullable=False
    )
    fgh_balance_cache: Mapped[int] = mapped_column(
        BigInteger, default=0, server_default="0"
    )
    credit_balance_lamports: Mapped[int] = mapped_column(
        BigInteger, default=0, server_default="0"
    )
    stripe_customer_id: Mapped[str | None] = mapped_column(
        String(50), unique=True, nullable=True
    )
    is_builder: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )

    # Relationships
    activations: Mapped[List["Activation"]] = relationship(
        back_populates="user", lazy="selectin"
    )
    runs: Mapped[List["Run"]] = relationship(
        back_populates="user", lazy="selectin"
    )
    payments: Mapped[List["Payment"]] = relationship(
        back_populates="user",
        lazy="selectin",
        foreign_keys="Payment.user_id",
    )
