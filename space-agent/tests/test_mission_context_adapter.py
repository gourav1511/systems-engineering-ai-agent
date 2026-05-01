"""Tests for GUI-to-agent mission context adapter."""

from utils.mission_context_adapter import build_agent_mission_context


def test_build_agent_mission_context():
    gui_input = {
        "mission_name": "AlpineWatch-1",
        "mission_type": "Earth Observation",
        "altitude_km": 550,
        "inclination_deg": 97.6,
        "lifetime_years": 3,
        "payload_details": "Multispectral payload with 40 km swath width and 5 m GSD.",
        "mission_scope": "single_satellite",
        "payload_type": "earth_observation",
    }

    expected = {
        "mission_name": "AlpineWatch-1",
        "mission_type": "Earth Observation",
        "orbit": "550 km circular orbit, 97.6 deg inclination",
        "lifetime_years": 3,
        "launch_vehicle": "Launch vehicle not specified for MVP",
        "payload_description": "Multispectral payload with 40 km swath width and 5 m GSD.",
    }

    assert build_agent_mission_context(gui_input) == expected