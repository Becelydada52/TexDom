from __future__ import annotations

from litestar.static_files import create_static_files_router

from app.container import settings


route_handlers = [
    create_static_files_router(path="/assets", directories=[settings.static_dir], name="assets"),
]

