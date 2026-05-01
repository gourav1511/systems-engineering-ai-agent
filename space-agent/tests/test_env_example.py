"""Smoke checks for .env.example placeholders."""

from pathlib import Path


def test_env_example_exists_with_placeholders():
    path = Path('.env.example')
    assert path.exists()
    text = path.read_text(encoding='utf-8')
    assert 'OPENAI_API_KEY=your_openai_api_key_here' in text
    assert 'APP_PASSWORD=optional_demo_password_here' in text
    assert 'sk-' not in text