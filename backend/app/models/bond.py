import uuid
from datetime import date, datetime

from sqlalchemy import String, Enum, Date, Numeric, DateTime, Text, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Bond(Base):
    __tablename__ = "bonds"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=True)
    bond_type: Mapped[str] = mapped_column(
        Enum("国债", "政金债", "企业债", "公司债", "可转债", "地方债", "同业存单", name="bond_type_enum"),
        nullable=False,
    )
    issuer: Mapped[str] = mapped_column(String(200), nullable=False)
    issue_date: Mapped[date] = mapped_column(Date, nullable=True)
    maturity_date: Mapped[date] = mapped_column(Date, nullable=True)
    coupon_rate: Mapped[float] = mapped_column(Numeric(8, 4), nullable=True)
    coupon_type: Mapped[str] = mapped_column(
        Enum("固定利率", "浮动利率", "零息", "贴现", name="coupon_type_enum"),
        nullable=True,
    )
    face_value: Mapped[float] = mapped_column(Numeric(15, 2), default=100.0)
    credit_rating: Mapped[str] = mapped_column(String(10), nullable=True)
    remaining_term: Mapped[float] = mapped_column(Numeric(8, 4), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    quotes = relationship("Quote", back_populates="bond", lazy="selectin")
    trades = relationship("Trade", back_populates="bond", lazy="selectin")
    swap_quotes = relationship("SwapQuote", back_populates="bond", lazy="selectin")


class MarketSource(Base):
    __tablename__ = "market_sources"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    source_type: Mapped[str] = mapped_column(
        Enum("xbond", "broker", "exchange", "swap", "futures", name="source_type_enum"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Enum("online", "offline", "error", name="source_status_enum"),
        default="online",
    )
    description: Mapped[str] = mapped_column(Text, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    quotes = relationship("Quote", back_populates="source", lazy="selectin")
    trades = relationship("Trade", back_populates="source", lazy="selectin")
