# AutoExpert AI - Inspection automatisee de vehicules

> Projet de la matiere **Microsoft Azure** - EPITA
> Un systeme qui inspecte un vehicule a partir de photos, evalue son etat, et
> orchestre les demarches d'evaluation et de negociation via des agents.

Le systeme combine trois briques au programme du cours :

| Brique | Technologie | Role |
|--------|-------------|------|
| **1 - Computer Vision** | Azure AI Vision (Cognitive Services) | Detecte les dommages visibles (rayures, bosses, fissures, usure pneus...) |
| **3 - Machine Learning** | Azure Machine Learning | Estime le cout de reparation et la valeur marchande |
| **4 - Agentique** | Agent orchestrateur + sous-agents (Ollama) | Coordonne evaluation, historique, rapport, negociation |
| **2 - Edge / Docker** | FastAPI + Docker | Application web locale qui heberge le tout |

> Le projet demarre sans aucun compte Azure ni cle. Par defaut tout
> fonctionne en mode **mock** (services simules, deterministes). Le code est
> neanmoins cable sur les vrais SDK Azure : il suffit de passer `AZURE_MODE=real`
> et de fournir les cles pour basculer en production. Voir [docs/rapport.md](docs/rapport.md).

---

## Demarrage rapide (mode mock, zero configuration)

### Option A - En local avec Python (recommande pour debuter)

```bash
python -m venv .venv
.\.venv\Scripts\activate        # Windows PowerShell
# source .venv/bin/activate     # macOS / Linux

pip install -r requirements.txt

# Lancer l'interface web
uvicorn app.main:app --reload
#  -> ouvrir http://localhost:8000

# OU lancer la demo en ligne de commande (sans navigateur)
python demo_cli.py
```

> Note : pour le mode mock, les SDK Azure ne sont pas strictement necessaires.
> Si l'installation des paquets azure-* pose souci, vous pouvez les commenter
> dans requirements.txt - l'application reste pleinement fonctionnelle.

### Option B - Avec Docker

```bash
docker compose up --build
#  -> ouvrir http://localhost:8000

# Avec un LLM Ollama local pour les syntheses des agents :
docker compose --profile llm up --build
```

---

## Utilisation

1. Ouvrir http://localhost:8000
2. Renseigner les infos du vehicule (un bouton "Charger un exemple" existe).
3. Optionnel : ajouter des photos / une video 360.
4. Cliquer "Lancer l'inspection".
5. Le rapport s'affiche : dommages, cout des reparations, historique,
   valorisation, strategie de negociation, et le journal des agents.

---

## Tests

```bash
pytest -q
```

Les tests valident le pipeline complet en mode mock (determinisme de la vision,
coherence des couts, orchestration de bout en bout).

---

## Structure du projet

```
Projet_MAZU/
├── app/
│   ├── main.py                 # API web FastAPI (brique Edge/Docker)
│   ├── config.py               # Configuration (.env), bascule mock/real
│   ├── models/schemas.py       # Contrats de donnees (Pydantic) partages
│   ├── computer_vision/        # BRIQUE 1 - Azure AI Vision (+ mock)
│   ├── machine_learning/       # BRIQUE 3 - Azure ML : cout + valeur (+ mock)
│   ├── services/history_api.py # API externe d'historique vehicule (+ mock)
│   ├── llm/                    # Acces LLM Ollama (+ fallback template)
│   ├── agents/                # BRIQUE 4 - orchestrateur + 4 sous-agents
│   │   ├── orchestrator.py     #   agent principal (coordination)
│   │   ├── evaluation_agent.py #   sous-agent evaluation mecanique
│   │   ├── history_agent.py    #   sous-agent verification historique
│   │   ├── negotiation_agent.py#   sous-agent negociation de prix
│   │   └── report_agent.py     #   sous-agent generation de rapport
│   └── static/                # Interface web (HTML/CSS/JS)
├── data/sample_vehicles.json   # Vehicules d'exemple
├── tests/test_pipeline.py      # Tests automatises
├── demo_cli.py                 # Demo sans navigateur
├── Dockerfile / docker-compose.yml
├── docs/
│   ├── rapport.md              # RAPPORT ACADEMIQUE (a lire / rendre)
│   └── architecture.md         # Schema et flux detailles
└── .env.example                # Configuration (copier en .env)
```

---

## Passer en mode Azure reel

1. Copier .env.example en .env
2. Renseigner AZURE_MODE=real + les cles Azure Vision et/ou Azure ML.
3. (Optionnel) LLM_MODE=ollama pour des syntheses redigees par un LLM local.

Le detail de l'architecture Azure cible (ressources, deploiement, couts) est
dans [docs/rapport.md](docs/rapport.md).
