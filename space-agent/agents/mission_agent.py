"""Mission agent with two-pass correction."""

from __future__ import annotations

import json

from agents.base_agent import BaseAgent
from prompts.mission_prompt import MISSION_CRITIQUE_PROMPT, MISSION_SYSTEM_PROMPT
from schemas.output_schemas import MissionContext, MissionOutput


class MissionAgent(BaseAgent):
    def __init__(self):
        super().__init__("mission_agent", MISSION_SYSTEM_PROMPT, MissionOutput)

    async def run_for_context(self, mission_context: MissionContext) -> dict:
        base_message = (
            "Create mission objectives, requirements, ConOps summary, assumptions, and open questions "
            "for this mission context. Return JSON only.\n\n"
            f"Mission context:\n{mission_context.model_dump_json(indent=2)}"
        )
        first_pass = await super().run(base_message)
        correction_message = (
            "Critique and correct this draft output. Return corrected JSON only.\n\n"
            f"Draft JSON:\n{json.dumps(first_pass, indent=2)}\n\n"
            f"{MISSION_CRITIQUE_PROMPT}"
        )
        corrected = await super().run(correction_message)
        return corrected

    def _normalize_payload(self, payload: dict) -> dict:
        """Coerce common model output variants into MissionOutput schema."""
        normalized = dict(payload or {})

        # Objectives may come as mission_objectives list[dict] or objectives list[dict].
        objectives = normalized.get("objectives")
        if objectives is None and "mission_objectives" in normalized:
            objectives = normalized.get("mission_objectives")
        normalized["objectives"] = self._as_text_list(objectives)

        # Requirements may come with "statement" instead of "text".
        reqs = normalized.get("requirements", [])
        coerced_reqs: list[dict] = []
        if isinstance(reqs, list):
            for idx, req in enumerate(reqs):
                if not isinstance(req, dict):
                    continue
                req_id = str(req.get("id", f"MR-{idx+1:02d}"))
                text = str(req.get("text") or req.get("statement") or "").strip()
                rationale = str(req.get("rationale") or req.get("justification") or "Engineering rationale.").strip()
                if text:
                    coerced_reqs.append({"id": req_id, "text": text, "rationale": rationale})
        normalized["requirements"] = coerced_reqs

        # ConOps may come as structured dict of phases.
        conops = normalized.get("conops_summary")
        if isinstance(conops, dict):
            phase_order = [
                "launch",
                "orbit_insertion",
                "commissioning",
                "nominal_operations",
                "contingency_operations",
                "end_of_life",
            ]
            parts = []
            for phase in phase_order:
                value = conops.get(phase)
                if value:
                    parts.append(f"{phase.replace('_', ' ').title()}: {value}")
            normalized["conops_summary"] = " ".join(parts).strip()

        normalized["assumptions"] = self._as_text_list(normalized.get("assumptions"))
        normalized["open_questions"] = self._as_text_list(normalized.get("open_questions"))
        return normalized

    @staticmethod
    def _as_text_list(value) -> list[str]:
        if not isinstance(value, list):
            return []
        items: list[str] = []
        for entry in value:
            if isinstance(entry, str):
                text = entry.strip()
                if text:
                    items.append(text)
                continue
            if isinstance(entry, dict):
                text = str(entry.get("text") or entry.get("statement") or "").strip()
                if text:
                    items.append(text)
        return items
