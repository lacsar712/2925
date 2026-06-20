import uuid
from datetime import datetime

from sqlalchemy import Numeric, String, DateTime, Boolean, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Quote(Base):
    __tablename__ = "quotes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bond_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("bonds.id"), index=True)
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("market_sources.id"), index=True)
    bid_price: Mapped[float] = mapped_column(Numeric(10, 4), nullable=True)
    ask_price: Mapped[float] = mapped_column(Numeric(10, 4), nullable=True)
    bid_yield: Mapped[float] = mapped_column(Numeric(8, 4), nullable=True)
    ask_yield: Mapped[float] = mapped_column(Numeric(8, 4), nullable=True)
    bid_volume: Mapped[float] = mapped_column(Numeric(15, 2), nullable=True)
    ask_volume: Mapped[float] = mapped_column(Numeric(15, 2), nullable=True)
    counterparty: Mapped[str] = mapped_column(String(100), nullable=True)
    quote_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
    is_best: Mapped[bool] = mapped_column(Boolean, default=False)

    bond = relationship("Bond", back_populates="quotes")
    source = relationship("MarketSource", back_populates="quotes")
