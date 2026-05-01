"""Pipeline coordinator for space-agent."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Callable

from agents.base_agent import AgentExecutionError
from agents.cost_agent import CostAgent
from agents.mass_agent import MassAgent
from agents.mission_agent import MissionAgent
from agents.power_agent import PowerAgent
from agents.procurement_agent import ProcurementAgent
from assembler.proposal_builder import ProposalBuilder
from schemas.output_schemas import MissionContext


ProgressCallback = Callable[[str, str], None]


class Coordinator:
    """Orchestrates dependent execution across all agents."""

    def __init__(self, *, auto_yes: bool = False):
        self.auto_yes = auto_yes
        self.mission_agent = MissionAgent()
        self.mass_agent = MassAgent()
        self.power_agent = PowerAgent()
        self.cost_agent = CostAgent()
        self.procurement_agent = ProcurementAgent()
        self.builder = ProposalBuilder()

    async def run(self, mission_context: MissionContext) -> Path:
        result = await self.run_with_outputs(mission_context)
        return result["docx_path"]

    async def run_with_outputs(
        self,
        mission_context: MissionContext,
        *,
        progress_callback: ProgressCallback | None = None,
        build_docx: bool = True,
    ) -> dict:
        failures: list[dict] = []
        self._progress(progress_callback, "Mission analysis", "running")
        mission = await self.mission_agent.run_for_context(mission_context)
        print("Mission Agent complete")
        print(f"mission keys: {list(mission.keys())}")
        self._progress(progress_callback, "Mission analysis", "done")

        self._progress(progress_callback, "Mass budget", "running")
        mass = await self._run_noncritical(
            "mass", self.mass_agent.run_for_context(mission_context, mission), failures
        )
        print("Mass Agent complete")
        print(f"mass keys: {list(mass.keys())}")
        self._progress(progress_callback, "Mass budget", "done")

        if mass.get("status") == "RED" and not self._should_continue("Mass"):
            raise RuntimeError("Aborted by user after RED mass status.")

        self._progress(progress_callback, "Power budget", "running")
        self._progress(progress_callback, "Cost estimate", "running")
        power_coro = self._run_noncritical(
            "power", self.power_agent.run_for_context(mission_context, mission, mass), failures
        )
        cost_coro = self._run_noncritical(
            "cost", self.cost_agent.run_for_context(mission_context, mission, mass), failures
        )
        power, cost = await asyncio.gather(power_coro, cost_coro)
        print("Power Agent complete")
        print(f"power keys: {list(power.keys())}")
        print("Cost Agent complete")
        print(f"cost keys: {list(cost.keys())}")
        self._progress(progress_callback, "Power budget", "done")
        self._progress(progress_callback, "Cost estimate", "done")

        if power.get("status") == "RED" and not self._should_continue("Power"):
            raise RuntimeError("Aborted by user after RED power status.")

        self._progress(progress_callback, "Procurement search", "running")
        procurement = await self._run_noncritical(
            "procurement",
            self.procurement_agent.run_for_context(mission_context, mission, mass, power, cost),
            failures,
        )
        print("Procurement Agent complete")
        print(f"procurement keys: {list(procurement.keys())}")
        self._progress(progress_callback, "Procurement search", "done")

        outputs = {
            "mission_context": mission_context.model_dump(),
            "mission": mission,
            "mass": mass,
            "power": power,
            "cost": cost,
            "procurement": procurement,
        }

        docx_path = None
        if build_docx:
            self._progress(progress_callback, "Proposal assembly", "running")
            docx_path = self.builder.build_proposal(mission_context.model_dump(), outputs)
            self._progress(progress_callback, "Proposal assembly", "done")

        return {"outputs": outputs, "docx_path": docx_path, "failures": failures}

    async def _run_noncritical(self, section_name: str, coro, failures: list[dict]) -> dict:
        try:
            return await coro
        except AgentExecutionError as exc:
            message = f"{section_name} failed validation after retries: {exc}"
            print(f"WARNING: {message}")
            failures.append({"section": section_name, "error": str(exc)})
            return self._placeholder(section_name, str(exc))
        except Exception as exc:
            message = f"{section_name} failed with unexpected error: {exc}"
            print(f"WARNING: {message}")
            failures.append({"section": section_name, "error": str(exc)})
            return self._placeholder(section_name, str(exc))

    def _should_continue(self, section: str) -> bool:
        print(f"WARNING: {section} returned RED status.")
        if self.auto_yes:
            print("Auto-continue enabled; proceeding.")
            return True
        response = input("Continue anyway? [y/N]: ").strip().lower()
        return response in {"y", "yes"}

    def _progress(self, callback: ProgressCallback | None, step: str, status: str) -> None:
        if callback:
            callback(step, status)

    def _placeholder(self, section_name: str, error: str) -> dict:
        if section_name == "mass":
            return {
                "subsystems": [],
                "total_dry_mass_kg": 0.0,
                "total_wet_mass_kg": 0.0,
                "mass_margin_pct": 0.0,
                "status": "RED",
                "recommendations": ["Fallback used: Mass output unavailable; rerun analysis."],
                "_fallback": True,
                "_error": error,
            }
        if section_name == "power":
            return {
                "modes": {
                    "nominal": {"total_W": 0.0, "subsystems": []},
                    "peak": {"total_W": 0.0, "subsystems": []},
                    "safe mode": {"total_W": 0.0, "subsystems": []},
                },
                "solar_array_area_m2": 0.0,
                "battery_capacity_Wh": 0.0,
                "eclipse_duration_min": 0.0,
                "power_margin_pct": 0.0,
                "status": "RED",
                "recommendations": ["Fallback used: Power output unavailable; rerun analysis."],
                "_fallback": True,
                "_error": error,
            }
        if section_name == "cost":
            return {
                "cost_breakdown": [],
                "total_cost_kEUR": 0.0,
                "confidence": "LOW",
                "assumptions": ["Fallback used: Cost output unavailable; placeholder used."],
                "recommendations": ["Fallback used: Rerun cost estimate."],
                "_fallback": True,
                "_error": error,
            }
        if section_name == "procurement":
            return {
                "component_searches": [
                    {
                        "category": "Fallback",
                        "requirement_basis": "No validated procurement output.",
                        "alternatives": [],
                        "recommended": None,
                        "recommendation_rationale": "No recommendation due to missing validated output.",
                        "warnings": [f"Sourcing gap: procurement output unavailable. Fallback used. Error: {error}"],
                    }
                ],
                "_fallback": True,
                "_error": error,
            }
        return {}
