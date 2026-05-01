"""Deployment-oriented app safety utilities."""

from __future__ import annotations

import os
import re

MAX_GENERATIONS_PER_SESSION = 3


def sanitize_mission_name(value: str, max_length: int = 80) -> str:
    """Return a filesystem-safe mission name fragment."""
    text = (value or "mission").strip().lower().replace(" ", "_")
    text = re.sub(r"[^a-z0-9_-]", "", text)
    text = re.sub(r"_+", "_", text).strip("_")
    if not text:
        text = "mission"
    return text[:max_length]


def get_app_password() -> str | None:
    value = os.getenv("APP_PASSWORD", "").strip()
    return value or None


def has_demo_password() -> bool:
    return get_app_password() is not None


def verify_password(user_input: str, expected: str | None) -> bool:
    if expected is None:
        return True
    return (user_input or "") == expected


def generation_limit_reached(current_count: int, limit: int = MAX_GENERATIONS_PER_SESSION) -> bool:
    return current_count >= limit


def is_production_mode() -> bool:
    return os.getenv("APP_ENV", "").strip().lower() in {"prod", "production"}