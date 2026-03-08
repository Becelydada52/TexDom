from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.bot.routers import users


class DummyBot:
    async def get_chat(self, username: str) -> SimpleNamespace:
        if username == "@known_user":
            return SimpleNamespace(id=424242)
        raise RuntimeError("user not found")


class DummyMessage:
    def __init__(self) -> None:
        self.bot = DummyBot()


@pytest.mark.asyncio
async def test_resolve_target_accepts_user_id() -> None:
    resolved = await users._resolve_target("123456", DummyMessage())

    assert resolved == (123456, "123456")


@pytest.mark.asyncio
async def test_resolve_target_accepts_username() -> None:
    resolved = await users._resolve_target("@known_user", DummyMessage())

    assert resolved == (424242, "@known_user")


def test_admin_cannot_manage_developer_role() -> None:
    assert users._can_manage_role("admin", "developer") is False
    assert users._can_manage_role("developer", "developer") is True
