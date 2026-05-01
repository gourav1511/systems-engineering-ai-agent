"""Pydantic schemas for mission context and all agent outputs."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class MissionContext(BaseModel):
    mission_name: str
    mission_type: str
    orbit: str
    lifetime_years: float
    launch_vehicle: str
    payload_description: str


class MissionRequirement(BaseModel):
    id: str
    text: str
    rationale: str


class MissionOutput(BaseModel):
    objectives: list[str]
    requirements: list[MissionRequirement]
    conops_summary: str
    assumptions: list[str]
    open_questions: list[str]


class MassSubsystem(BaseModel):
    name: str
    mass_kg: float
    margin_pct: float
    notes: str


class MassOutput(BaseModel):
    subsystems: list[MassSubsystem]
    total_dry_mass_kg: float
    total_wet_mass_kg: float
    mass_margin_pct: float
    status: Literal["GREEN", "YELLOW", "RED"]
    recommendations: list[str]


class PowerSubsystem(BaseModel):
    name: str
    power_W: float


class PowerMode(BaseModel):
    total_W: float
    subsystems: list[PowerSubsystem]


class PowerOutput(BaseModel):
    modes: dict[str, PowerMode]
    solar_array_area_m2: float
    battery_capacity_Wh: float
    eclipse_duration_min: float
    power_margin_pct: float
    status: Literal["GREEN", "YELLOW", "RED"]
    recommendations: list[str]


class CostItem(BaseModel):
    category: str
    cost_kEUR: float
    basis: str


class CostOutput(BaseModel):
    cost_breakdown: list[CostItem]
    total_cost_kEUR: float
    confidence: Literal["LOW", "MEDIUM"]
    assumptions: list[str]
    recommendations: list[str]


class ComponentAlternative(BaseModel):
    rank: int
    product_name: str
    vendor: str
    source_url: str
    unit_price_kEUR: float | None
    lead_time_weeks: int | None
    meets_requirements: bool
    notes: str


class ComponentSearch(BaseModel):
    category: str
    requirement_basis: str
    alternatives: list[ComponentAlternative] = Field(default_factory=list)
    recommended: str | None
    recommendation_rationale: str
    warnings: list[str]


class ProcurementOutput(BaseModel):
    component_searches: list[ComponentSearch]