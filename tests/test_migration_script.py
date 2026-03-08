from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest


ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT_DIR / "scripts" / "migrate_json_to_sqlite.py"


def load_migration_module():
    spec = spec_from_file_location("migrate_json_to_sqlite", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.asyncio
async def test_main_does_not_backup_without_import(monkeypatch, tmp_path) -> None:
    module = load_migration_module()

    orders_file = tmp_path / "orders.json"
    keys_file = tmp_path / "keys.json"
    orders_file.write_text("[]", encoding="utf-8")
    keys_file.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(module, "ORDERS_FILE", orders_file)
    monkeypatch.setattr(module, "KEYS_FILE", keys_file)

    async def fake_init_models() -> None:
        return None

    async def fake_close_engine() -> None:
        return None

    async def fake_migrate_orders(data: object) -> int:
        return 0

    async def fake_migrate_users(data: object) -> int:
        return 0

    backups: list[Path] = []

    def fake_backup(path: Path) -> None:
        backups.append(path)

    monkeypatch.setattr(module, "init_models", fake_init_models)
    monkeypatch.setattr(module, "close_engine", fake_close_engine)
    monkeypatch.setattr(module, "migrate_orders", fake_migrate_orders)
    monkeypatch.setattr(module, "migrate_users", fake_migrate_users)
    monkeypatch.setattr(module, "_backup", fake_backup)

    await module.main()

    assert backups == []


@pytest.mark.asyncio
async def test_main_backups_only_imported_source(monkeypatch, tmp_path) -> None:
    module = load_migration_module()

    orders_file = tmp_path / "orders.json"
    keys_file = tmp_path / "keys.json"
    orders_file.write_text("[]", encoding="utf-8")
    keys_file.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(module, "ORDERS_FILE", orders_file)
    monkeypatch.setattr(module, "KEYS_FILE", keys_file)

    async def fake_init_models() -> None:
        return None

    async def fake_close_engine() -> None:
        return None

    async def fake_migrate_orders(data: object) -> int:
        return 2

    async def fake_migrate_users(data: object) -> int:
        return 0

    backups: list[Path] = []

    def fake_backup(path: Path) -> None:
        backups.append(path)

    monkeypatch.setattr(module, "init_models", fake_init_models)
    monkeypatch.setattr(module, "close_engine", fake_close_engine)
    monkeypatch.setattr(module, "migrate_orders", fake_migrate_orders)
    monkeypatch.setattr(module, "migrate_users", fake_migrate_users)
    monkeypatch.setattr(module, "_backup", fake_backup)

    await module.main()

    assert backups == [orders_file]
