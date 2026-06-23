from __future__ import annotations

from app.agents.base import AgentTrace
from app.agents.evaluation_agent import EvaluationAgent
from app.agents.history_agent import HistoryAgent
from app.agents.negotiation_agent import NegotiationAgent
from app.agents.report_agent import ReportAgent
from app.computer_vision import detect_damages
from app.machine_learning import estimate_market_value
from app.models.schemas import InspectionReport, VehicleInfo


class OrchestratorAgent:
    name = "orchestrateur"

    def run(
        self, vehicle: VehicleInfo, images: list[bytes]
    ) -> tuple[InspectionReport, list[dict]]:
        trace = AgentTrace()
        trace.log(self.name, "demarrage", f"inspection de {vehicle.make} {vehicle.model}")

        trace.log(self.name, "delegation", "Computer Vision : detection des dommages")
        vision = detect_damages(images)
        trace.log(
            self.name,
            "retour_vision",
            f"{len(vision.damages)} dommage(s) ({vision.provider})",
        )

        trace.log(self.name, "delegation", "Sous-agent EVALUATION")
        evaluation = EvaluationAgent(trace).run(vision, vehicle)

        trace.log(self.name, "delegation", "Sous-agent HISTORIQUE")
        history = HistoryAgent(trace).run(vehicle)

        trace.log(self.name, "delegation", "Machine Learning : valeur marchande")
        valuation = estimate_market_value(
            vehicle, evaluation.condition_score, evaluation.cost_estimate
        )
        trace.log(
            self.name,
            "retour_valeur",
            f"valeur ajustee {valuation.adjusted_value:.0f} EUR",
        )

        trace.log(self.name, "delegation", "Sous-agent NEGOCIATION")
        negotiation = NegotiationAgent(trace).run(valuation, evaluation, history)

        trace.log(self.name, "delegation", "Sous-agent RAPPORT")
        report = ReportAgent(trace).run(
            vehicle, vision, evaluation, history, valuation, negotiation
        )

        trace.log(self.name, "termine", "inspection complete")
        return report, trace.as_list()
