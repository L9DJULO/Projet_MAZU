from __future__ import annotations

from app.agents.base import AgentTrace, BaseAgent
from app.llm import generate_text
from app.machine_learning import estimate_base_value, estimate_repair_cost
from app.models.schemas import (
    MechanicalAssessment,
    RepairLine,
    Severity,
    VehicleInfo,
    VisionResult,
)

_SEVERITY_WEIGHT = {Severity.MINOR: 4, Severity.MODERATE: 10, Severity.SEVERE: 22}


def _condition_label(score: int, total_loss: bool = False) -> str:
    if total_loss:
        return "Epave (irreparable economiquement)"
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

        # Le score d'etat provient du verdict global du modele de vision quand
        # il classe tout le vehicule (ex: "Destroyed"), sinon il est deduit de
        # l'accumulation des dommages detectes.
        if vision.condition_score is not None:
            score = max(0, min(100, vision.condition_score))
        else:
            penalty = sum(_SEVERITY_WEIGHT[d.severity] for d in vision.damages)
            score = max(0, 100 - penalty)

        cost = estimate_repair_cost(vision.damages, vehicle)

        # Escalade pour un etat global tres degrade : au-dela des retouches
        # cosmetiques, un vehicule accidente implique des dommages structurels
        # (chassis, securite) dont le cout se rapproche de sa valeur.
        base_value = estimate_base_value(vehicle)
        if score < 50:
            structural = round(base_value * (50 - score) / 50, 2)
            if structural >= 1:
                cost.repair_lines.append(
                    RepairLine(
                        label="Dommages structurels / securite (estimation)",
                        estimated_cost=structural,
                    )
                )
                cost.total_repair_cost = round(cost.total_repair_cost + structural, 2)

        # Perte totale economique : reparer coute >= 80% de la valeur du vehicule.
        total_loss = bool(vision.total_loss) or (
            base_value > 0 and cost.total_repair_cost >= 0.8 * base_value
        )

        label = _condition_label(score, total_loss)
        self._log("score_etat", f"{score}/100 ({label})")
        self._log(
            "cout_reparation",
            f"{cost.total_repair_cost} EUR ({cost.provider})"
            + (" - perte totale" if total_loss else ""),
        )

        if total_loss:
            fallback = (
                f"Vehicule en tres mauvais etat ({score}/100), assimilable a une epave : "
                f"le cout estime des reparations ({cost.total_repair_cost:.0f} EUR) est "
                f"comparable ou superieur a sa valeur marchande. Reparation non rentable."
            )
        else:
            fallback = (
                f"Le vehicule presente {len(vision.damages)} dommage(s) visible(s), "
                f"pour un etat juge '{label}' ({score}/100). Le cout total estime "
                f"des reparations s'eleve a {cost.total_repair_cost:.0f} EUR."
            )
        prompt = (
            "Tu es un expert automobile. Redige en 2 phrases une synthese de "
            f"l'etat mecanique d'un {vehicle.label}. "
            f"Score d'etat: {score}/100 ({label}). "
            f"{'Vehicule considere comme epave (perte totale economique). ' if total_loss else ''}"
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
            total_loss=total_loss,
        )
