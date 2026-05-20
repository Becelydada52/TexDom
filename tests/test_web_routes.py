from __future__ import annotations

import asyncio
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
    "img/otopl/otop1.jpg",
    "img/otopl/otop2.jpg",
    "img/otopl/otop3.jpg",
    "img/otopl/otop4.jpg",
    "img/otopl/otop5.jpg",
    "img/otopl/otop6.jpg",
    "img/logo/miniintexdom.png",
)


def test_pages_routes_are_available() -> None:
    asyncio.run(init_models())
    with TestClient(app=app) as client:
        for path in ["/", "/Price", "/price", "/price1", "/price2", "/price3", "/obrsvaz", "/privacy"]:
            resp = client.get(path)
            assert resp.status_code == 200


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
        assert "Сборка распределительного щита" in electric_response.text
        assert "app.web.catalog" not in electric_response.text


def test_assets_route_and_static_redirect() -> None:
    asyncio.run(init_models())
    with TestClient(app=app) as client:
        assets_response = client.get("/assets/main.css")
        assert assets_response.status_code == 200

        redirect_response = client.get("/static/main.css", follow_redirects=False)
        assert redirect_response.status_code == 307
        assert redirect_response.headers["location"] == "/assets/main.css"


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
