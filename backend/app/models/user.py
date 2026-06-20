import uuid
from datetime import datetime

from sqlalchemy import String, Boolean, DateTime, Enum, ForeignKey, UniqueConstraint, func, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(50), nullable=False)
    role: Mapped[str] = mapped_column(
        Enum("admin", "trader", "viewer", name="user_role_enum"),
        default="trader",
    )
    department: Mapped[str] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    watchlist_groups: Mapped[list["WatchlistGroup"]] = relationship(
        "WatchlistGroup", back_populates="user", cascade="all, delete-orphan"
    )

    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", back_populates="user"
    )


class UserFavorite(Base):
    __tablename__ = "user_favorites"
    __table_args__ = (UniqueConstraint("user_id", "bond_id", name="uq_user_bond"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    bond_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("bonds.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class WatchlistGroup(Base):
    __tablename__ = "watchlist_groups"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_user_group_name"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship("User", back_populates="watchlist_groups")
    bonds: Mapped[list["WatchlistGroupBond"]] = relationship(
        "WatchlistGroupBond", back_populates="group", cascade="all, delete-orphan", order_by="WatchlistGroupBond.order_index"
    )


class WatchlistGroupBond(Base):
    __tablename__ = "watchlist_group_bonds"
    __table_args__ = (UniqueConstraint("group_id", "bond_id", name="uq_group_bond"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("watchlist_groups.id", ondelete="CASCADE"), index=True)
    bond_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("bonds.id"), index=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    group: Mapped["WatchlistGroup"] = relationship("WatchlistGroup", back_populates="bonds")
