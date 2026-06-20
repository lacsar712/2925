import uuid
from datetime import datetime

from sqlalchemy import Numeric, String, DateTime, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bond_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("bonds.id"), index=True)
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("market_sources.id"), index=True)
    price: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    yield_rate: Mapped[float] = mapped_column(Numeric(8, 4), nullable=True)
    volume: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=True)
    direction: Mapped[str] = mapped_column(
        Enum("buy", "sell", name="trade_direction_enum"),
        nullable=False,
    )
    counterparty: Mapped[str] = mapped_column(String(100), nullable=True)
    trade_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

    bond = relationship("Bond", back_populates="trades")
    source = relationship("MarketSource", back_populates="trades")
