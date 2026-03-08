from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def logs_kb(offset: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📜 Показать ещё", callback_data=f"logs_more:{offset}")],
            [InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")],
        ]
    )

