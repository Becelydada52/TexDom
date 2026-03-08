from __future__ import annotations

import logging

from aiogram import Bot

from app.config import Settings
from app.db.models import Order
from app.services.users import UserService


logger = logging.getLogger(__name__)
NOTIFICATION_ROLES = ("admin", "developer")


def format_order_message(order: Order) -> str:
    return (
        f"📩 Новый заказ (ID: {order.id})\n"
        f"👤 Имя: {order.name}\n"
        f"📞 Телефон: {order.telephone}\n"
        f"📧 Email: {order.email}\n"
        f"📌 Тема: {order.subject}\n"
        f"✉️ Сообщение:\n{order.message}\n\n"
        f"⏱ Создано: {order.created_at:%Y-%m-%d %H:%M:%S}\n"
        f"Статус: {order.status}"
    )


class NotificationService:
    def __init__(self, settings: Settings, user_service: UserService) -> None:
        self.settings = settings
        self.user_service = user_service
        self._bot: Bot | None = None

    def _get_bot(self) -> Bot | None:
        if not self.settings.bot_token:
            return None
        if self._bot is None:
            self._bot = Bot(token=self.settings.bot_token)
        return self._bot

    async def notify_new_order(self, order: Order) -> None:
        bot = self._get_bot()
        if bot is None:
            logger.warning("BOT_TOKEN is not configured, notification skipped")
            return

        recipients = await self.user_service.list_ids_by_roles(NOTIFICATION_ROLES)
        if not recipients:
            return

        text = format_order_message(order)
        for chat_id in set(recipients):
            try:
                await bot.send_message(chat_id=chat_id, text=text)
            except Exception:
                logger.exception("Failed to send notification to %s", chat_id)

    async def close(self) -> None:
        if self._bot is not None:
            await self._bot.session.close()
            self._bot = None
