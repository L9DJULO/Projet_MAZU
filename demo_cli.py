from __future__ import annotations

import json
from pathlib import Path

from app.agents import OrchestratorAgent
from app.models.schemas import VehicleInfo

SAMPLES = Path(__file__).parent / "data" / "sample_vehicles.json"


def euros(n: float) -> str:
    return f"{n:,.0f} EUR".replace(",", " ")


def run_one(data: dict) -> None:
    vehicle = VehicleInfo(**data)
    images = [f"{vehicle.make}{vehicle.model}{vehicle.year}".encode()]

    report, trace = OrchestratorAgent().run(vehicle, images)

    print("=" * 70)
    print(f"  {vehicle.make} {vehicle.model} ({vehicle.year}) - {vehicle.mileage_km} km")
    print("=" * 70)
    print(f"\n[RESUME] {report.executive_summary}\n")
    print(f"  Etat               : {report.mechanical.condition_label} "
          f"({report.mechanical.condition_score}/100)")
    print(f"  Dommages detectes  : {len(report.vision.damages)} ({report.vision.provider})")
    print(f"  Cout reparations   : {euros(report.mechanical.cost_estimate.total_repair_cost)}")
    print(f"  Valeur ajustee     : {euros(report.valuation.adjusted_value)}")
    print(f"  Offre recommandee  : {euros(report.negotiation.recommended_offer)} "
          f"(max {euros(report.negotiation.walk_away_price)})")
    print(f"\n  Etapes orchestrees : {len(trace)}")
    print()


def main() -> None:
    vehicles = json.loads(SAMPLES.read_text(encoding="utf-8"))
    for v in vehicles:
        run_one(v)


if __name__ == "__main__":
    main()
