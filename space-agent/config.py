"""Configuration and environment loading."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
import os


load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent
OUTPUTS_DIR = ROOT_DIR / "outputs"
DEBUG_DIR = OUTPUTS_DIR / "debug"

APPROVED_PROCUREMENT_DOMAINS = ["satsearch.co"]
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4")


class ConfigError(RuntimeError):
    """Raised when required configuration is missing."""


def require_api_key() -> str:
    """Return OPENAI_API_KEY or raise a clear configuration error."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise ConfigError(
            "OPENAI_API_KEY is missing. Add it to your environment or .env file."
        )
    return api_key