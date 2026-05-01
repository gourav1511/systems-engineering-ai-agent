"""Procurement alternatives agent."""

from __future__ import annotations

from agents.base_agent import BaseAgent
from config import APPROVED_PROCUREMENT_DOMAINS
from prompts.procurement_prompt import PROCUREMENT_SYSTEM_PROMPT
from schemas.output_schemas import MissionContext, ProcurementOutput


class ProcurementAgent(BaseAgent):
    def __init__(self):
        super().__init__("procurement_agent", PROCUREMENT_SYSTEM_PROMPT, ProcurementOutput)

    async def run_for_context(
        self,
        mission_context: MissionContext,
        mission_output: dict,
        mass_output: dict,
        power_output: dict,
        cost_output: dict,
    ) -> dict:
        msg = (
            "Find component alternatives under approved domains, or provide a no-fabrication fallback sourcing plan "
            "if web search is unavailable. Return JSON only.\n\n"
            f"Approved domains: {APPROVED_PROCUREMENT_DOMAINS}\n\n"
            f"Mission context:\n{mission_context.model_dump_json(indent=2)}\n\n"
            f"Mission output:\n{mission_output}\n\n"
            f"Mass output:\n{mass_output}\n\n"
            f"Power output:\n{power_output}\n\n"
            f"Cost output:\n{cost_output}"
        )
        return await super().run(msg)

    def _normalize_payload(self, payload: dict) -> dict:
        """Coerce common procurement output variants into ProcurementOutput schema."""
        normalized = dict(payload or {})
        searches = normalized.get("component_searches")
        if not isinstance(searches, list):
            searches = normalized.get("searches", [])
        coerced_searches: list[dict] = []

        if isinstance(searches, list):
            for search in searches:
                if not isinstance(search, dict):
                    continue
                alternatives = search.get("alternatives")
                if not isinstance(alternatives, list):
                    alternatives = search.get("candidates", [])

                coerced_alts: list[dict] = []
                if isinstance(alternatives, list):
                    for i, alt in enumerate(alternatives):
                        if not isinstance(alt, dict):
                            continue
                        coerced_alts.append(
                            {
                                "rank": int(alt.get("rank", i + 1)),
                                "product_name": str(alt.get("product_name") or alt.get("name") or "Unknown"),
                                "vendor": str(alt.get("vendor") or alt.get("supplier") or "Unknown"),
                                "source_url": str(alt.get("source_url") or alt.get("url") or ""),
                                "unit_price_kEUR": self._as_float_or_none(alt.get("unit_price_kEUR", alt.get("price_kEUR"))),
                                "lead_time_weeks": self._as_int_or_none(alt.get("lead_time_weeks")),
                                "meets_requirements": bool(alt.get("meets_requirements", False)),
                                "notes": str(alt.get("notes") or alt.get("comment") or ""),
                            }
                        )

                coerced_searches.append(
                    {
                        "category": str(search.get("category", "Unknown")),
                        "requirement_basis": str(
                            search.get("requirement_basis")
                            or search.get("status")
                            or "Requirement basis not explicitly provided."
                        ),
                        "alternatives": coerced_alts,
                        "recommended": search.get("recommended"),
                        "recommendation_rationale": str(
                            search.get("recommendation_rationale")
                            or search.get("rationale")
                            or "No recommendation rationale provided."
                        ),
                        "warnings": [str(w) for w in search.get("warnings", [])] if isinstance(search.get("warnings"), list) else [],
                    }
                )

        normalized["component_searches"] = coerced_searches
        return normalized

    @staticmethod
    def _as_float_or_none(value):
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _as_int_or_none(value):
        if value is None or value == "":
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
