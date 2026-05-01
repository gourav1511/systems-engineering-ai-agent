"""Tests for power/cost normalization helpers."""

from agents.cost_agent import CostAgent
from agents.power_agent import PowerAgent


def test_power_agent_normalizes_mode_variants():
    agent = object.__new__(PowerAgent)
    raw = {
        "modes": {
            "nominal": {
                "total_with_margin_W": 170.8,
                "subsystem_consumption_W": {
                    "Payload": 50.0,
                    "OBC/Data Handling": 15.0,
                },
            }
        }
    }
    normalized = PowerAgent._normalize_payload(agent, raw)
    assert normalized["modes"]["nominal"]["total_W"] == 170.8
    assert len(normalized["modes"]["nominal"]["subsystems"]) == 2


def test_cost_agent_normalizes_breakdown_dict():
    agent = object.__new__(CostAgent)
    raw = {"cost_breakdown": {"Launch": 14000, "Operations": 7600}}
    normalized = CostAgent._normalize_payload(agent, raw)
    assert isinstance(normalized["cost_breakdown"], list)
    assert len(normalized["cost_breakdown"]) == 2
    assert normalized["cost_breakdown"][0]["category"] in {"Launch", "Operations"}