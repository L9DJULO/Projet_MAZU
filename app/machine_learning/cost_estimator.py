from __future__ import annotations

from app.config import get_settings
from app.models.schemas import (
    CostEstimate,
    Damage,
    DamageType,
    RepairLine,
    Severity,
    VehicleInfo,
)

_BASE_COST = {
    DamageType.SCRATCH: 180,
    DamageType.DENT: 350,
    DamageType.CRACK: 250,
    DamageType.TIRE_WEAR: 120,
    DamageType.RUST: 400,
    DamageType.BROKEN_GLASS: 600,
}

_SEVERITY_FACTOR = {
    Severity.MINOR: 0.6,
    Severity.MODERATE: 1.0,
    Severity.SEVERE: 1.8,
}

_PREMIUM_MAKES = {"bmw", "audi", "mercedes", "tesla", "volvo", "lexus"}


def estimate_repair_cost(
    damages: list[Damage], vehicle: VehicleInfo
) -> CostEstimate:
    settings = get_settings()
    if settings.ml_is_real:
        return _estimate_with_azure_ml(damages, vehicle)
    return _estimate_mock(damages, vehicle)


def _estimate_mock(damages: list[Damage], vehicle: VehicleInfo) -> CostEstimate:
    premium = 1.3 if vehicle.make.lower() in _PREMIUM_MAKES else 1.0
    lines: list[RepairLine] = []

    for d in damages:
        base = _BASE_COST.get(d.type, 200)
        cost = base * _SEVERITY_FACTOR[d.severity] * premium
        cost *= 0.85 + 0.15 * d.confidence
        lines.append(
            RepairLine(
                label=f"{d.type.value.replace('_', ' ').title()} - {d.location} ({d.severity.value})",
                estimated_cost=round(cost, 2),
            )
        )

    total = round(sum(line.estimated_cost for line in lines), 2)
    return CostEstimate(repair_lines=lines, total_repair_cost=total, provider="mock")


def _estimate_with_azure_ml(
    damages: list[Damage], vehicle: VehicleInfo
) -> CostEstimate:
    import httpx

    settings = get_settings()
    premium = 1.0 if vehicle.make.lower() not in _PREMIUM_MAKES else 1.3
    payload = {
        "input_data": {
            "columns": ["damage_type", "severity", "confidence", "premium", "year", "mileage_km"],
            "data": [
                [d.type.value, d.severity.value, d.confidence, premium, vehicle.year, vehicle.mileage_km]
                for d in damages
            ],
        }
    }
    headers = {
        "Authorization": f"Bearer {settings.azure_ml_key}",
        "Content-Type": "application/json",
    }
    resp = httpx.post(settings.azure_ml_endpoint, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    predicted_costs = resp.json()

    lines = [
        RepairLine(
            label=f"{d.type.value} - {d.location}",
            estimated_cost=round(float(c), 2),
        )
        for d, c in zip(damages, predicted_costs)
    ]
    total = round(sum(line.estimated_cost for line in lines), 2)
    return CostEstimate(repair_lines=lines, total_repair_cost=total, provider="azure")
