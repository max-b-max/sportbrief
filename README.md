# SPORTBRIEF

SportBrief est un pipeline de données permettant d'agréger, filtrer et synthétiser des actualités sportives personnalisées afin de réduire le temps passé devant les écrans.

## Problèmes métier

Les amateurs de sport sont confrontés à une multiplication des sources d'information sportives (sites, applications, réseaux sociaux), rendant la consommation d'actualités chronophage et fragmentée.
Assimiler l'ensemble des informations pertinentes nécessite de consulter plusieurs plateformes, souvent à des moments peu adaptés comme le matin au réveil ou le soir avant de dormir.
Ce projet vise à centraliser, filtrer et synthétiser automatiquement les informations sportives pertinentes afin de réduire le temps d'écran tout en conservant un niveau d'information élevé.

## Cible utilisateur

Utilisateurs passionnés de sport souhaitant rester informés de l'actualité sportive sans multiplier les consultations d'écrans.
Le projet est initialement conçu pour un usage personnel, puis étendu à des utilisateurs génériques partageant les mêmes besoins.

## Sports couverts

- Football
- Basketball (NBA)
- Rugby
- Handball
- Tennis
- Biathlon
- Formule 1
- Cyclisme
- Tennis de table
- MMA
- Volleyball
- Jeux Olympiques (lorsqu'ils sont actifs)

## Sources de données

Le projet repose principalement sur des flux RSS multi-sports (RMC Sport, L'Équipe, Dailysport), complétés par des APIs lorsque des données structurées sont nécessaires :
- **RSS** : RMC Sport, L'Équipe, Dailysport
- **APIs** : API-Football, API-Basketball, Football-Data.org, biathlonresults

## Stack technique

- **Python 3.11+** - Langage principal
- **feedparser** - Collecte des flux RSS
- **requests** - Appels API REST
- **Google Gemini** - Synthèse LLM du briefing
- **Edge-TTS** - Génération audio (voix française)
- **Streamlit** - Dashboard de configuration et lecture
- **n8n** - Automatisation quotidienne (Oracle Cloud)

## Installation

```bash
# Cloner le repo
git clone https://github.com/max-b-max/SportBrief.git
cd SportBrief

# Installer les dépendances
pip install -r requirements.txt

# Configurer les clés API
cp .env.example .env
# Éditer .env avec vos clés
```

## Utilisation

```bash
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

## Architecture

```text
Sources (RSS & APIs)
        ↓
Data brute (raw)
        ↓
Filtrage & règles métier
        ↓
Données structurées
        ↓
Sortie finale (résumé texte + audio MP3)
```

## Personnalisation

Éditez `user_preferences.json` pour configurer :
- Sports activés/désactivés
- Équipes et clubs suivis
- Ligues à surveiller
- Durée du briefing
- Voix TTS

## Méthodologie

Le projet est développé de manière itérative et incrémentale, avec une approche MVP, en évitant la sur-ingénierie et en restant aligné avec un rôle de Data Analyst / Business Analyst.
