# Rapport de projet — AutoExpert AI
### Inspection automatisée de véhicules d'occasion
**Matière : Microsoft Azure — EPITA**

---

## Sommaire

1. [Contexte et objectifs](#1-contexte-et-objectifs)
2. [Concept fonctionnel](#2-concept-fonctionnel)
3. [Architecture technique](#3-architecture-technique)
4. [Brique 1 — Computer Vision (Azure AI Vision)](#4-brique-1--computer-vision-azure-ai-vision)
5. [Brique 3 — Machine Learning (Azure ML)](#5-brique-3--machine-learning-azure-ml)
6. [Brique 4 — Système multi-agents](#6-brique-4--système-multi-agents)
7. [Brique 2 — Déploiement Edge / Docker](#7-brique-2--déploiement-edge--docker)
8. [Choix de conception et justifications](#8-choix-de-conception-et-justifications)
9. [Stratégie mock vs. Azure réel](#9-stratégie-mock-vs-azure-réel)
10. [Tests et validation](#10-tests-et-validation)
11. [Estimation des coûts Azure](#11-estimation-des-coûts-azure)
12. [Limites et pistes d'amélioration](#12-limites-et-pistes-damélioration)
13. [Conclusion](#13-conclusion)

---

## 1. Contexte et objectifs

L'achat d'un véhicule d'occasion est un acte à fort risque d'asymétrie
d'information : l'acheteur dispose rarement de l'expertise nécessaire pour
évaluer l'état réel d'un véhicule et négocier un prix juste. **AutoExpert AI**
répond à ce problème en automatisant l'inspection : à partir de simples photos,
le système détecte les dommages, chiffre les réparations, vérifie l'historique
administratif, estime la valeur marchande et propose une stratégie de
négociation.

Le projet illustre l'intégration de plusieurs services de l'écosystème
**Microsoft Azure** dans une architecture orientée IA :

- **Azure AI Vision** (Cognitive Services) pour la vision par ordinateur ;
- **Azure Machine Learning** pour les modèles d'estimation ;
- un **système multi-agents** (orchestrateur + sous-agents) inspiré du
  *Microsoft Agent Framework*, avec un LLM local (Ollama) ;
- un **déploiement conteneurisé** (Docker / Edge).

---

## 2. Concept fonctionnel

> *Un système qui inspecte un véhicule, évalue son état et orchestre les
> démarches administratives et commerciales.*

Le parcours utilisateur est le suivant :

1. L'utilisateur fournit des **photos ou une vidéo 360°** du véhicule, plus
   quelques informations déclaratives (marque, modèle, année, kilométrage, VIN).
2. La **Computer Vision** identifie les dommages visibles : rayures, bosses,
   fissures, usure des pneus, corrosion, vitrage cassé.
3. Le **Machine Learning** estime le **coût de réparation** et la **valeur
   marchande** en fonction de l'état détecté.
4. Un **agent orchestrateur** délègue à quatre **sous-agents** spécialisés :
   évaluation mécanique, vérification d'historique, génération de rapport,
   négociation de prix.
5. L'utilisateur reçoit un **rapport d'inspection** complet avec une
   recommandation d'offre d'achat chiffrée.

---

## 3. Architecture technique

L'architecture suit fidèlement le schéma du sujet (détail dans
[architecture.md](architecture.md)). Quatre couches :

| Couche | Composant | Technologie |
|--------|-----------|-------------|
| Présentation | Interface web (upload + rapport) | HTML/CSS/JS |
| Application (Edge) | API + serveur | FastAPI, Docker |
| Orchestration | Agent principal + 4 sous-agents | Pattern Agent Framework + Ollama |
| Services IA | Vision, ML, API historique | Azure AI Vision, Azure ML, API tierce |

**Principe directeur :** un *contrat de données* unique (modèles Pydantic dans
`app/models/schemas.py`) relie toutes les couches. Chaque service expose la même
interface qu'il tourne en mode simulé (*mock*) ou réel (Azure), ce qui rend le
système **modulaire et testable**.

---

## 4. Brique 1 — Computer Vision (Azure AI Vision)

**Objectif :** détecter et localiser les dommages visibles sur la carrosserie.

### Implémentation réelle (Azure)

Le module [`damage_detector.py`](../app/computer_vision/damage_detector.py)
utilise le SDK officiel `azure-ai-vision-imageanalysis`. Il envoie chaque image
au service **Image Analysis** d'Azure AI Vision et demande la détection
d'**objets** et de **tags**, puis mappe les résultats vers notre modèle
`Damage` (type, sévérité, localisation, confiance, *bounding box*).

> **Note de conception :** en production, on remplacerait l'analyse générique par
> un modèle **Azure Custom Vision** *entraîné spécifiquement* sur un jeu de
> données de dommages carrosserie (transfer learning). Le service générique sert
> ici à démontrer l'intégration du SDK ; l'interface `detect_damages()` resterait
> identique.

### Implémentation simulée (mock, par défaut)

Pour permettre une démonstration **sans compte Azure**, un simulateur génère une
liste de dommages **déterministe** : une graine est dérivée du *hash* SHA-256 du
contenu des images, garantissant que les mêmes photos produisent toujours le même
résultat (essentiel pour une démo reproductible et pour les tests). La sévérité
suit une distribution réaliste (50 % légers, 35 % modérés, 15 % graves).

**Sortie :** un objet `VisionResult { damages[], images_analyzed, provider }`.

---

## 5. Brique 3 — Machine Learning (Azure ML)

Deux modèles distincts sont mobilisés.

### 5.1 Estimation du coût de réparation

[`cost_estimator.py`](../app/machine_learning/cost_estimator.py) prédit un coût
par dommage. En mode réel, il appelle un **online endpoint Azure ML** (un modèle
de régression déployé) avec une matrice de *features* : type de dommage,
sévérité, confiance, premium marque, année, kilométrage.

En mode mock, un **barème métier explicable** joue le rôle du modèle entraîné :

```
coût = coût_base(type) × facteur(sévérité) × premium(marque) × f(confiance)
```

Ce choix d'un modèle *transparent* est volontaire : il est **explicable** (on
justifie chaque euro), ce qui est précieux dans un contexte d'évaluation
financière, et il fournit un *baseline* réaliste contre lequel comparer un futur
modèle Azure ML.

### 5.2 Estimation de la valeur marchande

[`market_value.py`](../app/machine_learning/market_value.py) calcule une valeur
ajustée par dépréciation :

```
valeur_base   = valeur_neuf(marque) × (0.85 ^ âge) × (1 − pénalité_km)
facteur_état  = 0.55 + 0.45 × (score_état / 100)
valeur_ajustée = valeur_base × facteur_état − 0.6 × coût_réparation
```

La logique reflète le comportement réel d'un acheteur : il déduit *une partie*
(et non la totalité) des réparations à venir, et applique une décote liée à
l'état général.

---

## 6. Brique 4 — Système multi-agents

C'est le cœur « agentique » du projet, inspiré du **Microsoft Agent Framework**.
Un **agent orchestrateur** ne réalise aucun calcul lui-même : il **coordonne**
quatre sous-agents spécialisés et gère les dépendances de données entre eux.

### 6.1 L'orchestrateur

[`orchestrator.py`](../app/agents/orchestrator.py) exécute la séquence :
Vision → (Évaluation ‖ Historique) → ML valeur → Négociation → Rapport.
Chaque délégation est journalisée dans un objet `AgentTrace`, renvoyé à
l'interface : on **visualise qui fait quoi**, ce qui rend le raisonnement du
système transparent et défendable.

### 6.2 Les sous-agents

| Sous-agent | Fichier | Rôle |
|------------|---------|------|
| **Évaluation mécanique** | `evaluation_agent.py` | Calcule un score d'état /100 et déclenche le chiffrage Azure ML. |
| **Historique** | `history_agent.py` | Interroge l'API externe d'historique, lève les alertes (sinistres, vol, km incohérent, rappels). |
| **Génération de rapport** | `report_agent.py` | Consolide toutes les sorties en un rapport + résumé exécutif. |
| **Négociation** | `negotiation_agent.py` | Calcule une fourchette de prix (offre / juste / max) et produit des arguments de négociation. |

### 6.3 Rôle du LLM (Ollama)

Conformément au schéma (*« Agent Framework + Ollama »*), les sous-agents peuvent
s'appuyer sur un **LLM local Ollama** pour rédiger leurs synthèses en langage
naturel (résumé mécanique, conseils de négociation, résumé exécutif). Pour
garantir que le projet **tourne sans rien installer**, la couche
[`llm/client.py`](../app/llm/client.py) implémente un *fallback* : si Ollama est
indisponible (ou `LLM_MODE=template`), chaque agent retombe sur une synthèse
templatée déterministe déjà rédigée. La qualité reste correcte sans LLM, et
s'améliore nettement avec.

> **Choix d'architecture :** plutôt que d'imposer la dépendance lourde du
> Microsoft Agent Framework (qui complique l'installation et le déploiement
> *edge*), nous en **reproduisons le pattern** (orchestrateur + sous-agents +
> journal d'exécution) avec une implémentation légère et autonome. Le concept
> pédagogique est démontré sans sacrifier la portabilité.

---

## 7. Brique 2 — Déploiement Edge / Docker

L'application est packagée dans une image **Docker** (`Dockerfile`) basée sur
`python:3.11-slim`. Le `docker-compose.yml` orchestre :

- le service **web** (FastAPI / Uvicorn, port 8000) ;
- un service **Ollama** optionnel (profil `llm`) pour le LLM local.

Ce conditionnement *edge* permet d'exécuter l'inspection **localement** chez un
concessionnaire ou un particulier, sans envoyer les photos vers le cloud — un
atout pour la **confidentialité** et la **latence**. Seuls les appels Azure
Vision/ML sortent du réseau local, et uniquement en mode `real`.

---

## 8. Choix de conception et justifications

| Décision | Justification |
|----------|---------------|
| **Python + FastAPI** | Écosystème naturel pour Azure ML / Vision (SDK Python officiels), API async performante, typage Pydantic. |
| **Contrats Pydantic partagés** | Découplage fort : mock et Azure sont interchangeables sans impact sur les agents. |
| **Mode mock par défaut** | Le projet doit être démontrable sans budget Azure ni configuration ; le déterminisme rend la démo et les tests fiables. |
| **Barèmes ML explicables** | Dans un contexte financier, l'explicabilité prime ; sert aussi de baseline pour un vrai modèle Azure ML. |
| **Pattern agent léger** | Démontre le concept multi-agents sans dépendance lourde, compatible *edge*. |
| **Fallback LLM par template** | Robustesse : le système ne tombe jamais en panne faute de LLM. |
| **Journal d'exécution (trace)** | Transparence et explicabilité du raisonnement des agents. |

---

## 9. Stratégie mock vs. Azure réel

Le paramètre `AZURE_MODE` (dans `.env`) contrôle, pour chaque brique, la bascule
entre simulateur et service Azure :

| Variable | `mock` (défaut) | `real` |
|----------|-----------------|--------|
| Computer Vision | Simulateur déterministe | Azure AI Vision (Image Analysis / Custom Vision) |
| Coût réparation | Barème métier | Online endpoint Azure ML |
| Valeur marchande | Modèle de dépréciation | Modèle Azure ML de cote |
| Historique | Données simulées par VIN | API tierce (Histovec, CarVertical…) |
| LLM agents | Templates | Ollama local |

Le code des deux modes coexiste dans chaque module : **passer en production ne
demande aucune réécriture**, seulement des clés et un changement de variable.

---

## 10. Tests et validation

La suite `tests/test_pipeline.py` (exécutable via `pytest`) valide :

- le **déterminisme** de la Computer Vision (mêmes images → même résultat) ;
- la **cohérence des coûts** (positifs, une ligne par dommage) ;
- les **bornes de la valorisation** (facteur d'état ∈ [0.55 ; 1]) ;
- l'**orchestration de bout en bout** (rapport complet + trace contenant les
  cinq agents) ;
- une **règle métier** (une marque premium coûte plus cher à réparer).

**Résultat :** `5 passed`. La démo CLI (`python demo_cli.py`) confirme le
fonctionnement sur quatre véhicules d'exemple aux profils contrastés.

---

## 11. Estimation des coûts Azure

Ordre de grandeur pour un déploiement réel (tarifs indicatifs, région Europe) :

| Service | Modèle de coût | Estimation |
|---------|----------------|------------|
| Azure AI Vision | ~1 € / 1 000 transactions | Faible à l'usage |
| Azure Custom Vision | Entraînement + prédiction à l'heure/transaction | Modéré |
| Azure ML (online endpoint) | Coût du compute déployé (par heure) | Principal poste |
| Stockage (Blob) photos | Au Go/mois | Négligeable |

Le mode *edge* (Docker local) réduit les coûts en ne sollicitant Azure que pour
l'inférence, et le mode mock permet tout le développement à **coût nul**.

---

## 12. Limites et pistes d'amélioration

- **Vision :** le mode réel utilise un modèle générique ; un **Azure Custom
  Vision** entraîné sur des dommages réels améliorerait nettement la précision.
- **ML :** remplacer les barèmes par de vrais modèles entraînés sur des données
  de réparation et de cote (Azure ML pipelines, AutoML).
- **Agents :** introduire de la **parallélisation réelle** (async) entre les
  sous-agents indépendants (Évaluation ‖ Historique).
- **Historique :** intégrer une API officielle (Histovec en France).
- **Sécurité :** gestion des clés via **Azure Key Vault** plutôt que `.env`.
- **Vidéo 360° :** extraction de *frames* clés et agrégation multi-vues.

---

## 13. Conclusion

AutoExpert AI démontre l'intégration cohérente des briques au programme —
**Computer Vision**, **Machine Learning**, **système multi-agents** et
**déploiement edge** — au sein d'un cas d'usage concret et complet. L'accent mis
sur la **modularité** (contrats partagés), l'**explicabilité** (barèmes
transparents, journal des agents) et la **portabilité** (mode mock sans coût,
bascule Azure sans réécriture) en fait à la fois un livrable pédagogique clair et
une base réaliste pour une mise en production.
