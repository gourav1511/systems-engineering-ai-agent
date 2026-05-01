"""Tests for defensive JSON extraction utility."""

import pytest

from utils.json_utils import JsonExtractionError, extract_json_object


def test_extract_plain_json():
    assert extract_json_object('{"a": 1, "b": "x"}') == {"a": 1, "b": "x"}


def test_extract_fenced_json():
    text = '```json\n{"a": 1}\n```'
    assert extract_json_object(text) == {"a": 1}


def test_extract_json_with_surrounding_text():
    text = 'hello\n{"a": 1, "b": 2}\nthanks'
    assert extract_json_object(text) == {"a": 1, "b": 2}


def test_extract_invalid_json_raises():
    with pytest.raises(JsonExtractionError):
        extract_json_object('not json')