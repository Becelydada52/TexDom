from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.bot.deps import ALLOWED_ROLES, ensure_callback_role, ensure_message_role
from app.bot.keyboards.main import main_menu_kb
from app.services.users import UserService


logger = logging.getLogger(__name__)
router = Router(name="common")


def _menu_text(role: str) -> str:
    return f"Здравствуйте! Ваша роль: {role}\nВыберите действие ниже:"


def _command_args(message: Message) -> str:
    if not message.text:
        return ""
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return ""
    return parts[1].strip()


@router.message(Command("start"))
async def cmd_start(message: Message, user_service: UserService) -> None:
    role = await ensure_message_role(message, user_service, ALLOWED_ROLES)
    if role is None:
        return
    await message.answer(_menu_text(role), reply_markup=main_menu_kb(role))


@router.message(Command("id"))
async def cmd_id(message: Message, user_service: UserService) -> None:
    role = await user_service.get_role(message.chat.id)
    await message.answer(f"Ваш chat_id: {message.chat.id}\nВаша роль: {role}")


@router.message(Command("getid"))
async def cmd_getid(message: Message, user_service: UserService) -> None:
    role = await ensure_message_role(message, user_service, ("admin", "developer"), denied_text="Нет доступа.")
    if role is None:
        return

    raw = _command_args(message)
    if not raw:
        await message.answer("Использование: /getid @username")
        return

    username = raw.lstrip("@")
    try:
        user = await message.bot.get_chat(f"@{username}")
        await message.answer(f"ID пользователя @{username}: {user.id}")
    except Exception:
        logger.exception("Failed to resolve telegram username @%s", username)
        await message.answer(f"Не удалось найти @{username}. Проверьте username и попробуйте снова.")


@router.callback_query(F.data == "main_menu")
async def cb_main_menu(call: CallbackQuery, user_service: UserService) -> None:
    role = await ensure_callback_role(call, user_service, ALLOWED_ROLES)
    if role is None or call.message is None:
        return
    await call.answer()
    try:
        await call.message.edit_text(_menu_text(role), reply_markup=main_menu_kb(role))
    except TelegramBadRequest as exc:
        if "message is not modified" not in str(exc).lower():
            raise
