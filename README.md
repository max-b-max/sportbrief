# SportBrief - Briefing Sportif Automatisé
### Projet Data Analyst — Collecte multi-sources, traitement automatisé & restitution audio

---

## Sommaire

- [Contexte](#contexte)
- [Problématique](#problématique)
- [Objectifs du projet](#objectifs-du-projet)
- [Sources de données](#sources-de-données)
  - [Flux RSS](#flux-rss)
  - [APIs sportives](#apis-sportives)
- [Technologies utilisées](#technologies-utilisées)
  - [Langage](#langage)
  - [Librairies Python](#librairies-python)
  - [Intelligence Artificielle](#intelligence-artificielle)
  - [Automatisation & Déploiement](#automatisation--déploiement)
  - [Environnement](#environnement)
- [Architecture du projet](#architecture-du-projet)
- [Pipeline analytique](#pipeline-analytique)
  - [Flux global du projet](#flux-global-du-projet)
- [Utilisation](#utilisation)
- [Personnalisation](#personnalisation)
- [Résultats clés](#résultats-clés)
- [Limites du projet](#limites-du-projet)
- [Perspectives d'évolution](#perspectives-dévolution)
- [Licence](#licence)

---

## Contexte

Ce projet a été réalisé dans le cadre d'un projet personnel à la suite de ma certification **Data Analyst**, avec pour objectif de mettre en pratique les compétences acquises sur un cas concret : la collecte, le traitement et la restitution automatisée de données.

Les amateurs de sport sont confrontés à une multiplication des sources d'information (sites, applications, réseaux sociaux), rendant la consommation d'actualités chronophage et fragmentée. Assimiler l'ensemble des informations pertinentes nécessite de consulter plusieurs plateformes, souvent à des moments peu adaptés comme le matin au réveil ou le soir avant de dormir.

Le projet combine **collecte de données multi-sources**, **agrégation structurée**, **synthèse par LLM** et **génération audio TTS**, le tout orchestré par un système d'automatisation quotidienne.

---

## Problématique

**Comment centraliser, filtrer et synthétiser automatiquement les informations sportives provenant de sources hétérogènes afin de réduire le temps d'écran tout en conservant un niveau d'information élevé ?**

---

## Objectifs du projet

- Collecter automatiquement les actualités sportives depuis des flux RSS et APIs
- Normaliser et dédupliquer les données issues de sources hétérogènes
- Agréger les données structurées et non structurées en un format unifié
- Générer un briefing synthétique via un modèle de langage (LLM)
- Produire un fichier audio MP3 permettant une écoute sans écran
- Automatiser l'exécution quotidienne du pipeline sur un serveur cloud

---

## Sources de données

Les données utilisées dans ce projet proviennent de deux types de sources, combinant flux RSS et APIs sportives.

### Flux RSS

- **RMC Sport** : football, rugby, basketball, handball, tennis, MMA, cyclisme, formule 1
- **L'Équipe** : football, rugby, basketball, handball, tennis, biathlon, ski alpin
- **Dailysport** : football, basketball, rugby, MMA, tennis de table

### APIs sportives

- **Football-data.org** : résultats, classements et calendriers football (Ligue 1, Premier League, Champions League, etc.)
- **nba_api** : statistiques NBA et joueurs français
- **OpenF1** : données en temps réel Formule 1
- **biathlonresults** : résultats et classements biathlon
- **LNV** : résultats et classements volleyball (Ligue A, équipe de France)

---

## Technologies utilisées

### Langage
- Python 3.11+

### Librairies Python
- feedparser : collecte et parsing des flux RSS
- requests : appels API REST
- python-dateutil : manipulation des dates
- python-dotenv : gestion sécurisée des clés API
- nba_api : données NBA
- biathlonresults : données biathlon

### Intelligence Artificielle
- Google Gemini : synthèse LLM du briefing sportif
- Edge-TTS : génération audio en voix française

### Automatisation & Déploiement
- n8n : orchestration et automatisation quotidienne
- Oracle Cloud Free Tier : hébergement du pipeline (VM ARM)
- systemd : gestion des services sur le serveur

### Environnement
- Streamlit : dashboard de configuration et lecture
- Visual Studio Code
- Git / GitHub

---

## Architecture du projet

```text
SPORTBRIEF/
├── src/
│   ├── collect/
│   │   ├── collect_rss.py
│   │   ├── collect_footballdata.py
│   │   ├── collect_nba.py
│   │   ├── collect_f1.py
│   │   ├── collect_biathlon.py
│   │   └── collect_lnv.py
│   │
│   ├── process/
│   │   ├── merge_rss.py
│   │   ├── normalize_rss.py
│   │   └── deduplicate_rss.py
│   │
│   ├── aggregate/
│   │   └── aggregate_data.py
│   │
│   ├── synthesize/
│   │   ├── generate_briefing.py
│   │   └── generate_audio.py
│   │
│   ├── config/
│   │   ├── api_config.py
│   │   ├── rss_sources.py
│   │   └── preferences.py
│   │
│   └── app/
│       ├── main.py
│       ├── services/
│       └── components/
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── output/
│
├── deploy/
│   ├── n8n_workflow.json
│   ├── docker-compose.yml
│   ├── install.sh
│   └── DEPLOY_ORACLE_CLOUD.md
│
├── sportbrief.py
├── run_dashboard.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## Pipeline analytique

Le projet repose sur un pipeline structuré en cinq étapes, depuis la collecte de données hétérogènes jusqu'à la restitution audio :

- **Collecte** : récupération parallèle des flux RSS (40+ sources) et des données API (5 collecteurs)
- **Traitement** : fusion, normalisation et déduplication des articles RSS
- **Agrégation** : combinaison des données RSS et API en un format JSON unifié
- **Synthèse** : génération du script du briefing via Google Gemini
- **Audio** : conversion texte-parole via Edge-TTS (voix française)

### Flux global du projet

```text
RSS (RMC, L'Équipe, Dailysport) + APIs (football-data, nba_api, OpenF1, biathlon, LNV)
                        ↓
Python (collecte, normalisation, déduplication)
                        ↓
Agrégation (JSON unifié)
                        ↓
Google Gemini (synthèse LLM)
                        ↓
Edge-TTS (briefing audio MP3)
                        ↓
n8n / Oracle Cloud (automatisation quotidienne 7h)
```

---

## Utilisation

```bash
# Cloner le repo
git clone https://github.com/max-b-max/sportbrief.git
cd sportbrief

# Installer les dépendances
pip install -r requirements.txt

# Configurer les clés API
cp .env.example .env
# Éditer .env avec vos clés

# Pipeline complet (collecte + agrégation)
python sportbrief.py

# Avec génération du briefing texte
python sportbrief.py -b

# Avec briefing + audio
python sportbrief.py -a

# Mode debug (sauvegarde le prompt LLM)
python sportbrief.py -a -d

# Dashboard Streamlit
python run_dashboard.py
```

---

## Personnalisation

Le fichier `user_preferences.json` permet de configurer :

- Sports activés/désactivés
- Équipes et clubs suivis
- Ligues à surveiller
- Durée du briefing
- Voix TTS

---

## Résultats clés

- Le pipeline collecte et traite en moyenne **40+ flux RSS** et **5 APIs** en 5 à 10 minutes (collecte séquentielle + appels LLM + génération audio)
- Le briefing généré couvre l'ensemble des sports configurés avec une synthèse de 5 à 15 minutes en audio selon le mode choisi
- L'automatisation quotidienne via n8n sur Oracle Cloud Free Tier assure une exécution fiable sans intervention manuelle
- Le format audio MP3 permet une consommation d'information sans écran, répondant directement à la problématique initiale

---

## Limites du projet

- Les flux RSS dépendent de la disponibilité et de la structure des sites sources, susceptibles de changer sans préavis
- La qualité de la synthèse LLM varie selon le volume et la pertinence des données collectées
- Certains sports (tennis, ping-pong, cyclisme) ne disposent pas encore de collecteur API dédié et reposent uniquement sur les flux RSS
- Le plan gratuit de certaines APIs impose des limites de requêtes quotidiennes

---

## Perspectives d'évolution

- Ajout de collecteurs API pour les sports non encore couverts (tennis, cyclisme)
- Intégration de notifications push pour la livraison du briefing
- Personnalisation avancée du style de synthèse via des prompts configurables
- Ajout d'un module d'analyse de tendances sur les données collectées
- Extension multi-utilisateurs avec profils de préférences distincts

---

## Licence

Projet réalisé à des fins personnelles et pédagogiques.
