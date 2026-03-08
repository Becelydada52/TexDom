from __future__ import annotations

import logging
from pathlib import Path


def configure_logging(log_path: Path) -> None:
    log_path = log_path.resolve()
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    root = logging.getLogger()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    root.setLevel(logging.INFO)

    has_file_handler = any(
        isinstance(handler, logging.FileHandler)
        and Path(getattr(handler, "baseFilename", "")).resolve() == log_path
        for handler in root.handlers
    )
    if not has_file_handler:
        file_handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

    has_stream_handler = any(
        isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler)
        for handler in root.handlers
    )
    if not has_stream_handler:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        root.addHandler(stream_handler)
