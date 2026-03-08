from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.bot.deps import ensure_callback_role, ensure_message_role
from app.bot.keyboards.logs import logs_kb
from app.container import settings
from app.services.users import UserService


logger = logging.getLogger(__name__)
router = Router(name="admin")

LOGS_PAGE_SIZE = 30
LOGS_READ_CHUNK_SIZE = 4096


def _command_args(message: Message) -> list[str]:
    if not message.text:
        return []
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return []
    return parts[1].strip().split()


def _parse_logs_offset(data: str | None) -> int | None:
    raw_value = (data or "logs_more:0").split(":", maxsplit=1)[-1]
    try:
        offset = int(raw_value)
    except (TypeError, ValueError):
        return None
    if offset < 0:
        return None
    return offset


def _read_log_page(path: Path, offset: int, page_size: int = LOGS_PAGE_SIZE) -> list[str]:
    if offset < 0:
        raise ValueError("offset must be non-negative")

    required_lines = offset + page_size
    chunks: list[bytes] = []

    with path.open("rb") as file_obj:
        file_obj.seek(0, os.SEEK_END)
        position = file_obj.tell()
        newline_count = 0

        while position > 0 and newline_count <= required_lines:
            read_size = min(LOGS_READ_CHUNK_SIZE, position)
            position -= read_size
            file_obj.seek(position)
            chunk = file_obj.read(read_size)
            chunks.append(chunk)
            newline_count += chunk.count(b"\n")

    content = b"".join(reversed(chunks)).decode("utf-8", errors="ignore")
    lines = content.splitlines(keepends=True)
    return lines[-required_lines : -offset if offset else None]


async def _send_logs(bot_message: Message, offset: int) -> None:
    path = Path(settings.bot_log_path)
    if not path.exists():
        await bot_message.answer("📜 Лог-файл не найден.")
        return

    lines = await asyncio.to_thread(_read_log_page, path, offset)
    if not lines:
        await bot_message.answer("📜 Больше логов нет.")
        return

    text = "Последние логи:\n\n" + "".join(lines)
    await bot_message.answer(text[-4000:], reply_markup=logs_kb(offset + LOGS_PAGE_SIZE))


@router.message(Command("grant"))
async def cmd_grant(message: Message, user_service: UserService) -> None:
    role = await ensure_message_role(message, user_service, ("developer",), denied_text="Нет доступа.")
    if role is None:
        return

    args = _command_args(message)
    if len(args) != 2:
        await message.answer("Использование: /grant <user_id> <role>")
        return

    uid_raw, target_role = args
    if not uid_raw.lstrip("-").isdigit():
        await message.answer("user_id должен быть числом")
        return
    target_role = target_role.lower()
    if target_role not in ("user", "admin", "developer"):
        await message.answer("Недопустимая роль. Используйте user, admin, developer")
        return

    uid = int(uid_raw)
    await user_service.upsert_role(uid, target_role)
    await message.answer(f"✅ Пользователю {uid} выдана роль {target_role}")


@router.message(Command("revoke"))
async def cmd_revoke(message: Message, user_service: UserService) -> None:
    role = await ensure_message_role(message, user_service, ("developer",), denied_text="Нет доступа.")
    if role is None:
        return

    args = _command_args(message)
    if len(args) != 1 or not args[0].lstrip("-").isdigit():
        await message.answer("Использование: /revoke <user_id>")
        return

    uid = int(args[0])
    removed = await user_service.revoke(uid)
    await message.answer("✅ Роль удалена." if removed else "Пользователь не найден.")


@router.message(Command("restart"))
async def cmd_restart(message: Message, user_service: UserService) -> None:
    role = await ensure_message_role(message, user_service, ("developer",))
    if role is None:
        return

    await message.answer("♻️ Перезапуск бота...")
    os.execl(sys.executable, sys.executable, *sys.argv)


@router.message(Command("logs"))
async def cmd_logs(message: Message, user_service: UserService) -> None:
    role = await ensure_message_role(message, user_service, ("developer",))
    if role is None:
        return
    await _send_logs(message, 0)


@router.callback_query(F.data == "logs_open")
async def cb_logs_open(call: CallbackQuery, user_service: UserService) -> None:
    role = await ensure_callback_role(call, user_service, ("developer",))
    if role is None or call.message is None:
        return
    await call.answer()
    await _send_logs(call.message, 0)


@router.callback_query(F.data.startswith("logs_more:"))
async def cb_logs_more(call: CallbackQuery, user_service: UserService) -> None:
    role = await ensure_callback_role(call, user_service, ("developer",))
    if role is None or call.message is None:
        return

    offset = _parse_logs_offset(call.data)
    if offset is None:
        await call.answer("Некорректная пагинация логов", show_alert=True)
        return

    await call.answer()
    try:
        await _send_logs(call.message, offset)
    except OSError:
        logger.exception("Failed to read bot logs")
        await call.message.answer("Не удалось прочитать лог-файл.")
