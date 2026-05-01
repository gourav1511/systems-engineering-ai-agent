"""Smoke tests for mission context parser."""

import pytest

from utils import mission_context_parser as mcp


def test_parse_mission_description_with_overrides(monkeypatch):
    class FakeParsed:
        def model_dump(self):
            return {
                "mission_name": "AutoName",
                "mission_type": "Earth Observation",
                "orbit": "SSO",
                "lifetime_years": 2.0,
                "launch_vehicle": "Rideshare",
                "payload_description": "Camera",
                "warnings": ["Inferred orbit details."],
            }

    async def fake_parse_async(description: str):
        _ = description
        return FakeParsed()

    monkeypatch.setattr(mcp, "_parse_async", fake_parse_async)

    result = mcp.parse_mission_description(
        "A mission",
        overrides={"mission_name": "OverrideName", "lifetime_years": 3.0},
    )

    assert result["mission_name"] == "OverrideName"
    assert result["lifetime_years"] == 3.0
    assert "warnings" in result


def test_parse_mission_description_empty_raises():
    with pytest.raises(ValueError):
        mcp.parse_mission_description("   ")