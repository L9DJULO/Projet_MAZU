# MVP, cas d'usage et iterations

Ce document repond explicitement aux points "Solve a real-life topic (multi use
cases inside)", "Define your MVP" et "Iteration [Question, Diagram, Data]" du
sujet.

---

## 1. Probleme reel adresse

Le marche de l'occasion automobile souffre d'une forte **asymetrie
d'information** : le vendeur connait le vehicule, l'acheteur non. Resultat :
prix mal evalues, litiges, mauvaises affaires. AutoExpert AI automatise
l'expertise pour retablir l'equilibre, a partir de simples photos.

---

## 2. Cas d'usage multiples (un meme socle, plusieurs publics)

| # | Acteur | Cas d'usage | Valeur apportee |
|---|--------|-------------|-----------------|
| 1 | **Acheteur particulier** | Inspecter avant achat, obtenir un prix d'offre | Negocier en confiance, eviter les pieges |
| 2 | **Vendeur particulier** | Estimer son vehicule avant mise en vente | Fixer un prix juste et credible |
| 3 | **Concessionnaire / garage** | Pre-chiffrer les reparations en reprise | Gagner du temps sur l'estimation |
| 4 | **Assureur / expert** | Premiere evaluation de sinistre a distance | Reduire les deplacements d'expert |
| 5 | **Gestionnaire de flotte** | Suivre l'etat d'un parc de vehicules | Planifier l'entretien et la revente |

Tous ces cas reposent sur le **meme pipeline** (Vision -> ML -> Agents), seules
les donnees d'entree et la lecture du rapport changent : c'est ce qui en fait un
produit et pas une demo jetable.

---

## 3. Definition du MVP

Le MVP livre (ce qui est dans ce depot) couvre le **parcours acheteur de bout en
bout** :

**Inclus dans le MVP :**
- Upload de photos via une webapp locale.
- Detection des dommages (Computer Vision).
- Estimation du cout de reparation + valeur marchande (Machine Learning).
- Verification d'historique (API externe).
- Orchestration multi-agents + rapport consolide avec offre de prix.
- Execution locale Docker (Edge), sans dependance cloud obligatoire.

**Hors MVP (evolutions futures) :**
- Modeles Azure entraines sur de vraies donnees (vs barèmes / mock).
- Traitement video 360 (extraction de frames).
- Comptes utilisateurs, historique des inspections, export PDF.
- Application mobile.

Le MVP est volontairement **fonctionnel sans budget Azure** (mode mock), puis
**branchable sur Azure** sans reecriture (voir `azure-deployment.md`).

---

## 4. Iterations (Question -> Diagramme -> Data)

Trace des iterations de conception, comme demande dans le suivi du projet.

### Iteration 1 - Cadrage
- **Question :** quel probleme reel, quel utilisateur prioritaire ?
- **Diagramme :** schema a 4 couches (User -> WebApp -> Orchestrateur -> services).
- **Data :** informations vehicule (marque, modele, annee, km, VIN) + photos.

### Iteration 2 - Pipeline IA
- **Question :** comment passer d'une photo a un prix justifie ?
- **Diagramme :** chaine Vision -> Evaluation/Historique -> ML valeur ->
  Negociation -> Rapport (voir `architecture.md`).
- **Data :** schemas partages `VisionResult`, `CostEstimate`, `MarketValuation`.

### Iteration 3 - Integration Azure
- **Question :** comment demontrer les 4 capacites sans bloquer la demo ?
- **Diagramme :** double chemin mock/real par brique, pilote par `AZURE_MODE`.
- **Data :** format reel des endpoints (Custom Vision, ML Designer Inputs/Results).

### Iteration 4 - Industrialisation
- **Question :** comment rendre le projet portable et presentable ?
- **Diagramme :** conteneurisation Docker + profil Ollama optionnel.
- **Data :** vehicules d'exemple, tests automatises, journal d'agents.

---

## 5. Mesure de succes du MVP

- Le pipeline produit un rapport complet en moins de quelques secondes.
- Resultat **reproductible** (memes entrees -> meme sortie) pour la demo.
- Les 4 capacites sont demontrables (mock en local, real sur Azure).
- Tests automatises au vert (`pytest`).
