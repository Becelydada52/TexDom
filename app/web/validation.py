from __future__ import annotations

import re


PHONE_PATTERN = re.compile(r"^(\+7|8)\d{10}$")


def normalize_phone(raw_phone: str) -> str:
    return re.sub(r"[^\d+]", "", raw_phone or "")


def is_valid_phone(phone: str) -> bool:
    return bool(PHONE_PATTERN.match(phone))

