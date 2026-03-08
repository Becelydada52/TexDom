from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.db.models import Order


@dataclass(slots=True)
class OrderView:
    id: str
    name: str
    telephone: str
    email: str
    subject: str
    message: str
    status: str
    source: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, model: Order) -> "OrderView":
        return cls(
            id=model.id,
            name=model.name,
            telephone=model.telephone,
            email=model.email,
            subject=model.subject,
            message=model.message,
            status=model.status,
            source=model.source,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

