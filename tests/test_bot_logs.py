from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from app.bot.routers import admin


class DummyUserService:
    async def get_role(self, telegram_id: int) -> str:
        return "developer"


class DummyMessage:
    def __init__(self) -> None:
        self.answers: list[tuple[str, object | None]] = []

    async def answer(self, text: str, reply_markup: object | None = None) -> None:
        self.answers.append((text, reply_markup))


class DummyCallback:
    def __init__(self, data: str, message: DummyMessage) -> None:
        self.data = data
        self.message = message
        self.from_user = SimpleNamespace(id=777)
        self.answers: list[tuple[str, bool]] = []

    async def answer(self, text: str = "", show_alert: bool = False) -> None:
        self.answers.append((text, show_alert))


def _write_log(path: Path, total_lines: int) -> None:
    path.write_text("".join(f"line {index}\n" for index in range(total_lines)), encoding="utf-8")


def test_read_log_page_reads_latest_lines_from_large_file(tmp_path) -> None:
    log_path = tmp_path / "bot.log"
    _write_log(log_path, 200)

    latest_page = admin._read_log_page(log_path, 0)
    older_page = admin._read_log_page(log_path, 30)

    assert latest_page[0].strip() == "line 170"
    assert latest_page[-1].strip() == "line 199"
    assert older_page[0].strip() == "line 140"
    assert older_page[-1].strip() == "line 169"


@pytest.mark.asyncio
async def test_logs_more_rejects_invalid_offset() -> None:
    call = DummyCallback("logs_more:not-a-number", DummyMessage())

    await admin.cb_logs_more(call, DummyUserService())

    assert call.answers[-1] == ("Некорректная пагинация логов", True)
    assert call.message.answers == []
