from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class VehicleInfo(BaseModel):
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = Field(None, ge=1980, le=2030)
    mileage_km: Optional[int] = Field(None, ge=0)
    vin: Optional[str] = None
    base_market_value: Optional[float] = None

    @property
    def label(self) -> str:
        parts = [p for p in (self.make, self.model, str(self.year) if self.year else None) if p]
        return " ".join(parts) or "vehicule (details non fournis)"

    @property
    def has_market_info(self) -> bool:
        return bool(self.make and self.model and self.year and self.mileage_km)


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
    # Verdict d'etat global du vehicule (0-100) quand le modele classe
    # l'ensemble du vehicule (ex: "Destroyed"/"Good"). None = mode par dommages.
    condition_score: Optional[int] = None
    total_loss: bool = False


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
    total_loss: bool = False


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
    valuation: Optional[MarketValuation] = None
    negotiation: Optional[NegotiationStrategy] = None
    executive_summary: str
    generated_at: str
