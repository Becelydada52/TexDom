from __future__ import annotations

import io
import logging
from pathlib import Path

from app.logging import configure_logging


def test_configure_logging_adds_file_handler_when_root_already_configured(tmp_path) -> None:
    root = logging.getLogger()
    old_handlers = list(root.handlers)
    old_level = root.level

    for handler in list(root.handlers):
        root.removeHandler(handler)

    buffer_stream = io.StringIO()
    root.addHandler(logging.StreamHandler(buffer_stream))

    log_path = tmp_path / "bot.log"

    try:
        configure_logging(log_path)

        matching_file_handlers = [
            handler
            for handler in root.handlers
            if isinstance(handler, logging.FileHandler)
            and Path(getattr(handler, "baseFilename", "")).resolve() == log_path.resolve()
        ]
        assert matching_file_handlers

        root.info("test-log-line")
        assert log_path.exists()
        assert "test-log-line" in log_path.read_text(encoding="utf-8")
    finally:
        new_handlers = [handler for handler in list(root.handlers) if handler not in old_handlers]
        for handler in new_handlers:
            root.removeHandler(handler)
            handler.close()

        for handler in list(root.handlers):
            root.removeHandler(handler)

        for handler in old_handlers:
            root.addHandler(handler)

        root.setLevel(old_level)
