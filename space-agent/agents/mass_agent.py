"""Mass budget agent."""

from __future__ import annotations

from agents.base_agent import BaseAgent
from prompts.mass_prompt import MASS_SYSTEM_PROMPT
from schemas.output_schemas import MassOutput, MissionContext


class MassAgent(BaseAgent):
    def __init__(self):
        super().__init__("mass_agent", MASS_SYSTEM_PROMPT, MassOutput)

    async def run_for_context(self, mission_context: MissionContext, mission_output: dict) -> dict:
        msg = (
            "Estimate mass budget from mission context and mission output. Return JSON only.\n\n"
            f"Mission context:\n{mission_context.model_dump_json(indent=2)}\n\n"
            f"Mission output:\n{mission_output}"
        )
        return await super().run(msg)