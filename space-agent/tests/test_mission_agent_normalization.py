"""Tests mission agent payload normalization."""

from agents.mission_agent import MissionAgent


def test_mission_agent_normalizes_variant_payload():
    agent = object.__new__(MissionAgent)

    raw = {
        "mission_objectives": [{"id": "OBJ-01", "statement": "Objective text"}],
        "requirements": [
            {"id": "MR-01", "statement": "The system shall do X.", "justification": "Needed for mission."}
        ],
        "conops_summary": {
            "launch": "Launch phase.",
            "orbit_insertion": "Insertion phase.",
            "commissioning": "Commissioning phase.",
            "nominal_operations": "Nominal ops.",
            "contingency_operations": "Contingency ops.",
            "end_of_life": "EOL ops.",
        },
        "assumptions": [{"id": "A-01", "statement": "Assumption text"}],
        "open_questions": [{"id": "Q-01", "text": "Question text"}],
    }

    normalized = MissionAgent._normalize_payload(agent, raw)

    assert normalized["objectives"] == ["Objective text"]
    assert normalized["requirements"][0]["text"] == "The system shall do X."
    assert normalized["requirements"][0]["rationale"] == "Needed for mission."
    assert isinstance(normalized["conops_summary"], str)
    assert "Launch:" in normalized["conops_summary"]
    assert normalized["assumptions"] == ["Assumption text"]
    assert normalized["open_questions"] == ["Question text"]