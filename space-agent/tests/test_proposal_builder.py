"""Tests for proposal builder output."""

from pathlib import Path
import shutil

from docx import Document

from assembler.proposal_builder import ProposalBuilder


def test_proposal_builder_creates_docx(monkeypatch):
    local_tmp = Path("tests_tmp_output")
    if local_tmp.exists():
        shutil.rmtree(local_tmp)
    local_tmp.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr("assembler.proposal_builder.OUTPUTS_DIR", local_tmp)

    mission_context = {
        "mission_name": "LunaObserver-1",
        "mission_type": "Lunar Orbit Remote Sensing",
        "orbit": "Low Lunar Orbit, 100 km circular",
        "lifetime_years": 2,
        "launch_vehicle": "Falcon 9 rideshare",
        "payload_description": "Hyperspectral imager, 10 kg, 50 W",
    }

    outputs = {
        "mission": {
            "objectives": ["Objective A"],
            "requirements": [{"id": "MR-01", "text": "The system shall do X.", "rationale": "Because Y."}],
            "conops_summary": "Launch to EOL summary.",
            "assumptions": ["Assumption A"],
            "open_questions": ["Question A"],
        },
        "mass": {
            "subsystems": [{"name": "Structure", "mass_kg": 20.0, "margin_pct": 20.0, "notes": "Note"}],
            "total_dry_mass_kg": 100.0,
            "total_wet_mass_kg": 130.0,
            "mass_margin_pct": 20.0,
            "status": "GREEN",
            "recommendations": [],
        },
        "power": {
            "modes": {"nominal": {"total_W": 100.0, "subsystems": []}, "peak": {"total_W": 120.0, "subsystems": []}, "safe mode": {"total_W": 40.0, "subsystems": []}},
            "solar_array_area_m2": 1.2,
            "battery_capacity_Wh": 500.0,
            "eclipse_duration_min": 30.0,
            "power_margin_pct": 18.0,
            "status": "GREEN",
            "recommendations": [],
        },
        "cost": {
            "cost_breakdown": [{"category": "Launch", "cost_kEUR": 5000.0, "basis": "Analogy"}],
            "total_cost_kEUR": 10000.0,
            "confidence": "LOW",
            "assumptions": [],
            "recommendations": [],
        },
        "procurement": {
            "component_searches": [
                {
                    "category": "OBC",
                    "requirement_basis": "C&DH",
                    "alternatives": [
                        {
                            "rank": 1,
                            "product_name": "Placeholder",
                            "vendor": "TBD",
                            "source_url": "https://satsearch.co",
                            "unit_price_kEUR": None,
                            "lead_time_weeks": None,
                            "meets_requirements": False,
                            "notes": "Fallback",
                        }
                    ],
                    "recommended": None,
                    "recommendation_rationale": "No live data",
                    "warnings": ["Gap"],
                }
            ]
        },
    }

    builder = ProposalBuilder()
    output_path = builder.build_proposal(mission_context, outputs)

    assert output_path.exists()
    assert output_path.suffix == ".docx"
    assert output_path.stat().st_size > 0

    doc = Document(output_path)
    text = "\n".join(p.text for p in doc.paragraphs)
    for heading in [
        "MVP Scope and Limitations",
        "Executive Summary",
        "Mission Overview",
        "Mission Requirements",
        "Mass Budget",
        "Power Budget",
        "Cost Estimate",
        "Component Alternatives",
        "Assumptions and Open Items",
        "Disclaimer",
    ]:
        assert heading in text
