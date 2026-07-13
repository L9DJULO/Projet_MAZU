from __future__ import annotations

import time
from typing import Iterator

from app.agents.base import AgentTrace
from app.agents.evaluation_agent import EvaluationAgent
from app.agents.negotiation_agent import NegotiationAgent
from app.agents.report_agent import ReportAgent
from app.computer_vision import detect_damages
from app.machine_learning import estimate_market_value
from app.models.schemas import InspectionReport, VehicleInfo

AGENTS = [
    {"id": "orchestrateur", "label": "Orchestrateur", "kind": "orchestrator"},
    {"id": "computer_vision", "label": "Computer Vision", "kind": "service"},
    {"id": "evaluation", "label": "Evaluation mecanique", "kind": "agent"},
    {"id": "machine_learning", "label": "Machine Learning", "kind": "service"},
    {"id": "negociation", "label": "Negociation", "kind": "agent"},
    {"id": "rapport", "label": "Rapport", "kind": "agent"},
]


class OrchestratorAgent:
    name = "orchestrateur"

    def run(
        self, vehicle: VehicleInfo, images: list[bytes]
    ) -> tuple[InspectionReport, list[dict]]:
        trace = AgentTrace()
        trace.log(self.name, "demarrage", f"inspection de {vehicle.label}")

        trace.log(self.name, "delegation", "Computer Vision : detection des dommages")
        vision = detect_damages(images)
        trace.log(
            self.name,
            "retour_vision",
            f"{len(vision.damages)} dommage(s) ({vision.provider})",
        )

        trace.log(self.name, "delegation", "Sous-agent EVALUATION")
        evaluation = EvaluationAgent(trace).run(vision, vehicle)

        # Valorisation et negociation ne sont possibles que si l'on connait le
        # vehicule (marque/modele/annee/km). En mode "image seule", on s'arrete
        # a l'evaluation mecanique.
        valuation = None
        negotiation = None
        if vehicle.has_market_info:
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
            negotiation = NegotiationAgent(trace).run(valuation, evaluation)
        else:
            trace.log(
                self.name,
                "info",
                "infos vehicule incompletes : valorisation et negociation ignorees",
            )

        trace.log(self.name, "delegation", "Sous-agent RAPPORT")
        report = ReportAgent(trace).run(
            vehicle, vision, evaluation, valuation, negotiation
        )

        trace.log(self.name, "termine", "inspection complete")
        return report, trace.as_list()

    def run_iter(
        self, vehicle: VehicleInfo, images: list[bytes], pace: float = 0.0
    ) -> Iterator[dict]:
        """Meme orchestration que run(), mais emet chaque echange entre agents.

        Chaque etape produit un ou deux messages (delegation puis resultat) que
        l'interface affiche en direct, pour rendre la communication multi-agents
        visible pendant la demonstration.
        """
        trace = AgentTrace()

        def msg(sender: str, receiver: str, kind: str, text: str) -> dict:
            trace.log(sender, kind, f"-> {receiver}: {text}")
            if pace:
                time.sleep(pace)
            return {
                "event": "message",
                "from": sender,
                "to": receiver,
                "type": kind,
                "text": text,
            }

        yield {"event": "start", "agents": AGENTS, "vehicle": vehicle.label}

        yield msg("orchestrateur", "computer_vision", "delegation",
                  "Analyse les photos et detecte les dommages visibles.")
        vision = detect_damages(images)
        yield msg("computer_vision", "orchestrateur", "resultat",
                  f"{len(vision.damages)} dommage(s) detecte(s) (source: {vision.provider}).")

        yield msg("orchestrateur", "evaluation", "delegation",
                  "Evalue l'etat mecanique et chiffre les reparations.")
        yield msg("evaluation", "machine_learning", "delegation",
                  "Estime le cout de reparation pour ces dommages.")
        evaluation = EvaluationAgent(trace).run(vision, vehicle)
        yield msg("machine_learning", "evaluation", "resultat",
                  f"Cout total estime: {evaluation.cost_estimate.total_repair_cost:.0f} EUR.")
        yield msg("evaluation", "orchestrateur", "resultat",
                  f"Etat {evaluation.condition_score}/100 ({evaluation.condition_label}), "
                  f"reparations {evaluation.cost_estimate.total_repair_cost:.0f} EUR.")

        # Valorisation et negociation uniquement si le vehicule est identifie
        # (marque/modele/annee/km). En mode "image seule", on les ignore.
        valuation = None
        negotiation = None
        if vehicle.has_market_info:
            yield msg("orchestrateur", "machine_learning", "delegation",
                      "Estime la valeur marchande selon l'etat detecte.")
            valuation = estimate_market_value(
                vehicle, evaluation.condition_score, evaluation.cost_estimate
            )
            yield msg("machine_learning", "orchestrateur", "resultat",
                      f"Valeur marchande ajustee: {valuation.adjusted_value:.0f} EUR.")

            yield msg("orchestrateur", "negociation", "delegation",
                      "Construis une strategie de prix et une offre d'achat.")
            negotiation = NegotiationAgent(trace).run(valuation, evaluation)
            yield msg("negociation", "orchestrateur", "resultat",
                      f"Offre conseillee: {negotiation.recommended_offer:.0f} EUR "
                      f"(max {negotiation.walk_away_price:.0f} EUR).")
        else:
            yield msg("orchestrateur", "orchestrateur", "resultat",
                      "Infos vehicule incompletes : valorisation et negociation ignorees.")

        yield msg("orchestrateur", "rapport", "delegation",
                  "Consolide toutes les analyses en un rapport final.")
        report = ReportAgent(trace).run(
            vehicle, vision, evaluation, valuation, negotiation
        )
        yield msg("rapport", "orchestrateur", "resultat",
                  "Rapport d'inspection genere.")

        yield {
            "event": "done",
            "report": report.model_dump(mode="json"),
            "trace": trace.as_list(),
        }
