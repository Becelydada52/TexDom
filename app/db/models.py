from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SAEnum, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserRole(str, Enum):
    user = "user"
    admin = "admin"
    developer = "developer"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    telephone: Mapped[str] = mapped_column(String(32), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, default="Не указано")
    subject: Mapped[str] = mapped_column(String(255), nullable=False, default="Без темы")
    message: Mapped[str] = mapped_column(Text, nullable=False, default="Пустое сообщение")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="new")
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="web")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (Index("ix_orders_created_at", "created_at"),)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(nullable=False, unique=True, index=True)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, native_enum=False, length=16),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

