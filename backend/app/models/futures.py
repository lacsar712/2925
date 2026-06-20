import uuid
from datetime import datetime

from sqlalchemy import String, Numeric, Integer, DateTime, Enum, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class FuturesQuote(Base):
    __tablename__ = "futures_quotes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_code: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    contract_type: Mapped[str] = mapped_column(
        Enum("T", "TF", "TS", name="futures_type_enum"),
        nullable=False,
    )
    latest_price: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    settlement_price: Mapped[float] = mapped_column(Numeric(10, 4), nullable=True)
    open_price: Mapped[float] = mapped_column(Numeric(10, 4), nullable=True)
    high_price: Mapped[float] = mapped_column(Numeric(10, 4), nullable=True)
    low_price: Mapped[float] = mapped_column(Numeric(10, 4), nullable=True)
    prev_close: Mapped[float] = mapped_column(Numeric(10, 4), nullable=True)
    change_pct: Mapped[float] = mapped_column(Numeric(8, 4), nullable=True)
    volume: Mapped[int] = mapped_column(Integer, nullable=True)
    open_interest: Mapped[int] = mapped_column(Integer, nullable=True)
    basis: Mapped[float] = mapped_column(Numeric(8, 4), nullable=True)
    quote_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
