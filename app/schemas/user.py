from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.db.models import User


@dataclass(slots=True)
class UserView:
    telegram_id: int
    role: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, model: User) -> "UserView":
        return cls(
            telegram_id=model.telegram_id,
            role=model.role.value,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

