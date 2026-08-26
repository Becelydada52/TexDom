from __future__ import annotations

from datetime import datetime, timedelta, timezone


MOSCOW_TZ = timezone(timedelta(hours=3), name="UTC+3")


def utcnow() -> datetime:
    """Naive UTC timestamp, consistent with SQLite CURRENT_TIMESTAMP."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def format_moscow(value: datetime) -> str:
    """Format naive-UTC datetime as Moscow local time string."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(MOSCOW_TZ).strftime("%d.%m.%Y %H:%M:%S") + " (МСК)"
