from __future__ import annotations

import asyncio
import logging

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from app.bot.routers import admin, common, orders, users
from app.container import order_service, settings, user_service
from app.db.session import close_engine
from app.logging import configure_logging


logger = logging.getLogger(__name__)


def build_dispatcher() -> Dispatcher:
    dispatcher = Dispatcher()
    dispatcher.include_router(common.router)
    dispatcher.include_router(orders.router)
    dispatcher.include_router(users.router)
    dispatcher.include_router(admin.router)
    dispatcher.workflow_data.update(
        {
            "order_service": order_service,
            "user_service": user_service,
        }
    )
    return dispatcher


async def run_polling(bot: Bot, dispatcher: Dispatcher) -> None:
    logger.info("Starting bot in polling mode")
    await bot.delete_webhook(drop_pending_updates=True)
    await dispatcher.start_polling(bot)


async def run_webhook(bot: Bot, dispatcher: Dispatcher) -> None:
    path = settings.bot_webhook_path
    if not path.startswith("/"):
        path = "/" + path

    webhook_url = settings.bot_webhook_url.rstrip("/") + path
    if not settings.bot_webhook_url:
        logger.warning("BOT_WEBHOOK_URL is empty, fallback to polling mode")
        await run_polling(bot, dispatcher)
        return

    await bot.set_webhook(webhook_url, drop_pending_updates=True)

    app = web.Application()
    SimpleRequestHandler(dispatcher=dispatcher, bot=bot).register(app, path=path)
    setup_application(app, dispatcher, bot=bot)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=settings.bot_webhook_host, port=settings.bot_webhook_port)
    await site.start()
    logger.info(
        "Webhook bot started on %s:%s%s",
        settings.bot_webhook_host,
        settings.bot_webhook_port,
        path,
    )

    try:
        await asyncio.Event().wait()
    finally:
        await bot.delete_webhook()
        await runner.cleanup()


async def run_bot() -> None:
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is required")

    configure_logging(settings.bot_log_path)

    bot = Bot(token=settings.bot_token)
    dispatcher = build_dispatcher()

    try:
        if settings.bot_mode == "webhook":
            await run_webhook(bot, dispatcher)
        else:
            await run_polling(bot, dispatcher)
    finally:
        await bot.session.close()
        await close_engine()
