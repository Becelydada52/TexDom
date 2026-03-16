from __future__ import annotations

import asyncio
from pathlib import Path

from litestar.testing import TestClient

from app.container import settings
from app.db.session import init_models
from app.web.app import app
from app.web.catalog import SERVICES_CATALOG


def test_pages_routes_are_available() -> None:
    asyncio.run(init_models())
    with TestClient(app=app) as client:
        for path in ["/", "/Price", "/price", "/price1", "/price2", "/price3", "/obrsvaz"]:
            resp = client.get(path)
            assert resp.status_code == 200


def test_service_detail_routes() -> None:
    asyncio.run(init_models())
    with TestClient(app=app) as client:
        for slug in SERVICES_CATALOG:
            assert client.get(f"/services/{slug}").status_code == 200
        assert client.get("/services/unknown").status_code == 404


def test_assets_route_and_static_redirect() -> None:
    asyncio.run(init_models())
    with TestClient(app=app) as client:
        assets_response = client.get("/assets/main.css")
        assert assets_response.status_code == 200

        redirect_response = client.get("/static/main.css", follow_redirects=False)
        assert redirect_response.status_code == 307
        assert redirect_response.headers["location"] == "/assets/main.css"


def test_service_catalog_assets_exist() -> None:
    static_dir = settings.static_dir.resolve()
    missing_assets: list[str] = []

    for service in SERVICES_CATALOG.values():
        for album in service.get("albums", []):
            for item in album.get("items", []):
                src = item.get("src")
                if not isinstance(src, str) or not src.startswith("/assets/"):
                    continue
                asset_path = static_dir / Path(src.removeprefix("/assets/"))
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
    }
    with TestClient(app=app) as client:
        resp = client.post("/feedback", json=payload)
        assert resp.status_code == 400
        assert resp.json()["status"] == "error"
