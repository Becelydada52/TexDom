from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True, slots=True)
class Settings:
    bot_token: str
    bot_mode: str
    database_url: str
    bot_webhook_url: str
    bot_webhook_path: str
    bot_webhook_host: str
    bot_webhook_port: int
    templates_dir: Path
    static_dir: Path
    bot_log_path: Path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    default_db_path = (BASE_DIR / "app.db").resolve()
    default_database_url = f"sqlite+aiosqlite:///{default_db_path.as_posix()}"

    bot_token = os.getenv("BOT_TOKEN", "").strip()
    bot_mode = os.getenv("BOT_MODE", "polling").strip().lower()
    database_url = os.getenv("DATABASE_URL", default_database_url).strip()
    bot_webhook_url = os.getenv("BOT_WEBHOOK_URL", "").strip()
    bot_webhook_path = os.getenv("BOT_WEBHOOK_PATH", "/webhook").strip() or "/webhook"
    bot_webhook_host = os.getenv("BOT_WEBHOOK_HOST", "0.0.0.0").strip()
    bot_webhook_port = int(os.getenv("BOT_WEBHOOK_PORT", "8081"))

    if bot_mode not in {"polling", "webhook"}:
        bot_mode = "polling"

    return Settings(
        bot_token=bot_token,
        bot_mode=bot_mode,
        database_url=database_url,
        bot_webhook_url=bot_webhook_url,
        bot_webhook_path=bot_webhook_path,
        bot_webhook_host=bot_webhook_host,
        bot_webhook_port=bot_webhook_port,
        templates_dir=BASE_DIR / "templates",
        static_dir=BASE_DIR / "static",
        bot_log_path=BASE_DIR / "bot.log",
    )
