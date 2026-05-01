"""Smoke tests for PDF builder."""

from pathlib import Path
import shutil

from assembler.pdf_builder import build_pdf_proposal


def test_build_pdf_proposal_creates_file():
    local_tmp = Path("tests_tmp_pdf")
    if local_tmp.exists():
        shutil.rmtree(local_tmp)
    local_tmp.mkdir(parents=True, exist_ok=True)

    outputs = {
        "mission_context": {
            "mission_name": "LunaObserver-1",
            "mission_type": "Lunar Orbit Remote Sensing",
        },
        "mission": {
            "objectives": ["Map terrain"],
            "requirements": [{"id": "MR-01", "text": "The payload shall capture imagery.", "rationale": "Science return"}],
            "conops_summary": "Launch and operate.",
            "assumptions": ["Assumption A"],
            "open_questions": ["Question A"],
        },
        "mass": {"status": "GREEN", "subsystems": []},
        "power": {"status": "GREEN", "modes": {"nominal": {"total_W": 25.0, "subsystems": []}}},
        "cost": {"cost_breakdown": []},
        "procurement": {"component_searches": []},
    }

    out = local_tmp / "proposal.pdf"
    result = build_pdf_proposal(outputs, str(out))
    assert Path(result).exists()
    assert Path(result).stat().st_size > 0