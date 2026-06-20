import uuid
from datetime import datetime

from sqlalchemy import String, Numeric, DateTime, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SwapQuote(Base):
    __tablename__ = "swap_quotes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bond_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("bonds.id"), index=True)
    dealer: Mapped[str] = mapped_column(String(100), nullable=False)
    swap_rate: Mapped[float] = mapped_column(Numeric(8, 4), nullable=False)
    tenor: Mapped[str] = mapped_column(String(20), nullable=False)
    direction: Mapped[str] = mapped_column(
        Enum("pay_fixed", "receive_fixed", name="swap_direction_enum"),
        nullable=False,
    )
    notional_min: Mapped[float] = mapped_column(Numeric(18, 2), nullable=True)
    quote_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

    bond = relationship("Bond", back_populates="swap_quotes")
