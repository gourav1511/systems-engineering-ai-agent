"""Parse plain-text mission descriptions into structured mission context."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError

from config import DEFAULT_MODEL, require_api_key
from schemas.output_schemas import MissionContext
from utils.json_utils import extract_json_object
from utils.retry import retry_async


PARSER_SYSTEM_PROMPT = (
    "Extract a structured spacecraft mission context from the user's plain-text mission description. "
    "Return only valid JSON matching the required schema. Do not include markdown. "
    "If a field is missing, infer conservatively and mark uncertainty in a warnings array."
)


class ParserOutput(BaseModel):
    mission_name: str
    mission_type: str
    orbit: str
    lifetime_years: float
    launch_vehicle: str
    payload_description: str
    warnings: list[str] = Field(default_factory=list)


def parse_mission_description(description: str, overrides: dict | None = None) -> dict:
    """Parse mission description and return mission context plus warnings."""
    if not description or not description.strip():
        raise ValueError("Mission description is empty.")

    parsed = asyncio.run(_parse_async(description))
    merged = parsed.model_dump()

    if overrides:
        for key, value in overrides.items():
            if value is None:
                continue
            if isinstance(value, str) and not value.strip():
                continue
            merged[key] = value

    context_payload = {
        "mission_name": merged.get("mission_name", "Unnamed-Mission"),
        "mission_type": merged.get("mission_type", "Unspecified mission type"),
        "orbit": merged.get("orbit", "Unspecified orbit"),
        "lifetime_years": merged.get("lifetime_years", 1.0),
        "launch_vehicle": merged.get("launch_vehicle", "TBD launch vehicle"),
        "payload_description": merged.get("payload_description", "Payload details TBD"),
    }

    try:
        validated = MissionContext.model_validate(context_payload)
    except ValidationError as exc:
        raise ValueError(f"Parsed mission context failed validation: {exc}") from exc

    final = validated.model_dump()
    final["warnings"] = merged.get("warnings", [])
    return final


async def _parse_async(description: str) -> ParserOutput:
    client = OpenAI(api_key=require_api_key())

    async def _invoke() -> str:
        return await asyncio.to_thread(_sync_parse_call, client, description)

    raw_text = await retry_async(_invoke, max_attempts=3, base_delay_seconds=1.0)
    payload = extract_json_object(str(raw_text))
    return ParserOutput.model_validate(payload)


def _sync_parse_call(client: OpenAI, description: str) -> str:
    response = client.responses.create(
        model=DEFAULT_MODEL,
        input=[
            {"role": "system", "content": PARSER_SYSTEM_PROMPT},
            {"role": "user", "content": description},
        ],
    )
    text = getattr(response, "output_text", None)
    if text:
        return text
    try:
        return json.dumps(response.model_dump())
    except Exception:
        return str(response)