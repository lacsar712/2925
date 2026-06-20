import uuid
from datetime import datetime

from sqlalchemy import String, Enum, Numeric, DateTime, Boolean, ForeignKey, func, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PriceAlertRule(Base):
    __tablename__ = "price_alert_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False)
    bond_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("bonds.id"), index=True, nullable=False)
    alert_type: Mapped[str] = mapped_column(
        Enum("yield", "net_price", name="alert_type_enum"),
        nullable=False,
        comment="预警类型：yield=收益率，net_price=净价",
    )
    condition: Mapped[str] = mapped_column(
        Enum("above", "below", name="alert_condition_enum"),
        nullable=False,
        comment="触发条件：above=高于阈值，below=低于阈值",
    )
    threshold: Mapped[float] = mapped_column(Numeric(12, 6), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    last_triggered_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    trigger_cooldown_minutes: Mapped[int] = mapped_column(Integer, default=5, nullable=False, comment="冷却时间（分钟），避免重复触发")
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    bond = relationship("Bond", lazy="selectin")
    triggers = relationship("PriceAlertTrigger", back_populates="rule", lazy="selectin", cascade="all, delete-orphan")


class PriceAlertTrigger(Base):
    __tablename__ = "price_alert_triggers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("price_alert_rules.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False)
    bond_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("bonds.id"), index=True, nullable=False)
    alert_type: Mapped[str] = mapped_column(
        Enum("yield", "net_price", name="trigger_alert_type_enum"),
        nullable=False,
    )
    condition: Mapped[str] = mapped_column(
        Enum("above", "below", name="trigger_condition_enum"),
        nullable=False,
    )
    threshold: Mapped[float] = mapped_column(Numeric(12, 6), nullable=False)
    actual_value: Mapped[float] = mapped_column(Numeric(12, 6), nullable=False, comment="触发时的实际值")
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

    rule = relationship("PriceAlertRule", back_populates="triggers")
    bond = relationship("Bond", lazy="selectin")
