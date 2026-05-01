"""Shared base implementation for LLM-backed agents."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from openai import OpenAI
from pydantic import BaseModel, ValidationError

from config import DEFAULT_MODEL, require_api_key
from utils.json_utils import JsonExtractionError, extract_json_object
from utils.logging_utils import log_invalid_output
from utils.retry import retry_async


class AgentExecutionError(RuntimeError):
    """Raised when an agent cannot produce valid structured output."""


class BaseAgent:
    """Base class handling model calls, extraction, validation, and retries."""

    def __init__(self, name: str, system_prompt: str, output_schema: type[BaseModel], model: str | None = None):
        self.name = name
        self.system_prompt = system_prompt
        self.output_schema = output_schema
        self.model = model or DEFAULT_MODEL
        self.client = OpenAI(api_key=require_api_key())

    async def run(self, user_message: str) -> dict:
        """Run one agent call and return validated dictionary output."""
        first_raw = await self._call_model(user_message)
        try:
            return self._parse_and_validate(first_raw)
        except (JsonExtractionError, ValidationError) as exc:
            log_invalid_output(self.name, first_raw, f"First parse/validation failure: {exc}")
            correction = (
                f"Your previous response failed validation for agent {self.name}: {exc}. "
                "Return only corrected JSON matching the schema exactly."
            )
            second_raw = await self._call_model(f"{user_message}\n\n{correction}")
            try:
                return self._parse_and_validate(second_raw)
            except (JsonExtractionError, ValidationError) as exc2:
                log_invalid_output(self.name, second_raw, f"Second parse/validation failure: {exc2}")
                raise AgentExecutionError(
                    f"{self.name} failed to produce valid output after retry."
                ) from exc2

    async def _call_model(self, user_message: str) -> str:
        """Call OpenAI with API retry handling and return plain text."""

        async def _invoke() -> str:
            return await asyncio.to_thread(self._sync_call_model, user_message)

        result = await retry_async(_invoke, max_attempts=3, base_delay_seconds=1.0)
        return str(result)

    def _sync_call_model(self, user_message: str) -> str:
        response = self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_message},
            ],
        )
        text = getattr(response, "output_text", None)
        if text:
            return text
        try:
            return json.dumps(response.model_dump())
        except Exception:
            return str(response)

    def _parse_and_validate(self, raw_text: str) -> dict:
        """Extract JSON object and validate against configured schema."""
        payload = extract_json_object(raw_text)
        payload = self._normalize_payload(payload)
        model = self.output_schema.model_validate(payload)
        return model.model_dump()

    def _normalize_payload(self, payload: dict) -> dict:
        """Hook for subclasses to coerce near-schema payloads before validation."""
        return payload
