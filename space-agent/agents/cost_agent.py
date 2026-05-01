"""Cost estimate agent."""

from __future__ import annotations

from agents.base_agent import BaseAgent
from prompts.cost_prompt import COST_SYSTEM_PROMPT
from schemas.output_schemas import CostOutput, MissionContext


class CostAgent(BaseAgent):
    def __init__(self):
        super().__init__("cost_agent", COST_SYSTEM_PROMPT, CostOutput)

    async def run_for_context(
        self, mission_context: MissionContext, mission_output: dict, mass_output: dict
    ) -> dict:
        msg = (
            "Create a Phase 0 ROM cost estimate from these inputs. Return JSON only.\n\n"
            f"Mission context:\n{mission_context.model_dump_json(indent=2)}\n\n"
            f"Mission output:\n{mission_output}\n\n"
            f"Mass output:\n{mass_output}"
        )
        return await super().run(msg)

    def _normalize_payload(self, payload: dict) -> dict:
        """Coerce common model output variants into CostOutput schema."""
        normalized = dict(payload or {})
        breakdown = normalized.get("cost_breakdown", [])
        if isinstance(breakdown, dict):
            normalized["cost_breakdown"] = [
                {
                    "category": self._normalize_category_name(str(category)),
                    "cost_kEUR": float(value),
                    "basis": "Engineering judgment",
                }
                for category, value in breakdown.items()
            ]
        assumptions = normalized.get("assumptions")
        if not isinstance(assumptions, list):
            assumptions = normalized.get("key_assumptions", [])
        normalized["assumptions"] = [str(item) for item in assumptions] if isinstance(assumptions, list) else []

        recommendations = normalized.get("recommendations", [])
        if not isinstance(recommendations, list):
            recommendations = []
        normalized["recommendations"] = [str(item) for item in recommendations]
        return normalized

    @staticmethod
    def _normalize_category_name(raw: str) -> str:
        key = raw.strip().replace("_kEUR", "").replace("_", " ").strip()
        mapping = {
            "spacecraft hardware": "Spacecraft Hardware",
            "integration and test": "Integration & Test",
            "launch": "Launch",
            "ground segment": "Ground Segment",
            "operations": "Operations",
            "program management": "Program Management",
            "contingency": "Contingency",
        }
        return mapping.get(key.lower(), key.title())
