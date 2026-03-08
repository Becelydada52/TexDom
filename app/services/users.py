from __future__ import annotations

from collections.abc import Callable, Iterable

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import UserRole
from app.db.repositories import UserRepository


ROLE_PRIORITY: dict[str, int] = {"user": 1, "admin": 2, "developer": 3}


class UserService:
    def __init__(self, session_factory: Callable[[], AsyncSession]) -> None:
        self.session_factory = session_factory

    async def get_role(self, telegram_id: int) -> str:
        async with self.session_factory() as session:
            repo = UserRepository(session)
            user = await repo.get_by_telegram_id(telegram_id)
            if user is None:
                return "guest"
            return user.role.value

    async def list_ids_by_roles(self, roles: Iterable[str]) -> list[int]:
        valid_roles = [UserRole(role) for role in roles]
        async with self.session_factory() as session:
            repo = UserRepository(session)
            users = await repo.list_by_roles(valid_roles)
            return [u.telegram_id for u in users]

    async def upsert_role(self, telegram_id: int, role: str, *, keep_higher_role: bool = False) -> str:
        if role not in ROLE_PRIORITY:
            raise ValueError("Недопустимая роль")
        new_role = UserRole(role)
        async with self.session_factory() as session:
            repo = UserRepository(session)
            current = await repo.get_by_telegram_id(telegram_id)
            if current and keep_higher_role:
                if ROLE_PRIORITY[current.role.value] >= ROLE_PRIORITY[new_role.value]:
                    return current.role.value
            updated = await repo.upsert_role(telegram_id, new_role)
            return updated.role.value

    async def revoke(self, telegram_id: int) -> bool:
        async with self.session_factory() as session:
            repo = UserRepository(session)
            return await repo.delete_user(telegram_id)

    async def users_by_role(self) -> dict[str, list[int]]:
        result = {"developer": [], "admin": [], "user": []}
        async with self.session_factory() as session:
            repo = UserRepository(session)
            for role in (UserRole.developer, UserRole.admin, UserRole.user):
                users = await repo.list_by_roles([role])
                result[role.value] = [u.telegram_id for u in users]
        return result

