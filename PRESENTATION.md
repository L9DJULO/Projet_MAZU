# AutoExpert AI — Texte de la présentation

Durée cible : **~15 minutes** + 5 min de questions.
Équipe : **Jules Lange**, **Arthur Goullet De Rugy**, **Évariste Balvay**.

Répartition proposée :
- **Jules** : intro, problème, concept, agents, démo, conclusion
- **Arthur** : capacités & architecture, Computer Vision
- **Évariste** : Machine Learning, Edge, MVP

> Le texte ci-dessous est rédigé pour être lu ou reformulé naturellement. Les
> indications entre parenthèses *(action)* sont des gestes à faire, pas à dire.

---

## Slide 1 — Couverture  ·  *Jules*

Bonjour à toutes et à tous. Nous sommes l'équipe **AutoExpert AI** : Jules,
Arthur et Évariste.

Notre projet illustre l'infusion de l'IA dans une application concrète. L'idée
de départ est simple : on prend en photo un véhicule d'occasion, et le système
en déduit son état, chiffre les réparations, estime sa valeur, et va même
jusqu'à conseiller un prix d'achat.

Nous allons vous montrer comment il réunit les **quatre capacités Azure**
demandées — cognitive, edge, machine learning et agentique — puis nous
terminerons par une **démonstration en direct**.

---

## Slide 2 — Le problème  ·  *Jules*

Pourquoi ce projet ? Parce qu'il répond à un problème bien réel : le marché de
l'occasion automobile souffre d'une forte **asymétrie d'information**.

D'un côté, le vendeur connaît son véhicule. De l'autre, l'acheteur, lui, est
souvent démuni : il n'a pas l'expertise technique pour repérer les dommages,
certains défauts sont invisibles à l'œil nu, et il n'a aucun moyen objectif de
juger si le prix est correct. Résultat : de mauvaises affaires, des litiges, et
parfois de véritables arnaques.

*(Montrer la carte de droite.)*

AutoExpert AI rétablit l'équilibre : à partir de simples photos, il apporte à
l'acheteur une expertise automatique — des dommages détectés, un coût de
réparation chiffré, une valeur de marché estimée, et un prix d'achat conseillé
et argumenté.

---

## Slide 3 — Le concept  ·  *Jules*

Le concept tient en une seule chaîne de traitement.

*(Suivre le pipeline de gauche à droite.)*

Une photo entre. Elle passe par la **vision par ordinateur**, qui lit l'état du
véhicule. Puis par le **machine learning**, qui chiffre le coût et la valeur.
Ensuite, nos **agents** orchestrent l'analyse. Et il en ressort un **rapport**
complet, avec un prix.

Un point important : ce même pipeline sert **plusieurs publics**. L'acheteur,
bien sûr, mais aussi le vendeur qui veut estimer son bien, le garage en reprise,
l'assureur pour une première évaluation à distance, ou un gestionnaire de flotte.
C'est ce qui en fait un vrai produit, et pas une simple démo jetable.

---

## Slide 4 — Les 4 capacités Azure  ·  *Arthur*

Cette diapositive répond directement à la consigne du projet : démontrer quatre
capacités.

**Un**, les capacités **cognitives**, avec Azure Computer Vision : détecter
l'état du véhicule sur une photo.

**Deux**, le scénario **Edge** : notre application web tourne en local, sur le
laptop, dans Docker.

**Trois**, le **machine learning**, avec Azure ML : estimer le coût de
réparation et la valeur marchande.

**Quatre**, l'**agentique** : un agent orchestrateur qui délègue à trois
sous-agents spécialisés.

Nous allons maintenant détailler chacune de ces briques.

---

## Slide 5 — Architecture  ·  *Arthur*

Voici la vue d'ensemble.

*(Descendre couche par couche.)*

Tout en haut, l'**utilisateur** fournit des photos. Il s'adresse à
l'**application web**, qui tourne en local — c'est notre couche Edge.

Cette application appelle un **agent orchestrateur**. Lui ne fait pas le travail
lui-même : il **coordonne** trois sous-agents — évaluation mécanique,
négociation et rapport.

Enfin, ces agents s'appuient sur deux **services** : la vision par ordinateur et
le machine learning.

L'intérêt de ce découpage : chaque couche est indépendante et remplaçable. On
peut passer d'un service simulé au vrai service Azure sans toucher au reste.

---

## Slide 6 — Brique 1 : Computer Vision  ·  *Arthur*

Première brique, la vision.

Nous avons **entraîné un modèle Azure Custom Vision** sur des images de
véhicules. Point clé pour la démonstration : nous l'avons **exporté en conteneur
Docker**, et il tourne **en local**, sur le port 88. Autrement dit, aucune clé
cloud n'est nécessaire pendant la démo — le modèle s'exécute sur la machine.

Concrètement, le modèle classe l'état global du véhicule : **« Bon »** ou
**« Détruit »**, avec une probabilité.

*(Montrer le passage verdict → score.)*

À partir de ce verdict, on calcule un **score d'état sur 100**. Et si la
réparation estimée dépasse **80 % de la valeur** du véhicule, on le déclare en
**perte totale** — une épave, économiquement irréparable.

---

## Slide 7 — Brique 3 : Machine Learning  ·  *Évariste*

Deuxième brique technique : le machine learning, avec Azure ML.

Deux estimations. La première, le **coût de réparation**. C'est exactement la
démarche du **tutoriel vu en cours** : un modèle de régression entraîné dans ML
Designer, déployé en **endpoint temps réel**, et consommé en REST. Il prend en
entrée le type de dommage, sa sévérité, la marque, l'année, le kilométrage.

La seconde, la **valeur marchande**, estimée par dépréciation — marque, année,
kilométrage — puis ajustée par le facteur d'état issu de la vision. C'est la base
d'une offre de prix réaliste.

*(Montrer le bandeau.)*

Et la règle métier qui relie les deux : si réparer coûte **plus de 80 % de la
valeur**, c'est une **perte totale économique**. L'achat n'a alors plus
d'intérêt, et on le signale clairement.

---

## Slide 8 — Brique 4 : Agentique  ·  *Jules*

On arrive au cœur du projet : la partie agentique.

Un **agent orchestrateur** ne réalise aucun calcul lui-même. Son rôle, c'est de
**déléguer** à trois sous-agents spécialisés : l'évaluation, la négociation et
le rapport.

Ce que nous voulons vraiment vous montrer, c'est que cette **communication entre
agents est visible en direct**. Chaque délégation et chaque réponse s'affiche en
streaming dans l'interface, au moment où elle se produit. Ce ne sont pas des
étapes pré-écrites : ce sont de vrais messages échangés.

*(Montrer le bandeau LLM.)*

Et pour rédiger leurs synthèses, les agents s'appuient sur un **LLM**. Ici nous
utilisons **Mistral**, mais Ollama en local ou Gemini sont tout aussi
branchables.

---

## Slide 9 — Brique 2 : Edge  ·  *Évariste*

La brique Edge, maintenant.

Toute l'application est **conteneurisée** et tourne sur le laptop. Une seule
commande, `docker compose up`, et la webapp est accessible dans le navigateur,
en local. Aucune dépendance au cloud pour l'exécution.

*(Montrer la carte du bas.)*

Et un détail qui compte : une **seule variable**, `AZURE_MODE`, fait basculer
tout le système. En mode **mock**, tout est simulé — on démarre sans compte
Azure ni clé, ce qui est parfait pour développer et démontrer. En mode **réel**,
les mêmes appels partent vers Azure, **sans changer une seule ligne de code**.

---

## Slide 10 — Démo live  ·  *Jules (+ toute l'équipe)*

Passons maintenant à la démonstration.

*(Basculer sur le navigateur.)*

On lance l'application en local. On saisit un véhicule, et surtout on **ajoute
une photo** — c'est elle qui sera analysée par notre modèle de vision.

*(Cliquer sur « Lancer l'inspection ».)*

Regardez le panneau d'orchestration : les **agents communiquent en direct**,
l'orchestrateur délègue, les sous-agents répondent. La petite latence, c'est le
LLM qui rédige réellement.

Et à la fin, le **rapport complet** : dommages détectés, coût de réparation,
valeur marchande, et le prix d'achat conseillé.

> Si la démo live échoue, on bascule sur le mode simulé (fallback automatique) —
> le scénario se déroule quand même.

---

## Slide 11 — Notre MVP  ·  *Évariste*

Un mot sur le périmètre.

Notre **MVP** couvre le parcours complet de l'acheteur, et il est **entièrement
fonctionnel** : upload de photos, détection de l'état, chiffrage du coût et de la
valeur, orchestration multi-agents, et prix conseillé.

*(Montrer la colonne de droite.)*

Hors périmètre, ce sont les **évolutions** : entraîner les modèles Azure sur des
données réelles, détecter finement le type de dommage, traiter la vidéo 360°,
ajouter des comptes utilisateurs, un export PDF, une application mobile.

L'essentiel : c'est **fonctionnel sans budget Azure**, et **branchable sur Azure
sans réécriture**.

---

## Slide 12 — Conclusion  ·  *Jules*

Pour conclure.

AutoExpert AI est un **cas concret** qui réunit les quatre briques du cours — la
vision, le machine learning, les agents et l'exécution Edge — autour d'un
problème réel. C'est **démontrable en local dès aujourd'hui**, et **déployable
sur Azure sans réécriture**.

Merci de votre attention. Nous sommes prêts pour vos questions.

---

## Questions probables du jury — réponses prêtes

- **« Utilisez-vous vraiment Azure ? »**
  Oui : le modèle de vision est un vrai Custom Vision entraîné puis exporté, et
  le code du machine learning consomme un endpoint Azure ML au format réel. Le
  mode simulé sert uniquement à démontrer sans coût.

- **« Pourquoi des mocks ? »**
  Pour une démo reproductible et sans budget. La bascule vers Azure se fait avec
  une variable, sans réécriture — l'architecture est prête pour la production.

- **« En quoi est-ce vraiment multi-agents ? »**
  L'orchestrateur délègue à des sous-agents autonomes qui échangent des messages,
  visibles en direct dans l'interface. Chacun a un rôle et un LLM.

- **« Comment estimez-vous le coût et la valeur ? »**
  Barème explicable en mode simulé ; en production, un modèle de régression Azure
  ML entraîné dans ML Designer, comme dans le tutoriel, consommé en REST.

- **« Et la fiabilité de la détection ? »**
  Notre modèle classe l'état global (Bon / Détruit). Une évolution serait un
  modèle de détection d'objets pour localiser précisément chaque dommage.
