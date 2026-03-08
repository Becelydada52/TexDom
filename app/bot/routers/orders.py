from __future__ import annotations

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery

from app.bot.deps import ALLOWED_ROLES, ensure_callback_role
from app.bot.keyboards.orders import order_details_kb, orders_list_kb
from app.db.models import Order
from app.services.orders import OrderService
from app.services.users import UserService


router = Router(name="orders")


def _format_order(order: Order) -> str:
    return (
        f"🆔 ID: {order.id}\n"
        f"👤 Имя: {order.name}\n"
        f"📞 Телефон: {order.telephone}\n"
        f"📧 Email: {order.email}\n"
        f"📌 Тема: {order.subject}\n"
        f"✉️ Сообщение:\n{order.message}\n\n"
        f"⏱ Создано: {order.created_at:%Y-%m-%d %H:%M:%S}\n"
        f"📦 Статус: {order.status}"
    )


async def _render_orders_list(call: CallbackQuery, order_service: OrderService) -> None:
    if call.message is None:
        return
    all_orders = await order_service.list_orders()
    latest_orders = list(reversed(all_orders))[:10]
    await call.message.edit_text(
        f"Найдено заказов: {len(all_orders)}",
        reply_markup=orders_list_kb(latest_orders),
    )


@router.callback_query(F.data == "view_orders")
async def cb_view_orders(call: CallbackQuery, user_service: UserService, order_service: OrderService) -> None:
    role = await ensure_callback_role(call, user_service, ALLOWED_ROLES)
    if role is None:
        return
    await call.answer()
    await _render_orders_list(call, order_service)


@router.callback_query(F.data.startswith("order:"))
async def cb_order_details(call: CallbackQuery, user_service: UserService, order_service: OrderService) -> None:
    role = await ensure_callback_role(call, user_service, ALLOWED_ROLES)
    if role is None or call.message is None:
        return

    order_id = (call.data or "").split(":", 1)[1]
    await call.answer()
    order = await order_service.get_order(order_id)
    if order is None:
        await _render_orders_list(call, order_service)
        return

    await call.message.edit_text(_format_order(order), reply_markup=order_details_kb(order_id, role))


@router.callback_query(F.data.startswith("order_status:"))
async def cb_order_status(call: CallbackQuery, user_service: UserService, order_service: OrderService) -> None:
    role = await ensure_callback_role(call, user_service, ALLOWED_ROLES)
    if role is None or call.message is None:
        return

    _, order_id, status = (call.data or "").split(":", 2)
    await call.answer("Статус обновлён")
    order = await order_service.update_order_status(order_id, status)
    if order is None:
        await _render_orders_list(call, order_service)
        return
    try:
        await call.message.edit_text(_format_order(order), reply_markup=order_details_kb(order_id, role))
    except TelegramBadRequest as exc:
        if "message is not modified" not in str(exc).lower():
            raise


@router.callback_query(F.data.startswith("order_del:"))
async def cb_order_delete(call: CallbackQuery, user_service: UserService, order_service: OrderService) -> None:
    role = await ensure_callback_role(call, user_service, ("admin", "developer"))
    if role is None or call.message is None:
        return
    order_id = (call.data or "").split(":", 1)[1]
    await call.answer("Удалено")
    await order_service.delete_order(order_id)
    await _render_orders_list(call, order_service)

