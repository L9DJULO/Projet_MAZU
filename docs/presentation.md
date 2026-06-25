# Script de presentation (15 min + 5 Q&A)

Plan minute par minute pour la soutenance, avec le mapping explicite des quatre
capacites exigees.

---

## Mapping des 4 capacites exigees

| Capacite demandee | Ou c'est demontre | Fichier |
|-------------------|-------------------|---------|
| (1) Cognitive - Azure Computer Vision | Detection des dommages sur photo | `app/computer_vision/` |
| (2) Edge - Docker local + webapp locale | `docker compose up`, app sur localhost | `Dockerfile`, `docker-compose.yml` |
| (3) Machine Learning - Azure ML | Cout reparation via endpoint ML Designer | `app/machine_learning/` |
| (4) Agentique - Agent Framework + Ollama/Gemini | Orchestrateur + 4 sous-agents | `app/agents/`, `app/llm/` |

---

## Deroule (15 min)

**0-2 min - Le probleme (accroche)**
- L'asymetrie d'information sur l'occasion auto.
- L'idee : photographier un vehicule -> rapport d'expertise + prix d'offre.
- Annoncer les 5 cas d'usage (acheteur, vendeur, garage, assureur, flotte).

**2-4 min - Architecture**
- Montrer le schema (`architecture.md`) : 4 couches.
- Insister sur le pattern orchestrateur + sous-agents.
- Mentionner la bascule mock/real (demo sans cout, prod sur Azure).

**4-10 min - Demo live**
1. Lancer la webapp (idealement via Docker pour appuyer la capacite Edge).
2. Cliquer "Charger un exemple" (cas BMW), lancer l'inspection.
3. Commenter le rapport : dommages detectes (Vision), cout (ML), historique
   (API), valorisation (ML), strategie de negociation (agent).
4. Derouler le **journal des agents** : montrer que l'orchestrateur delegue.
5. Bonus : montrer le cas Peugeot d'exemple qui declenche les alertes (vol, km
   incoherent) pour illustrer la robustesse.

**10-13 min - Le cote Azure (la note technique)**
- Expliquer comment chaque brique se branche sur Azure (`azure-deployment.md`).
- Montrer le code du client Azure ML : format `Inputs/GlobalParameters` ->
  `Results`, identique au tutoriel du cours (Titanic -> ici cout de reparation).
- Montrer le client Custom Vision et le backend Gemini/Ollama.

**13-15 min - MVP, limites, suite**
- Rappeler le perimetre du MVP et les evolutions (modeles entraines, video 360).
- Conclure sur la modularite et l'explicabilite.

---

## Reponses preparees (Q&A)

- **"Pourquoi des mocks ?"** -> Pour demontrer l'architecture sans budget Azure et
  garantir une demo reproductible ; le code reel Azure est present et active par
  une variable, sans reecriture.
- **"Utilisez-vous vraiment le Microsoft Agent Framework ?"** -> On implemente le
  pattern orchestrateur + sous-agents avec journal d'execution ; le LLM (Ollama
  ou Gemini) alimente les agents. Le passage au SDK officiel est documente comme
  evolution (voir note ci-dessous).
- **"Comment estimez-vous le cout ?"** -> Bareme explicable en mock ; en prod, un
  modele de regression Azure ML entraine via Designer, consomme en REST.
- **"Et la precision de la detection ?"** -> Custom Vision entraine sur des
  dommages annotes ameliore nettement la detection vs le modele generique.

---

## Note honnete sur la capacite agentique

Le sujet cite "Microsoft Agent Framework". Ce projet en reproduit fidelement le
**pattern** (un agent orchestrateur qui delegue a des sous-agents specialises,
avec tracage), sans imposer la dependance du SDK pour rester portable et
executable a froid. Si le bareme l'exige strictement, la couche `app/llm/` et
`app/agents/` peut etre rebranchee sur le SDK `agent-framework` avec un backend
LLM (Azure OpenAI, Ollama via API compatible OpenAI, ou Gemini) sans changer la
logique metier des sous-agents. A decider en equipe selon le temps disponible.
