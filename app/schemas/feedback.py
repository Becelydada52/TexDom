from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class FeedbackPayload:
    name: str
    telephone: str
    email: str
    subject: str
    message: str

    @classmethod
    def from_payload(cls, data: dict[str, object]) -> "FeedbackPayload":
        name = str(data.get("name") or "").strip()
        telephone = str(data.get("telephone") or "").strip()
        if not name:
            raise ValueError("Поле 'name' обязательно")
        if not telephone:
            raise ValueError("Поле 'telephone' обязательно")

        return cls(
            name=name,
            telephone=telephone,
            email=str(data.get("email") or "Не указано"),
            subject=str(data.get("subject") or "Без темы"),
            message=str(data.get("message") or "Пустое сообщение"),
        )
