from __future__ import annotations

from litestar import Request, get
from litestar.response import Response

from app.container import settings
from app.web.catalog import SERVICES_CATALOG
from app.web.templates import TemplateRenderer


renderer = TemplateRenderer(settings.templates_dir)


@get("/", name="main")
async def main_page(request: Request) -> Response[str]:
    return renderer.render("main.html", request)


@get("/Price", name="price_upper")
async def price_page_upper(request: Request) -> Response[str]:
    return renderer.render("Price.html", request)


@get("/price", name="price")
async def price_page(request: Request) -> Response[str]:
    return renderer.render("Price.html", request)


@get("/price1", name="price1")
async def price1_page(request: Request) -> Response[str]:
    return renderer.render("price1.html", request)


@get("/price2", name="price2")
async def price2_page(request: Request) -> Response[str]:
    return renderer.render("price2.html", request)


@get("/price3", name="price3")
async def price3_page(request: Request) -> Response[str]:
    return renderer.render("price3.html", request)


@get("/obrsvaz", name="obrsvaz")
async def obrsvaz_page(request: Request) -> Response[str]:
    return renderer.render("obrsvaz.html", request)


@get("/privacy", name="privacy")
async def privacy_page(request: Request) -> Response[str]:
    return renderer.render("privacy.html", request)


@get("/services/{slug:str}", name="service_detail")
async def service_detail_page(request: Request, slug: str) -> Response[str]:
    service = SERVICES_CATALOG.get(slug)
    if service is None:
        return renderer.render("service_detail.html", request, {"service": None}, status_code=404)
    return renderer.render("service_detail.html", request, {"service": service})


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
    price_page_upper,
    price_page,
    price1_page,
    price2_page,
    price3_page,
    obrsvaz_page,
    privacy_page,
    service_detail_page,
    static_compat,
]
