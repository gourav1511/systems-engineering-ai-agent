"""Pipeline test for non-empty power and cost outputs."""

import asyncio

from coordinator import Coordinator
from schemas.output_schemas import MissionContext


def test_power_cost_pipeline_nonzero(monkeypatch):
    context = MissionContext.model_validate(
        {
            "mission_name": "NewSat",
            "mission_type": "Earth Observation",
            "orbit": "550 km circular orbit, 97.6 deg inclination",
            "lifetime_years": 3,
            "launch_vehicle": "Falcon 9 Transporter rideshare",
            "payload_description": "Multispectral Earth Observation payload with 40 km swath width, 1 m GSD, 40 kg payload mass, and 60 W nominal power consumption.",
        }
    )

    coordinator = Coordinator(auto_yes=True)

    async def mission_stub(_context):
        return {
            "objectives": ["EO imaging"],
            "requirements": [{"id": "MR-01", "text": "The payload shall image Earth.", "rationale": "Mission objective."}],
            "conops_summary": "Launch and operate.",
            "assumptions": ["Assumption"],
            "open_questions": ["Question"],
        }

    async def mass_stub(_context, _mission):
        return {
            "subsystems": [{"name": "Payload", "mass_kg": 40.0, "margin_pct": 20.0, "notes": "Given"}],
            "total_dry_mass_kg": 180.0,
            "total_wet_mass_kg": 220.0,
            "mass_margin_pct": 20.0,
            "status": "GREEN",
            "recommendations": ["Refine in Phase A"],
        }

    async def power_stub(_context, _mission, _mass):
        return {
            "modes": {
                "nominal": {"total_W": 180.0, "subsystems": [{"name": "Payload", "power_W": 60.0}]},
                "peak": {"total_W": 240.0, "subsystems": [{"name": "Payload", "power_W": 80.0}]},
                "safe_mode": {"total_W": 90.0, "subsystems": [{"name": "Payload", "power_W": 20.0}]},
            },
            "solar_array_area_m2": 1.9,
            "battery_capacity_Wh": 750.0,
            "eclipse_duration_min": 36.0,
            "power_margin_pct": 18.0,
            "status": "GREEN",
            "recommendations": ["Validate with detailed EPS model."],
        }

    async def cost_stub(_context, _mission, _mass):
        return {
            "cost_breakdown": [
                {"category": "Spacecraft Hardware", "cost_kEUR": 8200.0, "basis": "Parametric model"},
                {"category": "Integration & Test", "cost_kEUR": 2600.0, "basis": "Engineering judgment"},
                {"category": "Launch", "cost_kEUR": 5200.0, "basis": "Analogy"},
                {"category": "Ground Segment", "cost_kEUR": 1100.0, "basis": "Analogy"},
                {"category": "Operations", "cost_kEUR": 1800.0, "basis": "Engineering judgment"},
                {"category": "Program Management", "cost_kEUR": 1200.0, "basis": "Engineering judgment"},
                {"category": "Contingency", "cost_kEUR": 4000.0, "basis": "Phase 0 uncertainty"},
            ],
            "total_cost_kEUR": 24100.0,
            "confidence": "LOW",
            "assumptions": ["ROM estimate."],
            "recommendations": ["Refine with vendor quotes."],
        }

    async def procurement_stub(_context, _mission, _mass, _power, _cost):
        return {
            "component_searches": [
                {
                    "category": "OBC",
                    "requirement_basis": "EO mission baseline",
                    "alternatives": [],
                    "recommended": None,
                    "recommendation_rationale": "Placeholder",
                    "warnings": ["Web search unavailable"],
                }
            ]
        }

    monkeypatch.setattr(coordinator.mission_agent, "run_for_context", mission_stub)
    monkeypatch.setattr(coordinator.mass_agent, "run_for_context", mass_stub)
    monkeypatch.setattr(coordinator.power_agent, "run_for_context", power_stub)
    monkeypatch.setattr(coordinator.cost_agent, "run_for_context", cost_stub)
    monkeypatch.setattr(coordinator.procurement_agent, "run_for_context", procurement_stub)

    result = asyncio.run(coordinator.run_with_outputs(context, build_docx=False))
    outputs = result["outputs"]

    power = outputs["power"]
    cost = outputs["cost"]

    assert power["modes"]["nominal"]["total_W"] > 0
    assert power["modes"]["peak"]["total_W"] > 0
    assert power["solar_array_area_m2"] > 0
    assert power["battery_capacity_Wh"] > 0
    assert len(cost["cost_breakdown"]) >= 5
    assert cost["total_cost_kEUR"] > 0
