from __future__ import annotations

import re
from dataclasses import dataclass


NAME_MAX_LENGTH = 200
EMAIL_MAX_LENGTH = 254
SUBJECT_MAX_LENGTH = 255
MESSAGE_MAX_LENGTH = 3500

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_PATTERN.match(email))


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
            name=name[:NAME_MAX_LENGTH],
            telephone=telephone,
            email=str(data.get("email") or "Не указано")[:EMAIL_MAX_LENGTH],
            subject=str(data.get("subject") or "Без темы")[:SUBJECT_MAX_LENGTH],
            message=str(data.get("message") or "Пустое сообщение")[:MESSAGE_MAX_LENGTH],
        )
