from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Order
from app.db.repositories import OrderRepository
from app.schemas.feedback import FeedbackPayload


class OrderService:
    def __init__(self, session_factory: Callable[[], AsyncSession]) -> None:
        self.session_factory = session_factory

    async def create_from_feedback(self, payload: FeedbackPayload, source: str = "web") -> Order:
        async with self.session_factory() as session:
            repo = OrderRepository(session)
            order = Order(
                id=uuid.uuid4().hex[:12],
                name=payload.name,
                telephone=payload.telephone,
                email=payload.email,
                subject=payload.subject,
                message=payload.message,
                status="new",
                source=source,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            return await repo.create(order)

    async def list_recent_orders(self, limit: int = 10) -> list[Order]:
        async with self.session_factory() as session:
            repo = OrderRepository(session)
            return await repo.list_recent(limit)

    async def list_orders(self) -> list[Order]:
        async with self.session_factory() as session:
            repo = OrderRepository(session)
            return await repo.list_all()

    async def get_order(self, order_id: str) -> Order | None:
        async with self.session_factory() as session:
            repo = OrderRepository(session)
            return await repo.get_by_id(order_id)

    async def update_order_status(self, order_id: str, status: str) -> Order | None:
        async with self.session_factory() as session:
            repo = OrderRepository(session)
            return await repo.update_status(order_id, status)

    async def delete_order(self, order_id: str) -> bool:
        async with self.session_factory() as session:
            repo = OrderRepository(session)
            return await repo.delete(order_id)

    async def order_exists(self, order_id: str) -> bool:
        async with self.session_factory() as session:
            repo = OrderRepository(session)
            return await repo.exists(order_id)

