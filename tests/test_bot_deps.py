from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.bot.deps import ensure_callback_role


class DummyUserService:
    def __init__(self, roles: dict[int, str]) -> None:
        self.roles = roles

    async def get_role(self, telegram_id: int) -> str:
        return self.roles.get(telegram_id, "guest")


class DummyCallback:
    def __init__(self, *, chat_id: int | None, from_user_id: int | None) -> None:
        self.message = None if chat_id is None else SimpleNamespace(chat=SimpleNamespace(id=chat_id))
        self.from_user = None if from_user_id is None else SimpleNamespace(id=from_user_id)
        self.answers: list[tuple[str, bool]] = []

    async def answer(self, text: str, show_alert: bool = False) -> None:
        self.answers.append((text, show_alert))


@pytest.mark.asyncio
async def test_ensure_callback_role_uses_from_user_id() -> None:
    call = DummyCallback(chat_id=111, from_user_id=777)
    user_service = DummyUserService({777: "admin", 111: "guest"})

    role = await ensure_callback_role(call, user_service, ("admin", "developer"))

    assert role == "admin"


@pytest.mark.asyncio
async def test_ensure_callback_role_without_from_user() -> None:
    call = DummyCallback(chat_id=111, from_user_id=None)
    user_service = DummyUserService({111: "admin"})

    role = await ensure_callback_role(call, user_service, ("admin",))

    assert role is None
    assert call.answers
    assert call.answers[-1][0] == "Пользователь не определён"
    assert call.answers[-1][1] is True
