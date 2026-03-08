from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_kb(role: str) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(text="📋 Заказы", callback_data="view_orders")],
    ]
    if role in {"admin", "developer"}:
        rows.append([InlineKeyboardButton(text="👥 Доступ и заявки", callback_data="users_menu")])
    if role == "developer":
        rows.append([InlineKeyboardButton(text="📜 Логи", callback_data="logs_open")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
