from __future__ import annotations

from app.agents.base import AgentTrace, BaseAgent
from app.models.schemas import HistoryReport, VehicleInfo
from app.services.history_api import fetch_history


class HistoryAgent(BaseAgent):
    name = "historique"
    role = "Verification de l'historique administratif et des sinistres"

    def run(self, vehicle: VehicleInfo) -> HistoryReport:
        self._log("appel_api", f"interrogation historique VIN={vehicle.vin or 'N/A'}")
        report = fetch_history(vehicle)
        alerts = []
        if report.stolen_flag:
            alerts.append("vol")
        if report.accidents:
            alerts.append(f"{report.accidents} sinistre(s)")
        if not report.odometer_consistent:
            alerts.append("km incoherent")
        if report.open_recalls:
            alerts.append("rappel ouvert")
        self._log(
            "resultat",
            f"source={report.source}; alertes={', '.join(alerts) or 'aucune'}",
        )
        return report
