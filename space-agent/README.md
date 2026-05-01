# space-agent

`space-agent` is a Python 3.11+ CLI tool that generates a Phase 0 spacecraft mission proposal Word document from mission context input.

## Architecture

```text
User mission input
        |
        v
Coordinator
        |
        v
Mission Agent
        |
        v
Mass Agent
        |
        +-------------------+
        |                   |
        v                   v
Power Agent           Cost Agent
        |                   |
        +---------+---------+
                  |
                  v
Procurement Agent
                  |
                  v
Proposal Builder (.docx)
```

## Setup

1. Create and activate Python 3.11+ environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure environment:

```bash
copy .env.example .env
```

Set `OPENAI_API_KEY` in `.env`.

## Run

Interactive:

```bash
python main.py
```

JSON file input:

```bash
python main.py --input mission_context.json
```

Sample mission:

```bash
python main.py --sample
python main.py --sample --yes
```

Streamlit app:

```bash
streamlit run app.py
```

## Sample input JSON

```json
{
  "mission_name": "LunaObserver-1",
  "mission_type": "Lunar Orbit Remote Sensing",
  "orbit": "Low Lunar Orbit, 100 km circular",
  "lifetime_years": 2,
  "launch_vehicle": "Falcon 9 rideshare",
  "payload_description": "Hyperspectral imager, 10 kg, 50 W"
}
```

## Expected output

Generated file:

```text
outputs/Phase_0_Proposal_<mission_name>.docx
```

## Known limitations

- Procurement data may use structured fallback plans when live web sourcing is unavailable.
- Outputs are Phase 0 draft estimates and require engineering review.
- No high-fidelity subsystem simulation is included.

## Future extensions

- Add Thermal, ADCS, Communications, Orbit/Access, and Risk agents.
- Add more approved procurement domains.
- Add PDF export and optional web UI.
- Add persistent mission history and report comparison workflows.

## Deployment note

This Streamlit version is intended for MVP validation. A future Vercel deployment would require either a React/Next.js frontend with a Python API backend, or migration to a platform that supports Streamlit directly.
