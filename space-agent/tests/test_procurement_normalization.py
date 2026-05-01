"""Tests for procurement normalization helper."""

from agents.procurement_agent import ProcurementAgent


def test_procurement_agent_normalizes_variant_payload():
    agent = object.__new__(ProcurementAgent)
    raw = {
        "component_searches": [
            {
                "category": "OBC",
                "status": "Need rad-tolerant computer",
                "candidates": [
                    {
                        "name": "Example OBC",
                        "supplier": "Vendor A",
                        "url": "https://satsearch.co",
                        "price_kEUR": 12.5,
                        "lead_time_weeks": 20,
                        "comment": "Potential fit",
                    }
                ],
            }
        ]
    }

    normalized = ProcurementAgent._normalize_payload(agent, raw)
    search = normalized["component_searches"][0]

    assert search["requirement_basis"] == "Need rad-tolerant computer"
    assert search["recommended"] is None
    assert "recommendation_rationale" in search
    assert isinstance(search["warnings"], list)
    assert search["alternatives"][0]["product_name"] == "Example OBC"
    assert search["alternatives"][0]["vendor"] == "Vendor A"