# Guide de deploiement Azure

Ce guide explique comment brancher le projet sur de vrais services Azure, en
reprenant exactement la demarche du tutoriel "AIZU Machine learning" vu en cours.
Tant que `AZURE_MODE=mock`, rien de tout cela n'est necessaire : le projet tourne
en local. Ce guide sert pour la mise en production et pour la soutenance.

---

## 1. Pre-requis

- Un compte Azure (abonnement etudiant ou essai gratuit).
- Un groupe de ressources dedie, par ex. `rg-autoexpert`, a supprimer en fin de
  projet pour eviter les couts (voir section "Nettoyage").

---

## 2. Brique 1 - Computer Vision

Deux options, selon le niveau de realisme souhaite.

### Option A (rapide) - Azure AI Vision / Image Analysis

1. Portail Azure -> Creer une ressource -> "Computer Vision" (ou "Azure AI
   services").
2. Recuperer la cle et l'endpoint (onglet "Keys and Endpoint").
3. Dans `.env` :
   ```
   AZURE_MODE=real
   VISION_PROVIDER=image_analysis
   AZURE_VISION_ENDPOINT=https://<ressource>.cognitiveservices.azure.com/
   AZURE_VISION_KEY=<cle>
   ```

C'est l'integration la plus simple, mais le modele est generique (il ne connait
pas specifiquement les dommages de carrosserie).

### Option B (recommandee pour le theme) - Azure Custom Vision

Pour vraiment detecter rayures / bosses / fissures, on entraine un modele de
detection d'objets sur des images annotees.

1. Aller sur https://www.customvision.ai -> "New Project".
2. Type de projet : **Object Detection**.
3. Uploader des photos de vehicules et annoter les zones de dommages avec des
   tags : `rayure`, `bosse`, `fissure`, `corrosion`, `usure_pneu`, `vitre`.
4. "Train" puis "Publish" l'iteration.
5. Recuperer : Prediction URL, Prediction Key, Project ID, nom de l'iteration
   publiee.
6. Dans `.env` :
   ```
   AZURE_MODE=real
   VISION_PROVIDER=custom_vision
   CUSTOM_VISION_ENDPOINT=https://<ressource>.cognitiveservices.azure.com/
   CUSTOM_VISION_KEY=<prediction-key>
   CUSTOM_VISION_PROJECT_ID=<project-id>
   CUSTOM_VISION_ITERATION=<nom-iteration>
   ```

Le code (`app/computer_vision/damage_detector.py`) appelle deja l'API de
prediction Custom Vision et mappe les tags vers notre schema `Damage`.

---

## 3. Brique 3 - Azure Machine Learning (suit le tutoriel du cours)

Le tutoriel "AIZU Machine learning" deploie un modele en endpoint temps reel et
le consomme via REST. On reproduit la meme demarche, mais pour estimer un **cout
de reparation** (regression) au lieu de la survie du Titanic (classification).

### 3.1 Entrainer le modele (onglet Designer)

1. Azure ML Studio -> Designer -> nouveau pipeline (comme dans le tutoriel).
2. Source de donnees : un dataset de reparations avec les colonnes
   `damage_type, severity, confidence, premium, year, mileage_km, cost`.
   (A defaut de dataset reel, on peut generer un CSV synthetique a partir du
   bareme de `app/machine_learning/cost_estimator.py`.)
3. Composants : `Select Columns` -> `Split Data` -> un module de regression
   (ex. **Boosted Decision Tree Regression**) -> `Train Model` (label = `cost`)
   -> `Score Model` -> `Evaluate Model`.
4. Submit (creer une experience, ex. `Experiment_repair_cost`).

> C'est exactement le meme enchainement que le tutoriel Titanic, on remplace
> juste "Two-Class Boosted Decision Tree" par sa version regression et le label
> `Survived` par `cost`.

### 3.2 Pipeline d'inference + deploiement

1. "Create inference pipeline" -> "Real-time inference pipeline".
2. Nettoyer le pipeline (retirer Evaluate Model, etc.) comme dans le tutoriel.
3. Submit, puis "Deploy" -> "Deploy new real-time endpoint".
   - Nom : `endpoint-repair-cost`
   - Compute : **Azure Container Instance**, 1 CPU / 2 Go RAM.

### 3.3 Consommer l'endpoint depuis l'app

1. Onglet "Consume" de l'endpoint : recuperer l'URL REST et la cle.
2. Onglet "Test" : regarder le JSON d'entree/sortie pour noter les noms exacts
   des noeuds d'entree/sortie (souvent `input1` / `output1`, ou
   `WebServiceInput0` / `WebServiceOutput0`).
3. Dans `.env` :
   ```
   AZURE_MODE=real
   AZURE_ML_ENDPOINT=https://<endpoint>.<region>.inference.ml.azure.com/score
   AZURE_ML_KEY=<cle>
   AZURE_ML_INPUT_NAME=input1
   AZURE_ML_OUTPUT_NAME=output1
   ```

Le client (`app/machine_learning/cost_estimator.py`) envoie deja le format
attendu par les endpoints Designer :

```json
{ "Inputs": { "input1": [ { "damage_type": "...", "severity": "...", ... } ] },
  "GlobalParameters": {} }
```

et lit la prediction dans `Results -> output1`. Le parsing est tolerant aux
differents noms de colonne de sortie (`Scored Labels`, `predicted_cost`, ...).

---

## 4. Brique 4 - Agents (LLM Ollama ou Gemini)

Les sous-agents redigent leurs syntheses via un LLM, ou via des templates
deterministes par defaut.

- **Ollama (local)** : installer Ollama, `ollama pull llama3.2`, puis
  ```
  LLM_MODE=ollama
  OLLAMA_HOST=http://localhost:11434
  OLLAMA_MODEL=llama3.2
  ```
  En Docker : `docker compose --profile llm up`.

- **Gemini (cloud)** :
  ```
  LLM_MODE=gemini
  GEMINI_API_KEY=<cle>
  GEMINI_MODEL=gemini-1.5-flash
  ```

- **Sans LLM** : `LLM_MODE=template` (defaut). Tout fonctionne quand meme.

---

## 5. Brique 2 - Edge / Docker (execution locale)

La demonstration "Edge" consiste a faire tourner la webapp en local dans Docker,
sur le laptop, sans dependre du cloud pour l'execution :

```
docker compose up --build
```

Seuls les appels Vision/ML sortent vers Azure (et uniquement en mode `real`).

---

## 6. Nettoyage (important pour les couts)

Comme indique dans le tutoriel :

1. Azure ML Studio -> "Compute" -> arreter l'instance de calcul.
2. "Endpoints" -> supprimer l'endpoint.
3. Portail Azure -> supprimer le groupe de ressources (`rg-autoexpert`) pour
   supprimer d'un coup toutes les ressources et stopper la facturation.
