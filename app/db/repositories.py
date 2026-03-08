from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Order, User, UserRole


class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, order: Order) -> Order:
        self.session.add(order)
        await self.session.commit()
        await self.session.refresh(order)
        return order

    async def get_by_id(self, order_id: str) -> Order | None:
        stmt = select(Order).where(Order.id == order_id)
        return await self.session.scalar(stmt)

    async def list_recent(self, limit: int = 10) -> list[Order]:
        stmt = select(Order).order_by(Order.created_at.desc()).limit(limit)
        result = await self.session.scalars(stmt)
        return list(result)

    async def list_all(self) -> list[Order]:
        stmt = select(Order).order_by(Order.created_at.asc())
        result = await self.session.scalars(stmt)
        return list(result)

    async def update_status(self, order_id: str, status: str) -> Order | None:
        order = await self.get_by_id(order_id)
        if order is None:
            return None
        order.status = status
        await self.session.commit()
        await self.session.refresh(order)
        return order

    async def delete(self, order_id: str) -> bool:
        order = await self.get_by_id(order_id)
        if order is None:
            return False
        await self.session.delete(order)
        await self.session.commit()
        return True

    async def exists(self, order_id: str) -> bool:
        return (await self.get_by_id(order_id)) is not None


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        stmt = select(User).where(User.telegram_id == telegram_id)
        return await self.session.scalar(stmt)

    async def list_by_roles(self, roles: Sequence[UserRole]) -> list[User]:
        stmt = select(User).where(User.role.in_(roles)).order_by(User.telegram_id.asc())
        result = await self.session.scalars(stmt)
        return list(result)

    async def upsert_role(self, telegram_id: int, role: UserRole) -> User:
        user = await self.get_by_telegram_id(telegram_id)
        if user is None:
            user = User(telegram_id=telegram_id, role=role)
            self.session.add(user)
        else:
            user.role = role
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def delete_user(self, telegram_id: int) -> bool:
        stmt = delete(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

