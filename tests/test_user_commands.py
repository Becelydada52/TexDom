from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.bot.keyboards.main import main_menu_kb
from app.bot.routers import users


class DummyBot:
    async def get_chat(self, username: str) -> SimpleNamespace:
        if username == "@known_user":
            return SimpleNamespace(id=424242)
        raise RuntimeError("user not found")


class DummyMessage:
    def __init__(self) -> None:
        self.bot = DummyBot()
        self.answers: list[tuple[str, object | None]] = []

    async def answer(self, text: str, reply_markup: object | None = None) -> None:
        self.answers.append((text, reply_markup))


class DummyCallback:
    def __init__(self) -> None:
        self.data = "users_menu"
        self.message = DummyMessage()
        self.from_user = SimpleNamespace(id=777)
        self.answers: list[tuple[str, bool]] = []

    async def answer(self, text: str = "", show_alert: bool = False) -> None:
        self.answers.append((text, show_alert))


class DummyUserService:
    async def get_role(self, telegram_id: int) -> str:
        return "admin"


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


def test_main_menu_shows_access_button_for_admin() -> None:
    keyboard = main_menu_kb("admin")
    callback_data = [button.callback_data for row in keyboard.inline_keyboard for button in row]

    assert "users_menu" in callback_data


@pytest.mark.asyncio
async def test_users_menu_callback_opens_keyboard() -> None:
    call = DummyCallback()

    await users.cb_users_menu(call, DummyUserService())

    assert call.answers[-1] == ("", False)
    assert call.message.answers
    assert "Управление доступом" in call.message.answers[-1][0]
