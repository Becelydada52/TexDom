from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.db.models import Order


def orders_list_kb(items: list[Order]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for item in items[:10]:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{item.name} | {item.telephone}",
                    callback_data=f"order:{item.id}",
                )
            ]
        )
    rows.append([InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def order_details_kb(order_id: str, role: str) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(text="🟡 В работе", callback_data=f"order_status:{order_id}:in_progress"),
            InlineKeyboardButton(text="🟢 Готово", callback_data=f"order_status:{order_id}:done"),
        ]
    ]
    if role in ("admin", "developer"):
        rows.append([InlineKeyboardButton(text="🗑 Удалить", callback_data=f"order_del:{order_id}")])
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="view_orders")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

