from __future__ import annotations

from typing import Annotated

from litestar import Request, get
from litestar.params import PathParameter
from litestar.response import Response

from app.container import settings
from app.web.templates import TemplateRenderer


renderer = TemplateRenderer(settings.templates_dir)

VALID_SERVICE_SLUGS = frozenset(
    {
        "electric",
        "water",
        "vent",
        "drenaj",
        "septiki",
        "excavator",
    }
)


@get("/", name="main")
async def main_page(request: Request) -> Response[str]:
    return renderer.render("main.html", request)


@get("/obrsvaz", name="obrsvaz")
async def obrsvaz_page(request: Request) -> Response[str]:
    return renderer.render("obrsvaz.html", request)


@get("/privacy", name="privacy")
async def privacy_page(request: Request) -> Response[str]:
    return renderer.render("privacy.html", request)


def _read_static_text(filename: str) -> str | None:
    path = settings.static_dir / filename
    if not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


@get("/robots.txt", name="robots")
async def robots_txt() -> Response[str]:
    content = _read_static_text("robots.txt")
    if content is None:
        return Response(content="Not Found", status_code=404, media_type="text/plain; charset=utf-8")
    return Response(content=content, media_type="text/plain; charset=utf-8")


@get("/sitemap.xml", name="sitemap")
async def sitemap_xml() -> Response[str]:
    content = _read_static_text("sitemap.xml")
    if content is None:
        return Response(content="Not Found", status_code=404, media_type="text/plain; charset=utf-8")
    return Response(content=content, media_type="application/xml; charset=utf-8")


@get("/favicon.ico", name="favicon")
async def favicon_ico() -> Response[bytes]:
    path = settings.static_dir / "img" / "logo" / "miniintexdom.png"
    if not path.is_file():
        return Response(content=b"Not Found", status_code=404, media_type="text/plain; charset=utf-8")
    return Response(
        content=path.read_bytes(),
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=86400"},
    )


@get("/services/{slug:str}", name="service_detail")
async def service_detail_page(request: Request, slug: Annotated[str, PathParameter()]) -> Response[str]:
    status_code = 200 if slug in VALID_SERVICE_SLUGS else 404
    return renderer.render("service_detail.html", request, {"slug": slug}, status_code=status_code)


@get("/static/{filename:path}", name="static")
async def static_compat(filename: Annotated[str, PathParameter()]) -> Response[str]:
    normalized_filename = filename.lstrip("/")
    return Response(
        status_code=301,
        media_type="text/plain",
        content="",
        headers={"Location": f"/assets/{normalized_filename}"},
    )


route_handlers = [
    main_page,
    obrsvaz_page,
    privacy_page,
    robots_txt,
    sitemap_xml,
    favicon_ico,
    service_detail_page,
    static_compat,
]
