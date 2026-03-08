from __future__ import annotations

from litestar import Litestar

from app.container import notification_service, settings
from app.db.session import close_engine
from app.logging import configure_logging
from app.web.routes_feedback import route_handlers as feedback_handlers
from app.web.routes_pages import route_handlers as pages_handlers
from app.web.routes_static import route_handlers as static_handlers


async def on_startup() -> None:
    configure_logging(settings.bot_log_path)


async def on_shutdown() -> None:
    await notification_service.close()
    await close_engine()


app = Litestar(
    route_handlers=[*pages_handlers, *feedback_handlers, *static_handlers],
    on_startup=[on_startup],
    on_shutdown=[on_shutdown],
)
