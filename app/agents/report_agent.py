from __future__ import annotations

from datetime import datetime

from app.agents.base import AgentTrace, BaseAgent
from app.llm import generate_text
from app.models.schemas import (
    HistoryReport,
    InspectionReport,
    MarketValuation,
    MechanicalAssessment,
    NegotiationStrategy,
    VehicleInfo,
    VisionResult,
)


class ReportAgent(BaseAgent):
    name = "rapport"
    role = "Consolidation et redaction du rapport d'inspection"

    def run(
        self,
        vehicle: VehicleInfo,
        vision: VisionResult,
        mechanical: MechanicalAssessment,
        history: HistoryReport,
        valuation: MarketValuation,
        negotiation: NegotiationStrategy,
    ) -> InspectionReport:
        self._log("demarrage", "consolidation des resultats")

        fallback = (
            f"Inspection du {vehicle.make} {vehicle.model} ({vehicle.year}, "
            f"{vehicle.mileage_km} km). Etat general : {mechanical.condition_label} "
            f"({mechanical.condition_score}/100), {len(vision.damages)} dommage(s) "
            f"detecte(s). Cout des reparations : {mechanical.cost_estimate.total_repair_cost:.0f} EUR. "
            f"Historique : {history.notes} "
            f"Valeur marchande ajustee : {valuation.adjusted_value:.0f} EUR. "
            f"Offre d'achat recommandee : {negotiation.recommended_offer:.0f} EUR."
        )
        prompt = (
            "Tu es un expert automobile. Synthese factuelle de 2 a 3 phrases maximum. "
            "Interdits: emoji, gras, markdown, titre, formule d'introduction ou de "
            "politesse. Uniquement des informations utiles, a partir de ces donnees:\n"
            f"- Vehicule: {vehicle.make} {vehicle.model} {vehicle.year}, {vehicle.mileage_km} km\n"
            f"- Etat: {mechanical.condition_label} ({mechanical.condition_score}/100)\n"
            f"- Dommages: {len(vision.damages)}\n"
            f"- Reparations: {mechanical.cost_estimate.total_repair_cost:.0f} EUR\n"
            f"- Historique: {history.notes}\n"
            f"- Valeur ajustee: {valuation.adjusted_value:.0f} EUR\n"
            f"- Offre conseillee: {negotiation.recommended_offer:.0f} EUR"
        )
        executive_summary = generate_text(prompt, fallback)

        self._log("termine", "rapport final genere")
        return InspectionReport(
            vehicle=vehicle,
            vision=vision,
            mechanical=mechanical,
            history=history,
            valuation=valuation,
            negotiation=negotiation,
            executive_summary=executive_summary,
            generated_at=datetime.now().isoformat(timespec="seconds"),
        )
