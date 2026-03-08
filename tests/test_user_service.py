from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.services.users import UserService


@pytest.mark.asyncio
async def test_user_service_role_priority(tmp_path) -> None:
    db_path = tmp_path / "service_users.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    service = UserService(session_factory)
    await service.upsert_role(77, "user")
    await service.upsert_role(77, "admin", keep_higher_role=True)
    assert await service.get_role(77) == "admin"
    await service.upsert_role(77, "user", keep_higher_role=True)
    assert await service.get_role(77) == "admin"

    await engine.dispose()


@pytest.mark.asyncio
async def test_user_service_lists_notification_recipients(tmp_path) -> None:
    db_path = tmp_path / "service_notifications.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    service = UserService(session_factory)
    await service.upsert_role(11, "user")
    await service.upsert_role(22, "admin")
    await service.upsert_role(33, "developer")

    recipients = await service.list_ids_by_roles(("admin", "developer"))

    assert recipients == [22, 33]

    await engine.dispose()
