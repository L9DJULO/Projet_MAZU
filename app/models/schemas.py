from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class VehicleInfo(BaseModel):
    make: str
    model: str
    year: int = Field(..., ge=1980, le=2030)
    mileage_km: int = Field(..., ge=0)
    vin: Optional[str] = None
    base_market_value: Optional[float] = None


class DamageType(str, Enum):
    SCRATCH = "rayure"
    DENT = "bosse"
    CRACK = "fissure"
    TIRE_WEAR = "usure_pneu"
    RUST = "corrosion"
    BROKEN_GLASS = "vitre_cassee"


class Severity(str, Enum):
    MINOR = "leger"
    MODERATE = "modere"
    SEVERE = "grave"


class Damage(BaseModel):
    type: DamageType
    severity: Severity
    location: str
    confidence: float = Field(..., ge=0, le=1)
    bounding_box: Optional[list[int]] = None


class VisionResult(BaseModel):
    damages: list[Damage] = Field(default_factory=list)
    images_analyzed: int = 0
    provider: str = "mock"


class RepairLine(BaseModel):
    label: str
    estimated_cost: float


class CostEstimate(BaseModel):
    repair_lines: list[RepairLine] = Field(default_factory=list)
    total_repair_cost: float = 0.0
    provider: str = "mock"


class MarketValuation(BaseModel):
    base_value: float
    condition_factor: float
    adjusted_value: float
    provider: str = "mock"


class MechanicalAssessment(BaseModel):
    condition_score: int = Field(..., ge=0, le=100)
    condition_label: str
    cost_estimate: CostEstimate
    summary: str


class HistoryReport(BaseModel):
    vin: Optional[str]
    accidents: int = 0
    previous_owners: int = 1
    odometer_consistent: bool = True
    stolen_flag: bool = False
    open_recalls: int = 0
    notes: str = ""
    source: str = "mock"


class NegotiationStrategy(BaseModel):
    fair_value: float
    recommended_offer: float
    walk_away_price: float
    arguments: list[str] = Field(default_factory=list)
    summary: str


class InspectionReport(BaseModel):
    vehicle: VehicleInfo
    vision: VisionResult
    mechanical: MechanicalAssessment
    history: HistoryReport
    valuation: MarketValuation
    negotiation: NegotiationStrategy
    executive_summary: str
    generated_at: str
