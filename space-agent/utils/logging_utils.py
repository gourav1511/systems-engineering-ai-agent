"""Logging helpers for debug outputs."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from config import DEBUG_DIR


def log_invalid_output(agent_name: str, raw_text: str, reason: str) -> Path:
    """Write invalid model output for inspection and return path."""
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    path = DEBUG_DIR / f"{agent_name}_invalid_output.txt"
    with path.open("a", encoding="utf-8") as f:
        f.write(f"\n\n[{datetime.utcnow().isoformat()}Z] {reason}\n")
        f.write(raw_text)
        f.write("\n")
    return path