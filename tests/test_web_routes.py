from __future__ import annotations

import asyncio
import re
from pathlib import Path

from litestar.testing import TestClient

from app.container import settings
from app.db.session import init_models
from app.web.app import app
from app.web.routes_pages import VALID_SERVICE_SLUGS


TEMPLATE_ASSET_PATHS = (
    "img/electric/elec1.jpg",
    "img/electric/elec2.jpg",
    "img/electric/elec3.jpg",
    "img/electric/elec4.jpg",
    "img/electric/elec5.jpg",
    "img/electric/elec7.jpg",
    "img/electric/elec8.jpg",
    "img/otopl/otopl1.jpg",
    "img/otopl/otopl2.jpg",
    "img/otopl/otopl3.jpg",
    "img/otopl/otopl5.jpg",
    "img/otopl/otopl6.jpg",
    "img/otopl/otopl7.jpg",
    "img/otopl/otopl8.jpg",
    "img/logo/miniintexdom.png",
)


def test_pages_routes_are_available() -> None:
    asyncio.run(init_models())
    with TestClient(app=app) as client:
        for path in ["/", "/obrsvaz", "/privacy"]:
            resp = client.get(path)
            assert resp.status_code == 200


def test_price_routes_are_removed() -> None:
    asyncio.run(init_models())
    with TestClient(app=app) as client:
        for path in ["/price", "/Price", "/price1", "/price2", "/price3"]:
            assert client.get(path).status_code != 200


def test_robots_and_sitemap_routes() -> None:
    asyncio.run(init_models())
    with TestClient(app=app) as client:
        robots_response = client.get("/robots.txt")
        assert robots_response.status_code == 200
        assert "Sitemap: https://intexdom.ru/sitemap.xml" in robots_response.text

        sitemap_response = client.get("/sitemap.xml")
        assert sitemap_response.status_code == 200
        assert "<loc>https://intexdom.ru/</loc>" in sitemap_response.text
        assert "<loc>https://intexdom.ru/privacy</loc>" in sitemap_response.text
        for slug in VALID_SERVICE_SLUGS:
            assert f"<loc>https://intexdom.ru/services/{slug}</loc>" in sitemap_response.text


def test_main_page_has_seo_metadata() -> None:
    asyncio.run(init_models())
    with TestClient(app=app) as client:
        resp = client.get("/")
        assert resp.status_code == 200
        assert '<title>ИнТехДом — инженерные системы в Ярославле</title>' in resp.text
        assert '<meta name="description"' in resp.text
        assert '<link rel="canonical" href="https://intexdom.ru/">' in resp.text
        assert '<meta property="og:title"' in resp.text
        assert 'type="application/ld+json"' in resp.text
        assert '"@type": "LocalBusiness"' in resp.text
        assert "Комплексные инженерные системы для комфортной жизни" in resp.text
        assert "кофортной" not in resp.text


def test_privacy_page_contains_operator_details() -> None:
    asyncio.run(init_models())
    with TestClient(app=app) as client:
        resp = client.get("/privacy")
        assert "СЕРВИС ИНЖЕНЕРНЫХ СИСТЕМ" in resp.text
        assert "7627059630" in resp.text
        assert "1247600001846" in resp.text
        assert "panasenkovs@gmail.com" in resp.text


def test_service_detail_routes() -> None:
    asyncio.run(init_models())
    with TestClient(app=app) as client:
        for slug in VALID_SERVICE_SLUGS:
            assert client.get(f"/services/{slug}").status_code == 200
        assert client.get("/services/unknown").status_code == 404


def test_service_detail_renders_template_content() -> None:
    asyncio.run(init_models())
    with TestClient(app=app) as client:
        electric_response = client.get("/services/electric")
        assert "Электрика" in electric_response.text
        assert "/assets/img/electric/elec8.jpg" in electric_response.text
        assert "app.web.catalog" not in electric_response.text


def test_service_pages_have_seo_metadata_and_no_price_links() -> None:
    asyncio.run(init_models())
    with TestClient(app=app) as client:
        for slug in VALID_SERVICE_SLUGS:
            resp = client.get(f"/services/{slug}")
            assert resp.status_code == 200
            assert "Ярославле" in resp.text
            assert '<meta name="description"' in resp.text
            assert f'<link rel="canonical" href="https://intexdom.ru/services/{slug}">' in resp.text
            assert '<meta property="og:title"' in resp.text
            assert '<meta property="og:description"' in resp.text
            assert '<meta property="og:url"' in resp.text
            assert "/price" not in resp.text

            feature_section = re.search(
                r'<ul class="service-feature-list">(.*?)</ul>',
                resp.text,
                flags=re.DOTALL,
            )
            assert feature_section is not None
            assert feature_section.group(1).count("<li>") >= 5


def test_assets_route_and_static_redirect() -> None:
    asyncio.run(init_models())
    with TestClient(app=app) as client:
        assets_response = client.get("/assets/main.css")
        assert assets_response.status_code == 200

        redirect_response = client.get("/static/main.css", follow_redirects=False)
        assert redirect_response.status_code == 301
        assert redirect_response.headers["location"] == "/assets/main.css"


def test_favicon_route() -> None:
    asyncio.run(init_models())
    with TestClient(app=app) as client:
        resp = client.get("/favicon.ico")
        assert resp.status_code == 200
        assert "png" in resp.headers["content-type"]
        assert len(resp.content) > 0


def test_template_assets_exist() -> None:
    static_dir = settings.static_dir.resolve()
    missing_assets: list[str] = []

    for src in TEMPLATE_ASSET_PATHS:
        asset_path = static_dir / Path(src)
        if not asset_path.exists():
            missing_assets.append(src)

    assert missing_assets == []


def test_feedback_success() -> None:
    asyncio.run(init_models())
    payload = {
        "name": "Иван",
        "telephone": "+79991234567",
        "email": "ivan@example.com",
        "subject": "Тест",
        "message": "Проверка",
        "personal_data_consent": "on",
    }
    with TestClient(app=app) as client:
        resp = client.post("/feedback", json=payload)
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"


def test_feedback_rejects_non_object_json() -> None:
    asyncio.run(init_models())
    with TestClient(app=app) as client:
        resp = client.post("/feedback", json=[1, 2, 3])
        assert resp.status_code == 400
        assert resp.json()["status"] == "error"
        assert "структура JSON" in resp.json()["message"]


def test_feedback_requires_name() -> None:
    asyncio.run(init_models())
    payload = {
        "telephone": "+79991234567",
        "email": "ivan@example.com",
        "subject": "test",
        "message": "message",
        "personal_data_consent": "on",
    }
    with TestClient(app=app) as client:
        resp = client.post("/feedback", json=payload)
        assert resp.status_code == 400
        assert resp.json()["status"] == "error"
        assert resp.json()["message"] == "Поле 'name' обязательно"


def test_feedback_rejects_invalid_phone() -> None:
    asyncio.run(init_models())
    payload = {
        "name": "Ivan",
        "telephone": "123",
        "email": "ivan@example.com",
        "subject": "test",
        "message": "message",
        "personal_data_consent": "on",
    }
    with TestClient(app=app) as client:
        resp = client.post("/feedback", json=payload)
        assert resp.status_code == 400
        assert resp.json()["status"] == "error"


def test_feedback_requires_personal_data_consent() -> None:
    asyncio.run(init_models())
    payload = {
        "name": "Ivan",
        "telephone": "+79991234567",
        "email": "ivan@example.com",
        "subject": "test",
        "message": "message",
    }
    with TestClient(app=app) as client:
        resp = client.post("/feedback", json=payload)
        assert resp.status_code == 400
        assert resp.json()["status"] == "error"


def test_feedback_rejects_invalid_email() -> None:
    asyncio.run(init_models())
    payload = {
        "name": "Ivan",
        "telephone": "+79991234567",
        "email": "not-an-email",
        "subject": "test",
        "message": "message",
        "personal_data_consent": "on",
    }
    with TestClient(app=app) as client:
        resp = client.post("/feedback", json=payload)
        assert resp.status_code == 400
        assert resp.json()["message"] == "Некорректный email"


def test_feedback_rejects_oversized_message() -> None:
    asyncio.run(init_models())
    payload = {
        "name": "Ivan",
        "telephone": "+79991234567",
        "email": "ivan@example.com",
        "subject": "test",
        "message": "x" * 5000,
        "personal_data_consent": "on",
    }
    with TestClient(app=app) as client:
        resp = client.post("/feedback", json=payload)
        assert resp.status_code == 400


def test_feedback_honeypot_silent_success() -> None:
    from app.container import order_service

    asyncio.run(init_models())
    orders_before = len(asyncio.run(order_service.list_orders()))
    payload = {
        "name": "Spam Bot",
        "telephone": "+79991234567",
        "email": "spam@example.com",
        "subject": "spam",
        "message": "spam",
        "personal_data_consent": "on",
        "company_website": "https://spam.example",
    }
    with TestClient(app=app) as client:
        resp = client.post("/feedback", json=payload)
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    orders_after = len(asyncio.run(order_service.list_orders()))
    assert orders_after == orders_before
