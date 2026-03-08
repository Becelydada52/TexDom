from __future__ import annotations

from app import config


def test_default_database_url_is_absolute(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    config.get_settings.cache_clear()
    try:
        settings = config.get_settings()
        expected_path = (config.BASE_DIR / "app.db").resolve().as_posix()
        assert settings.database_url == f"sqlite+aiosqlite:///{expected_path}"
    finally:
        config.get_settings.cache_clear()
