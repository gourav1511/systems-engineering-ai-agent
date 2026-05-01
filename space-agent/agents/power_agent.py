"""Power budget agent."""

from __future__ import annotations

from agents.base_agent import BaseAgent
from prompts.power_prompt import POWER_SYSTEM_PROMPT
from schemas.output_schemas import MissionContext, PowerOutput


class PowerAgent(BaseAgent):
    def __init__(self):
        super().__init__("power_agent", POWER_SYSTEM_PROMPT, PowerOutput)

    async def run_for_context(
        self, mission_context: MissionContext, mission_output: dict, mass_output: dict
    ) -> dict:
        msg = (
            "Estimate power budget and EPS sizing from these inputs. Return JSON only.\n\n"
            f"Mission context:\n{mission_context.model_dump_json(indent=2)}\n\n"
            f"Mission output:\n{mission_output}\n\n"
            f"Mass output:\n{mass_output}"
        )
        return await super().run(msg)

    def _normalize_payload(self, payload: dict) -> dict:
        """Coerce common model output variants into PowerOutput schema."""
        normalized = dict(payload or {})
        modes = normalized.get("modes", {})
        coerced_modes: dict[str, dict] = {}

        if isinstance(modes, dict):
            for mode_name, mode_data in modes.items():
                if not isinstance(mode_data, dict):
                    continue
                total_w = mode_data.get("total_W")
                if total_w is None:
                    total_w = mode_data.get("total_with_margin_W")
                if total_w is None:
                    total_w = mode_data.get("total_power_W")

                subsystems = mode_data.get("subsystems")
                if subsystems is None and isinstance(mode_data.get("subsystem_consumption_W"), dict):
                    subsystems = [
                        {"name": str(k), "power_W": float(v)}
                        for k, v in mode_data["subsystem_consumption_W"].items()
                    ]

                coerced_modes[mode_name] = {
                    "total_W": float(total_w or 0.0),
                    "subsystems": subsystems if isinstance(subsystems, list) else [],
                }

        normalized["modes"] = coerced_modes
        return normalized
