from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.db.models import Order
from app.db.repositories import OrderRepository
from app.db.session import SessionFactory, close_engine, init_models
from app.services.users import ROLE_PRIORITY, UserService

ORDERS_FILE = BASE_DIR / "orders.json"
KEYS_FILE = BASE_DIR / "keys.json"


def _load_json(path: Path) -> object | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _backup(path: Path) -> None:
    if not path.exists():
        return
    target = Path(str(path) + ".bak")
    if target.exists():
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        target = Path(str(path) + f".{ts}.bak")
    path.replace(target)


def _parse_datetime(value: object) -> datetime:
    if isinstance(value, str):
        try:
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass
    return datetime.now()


async def migrate_orders(orders_data: object) -> int:
    if not isinstance(orders_data, list):
        return 0

    imported = 0
    async with SessionFactory() as session:
        repo = OrderRepository(session)
        for row in orders_data:
            if not isinstance(row, dict):
                continue
            order_id = str(row.get("id") or "").strip()
            if not order_id:
                continue
            if await repo.exists(order_id):
                continue
            order = Order(
                id=order_id,
                name=str(row.get("name") or "Не указано"),
                telephone=str(row.get("telephone") or "Не указано"),
                email=str(row.get("email") or "Не указано"),
                subject=str(row.get("subject") or "Без темы"),
                message=str(row.get("message") or "Пустое сообщение"),
                status=str(row.get("status") or "new"),
                source="legacy_json",
                created_at=_parse_datetime(row.get("created_at")),
                updated_at=datetime.now(),
            )
            await repo.create(order)
            imported += 1
    return imported


async def migrate_users(keys_data: object) -> int:
    if not isinstance(keys_data, dict):
        return 0

    legacy_map = {"USERS": "user", "ADMINS": "admin", "DEVELOPERS": "developer"}
    resolved_roles: dict[int, str] = {}
    for legacy_key, role in legacy_map.items():
        users = keys_data.get(legacy_key, [])
        if not isinstance(users, list):
            continue
        for raw_uid in users:
            try:
                uid = int(raw_uid)
            except (TypeError, ValueError):
                continue
            existing = resolved_roles.get(uid)
            if existing is None or ROLE_PRIORITY[role] > ROLE_PRIORITY[existing]:
                resolved_roles[uid] = role

    service = UserService(SessionFactory)
    imported = 0
    for uid, role in resolved_roles.items():
        current = await service.get_role(uid)
        if current == "guest":
            await service.upsert_role(uid, role)
            imported += 1
            continue
        if ROLE_PRIORITY[role] > ROLE_PRIORITY.get(current, 0):
            await service.upsert_role(uid, role)
    return imported


async def main() -> None:
    await init_models()

    orders_data = _load_json(ORDERS_FILE)
    keys_data = _load_json(KEYS_FILE)

    imported_orders = await migrate_orders(orders_data)
    imported_users = await migrate_users(keys_data)

    if orders_data is not None and imported_orders > 0:
        _backup(ORDERS_FILE)
    if keys_data is not None and imported_users > 0:
        _backup(KEYS_FILE)

    print(f"Imported orders: {imported_orders}")
    print(f"Imported users: {imported_users}")

    await close_engine()


if __name__ == "__main__":
    asyncio.run(main())
