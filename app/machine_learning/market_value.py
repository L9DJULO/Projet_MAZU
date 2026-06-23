from __future__ import annotations

from datetime import datetime

from app.models.schemas import CostEstimate, MarketValuation, VehicleInfo

_MAKE_NEW_VALUE = {
    "tesla": 45000, "bmw": 42000, "audi": 40000, "mercedes": 43000,
    "volvo": 38000, "lexus": 41000, "volkswagen": 28000, "peugeot": 24000,
    "renault": 22000, "citroen": 22000, "toyota": 26000, "ford": 25000,
    "_default": 24000,
}


def _estimate_base_value(vehicle: VehicleInfo) -> float:
    if vehicle.base_market_value:
        return vehicle.base_market_value

    new_value = _MAKE_NEW_VALUE.get(vehicle.make.lower(), _MAKE_NEW_VALUE["_default"])
    age = max(0, datetime.now().year - vehicle.year)

    age_factor = 0.85 ** age
    km_penalty = min(0.40, vehicle.mileage_km / 250_000)
    value = new_value * age_factor * (1 - km_penalty)
    return round(max(value, new_value * 0.08), 2)


def estimate_market_value(
    vehicle: VehicleInfo,
    condition_score: int,
    cost_estimate: CostEstimate,
) -> MarketValuation:
    base = _estimate_base_value(vehicle)

    condition_factor = round(0.55 + 0.45 * (condition_score / 100), 3)

    repair_deduction = 0.6 * cost_estimate.total_repair_cost

    adjusted = base * condition_factor - repair_deduction
    adjusted = round(max(adjusted, base * 0.1), 2)

    return MarketValuation(
        base_value=base,
        condition_factor=condition_factor,
        adjusted_value=adjusted,
        provider="mock",
    )
