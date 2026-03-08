from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.bot.deps import ensure_callback_role, ensure_message_role
from app.bot.keyboards.users import users_menu_kb
from app.services.notifications import NOTIFICATION_ROLES
from app.services.users import ROLE_PRIORITY, UserService


logger = logging.getLogger(__name__)
router = Router(name="users")

VALID_ROLES = tuple(ROLE_PRIORITY)


def _command_args(message: Message) -> list[str]:
    if not message.text:
        return []
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return []
    return parts[1].strip().split()


def _manageable_roles(actor_role: str) -> tuple[str, ...]:
    if actor_role == "developer":
        return VALID_ROLES
    if actor_role == "admin":
        return ("user", "admin")
    return ()


def _can_manage_role(actor_role: str, target_role: str) -> bool:
    return target_role in _manageable_roles(actor_role)


async def _resolve_target(raw: str, message: Message) -> tuple[int, str] | None:
    value = raw.strip()
    if not value:
        return None
    if value.lstrip("-").isdigit():
        user_id = int(value)
        return user_id, str(user_id)

    username = value.lstrip("@")
    try:
        chat = await message.bot.get_chat(f"@{username}")
        return int(chat.id), f"@{username}"
    except Exception:
        logger.exception("Failed to resolve telegram target %s", value)
        return None


def _format_group(name: str, ids: list[int]) -> str:
    rendered = ", ".join(str(item) for item in ids) if ids else "—"
    return f"{name}: {rendered}"


async def _list_notification_recipients(user_service: UserService) -> dict[str, list[int]]:
    groups = await user_service.users_by_role()
    return {role: groups.get(role, []) for role in NOTIFICATION_ROLES}


def _users_text(groups: dict[str, list[int]]) -> str:
    return (
        "👥 Пользователи по ролям:\n\n"
        f"{_format_group('DEVELOPERS', groups['developer'])}\n"
        f"{_format_group('ADMINS', groups['admin'])}\n"
        f"{_format_group('USERS', groups['user'])}"
    )


def _notify_text(recipients: dict[str, list[int]]) -> str:
    return (
        "📨 Получатели новых заявок:\n\n"
        f"{_format_group('DEVELOPERS', recipients['developer'])}\n"
        f"{_format_group('ADMINS', recipients['admin'])}"
    )


def _role_help_text(actor_role: str) -> str:
    base = [
        "➕ Назначение ролей",
        "",
        "Используйте:",
        "/role_set <@username|id> <role>",
        "/role_del <@username|id>",
        "",
        "Примеры:",
        "/role_set @username admin",
        "/role_set 123456789 user",
        "/role_del @username",
    ]
    if actor_role == "developer":
        base.append("")
        base.append("Developer может назначать: user | admin | developer")
    else:
        base.append("")
        base.append("Admin может назначать только: user | admin")
    return "\n".join(base)


def _notify_help_text(actor_role: str) -> str:
    lines = [
        "🔔 Настройка получателей заявок",
        "",
        "Используйте:",
        "/notify_add <@username|id> [role=admin|developer]",
        "/notify_del <@username|id>",
        "/notify_list",
        "",
        "Примеры:",
        "/notify_add @username admin",
        "/notify_add 123456789 developer",
        "/notify_del @username",
    ]
    if actor_role != "developer":
        lines.append("")
        lines.append("Admin может добавлять только получателей с ролью admin.")
    return "\n".join(lines)


def _developer_help_text() -> str:
    return "\n".join(
        [
            "🛠 Команды developer",
            "",
            "/grant <user_id> <role>",
            "/revoke <user_id>",
            "/logs",
            "/restart",
            "",
            "Для обычной работы удобнее использовать:",
            "/role_set, /role_del, /notify_add, /notify_del, /notify_list",
        ]
    )


@router.message(Command("users"))
async def cmd_users(message: Message, user_service: UserService) -> None:
    actor_role = await ensure_message_role(message, user_service, ("admin", "developer"))
    if actor_role is None:
        return

    groups = await user_service.users_by_role()
    await message.answer(_users_text(groups), reply_markup=users_menu_kb(actor_role))


@router.message(Command("notify_list"))
async def cmd_notify_list(message: Message, user_service: UserService) -> None:
    actor_role = await ensure_message_role(message, user_service, ("admin", "developer"))
    if actor_role is None:
        return

    recipients = await _list_notification_recipients(user_service)
    await message.answer(_notify_text(recipients), reply_markup=users_menu_kb(actor_role))


@router.message(Command("role_set"))
@router.message(Command("user_add"))
async def cmd_role_set(message: Message, user_service: UserService) -> None:
    actor_role = await ensure_message_role(message, user_service, ("admin", "developer"))
    if actor_role is None:
        return

    args = _command_args(message)
    if len(args) < 2:
        await message.answer("Использование: /role_set <@username|id> <role=user|admin|developer>")
        return

    target = await _resolve_target(args[0], message)
    if target is None:
        await message.answer("Не удалось определить пользователя по @username или user_id")
        return

    target_role = args[1].lower()
    if target_role not in VALID_ROLES:
        await message.answer("Роль должна быть: user | admin | developer")
        return
    if not _can_manage_role(actor_role, target_role):
        await message.answer("Эту роль может назначать только developer")
        return

    user_id, label = target
    await user_service.upsert_role(user_id, target_role)
    await message.answer(f"✅ Пользователю {label} назначена роль {target_role}")


@router.message(Command("role_del"))
@router.message(Command("user_del"))
async def cmd_role_del(message: Message, user_service: UserService) -> None:
    actor_role = await ensure_message_role(message, user_service, ("admin", "developer"))
    if actor_role is None:
        return

    args = _command_args(message)
    if not args:
        await message.answer("Использование: /role_del <@username|id>")
        return

    target = await _resolve_target(args[0], message)
    if target is None:
        await message.answer("Не удалось определить пользователя по @username или user_id")
        return

    user_id, label = target
    existing_role = await user_service.get_role(user_id)
    if existing_role == "guest":
        await message.answer("Пользователь не найден в таблице ролей")
        return
    if not _can_manage_role(actor_role, existing_role):
        await message.answer("Удалить developer может только developer")
        return

    deleted = await user_service.revoke(user_id)
    if deleted:
        await message.answer(f"✅ Пользователь {label} удален из таблицы ролей")
    else:
        await message.answer("Пользователь не найден в таблице ролей")


@router.message(Command("notify_add"))
async def cmd_notify_add(message: Message, user_service: UserService) -> None:
    actor_role = await ensure_message_role(message, user_service, ("admin", "developer"))
    if actor_role is None:
        return

    args = _command_args(message)
    if not args:
        await message.answer("Использование: /notify_add <@username|id> [role=admin|developer]")
        return

    target = await _resolve_target(args[0], message)
    if target is None:
        await message.answer("Не удалось определить пользователя по @username или user_id")
        return

    target_role = args[1].lower() if len(args) > 1 else "admin"
    if target_role not in NOTIFICATION_ROLES:
        await message.answer("Для просмотра заявок доступны роли: admin | developer")
        return
    if not _can_manage_role(actor_role, target_role):
        await message.answer("Роль developer может назначать только developer")
        return

    user_id, label = target
    await user_service.upsert_role(user_id, target_role)
    await message.answer(f"✅ {label} теперь получает новые заявки как {target_role}")


@router.message(Command("notify_del"))
async def cmd_notify_del(message: Message, user_service: UserService) -> None:
    actor_role = await ensure_message_role(message, user_service, ("admin", "developer"))
    if actor_role is None:
        return

    args = _command_args(message)
    if not args:
        await message.answer("Использование: /notify_del <@username|id>")
        return

    target = await _resolve_target(args[0], message)
    if target is None:
        await message.answer("Не удалось определить пользователя по @username или user_id")
        return

    user_id, label = target
    existing_role = await user_service.get_role(user_id)
    if existing_role == "guest" or existing_role not in NOTIFICATION_ROLES:
        await message.answer("Пользователь не получает новые заявки")
        return
    if not _can_manage_role(actor_role, existing_role):
        await message.answer("Удалить developer из получателей может только developer")
        return

    deleted = await user_service.revoke(user_id)
    if deleted:
        await message.answer(f"✅ {label} больше не получает новые заявки")
    else:
        await message.answer("Пользователь не получает новые заявки")


@router.callback_query(F.data == "users_menu")
async def cb_users_menu(call: CallbackQuery, user_service: UserService) -> None:
    actor_role = await ensure_callback_role(call, user_service, ("admin", "developer"))
    if actor_role is None or call.message is None:
        return
    await call.answer()
    await call.message.answer("Управление доступом и получателями заявок:", reply_markup=users_menu_kb(actor_role))


@router.callback_query(F.data == "users_list")
async def cb_users_list(call: CallbackQuery, user_service: UserService) -> None:
    actor_role = await ensure_callback_role(call, user_service, ("admin", "developer"))
    if actor_role is None or call.message is None:
        return
    await call.answer()
    groups = await user_service.users_by_role()
    await call.message.answer(_users_text(groups), reply_markup=users_menu_kb(actor_role))


@router.callback_query(F.data == "notify_list")
async def cb_notify_list(call: CallbackQuery, user_service: UserService) -> None:
    actor_role = await ensure_callback_role(call, user_service, ("admin", "developer"))
    if actor_role is None or call.message is None:
        return
    await call.answer()
    recipients = await _list_notification_recipients(user_service)
    await call.message.answer(_notify_text(recipients), reply_markup=users_menu_kb(actor_role))


@router.callback_query(F.data == "role_help")
async def cb_role_help(call: CallbackQuery, user_service: UserService) -> None:
    actor_role = await ensure_callback_role(call, user_service, ("admin", "developer"))
    if actor_role is None or call.message is None:
        return
    await call.answer()
    await call.message.answer(_role_help_text(actor_role), reply_markup=users_menu_kb(actor_role))


@router.callback_query(F.data == "notify_help")
async def cb_notify_help(call: CallbackQuery, user_service: UserService) -> None:
    actor_role = await ensure_callback_role(call, user_service, ("admin", "developer"))
    if actor_role is None or call.message is None:
        return
    await call.answer()
    await call.message.answer(_notify_help_text(actor_role), reply_markup=users_menu_kb(actor_role))


@router.callback_query(F.data == "developer_help")
async def cb_developer_help(call: CallbackQuery, user_service: UserService) -> None:
    actor_role = await ensure_callback_role(call, user_service, ("developer",))
    if actor_role is None or call.message is None:
        return
    await call.answer()
    await call.message.answer(_developer_help_text(), reply_markup=users_menu_kb(actor_role))
