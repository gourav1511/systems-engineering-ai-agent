# AGENTS.md

## Project goal

Build and maintain `space-agent`, a Python CLI tool that generates Phase 0 spacecraft mission proposal documents.

## Implementation rules

- Use Python 3.11+.
- Keep modules small and readable.
- Use Pydantic v2 for all structured data validation.
- Use the OpenAI Python SDK for LLM calls.
- Use `python-docx` for Word document generation.
- Do not bypass schema validation.
- Do not silently ignore invalid agent output.
- Do not add a GUI for the MVP.
- Do not introduce LangGraph or other orchestration frameworks in the MVP.
- Do not commit secrets or real API keys.

## Testing rules

- Add or update tests when modifying schemas, parsing, or document generation.
- Run `pytest` after implementation changes.
- Ensure `python main.py --sample` produces a `.docx` output.

## Style rules

- Prefer explicit functions and classes.
- Use clear names.
- Add docstrings for public classes and functions.
- Avoid unnecessary abstractions.