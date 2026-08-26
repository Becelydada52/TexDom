from __future__ import annotations

import json
import logging
from json import JSONDecodeError
from typing import Any

from litestar import Request, post
from litestar.response import Response

from app.container import notification_service, order_service
from app.schemas.feedback import (
    EMAIL_MAX_LENGTH,
    MESSAGE_MAX_LENGTH,
    NAME_MAX_LENGTH,
    SUBJECT_MAX_LENGTH,
    FeedbackPayload,
    is_valid_email,
)
from app.web.ratelimit import feedback_rate_limiter
from app.web.validation import is_valid_phone, normalize_phone


logger = logging.getLogger(__name__)

HONEYPOT_FIELD = "company_website"


def _json_response(payload: dict[str, str], status_code: int = 200) -> Response[str]:
    return Response(
        content=json.dumps(payload, ensure_ascii=False),
        media_type="application/json",
        status_code=status_code,
    )


@post("/feedback")
async def handle_feedback(request: Request) -> Response[str]:
    try:
        data = await request.json()
    except JSONDecodeError:
        return _json_response({"status": "error", "message": "Некорректный JSON в запросе"}, status_code=400)
    except Exception:
        logger.exception("Failed to parse feedback JSON")
        return _json_response({"status": "error", "message": "Не удалось прочитать данные формы"}, status_code=400)

    if not isinstance(data, dict):
        return _json_response(
            {"status": "error", "message": "Некорректная структура JSON: ожидается объект"},
            status_code=400,
        )

    client_ip = request.client.host if request.client else "unknown"
    if not feedback_rate_limiter.allow(client_ip):
        return _json_response(
            {"status": "error", "message": "Слишком много заявок. Попробуйте позже"},
            status_code=429,
        )

    payload_data: dict[str, Any] = dict(data)

    honeypot_value = str(payload_data.get(HONEYPOT_FIELD) or "").strip()
    if honeypot_value:
        return _json_response({"status": "success"})

    try:
        name = str(payload_data.get("name") or "").strip()
        if not name:
            return _json_response({"status": "error", "message": "Поле 'name' обязательно"}, status_code=400)
        if len(name) > NAME_MAX_LENGTH:
            return _json_response(
                {"status": "error", "message": f"Поле 'name' не должно превышать {NAME_MAX_LENGTH} символов"},
                status_code=400,
            )

        phone = normalize_phone(str(payload_data.get("telephone", "") or ""))
        if not is_valid_phone(phone):
            return _json_response(
                {"status": "error", "message": "Неверный формат телефона. Используйте +7 или 8 и 10 цифр"},
                status_code=400,
            )

        email = str(payload_data.get("email") or "").strip()
        if email and (len(email) > EMAIL_MAX_LENGTH or not is_valid_email(email)):
            return _json_response(
                {"status": "error", "message": "Некорректный email"},
                status_code=400,
            )

        subject = str(payload_data.get("subject") or "").strip()
        if len(subject) > SUBJECT_MAX_LENGTH:
            return _json_response(
                {"status": "error", "message": f"Поле 'subject' не должно превышать {SUBJECT_MAX_LENGTH} символов"},
                status_code=400,
            )

        message = str(payload_data.get("message") or "").strip()
        if len(message) > MESSAGE_MAX_LENGTH:
            return _json_response(
                {"status": "error", "message": f"Сообщение не должно превышать {MESSAGE_MAX_LENGTH} символов"},
                status_code=400,
            )

        consent = payload_data.get("personal_data_consent")
        consent_given = consent is True or str(consent).strip().lower() in {"1", "true", "on", "yes"}
        if not consent_given:
            return _json_response(
                {"status": "error", "message": "Необходимо согласие на обработку персональных данных"},
                status_code=400,
            )

        payload_data["name"] = name
        payload_data["telephone"] = phone

        payload = FeedbackPayload.from_payload(payload_data)
        order = await order_service.create_from_feedback(payload, source="web")
        await notification_service.notify_new_order(order)
        return _json_response({"status": "success"})
    except ValueError as exc:
        return _json_response({"status": "error", "message": str(exc)}, status_code=400)
    except Exception:
        logger.exception("Unhandled feedback error")
        return _json_response({"status": "error", "message": "Внутренняя ошибка сервера"}, status_code=500)


route_handlers = [handle_feedback]
