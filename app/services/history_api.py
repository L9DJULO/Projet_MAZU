from __future__ import annotations

import hashlib

from app.config import get_settings
from app.models.schemas import HistoryReport, VehicleInfo


def fetch_history(vehicle: VehicleInfo) -> HistoryReport:
    settings = get_settings()
    if settings.history_api_base != "mock":
        return _fetch_real(vehicle)
    return _fetch_mock(vehicle)


def _fetch_mock(vehicle: VehicleInfo) -> HistoryReport:
    key = vehicle.vin or f"{vehicle.make}{vehicle.model}{vehicle.year}"
    digest = hashlib.sha256(key.encode()).digest()

    accidents = digest[0] % 3
    previous_owners = 1 + (digest[1] % 4)
    stolen_flag = digest[2] % 23 == 0
    open_recalls = digest[3] % 2

    odometer_consistent = not (vehicle.year < 2015 and vehicle.mileage_km < 40_000)

    notes_parts = []
    if accidents:
        notes_parts.append(f"{accidents} sinistre(s) declare(s)")
    if not odometer_consistent:
        notes_parts.append("kilometrage potentiellement incoherent")
    if stolen_flag:
        notes_parts.append("ALERTE : signalement vol")
    if open_recalls:
        notes_parts.append("rappel constructeur non solde")
    notes = "; ".join(notes_parts) or "Aucune anomalie majeure relevee."

    return HistoryReport(
        vin=vehicle.vin,
        accidents=accidents,
        previous_owners=previous_owners,
        odometer_consistent=odometer_consistent,
        stolen_flag=stolen_flag,
        open_recalls=open_recalls,
        notes=notes,
        source="mock",
    )


def _fetch_real(vehicle: VehicleInfo) -> HistoryReport:
    import httpx

    settings = get_settings()
    resp = httpx.get(
        f"{settings.history_api_base}/vehicles/{vehicle.vin}",
        headers={"Authorization": f"Bearer {settings.history_api_key}"},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return HistoryReport(
        vin=vehicle.vin,
        accidents=data.get("accidents", 0),
        previous_owners=data.get("owners", 1),
        odometer_consistent=data.get("odometer_ok", True),
        stolen_flag=data.get("stolen", False),
        open_recalls=data.get("recalls", 0),
        notes=data.get("notes", ""),
        source="external_api",
    )
