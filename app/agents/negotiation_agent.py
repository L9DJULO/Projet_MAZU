from __future__ import annotations

from app.agents.base import AgentTrace, BaseAgent
from app.llm import generate_text
from app.models.schemas import (
    HistoryReport,
    MarketValuation,
    MechanicalAssessment,
    NegotiationStrategy,
)


class NegotiationAgent(BaseAgent):
    name = "negociation"
    role = "Strategie de negociation et fixation du prix d'offre"

    def run(
        self,
        valuation: MarketValuation,
        mechanical: MechanicalAssessment,
        history: HistoryReport,
    ) -> NegotiationStrategy:
        self._log("demarrage", "construction de la strategie de prix")

        fair = valuation.adjusted_value

        discount = 0.08
        arguments: list[str] = []

        if mechanical.cost_estimate.total_repair_cost > 0:
            discount += 0.04
            arguments.append(
                f"Reparations a prevoir : ~{mechanical.cost_estimate.total_repair_cost:.0f} EUR."
            )
        if history.accidents:
            discount += 0.05
            arguments.append(
                f"{history.accidents} sinistre(s) au carnet : decote justifiee."
            )
        if not history.odometer_consistent:
            discount += 0.06
            arguments.append("Kilometrage potentiellement incoherent : prudence.")
        if history.open_recalls:
            discount += 0.02
            arguments.append("Rappel constructeur non solde a faire realiser.")
        if mechanical.condition_score < 50:
            discount += 0.04
            arguments.append(
                f"Etat general '{mechanical.condition_label}' ({mechanical.condition_score}/100)."
            )
        if history.previous_owners >= 3:
            arguments.append(
                f"{history.previous_owners} proprietaires successifs."
            )

        discount = min(discount, 0.30)
        recommended_offer = round(fair * (1 - discount), 2)
        walk_away = round(fair * 1.02, 2)

        if not arguments:
            arguments.append("Vehicule sain : marge de negociation limitee.")

        self._log(
            "prix_calcule",
            f"juste={fair:.0f} offre={recommended_offer:.0f} (-{discount*100:.0f}%)",
        )

        # Montants calcules en dur (fiables) ; le LLM ne fournit que l'argument.
        argument_prompt = (
            "Donne UN seul argument de negociation, une phrase courte et factuelle, "
            "sans emoji, sans markdown, sans introduction, sans inventer de chiffres.\n"
            f"Leviers disponibles: {arguments}."
        )
        argument = generate_text(argument_prompt, arguments[0])
        summary = (
            f"Offre d'ouverture: {recommended_offer:.0f} EUR\n"
            f"Prix max: {walk_away:.0f} EUR\n"
            f"Argument cle: {argument}"
        )

        self._log("termine", "strategie de negociation prete")
        return NegotiationStrategy(
            fair_value=fair,
            recommended_offer=recommended_offer,
            walk_away_price=walk_away,
            arguments=arguments,
            summary=summary,
        )
