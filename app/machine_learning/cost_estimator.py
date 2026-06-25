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


def _build_rows(damages: list[Damage], vehicle: VehicleInfo) -> list[dict]:
    premium = 1.3 if vehicle.make.lower() in _PREMIUM_MAKES else 1.0
    return [
        {
            "damage_type": d.type.value,
            "severity": d.severity.value,
            "confidence": d.confidence,
            "premium": premium,
            "year": vehicle.year,
            "mileage_km": vehicle.mileage_km,
        }
        for d in damages
    ]


def _parse_predicted_cost(row: dict) -> float:
    for key in ("Scored Labels", "predicted_cost", "estimated_cost", "cost", "Results"):
        if key in row:
            return float(row[key])
    numeric = [v for v in row.values() if isinstance(v, (int, float))]
    return float(numeric[-1]) if numeric else 0.0


def _estimate_with_azure_ml(
    damages: list[Damage], vehicle: VehicleInfo
) -> CostEstimate:
    import httpx

    settings = get_settings()
    rows = _build_rows(damages, vehicle)

    payload = {
        "Inputs": {settings.azure_ml_input_name: rows},
        "GlobalParameters": {},
    }
    headers = {
        "Authorization": f"Bearer {settings.azure_ml_key}",
        "Content-Type": "application/json",
    }
    resp = httpx.post(settings.azure_ml_endpoint, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    body = resp.json()

    results = body.get("Results", body)
    output_rows = results.get(settings.azure_ml_output_name) if isinstance(results, dict) else results
    if not output_rows:
        output_rows = next(iter(results.values())) if isinstance(results, dict) else results

    lines = [
        RepairLine(
            label=f"{d.type.value} - {d.location}",
            estimated_cost=round(_parse_predicted_cost(row), 2),
        )
        for d, row in zip(damages, output_rows)
    ]
    total = round(sum(line.estimated_cost for line in lines), 2)
    return CostEstimate(repair_lines=lines, total_repair_cost=total, provider="azure")
