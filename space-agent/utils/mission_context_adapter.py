"""Adapter between GUI mission inputs and legacy agent mission context."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class GuiMissionContext(BaseModel):
    mission_name: str
    mission_type: str
    altitude_km: float
    inclination_deg: float
    lifetime_years: float
    payload_details: str
    mission_scope: str = Field(default="single_satellite")
    payload_type: str = Field(default="earth_observation")

    @field_validator("mission_name", "mission_type", "payload_details")
    @classmethod
    def _not_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Field cannot be empty.")
        return value.strip()

    @field_validator("altitude_km")
    @classmethod
    def _altitude_range(cls, value: float) -> float:
        if value <= 100 or value >= 2000:
            raise ValueError("altitude_km must be > 100 and < 2000.")
        return value

    @field_validator("inclination_deg")
    @classmethod
    def _inclination_range(cls, value: float) -> float:
        if value < 0 or value > 180:
            raise ValueError("inclination_deg must be >= 0 and <= 180.")
        return value

    @field_validator("lifetime_years")
    @classmethod
    def _lifetime_range(cls, value: float) -> float:
        if value <= 0 or value > 15:
            raise ValueError("lifetime_years must be > 0 and <= 15.")
        return value


def validate_gui_mission_context(gui_context: dict) -> GuiMissionContext:
    """Validate the GUI mission context schema and constraints."""
    return GuiMissionContext.model_validate(gui_context)


def payload_details_quality_warning(payload_details: str) -> str | None:
    """Return warning if payload details omit swath or resolution/GSD keywords."""
    details = (payload_details or "").lower()
    has_swath = "swath" in details
    has_resolution = "resolution" in details or "gsd" in details or "ground sampling" in details
    if has_swath and has_resolution:
        return None
    return (
        "Payload details should mention swath width and ground resolution/GSD for Earth Observation missions."
    )


def build_agent_mission_context(gui_context: dict) -> dict:
    """Convert GUI mission context into legacy agent-compatible mission context."""
    validated = validate_gui_mission_context(gui_context)
    return {
        "mission_name": validated.mission_name,
        "mission_type": validated.mission_type,
        "orbit": f"{validated.altitude_km:g} km circular orbit, {validated.inclination_deg:g} deg inclination",
        "lifetime_years": validated.lifetime_years,
        "launch_vehicle": "Launch vehicle not specified for MVP",
        "payload_description": validated.payload_details,
    }