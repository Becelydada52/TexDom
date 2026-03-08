from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def users_menu_kb(role: str) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(text="👥 Список ролей", callback_data="users_list")],
        [InlineKeyboardButton(text="📨 Получатели заявок", callback_data="notify_list")],
        [InlineKeyboardButton(text="➕ Как назначить роль", callback_data="role_help")],
        [InlineKeyboardButton(text="🔔 Как настроить заявки", callback_data="notify_help")],
    ]
    if role == "developer":
        rows.append([InlineKeyboardButton(text="🛠 Команды developer", callback_data="developer_help")])
    rows.append([InlineKeyboardButton(text="🏠 Назад", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
