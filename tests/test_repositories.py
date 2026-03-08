from __future__ import annotations

from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.models import Order, UserRole
from app.db.repositories import OrderRepository, UserRepository


@pytest.mark.asyncio
async def test_order_repository_crud(tmp_path) -> None:
    db_path = tmp_path / "repo_orders.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        repo = OrderRepository(session)
        order = Order(
            id="test-order-1",
            name="Name",
            telephone="+79991234567",
            email="mail@example.com",
            subject="Subj",
            message="Body",
            status="new",
            source="test",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        await repo.create(order)

        loaded = await repo.get_by_id("test-order-1")
        assert loaded is not None
        assert loaded.telephone == "+79991234567"

        updated = await repo.update_status("test-order-1", "done")
        assert updated is not None
        assert updated.status == "done"

        deleted = await repo.delete("test-order-1")
        assert deleted is True
        assert await repo.get_by_id("test-order-1") is None

    await engine.dispose()


@pytest.mark.asyncio
async def test_user_repository_upsert_and_delete(tmp_path) -> None:
    db_path = tmp_path / "repo_users.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        repo = UserRepository(session)
        user = await repo.upsert_role(123, UserRole.user)
        assert user.telegram_id == 123
        assert user.role == UserRole.user

        user = await repo.upsert_role(123, UserRole.developer)
        assert user.role == UserRole.developer

        deleted = await repo.delete_user(123)
        assert deleted is True

    await engine.dispose()

