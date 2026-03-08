from __future__ import annotations

from aiogram.types import CallbackQuery, Message

from app.services.users import UserService


ALLOWED_ROLES = ("user", "admin", "developer")


async def ensure_message_role(
    message: Message,
    user_service: UserService,
    allowed_roles: tuple[str, ...],
    denied_text: str = "🚫 Недостаточно прав.",
) -> str | None:
    role = await user_service.get_role(message.chat.id)
    if role not in allowed_roles:
        await message.answer(denied_text)
        return None
    return role


async def ensure_callback_role(
    call: CallbackQuery,
    user_service: UserService,
    allowed_roles: tuple[str, ...],
    denied_text: str = "🚫 Недостаточно прав.",
) -> str | None:
    if call.message is None:
        await call.answer("Сообщение недоступно", show_alert=True)
        return None
    if call.from_user is None:
        await call.answer("Пользователь не определён", show_alert=True)
        return None

    role = await user_service.get_role(call.from_user.id)
    if role not in allowed_roles:
        await call.answer(denied_text, show_alert=True)
        return None
    return role
