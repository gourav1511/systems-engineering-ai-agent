# Systems Engineering AI Agent

A Python + Streamlit application that generates AI-assisted Phase 0 spacecraft mission proposal drafts as editable DOCX files.

## What It Does
- Collects structured mission inputs (currently single-satellite Earth Observation scope).
- Runs a multi-agent pipeline for mission definition, mass budget, power budget, cost estimate, and procurement alternatives.
- Builds a downloadable proposal document (`.docx`) for engineering review and editing.

## How The Code Works
- `space-agent/app.py`: Streamlit UI, input validation, progress tracking, and export actions.
- `space-agent/coordinator.py`: Orchestrates agent execution order and error handling.
- `space-agent/agents/`: LLM-backed agent modules (mission, mass, power, cost, procurement).
- `space-agent/schemas/`: Pydantic models for strict structured I/O.
- `space-agent/assembler/`: DOCX/PDF proposal builders.

## How To Use It
1. Go to `space-agent/`.
2. Install dependencies: `pip install -r requirements.txt`.
3. Configure env vars (`OPENAI_API_KEY`, optional `APP_PASSWORD`) via local `.env` or deployment settings.
4. Run UI: `streamlit run app.py`.
5. Optional CLI: `python main.py --sample --yes`.

## Reuse / Extend
- Replace prompts in `space-agent/prompts/` for your domain.
- Add or swap agent modules in `space-agent/agents/`.
- Keep schemas updated to enforce output quality.