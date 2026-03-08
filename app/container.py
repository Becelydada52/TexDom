from __future__ import annotations

from app.config import get_settings
from app.db.session import SessionFactory
from app.services.notifications import NotificationService
from app.services.orders import OrderService
from app.services.users import UserService


settings = get_settings()
order_service = OrderService(SessionFactory)
user_service = UserService(SessionFactory)
notification_service = NotificationService(settings=settings, user_service=user_service)

