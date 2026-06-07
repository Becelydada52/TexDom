from __future__ import annotations

from litestar import Request, get
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


@get("/robots.txt", name="robots")
async def robots_txt() -> Response[str]:
    return Response(
        content=(settings.static_dir / "robots.txt").read_text(encoding="utf-8"),
        media_type="text/plain; charset=utf-8",
    )


@get("/sitemap.xml", name="sitemap")
async def sitemap_xml() -> Response[str]:
    return Response(
        content=(settings.static_dir / "sitemap.xml").read_text(encoding="utf-8"),
        media_type="application/xml; charset=utf-8",
    )


@get("/services/{slug:str}", name="service_detail")
async def service_detail_page(request: Request, slug: str) -> Response[str]:
    status_code = 200 if slug in VALID_SERVICE_SLUGS else 404
    return renderer.render("service_detail.html", request, {"slug": slug}, status_code=status_code)


@get("/static/{filename:path}", name="static")
async def static_compat(filename: str) -> Response[str]:
    normalized_filename = filename.lstrip("/")
    return Response(
        status_code=307,
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
    service_detail_page,
    static_compat,
]
