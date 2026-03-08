from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape
from litestar.connection import Request
from litestar.response import Response


class TemplateRenderer:
    def __init__(self, templates_dir: Path) -> None:
        self.env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=select_autoescape(("html", "xml")),
        )

    def render(
        self,
        template_name: str,
        request: Request[Any, Any, Any],
        context: dict[str, Any] | None = None,
        *,
        status_code: int = 200,
    ) -> Response[str]:
        payload = dict(context or {})
        payload["request"] = request
        payload["url_for"] = self.url_for
        html = self.env.get_template(template_name).render(**payload)
        return Response(content=html, media_type="text/html; charset=utf-8", status_code=status_code)

    @staticmethod
    def url_for(route_name: str, **params: Any) -> str:
        routes: dict[str, str] = {
            "main": "/",
            "price": "/price",
            "price1": "/price1",
            "price2": "/price2",
            "price3": "/price3",
            "obrsvaz": "/obrsvaz",
        }
        if route_name == "service_detail":
            slug = params.get("slug")
            return f"/services/{slug}"
        if route_name == "static":
            filename = params.get("filename", "")
            return f"/assets/{filename}"
        if route_name in routes:
            return routes[route_name]
        raise KeyError(f"Unsupported route name: {route_name}")
