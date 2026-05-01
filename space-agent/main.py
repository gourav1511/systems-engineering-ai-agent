"""CLI entry point for space-agent."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from config import ConfigError
from coordinator import Coordinator
from schemas.output_schemas import MissionContext


SAMPLE_MISSION = {
    "mission_name": "LunaObserver-1",
    "mission_type": "Lunar Orbit Remote Sensing",
    "orbit": "Low Lunar Orbit, 100 km circular",
    "lifetime_years": 2,
    "launch_vehicle": "Falcon 9 rideshare",
    "payload_description": "Hyperspectral imager, 10 kg, 50 W",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a Phase 0 spacecraft proposal.")
    parser.add_argument("--input", type=Path, help="Path to mission context JSON file")
    parser.add_argument("--sample", action="store_true", help="Run using sample mission")
    parser.add_argument("--yes", action="store_true", help="Auto-continue through RED warnings")
    return parser.parse_args()


def interactive_mission_context() -> MissionContext:
    print("Enter mission context:")
    return MissionContext(
        mission_name=input("Mission name: ").strip(),
        mission_type=input("Mission type: ").strip(),
        orbit=input("Orbit: ").strip(),
        lifetime_years=float(input("Lifetime (years): ").strip()),
        launch_vehicle=input("Launch vehicle: ").strip(),
        payload_description=input("Payload description: ").strip(),
    )


def load_context_from_file(path: Path) -> MissionContext:
    data = json.loads(path.read_text(encoding="utf-8"))
    return MissionContext.model_validate(data)


async def _run() -> int:
    args = parse_args()

    if args.sample:
        mission_context = MissionContext.model_validate(SAMPLE_MISSION)
    elif args.input:
        mission_context = load_context_from_file(args.input)
    else:
        mission_context = interactive_mission_context()

    coordinator = Coordinator(auto_yes=args.yes or args.sample)
    proposal_path = await coordinator.run(mission_context)
    print(f"Proposal generated: {proposal_path}")
    return 0


def main() -> int:
    try:
        return asyncio.run(_run())
    except ConfigError as exc:
        print(f"Configuration error: {exc}")
        return 2
    except Exception as exc:
        print(f"Run failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())