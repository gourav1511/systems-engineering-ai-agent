"""Utilities for extracting JSON objects from model output."""

from __future__ import annotations

import json
import re
from json import JSONDecodeError


class JsonExtractionError(ValueError):
    """Raised when no valid JSON object can be extracted."""


def extract_json_object(text: str) -> dict:
    """Extract and decode the first JSON object found in text."""
    if not text or not text.strip():
        raise JsonExtractionError("Empty response; expected a JSON object.")

    candidate = text.strip()

    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", candidate, re.DOTALL | re.IGNORECASE)
    if fence_match:
        candidate = fence_match.group(1).strip()

    try:
        obj = json.loads(candidate)
        if isinstance(obj, dict):
            return obj
    except JSONDecodeError:
        pass

    decoder = json.JSONDecoder()
    for i, ch in enumerate(text):
        if ch != "{":
            continue
        try:
            obj, end = decoder.raw_decode(text[i:])
            if isinstance(obj, dict):
                _ = end
                return obj
        except JSONDecodeError:
            continue

    raise JsonExtractionError("Could not extract a valid JSON object from model output.")