# Architecture — AutoExpert AI

## 1. Vue d'ensemble

```
┌──────────────────────────────────────────────────────────────────┐
│                         UTILISATEUR                                │
│                   Photos / vidéo 360°                              │
└───────────────────────────────┬──────────────────────────────────┘
                                 │ HTTP (formulaire + images)
                                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                WEB APP (local) — Docker / Edge                     │
│                   FastAPI  ·  app/main.py                          │
└───────────────────────────────┬──────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────┐
│               AGENT ORCHESTRATEUR (app/agents/orchestrator.py)     │
│        Agent Framework (pattern) + LLM Ollama (optionnel)          │
└───┬───────────────┬───────────────┬───────────────┬───────────────┘
    │ délègue       │               │               │
    ▼               ▼               ▼               ▼
┌─────────┐   ┌───────────┐   ┌───────────┐   ┌─────────────┐
│ ÉVALU-  │   │HISTORIQUE │   │  RAPPORT  │   │ NÉGOCIATION │
│ ATION   │   │ (via API) │   │ (synthèse)│   │ (prix/offre)│
└────┬────┘   └─────┬─────┘   └───────────┘   └─────────────┘
     │              │
     ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌────────────────────────┐
│ COMPUTER     │ │ MACHINE      │ │ API HISTORIQUE         │
│ VISION       │ │ LEARNING     │ │ (service externe)      │
│ Azure AI     │ │ Azure ML     │ │ Histovec / CarVertical │
│ Vision       │ │              │ │                        │
└──────────────┘ └──────────────┘ └────────────────────────┘
   BRIQUE 1         BRIQUE 3              service tiers
```

## 2. Séquence d'orchestration

L'agent orchestrateur ne réalise aucun calcul métier lui-même : il **coordonne**.

| # | Étape | Acteur | Dépend de |
|---|-------|--------|-----------|
| 1 | Détection des dommages | Computer Vision (Azure AI Vision) | images |
| 2a | Score d'état + coût réparation | Sous-agent **Évaluation** → Azure ML | 1 |
| 2b | Historique administratif | Sous-agent **Historique** → API externe | véhicule |
| 3 | Valeur marchande ajustée | Machine Learning (Azure ML) | 2a |
| 4 | Stratégie de prix & arguments | Sous-agent **Négociation** | 2a, 2b, 3 |
| 5 | Rapport consolidé + résumé exécutif | Sous-agent **Rapport** | tout |

Chaque action est tracée (`AgentTrace`) : le journal des agents est renvoyé à
l'interface pour la **transparence** (on voit qui fait quoi, dans quel ordre).

## 3. Contrats de données

Tous les modules échangent des objets **Pydantic** définis dans
[`app/models/schemas.py`](../app/models/schemas.py). C'est le « langage commun »
du système : changer une implémentation (mock → Azure) ne change pas l'interface.

```
VisionResult ──▶ MechanicalAssessment ──▶ MarketValuation ──▶ NegotiationStrategy
     │                    │                      │                    │
     └────────────────────┴──────────┬───────────┴────────────────────┘
                                      ▼
                              InspectionReport
```

## 4. Bascule mock / réel

Un seul interrupteur (`AZURE_MODE` dans `.env`) décide, pour chaque brique, si
on appelle le service Azure réel ou le simulateur déterministe. Cela permet :

- **Développement / démo** sans coût ni clé (mode `mock`) ;
- **Production** avec de vrais services (mode `real`), sans toucher au reste du
  code (orchestrateur, agents, interface restent identiques).

## 5. Correspondance avec le schéma du sujet

| Élément du schéma | Implémentation |
|-------------------|----------------|
| Utilisateur (photos / vidéo 360°) | Formulaire web + upload (`static/`) |
| Web App (local) · Docker · Edge | FastAPI + Dockerfile + docker-compose |
| Agent orchestrateur (Agent Framework + Ollama) | `agents/orchestrator.py` + `llm/` |
| Sous-agent Évaluation (dommages + coût) | `agents/evaluation_agent.py` |
| Sous-agent Historique (via API) | `agents/history_agent.py` + `services/history_api.py` |
| Sous-agent Rapport (synthèse) | `agents/report_agent.py` |
| Sous-agent Négociation (prix / offre) | `agents/negotiation_agent.py` |
| Computer Vision · Azure Cognitive | `computer_vision/damage_detector.py` |
| Machine Learning · Azure ML | `machine_learning/` |
| API historique · service externe | `services/history_api.py` |
