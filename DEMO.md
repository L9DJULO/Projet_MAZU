# Script de démonstration — AutoExpert AI

Durée visée : **3 à 4 minutes**. Objectif : montrer les 4 capacités en action,
en insistant sur **l'orchestration multi-agents visible en direct**.

---

## 1. Préparation (avant de passer devant le jury)

À faire une fois, tranquillement, avant la présentation.

**a) Démarrer le modèle de vision (Custom Vision, port 88)**

Le modèle exporté tourne dans un conteneur local. S'il n'est pas déjà lancé :

```bash
cd custom_vision_model
docker build -t autoexpert-vision .
docker run -p 127.0.0.1:88:80 -d autoexpert-vision
```

**b) Démarrer la webapp**

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**c) Vérifier que tout est branché**

```bash
curl http://127.0.0.1:8000/api/health
```

On doit voir `"vision": "local_http"` (le conteneur est bien connecté).

**d) Ouvrir le navigateur** sur http://127.0.0.1:8000

**e) Avoir une photo de voiture prête** sur le bureau (idéalement une voiture
abîmée pour un résultat parlant). Indispensable : le modèle de vision ne
s'active que si on **téléverse une vraie photo**.

> Checklist express : conteneur port 88 lancé · webapp lancée · badge
> `CV:local_http` visible en haut à droite · une photo prête.

---

## 2. Déroulé de la démo (ce qu'on dit + ce qu'on fait)

### Étape 1 — Présenter l'écran (15 s)

> « Voici notre application, qui tourne **en local** dans Docker — c'est la
> brique Edge. En haut à droite, le badge indique que la vision utilise notre
> **modèle Custom Vision local**, et les agents un **LLM Mistral**. »

*(Montrer le badge : `CV:local_http | ML:mock | LLM:mistral`.)*

### Étape 2 — Saisir le véhicule (20 s)

> « On renseigne le véhicule : marque, modèle, année, kilométrage. »

*(Cliquer sur **« Charger un exemple »** pour aller vite, puis **ajouter la
photo** via le champ fichier.)*

> « Et surtout, on **ajoute une photo** : c'est elle qui va être analysée par
> notre modèle de vision. »

### Étape 3 — Lancer l'inspection (5 s)

*(Cliquer sur **« Lancer l'inspection »**.)*

> « L'agent orchestrateur prend la main. »

### Étape 4 — L'orchestration en direct (60 s) — LE MOMENT CLÉ

*(Laisser le panneau « Orchestration multi-agents en direct » se dérouler.)*

> « Ce que vous voyez ici, ce ne sont **pas des étapes scriptées** : chaque
> flèche est un **vrai message échangé entre agents**, affiché au moment où il
> se produit. L'orchestrateur délègue à la Computer Vision, puis au sous-agent
> d'évaluation qui appelle le machine learning, ensuite à la négociation, et
> enfin au rapport. Les nœuds s'allument quand ils communiquent. »

> « La légère latence entre les messages, c'est le **LLM Mistral** qui rédige
> réellement les synthèses de chaque agent. »

### Étape 5 — Lire le rapport (45 s)

*(Faire défiler le rapport final.)*

> « Résultat : les **dommages détectés** par la vision, le **coût de
> réparation** et la **valeur marchande** estimés par le machine learning, et
> une **offre de prix conseillée** et argumentée par l'agent de négociation. »

*(Si le cas est une épave :)*

> « Ici le véhicule est classé en **perte totale** : réparer coûterait plus de
> 80 % de sa valeur — l'achat n'a pas d'intérêt. »

### Étape 6 — Conclure (15 s)

> « Tout ça tourne sur un simple laptop, sans compte Azure. Une seule variable
> bascule vers les services Azure réels, sans changer une ligne de code. »

---

## 3. Points à marteler pendant la démo

- **Multi-agents visible** : les messages entre agents sont réels et en direct.
- **Vision réelle en local** : notre modèle Custom Vision exporté, sur le port 88.
- **Machine learning** : coût de réparation + valeur, avec la logique d'épave.
- **Edge** : la webapp tourne en local dans Docker.
- **Mock ↔ réel** : bascule par une variable, sans réécriture.

---

## 4. Plan B (si quelque chose plante)

| Problème | Réaction |
|----------|----------|
| Le conteneur vision (port 88) ne répond pas | Aucun souci : l'app **retombe automatiquement sur le simulateur**. La démo continue, on le mentionne comme un choix de robustesse. |
| Pas de photo / photo invalide | Idem, fallback automatique sur le mode simulé. |
| Le LLM Mistral rame ou quota atteint | Mettre `LLM_MODE=template` dans `.env` et relancer : les textes deviennent déterministes, tout le reste marche. |
| Le port 8000 est pris | Relancer sur un autre port : `--port 8080`, puis ouvrir http://127.0.0.1:8080 |
| La page est blanche | Rafraîchir avec `Ctrl + Shift + R` (cache navigateur). |

> Message rassurant : **la démo ne peut pas planter en dur** — chaque brique a
> un mode de secours. On peut toujours dérouler le scénario complet.

---

## 5. Commandes utiles (antisèche)

```bash
# Santé de l'app (mode courant)
curl http://127.0.0.1:8000/api/health

# Lancer la webapp
uvicorn app.main:app --host 127.0.0.1 --port 8000

# Variante Docker (appuie la brique Edge)
docker compose up --build

# Démo sans navigateur (secours ultime)
python demo_cli.py

# Tests (si on veut prouver que ça marche)
pytest -q
```
