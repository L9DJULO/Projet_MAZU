from __future__ import annotations

from app.agents.base import AgentTrace, BaseAgent
from app.llm import generate_text
from app.machine_learning import estimate_repair_cost
from app.models.schemas import (
    MechanicalAssessment,
    Severity,
    VehicleInfo,
    VisionResult,
)

_SEVERITY_WEIGHT = {Severity.MINOR: 4, Severity.MODERATE: 10, Severity.SEVERE: 22}


def _condition_label(score: int) -> str:
    if score >= 85:
        return "Excellent"
    if score >= 70:
        return "Bon"
    if score >= 50:
        return "Correct"
    if score >= 30:
        return "Mediocre"
    return "Mauvais"


class EvaluationAgent(BaseAgent):
    name = "evaluation"
    role = "Evaluation mecanique et chiffrage des reparations"

    def run(self, vision: VisionResult, vehicle: VehicleInfo) -> MechanicalAssessment:
        self._log("demarrage", f"{len(vision.damages)} dommage(s) a evaluer")

        penalty = sum(_SEVERITY_WEIGHT[d.severity] for d in vision.damages)
        score = max(0, 100 - penalty)
        label = _condition_label(score)
        self._log("score_etat", f"{score}/100 ({label})")

        cost = estimate_repair_cost(vision.damages, vehicle)
        self._log(
            "cout_reparation",
            f"{cost.total_repair_cost} EUR ({cost.provider})",
        )

        fallback = (
            f"Le vehicule presente {len(vision.damages)} dommage(s) visible(s), "
            f"pour un etat juge '{label}' ({score}/100). Le cout total estime "
            f"des reparations s'eleve a {cost.total_repair_cost:.0f} EUR."
        )
        prompt = (
            "Tu es un expert automobile. Redige en 2 phrases une synthese de "
            f"l'etat mecanique d'un {vehicle.make} {vehicle.model} {vehicle.year}. "
            f"Score d'etat: {score}/100 ({label}). "
            f"Dommages: {[d.type.value + ' (' + d.severity.value + ')' for d in vision.damages]}. "
            f"Cout reparations estime: {cost.total_repair_cost:.0f} EUR."
        )
        summary = generate_text(prompt, fallback)

        self._log("termine", "synthese mecanique generee")
        return MechanicalAssessment(
            condition_score=score,
            condition_label=label,
            cost_estimate=cost,
            summary=summary,
        )
