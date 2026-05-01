"""Schema validation tests."""

from schemas.output_schemas import (
    CostOutput,
    MassOutput,
    MissionOutput,
    PowerOutput,
    ProcurementOutput,
)


def test_mission_output_schema_valid():
    payload = {
        "objectives": ["Map lunar mineralogy"],
        "requirements": [
            {
                "id": "MR-01",
                "text": "The payload shall capture hyperspectral imagery at 30 m GSD.",
                "rationale": "Meet remote sensing objective.",
            }
        ],
        "conops_summary": "Launch, insertion, commissioning, nominal, contingency, EOL.",
        "assumptions": ["Rideshare insertion accuracy within mission budget."],
        "open_questions": ["Confirm lunar relay availability for downlink windows."],
    }
    assert MissionOutput.model_validate(payload)


def test_mass_output_schema_valid():
    payload = {
        "subsystems": [{"name": "Structure", "mass_kg": 25.0, "margin_pct": 20.0, "notes": "Conceptual"}],
        "total_dry_mass_kg": 110.0,
        "total_wet_mass_kg": 140.0,
        "mass_margin_pct": 20.0,
        "status": "GREEN",
        "recommendations": ["Refine propulsion budget in Phase A."],
    }
    assert MassOutput.model_validate(payload)


def test_power_output_schema_valid():
    payload = {
        "modes": {
            "nominal": {"total_W": 120.0, "subsystems": [{"name": "Payload", "power_W": 50.0}]},
            "peak": {"total_W": 160.0, "subsystems": [{"name": "Comms", "power_W": 60.0}]},
            "safe mode": {"total_W": 45.0, "subsystems": [{"name": "OBC", "power_W": 20.0}]},
        },
        "solar_array_area_m2": 1.8,
        "battery_capacity_Wh": 620.0,
        "eclipse_duration_min": 35.0,
        "power_margin_pct": 18.0,
        "status": "GREEN",
        "recommendations": ["Run detailed EPS analysis in Phase A."],
    }
    assert PowerOutput.model_validate(payload)


def test_cost_output_schema_valid():
    payload = {
        "cost_breakdown": [{"category": "Launch", "cost_kEUR": 6500.0, "basis": "Analogy"}],
        "total_cost_kEUR": 18000.0,
        "confidence": "LOW",
        "assumptions": ["Shared launch integration profile."],
        "recommendations": ["Collect vendor quotes in next phase."],
    }
    assert CostOutput.model_validate(payload)


def test_procurement_output_schema_valid():
    payload = {
        "component_searches": [
            {
                "category": "OBC",
                "requirement_basis": "Radiation-tolerant command and data handling",
                "alternatives": [
                    {
                        "rank": 1,
                        "product_name": "Plan Placeholder",
                        "vendor": "TBD",
                        "source_url": "https://satsearch.co",
                        "unit_price_kEUR": None,
                        "lead_time_weeks": None,
                        "meets_requirements": False,
                        "notes": "Fallback sourcing plan.",
                    }
                ],
                "recommended": None,
                "recommendation_rationale": "No validated web results yet.",
                "warnings": ["Sourcing gap: web search unavailable."],
            }
        ]
    }
    assert ProcurementOutput.model_validate(payload)