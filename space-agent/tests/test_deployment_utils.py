"""Tests for deployment safety helpers."""

from utils.deployment_utils import (
    MAX_GENERATIONS_PER_SESSION,
    generation_limit_reached,
    sanitize_mission_name,
    verify_password,
)


def test_sanitize_mission_name():
    assert sanitize_mission_name(" Alpine Watch #1 ") == "alpine_watch_1"
    assert sanitize_mission_name("***") == "mission"


def test_generation_limit_helper():
    assert generation_limit_reached(MAX_GENERATIONS_PER_SESSION)
    assert not generation_limit_reached(MAX_GENERATIONS_PER_SESSION - 1)


def test_verify_password():
    assert verify_password("abc", "abc")
    assert not verify_password("abc", "xyz")
    assert verify_password("", None)