"""
Module LLM SportBrief
Genere le script audio du briefing sportif a partir des donnees agregees
"""

import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# Charger .env
from dotenv import load_dotenv
load_dotenv()

try:
    from dateutil import parser as date_parser
except ImportError:
    date_parser = None


# Configuration
INPUT_FILE = Path("data/processed/aggregated_data.json")
OUTPUT_DIR = Path("data/output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Prompt systeme de base pour le LLM (sera complete dynamiquement)
SYSTEM_PROMPT_BASE = """Tu es un journaliste sportif francais qui presente un briefing audio quotidien personnalise.

*** REGLE ABSOLUE - NE JAMAIS INVENTER ***
- Tu ne dois JAMAIS inventer de scores, resultats, statistiques ou informations
- Utilise UNIQUEMENT les donnees fournies dans le prompt
- Si un match est "a venir" (match_upcoming), dis "match a venir" et ne donne PAS de score
- Si tu n'as pas de resultat pour un match, ne l'invente pas
- Prefere dire "pas d'information disponible" plutot que d'inventer

*** REGLE ABSOLUE - PAS DE REPETITION ***
- NE JAMAIS repeter la meme information deux fois dans le briefing
- Si tu parles des joueurs francais en NBA, fais-le UNE SEULE FOIS
- Si tu mentionnes un evenement (UFC, match, etc.), une seule mention suffit
- Chaque info = une seule apparition dans le briefing

*** REGLE ABSOLUE - STATS NBA ***
- Pour les joueurs NBA, utilise EXACTEMENT les chiffres fournis dans les donnees
- Si les donnees disent "28 points", tu dis "28 points" (pas 33, pas 30)
- Si les donnees disent "vs HOU" et "W" (victoire), c'est une VICTOIRE contre Houston
- NE MODIFIE PAS les statistiques, recopie-les fidelement

*** REGLE ABSOLUE - SCORES VOLLEYBALL ***
- En volleyball, le score est au format "sets domicile - sets exterieur"
- Si le resultat est "Chaumont 2-3 MHSC", cela signifie: Chaumont (domicile) a PERDU 2 sets a 3 contre MHSC
- RECOPIE le score EXACTEMENT comme fourni, ne l'inverse JAMAIS
- Exemple: "Chaumont 2-3 MHSC" = "Chaumont s'est incline 2-3 face a MHSC" (PAS "3-2"!)

FOCUS PRINCIPAL: LES RESULTATS DES MATCHS (UNIQUEMENT CEUX FOURNIS)
- Ne mentionne que les scores PRESENTS dans les donnees
- Pour les matchs a venir, annonce-les sans score
- Mentionne les buteurs/marqueurs seulement si l'info est disponible
- Indique les classements fournis dans les donnees

SELECTION DES INFOS:
- Tu recois TOUTES les actualites disponibles
- Selectionne les plus RECENTES et les plus PERTINENTES
- Evite les doublons (meme info de sources differentes = une seule mention)
- Pour les equipes prioritaires, inclus TOUT ce qui les concerne

Ton style:
- Ton dynamique et enthousiaste mais professionnel
- Phrases courtes et percutantes, adaptees a l'ecoute audio
- Utilise des transitions fluides entre les sports

Structure du briefing:
1. Introduction courte (date, accroche)
2. RESULTATS des equipes favorites (UNIQUEMENT si fournis dans les donnees)
3. MATCHS A VENIR des equipes favorites
4. ACTUALITES DETAILLEES des equipes a priorite maximale (mercato, entraineur, coulisses)
5. Actualites des autres equipes favorites avec DETAILS
6. TOUS LES AUTRES SPORTS avec leurs actualites (developpe chaque sport)
7. Joueurs francais a l'etranger (stats detaillees)
8. Conclusion avec les prochains matchs

DEVELOPPEMENT DU CONTENU:
- Pour CHAQUE sport mentionne, donne des details substantiels
- Ne te contente pas d'une phrase par sport
- Developpe le contexte, les enjeux, les performances individuelles
- Meme les sports secondaires meritent 2-3 phrases minimum

FORMAT SPECIAL POUR LA NBA / BASKETBALL:
STRUCTURE OBLIGATOIRE de la section NBA:
1. CLASSEMENT: Commence par le TOP 5 de chaque conference (Est et Ouest)
   - Mentionne les leaders avec leurs stats (Victoires-Defaites, serie en cours)
2. MATCHS DE LA VEILLE: Resume des matchs joues hier
   - Scores finaux avec nom complet des equipes
3. JOUEURS FRANCAIS: Stats des joueurs francais pour les matchs de la veille
   - Format: Nom + equipe, resultat, stats (points, rebonds, passes)

- Pour chaque joueur francais, ne mentionne que son match de la VEILLE
- Format OBLIGATOIRE par joueur:
  1. Nom du joueur + equipe
  2. Resultat: victoire ou defaite + adversaire COMPLET
  3. Stats: X points, Y rebonds, Z passes decisives
- Exemple CORRECT: "Victor Wembanyama et les Spurs se sont imposes face aux Houston Rockets. Wemby a inscrit 28 points, capte 16 rebonds et delivre 3 passes decisives."
- Exemple INCORRECT: "Wembanyama et les Spurs ont gagne 28-16-3" (incomprehensible)
- DECODE les abreviations d'equipes NBA:
  SAS=San Antonio Spurs, HOU=Houston Rockets, MIN=Minnesota Timberwolves,
  OKC=Oklahoma City Thunder, LAC=Los Angeles Clippers, UTA=Utah Jazz,
  WAS=Washington Wizards, MIL=Milwaukee Bucks, DAL=Dallas Mavericks,
  ATL=Atlanta Hawks, NOP=New Orleans Pelicans, NYK=New York Knicks,
  SAC=Sacramento Kings, CHA=Charlotte Hornets, TOR=Toronto Raptors
- PERFORMANCES EXTRAORDINAIRES: Si un joueur (francais ou non) realise 40+ points, 20+ rebonds,
  15+ passes ou un triple-double, mentionne-le comme fait marquant

Regles:
- JAMAIS inventer de scores ou resultats
- TOUJOURS mentionner la DATE pour chaque match, combat ou evenement (passe ou futur)
  * Pour les matchs passes: "Samedi 25 janvier, l'OM a battu Lyon 2 a 0"
  * Pour les matchs a venir: "Ce samedi 1er fevrier, l'OM affrontera le Paris FC"
  * Pour les combats: "L'UFC 325 a lieu ce samedi a Sydney avec Benoit Saint Denis"
- INTERPRETATION DES DATES RELATIVES dans les actualites:
  * Si une actu du samedi 31 janvier dit "mardi", c'est le MARDI SUIVANT (3 fevrier)
  * Si une actu dit "ce week-end", c'est le week-end suivant la date de l'actu
  * NE JAMAIS confondre avec d'autres dates mentionnees dans les donnees structurees
- Ne pas utiliser d'emojis
- INTERDICTION ABSOLUE de repeter la meme info deux fois (meme reformulee)
  * Si tu parles de l'UFC 325, une seule fois suffit avec toutes les infos
  * Synthetise les infos similaires en une seule phrase complete
- Prononcer les scores clairement (ex: "3 a 1" et non "3-1")
- Pour les noms etrangers, utiliser une forme francisee si possible
- Ne pas mentionner les sources (L'Equipe, RMC, etc.)
- Pour chaque equipe prioritaire, mentionne le PROCHAIN MATCH avec date et adversaire
"""

# Configuration de duree par mode
DURATION_CONFIG = {
    "short": {
        "word_target": "300-600 mots",
        "min_words": 300,
        "duration": "2-4 minutes",
        "style": "Resume rapide, que l'essentiel des resultats",
        "details": "Seulement les scores et resultats principaux"
    },
    "medium": {
        "word_target": "800-1200 mots MINIMUM",
        "min_words": 800,
        "duration": "5-10 minutes",
        "style": "Briefing complet et detaille",
        "details": """Pour chaque sport, developpe:
- Les resultats avec contexte (enjeux, classement)
- Les performances individuelles notables
- Le mercato et les transferts
- Les blessures et absences
- Les prochains matchs importants
- Les anecdotes et faits marquants
Meme pour les sports non prioritaires, donne des details substantiels."""
    },
    "long": {
        "word_target": "1500-2500 mots MINIMUM",
        "min_words": 1500,
        "duration": "10-20 minutes",
        "style": "Analyse approfondie et exhaustive",
        "details": "Couvre TOUTES les actualites disponibles avec analyse et contexte historique"
    }
}


def clean_markdown_for_audio(text: str) -> str:
    """
    Nettoie le texte des balises markdown pour un rendu audio propre.
    Supprime: **bold**, *italic*, # headers, [links](url), etc.
    """
    if not text:
        return text

    # Supprimer les headers markdown (# ## ### etc.)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

    # Supprimer le gras **texte** ou __texte__
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)

    # Supprimer l'italique *texte* ou _texte_
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'(?<!\w)_(.+?)_(?!\w)', r'\1', text)

    # Supprimer les liens [texte](url) -> garder juste le texte
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)

    # Supprimer les images ![alt](url)
    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', text)

    # Supprimer le code inline `code`
    text = re.sub(r'`([^`]+)`', r'\1', text)

    # Supprimer les blocs de code ```
    text = re.sub(r'```[\s\S]*?```', '', text)

    # Supprimer les listes à puces (- ou * ou +) en debut de ligne
    text = re.sub(r'^[\s]*[-*+]\s+', '', text, flags=re.MULTILINE)

    # Supprimer les listes numerotees (1. 2. etc.)
    text = re.sub(r'^[\s]*\d+\.\s+', '', text, flags=re.MULTILINE)

    # Supprimer les lignes horizontales (---, ***, ___)
    text = re.sub(r'^[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)

    # Supprimer les blockquotes (>)
    text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)

    # Nettoyer les lignes vides multiples
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Supprimer les espaces en fin de ligne
    text = re.sub(r'[ \t]+$', '', text, flags=re.MULTILINE)

    return text.strip()


def get_jo_proximity_info(olympics_config: dict) -> dict:
    """
    Calcule la proximite des JO et retourne les infos contextuelles.
    """
    today = datetime.now().date()
    result = {
        "winter": None,
        "summer": None,
        "priority_event": None,
        "context_message": ""
    }

    next_games = olympics_config.get("next_games", {})

    # JO d'hiver
    winter = next_games.get("winter", {})
    if winter.get("date"):
        try:
            winter_date = datetime.strptime(winter["date"], "%Y-%m-%d").date()
            days_until = (winter_date - today).days
            result["winter"] = {
                "name": winter.get("name", "JO Hiver"),
                "date": winter["date"],
                "location": winter.get("location", ""),
                "days_until": days_until,
                "status": "en_cours" if days_until < 0 and days_until > -20 else (
                    "imminent" if 0 <= days_until <= 7 else (
                    "proche" if days_until <= 30 else (
                    "preparation" if days_until <= 180 else "lointain"
                )))
            }
        except ValueError:
            pass

    # JO d'ete
    summer = next_games.get("summer", {})
    if summer.get("date"):
        try:
            summer_date = datetime.strptime(summer["date"], "%Y-%m-%d").date()
            days_until = (summer_date - today).days
            result["summer"] = {
                "name": summer.get("name", "JO Ete"),
                "date": summer["date"],
                "location": summer.get("location", ""),
                "days_until": days_until,
                "status": "en_cours" if days_until < 0 and days_until > -20 else (
                    "imminent" if 0 <= days_until <= 7 else (
                    "proche" if days_until <= 30 else (
                    "preparation" if days_until <= 180 else "lointain"
                )))
            }
        except ValueError:
            pass

    # Determiner l'evenement prioritaire
    for jo_type in ["winter", "summer"]:
        jo = result[jo_type]
        if jo and jo["status"] in ["en_cours", "imminent", "proche"]:
            result["priority_event"] = jo_type
            if jo["status"] == "en_cours":
                result["context_message"] = f"LES {jo['name'].upper()} SONT EN COURS ! Priorite maximale sur les resultats."
            elif jo["status"] == "imminent":
                result["context_message"] = f"Les {jo['name']} commencent dans {jo['days_until']} jours ! Couvrir la preparation des athletes."
            elif jo["status"] == "proche":
                result["context_message"] = f"Les {jo['name']} approchent ({jo['days_until']} jours). Focus sur les qualifications."
            break

    return result


def build_system_prompt(prefs: dict) -> str:
    """Construit le prompt systeme avec les priorites utilisateur et la duree"""
    prompt = SYSTEM_PROMPT_BASE

    # Ajouter la configuration de duree
    duration_prefs = prefs.get("briefing_duration", {})
    mode = duration_prefs.get("mode", "medium")
    duration_config = DURATION_CONFIG.get(mode, DURATION_CONFIG["medium"])

    prompt += f"\n\n*** DUREE DU BRIEFING: {mode.upper()} - TRES IMPORTANT ***\n"
    prompt += f"- OBJECTIF OBLIGATOIRE: {duration_config['word_target']} ({duration_config['duration']} de lecture)\n"
    prompt += f"- Tu DOIS atteindre au minimum {duration_config['min_words']} mots\n"
    prompt += f"- Style: {duration_config['style']}\n"
    prompt += f"- Instructions: {duration_config['details']}\n"
    prompt += f"- NE PAS faire un briefing trop court. Developpe chaque section.\n"

    # Ajouter les priorites par equipe
    priorities = prefs.get("briefing_priorities", {})
    teams_priorities = priorities.get("teams_priorities", {})

    if teams_priorities:
        prompt += "\n\nPRIORITES PAR EQUIPE (respecte ces consignes):\n"
        for team, config in teams_priorities.items():
            level = config.get("level", "normal")
            topics = config.get("topics", [])
            desc = config.get("description", "")

            if level == "maximum":
                prompt += f"\n*** {team.upper()} (PRIORITE MAXIMALE) ***\n"
                prompt += f"- Couvre TOUS ces sujets: {', '.join(topics)}\n"
                prompt += f"- {desc}\n"
                prompt += f"- Consacre une part importante du briefing a cette equipe\n"
                prompt += f"- UTILISE TOUTES les actualites disponibles sur cette equipe dans les donnees\n"
                prompt += f"- Parle de l'entraineur, du mercato, des coulisses, des rumeurs\n"
            elif level == "high":
                prompt += f"\n** {team} (Priorite haute) **\n"
                prompt += f"- Sujets a couvrir: {', '.join(topics)}\n"
            elif level == "medium":
                prompt += f"\n* {team} (Priorite moyenne) *\n"
                prompt += f"- Sujets: {', '.join(topics)}\n"

    # Ajouter le focus JO si active
    olympics = prefs.get("olympics", {})
    if olympics.get("enabled"):
        jo_info = get_jo_proximity_info(olympics)
        priority_mode = olympics.get("priority_mode", False)

        prompt += "\n\n*** JEUX OLYMPIQUES ***\n"

        # Mode prioritaire force par l'utilisateur
        if priority_mode:
            prompt += "!!! MODE JO PRIORITAIRE ACTIVE !!!\n"
            prompt += "Les Jeux Olympiques sont le SUJET PRINCIPAL de ce briefing.\n"
            prompt += "STRUCTURE OBLIGATOIRE en mode JO prioritaire:\n"
            prompt += "1. Commence le briefing par une section JO complete et detaillee\n"
            prompt += "2. Consacre au moins 40% du contenu total aux actualites JO\n"
            prompt += "3. Couvre: qualifications, resultats, athletes francais engages, calendrier des epreuves\n"
            prompt += "4. Ensuite seulement, traite les autres sports\n\n"
        elif jo_info["context_message"]:
            prompt += f"!!! {jo_info['context_message']} !!!\n\n"

        # JO d'hiver
        if jo_info["winter"]:
            winter = jo_info["winter"]
            status_text = {
                "en_cours": "EN COURS",
                "imminent": f"DANS {winter['days_until']} JOURS",
                "proche": f"dans {winter['days_until']} jours",
                "preparation": f"dans {winter['days_until']} jours",
                "lointain": winter['date']
            }.get(winter["status"], winter['date'])
            prompt += f"- JO D'HIVER: {winter['name']} ({status_text}) - {winter['location']}\n"

        # JO d'ete
        if jo_info["summer"]:
            summer = jo_info["summer"]
            status_text = {
                "en_cours": "EN COURS",
                "imminent": f"DANS {summer['days_until']} JOURS",
                "proche": f"dans {summer['days_until']} jours",
                "preparation": f"dans {summer['days_until']} jours",
                "lointain": summer['date']
            }.get(summer["status"], summer['date'])
            prompt += f"- JO D'ETE: {summer['name']} ({status_text}) - {summer['location']}\n"

        # Instructions selon la proximite (si pas en mode prioritaire force)
        if not priority_mode:
            prompt += "\nFocus: qualifications, preparation athletes francais, calendrier\n"
            if jo_info["priority_event"]:
                prompt += "PRIORITE: Mentionner les actualites JO en debut de briefing !\n"
            prompt += "Si des infos JO sont disponibles, les mentionner selon leur importance.\n"

    # Rappel sur la distinction ski alpin / biathlon
    prompt += "\n\nATTENTION - DISTINCTION SPORTS:\n"
    prompt += "- SKI ALPIN (descente, slalom, geant): Lindsey Vonn, Alexis Pinturault, Clement Noel\n"
    prompt += "- BIATHLON (ski de fond + tir): Quentin Fillon Maillet, Julia Simon, Justine Braisaz-Bouchet\n"
    prompt += "- Ne PAS confondre ces deux sports !\n"

    return prompt


def load_aggregated_data() -> dict:
    """Charge les donnees agregees"""
    if not INPUT_FILE.exists():
        print(f"[ERROR] Fichier {INPUT_FILE} introuvable")
        print("        Lancez d'abord: python run_all_collectors.py")
        return {}

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_preferences() -> dict:
    """Charge les preferences utilisateur"""
    prefs_file = Path("user_preferences.json")
    if prefs_file.exists():
        with open(prefs_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def get_llm_config(prefs: dict) -> dict:
    """Recupere la configuration LLM"""
    config = prefs.get("llm", {
        "provider": "gemini",
        "model": "gemini-2.0-flash",
        "max_tokens": 1500,
    })
    # Ajouter la cle API Gemini si disponible
    api_keys = prefs.get("api_keys", {})
    if "gemini_api_key" in api_keys:
        config["gemini_api_key"] = api_keys["gemini_api_key"]
    return config


def build_user_prompt(data: dict, prefs: dict) -> str:
    """Construit le prompt utilisateur avec les donnees"""

    # Date du jour
    today = datetime.now().strftime("%A %d %B %Y")

    # Extraire les priorities
    priorities = prefs.get("briefing_priorities", {})
    teams_priorities = priorities.get("teams_priorities", {})

    # Extraire les preferences avec le sport associe
    sports_prefs = prefs.get("sports", {})
    favorite_teams = []
    favorite_teams_by_sport = {}
    for sport, config in sports_prefs.items():
        teams = config.get("teams", [])
        for team in teams:
            team_name = team.get("name", "") if isinstance(team, dict) else team
            if team_name:
                favorite_teams.append(team_name)
                if sport not in favorite_teams_by_sport:
                    favorite_teams_by_sport[sport] = []
                favorite_teams_by_sport[sport].append(team_name)

    # Construire la liste des favoris avec leurs priorites
    favorites_detail = []
    for sport, teams in favorite_teams_by_sport.items():
        for team in teams:
            priority_info = teams_priorities.get(team, {})
            level = priority_info.get("level", "normal")
            topics = priority_info.get("topics", ["resultats"])
            if level == "maximum":
                favorites_detail.append(f"  - {team.upper()} ({sport}) [PRIORITE MAX]: {', '.join(topics)}")
            elif level == "high":
                favorites_detail.append(f"  - {team} ({sport}) [Priorite haute]: {', '.join(topics)}")
            else:
                favorites_detail.append(f"  - {team} ({sport}): {', '.join(topics)}")

    # Construire le contexte
    prompt_parts = [
        f"Date: {today}",
        "",
        "*** PRIORITES DE CONTENU ***",
        "Focus principal: RESULTATS DES MATCHS (scores, buteurs, classements)",
        "",
        "*** EQUIPES FAVORITES ET SUJETS A COUVRIR ***",
    ]
    prompt_parts.extend(favorites_detail)
    prompt_parts.extend([
        "",
        "=== DONNEES SPORTIVES DU JOUR ===",
        ""
    ])

    # Organiser les items par sport et type
    items = data.get("items", [])

    # Grouper par sport
    by_sport = {}
    for item in items:
        sport = item.get("sport", "autre")
        if sport not in by_sport:
            by_sport[sport] = []
        by_sport[sport].append(item)

    # Date limite pour les actualites (7 jours max)
    today = datetime.now()
    max_age_days = 7

    def is_recent_news(item: dict) -> bool:
        """Verifie si une actualite date de moins de 7 jours"""
        published = item.get('published', '')
        if not published:
            return True  # Si pas de date, on garde par defaut

        try:
            if date_parser:
                # Parser differents formats de date avec dateutil
                pub_date = date_parser.parse(published, fuzzy=True)
                # Rendre naive si necessaire pour comparaison
                if pub_date.tzinfo is not None:
                    pub_date = pub_date.replace(tzinfo=None)
            else:
                # Fallback: essayer quelques formats courants
                for fmt in ["%a, %d %b %Y %H:%M:%S %Z", "%a, %d %b %Y %H:%M:%S %z",
                           "%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S"]:
                    try:
                        pub_date = datetime.strptime(published[:25], fmt)
                        break
                    except ValueError:
                        continue
                else:
                    return True  # Format non reconnu, on garde

            age = (today - pub_date).days
            return age <= max_age_days
        except (ValueError, TypeError, AttributeError):
            return True  # Si erreur de parsing, on garde par defaut

    def is_recent_match(item: dict) -> bool:
        """Verifie si un match/resultat date de moins de 7 jours"""
        match_date_str = item.get('date', '')
        if not match_date_str:
            return True  # Si pas de date, on garde par defaut

        try:
            # Format attendu: YYYY-MM-DD ou similaire
            if date_parser:
                match_date = date_parser.parse(match_date_str[:10], fuzzy=True)
                if match_date.tzinfo is not None:
                    match_date = match_date.replace(tzinfo=None)
            else:
                # Fallback: format ISO
                match_date = datetime.strptime(match_date_str[:10], "%Y-%m-%d")

            age = (today - match_date).days
            return age <= max_age_days
        except (ValueError, TypeError, AttributeError):
            return True  # Si erreur de parsing, on garde par defaut

    # Formater les donnees par sport
    for sport, sport_items in by_sport.items():
        prompt_parts.append(f"\n--- {sport.upper()} ---")

        # Priorite 1 d'abord (equipes favorites)
        priority_items = [i for i in sport_items if i.get("priority") == 1]
        other_items = [i for i in sport_items if i.get("priority") != 1]

        # TOUTES les news prioritaires RECENTES (moins de 7 jours) avec DATE
        priority_news = [i for i in priority_items if i.get("type") == "news" and is_recent_news(i)]
        if priority_news:
            prompt_parts.append("[ACTUALITES PRIORITAIRES]")
            for news in priority_news:
                pub_date = news.get('published', '')[:16] if news.get('published') else ''
                prompt_parts.append(f"  * [{pub_date}] {news.get('title', '')}")
                if news.get("summary"):
                    prompt_parts.append(f"    {news.get('summary')[:250]}")

        # Autres news RECENTES (moins de 7 jours) avec DATE
        other_news = [i for i in other_items if i.get("type") == "news" and is_recent_news(i)]
        if other_news:
            prompt_parts.append("\n[AUTRES ACTUALITES]")
            for news in other_news:
                pub_date = news.get('published', '')[:16] if news.get('published') else ''
                prompt_parts.append(f"  - [{pub_date}] {news.get('title', '')}")

        # Stats joueurs (basketball) - UNIQUEMENT le dernier match par joueur
        player_stats = [i for i in sport_items if i.get("type") == "player_stats"]
        if player_stats:
            # Dictionnaire pour decoder les abreviations NBA
            nba_teams = {
                "SAS": "San Antonio Spurs", "HOU": "Houston Rockets",
                "MIN": "Minnesota Timberwolves", "OKC": "Oklahoma City Thunder",
                "LAC": "Los Angeles Clippers", "UTA": "Utah Jazz",
                "WAS": "Washington Wizards", "MIL": "Milwaukee Bucks",
                "DAL": "Dallas Mavericks", "ATL": "Atlanta Hawks",
                "NOP": "New Orleans Pelicans", "NYK": "New York Knicks",
                "SAC": "Sacramento Kings", "CHA": "Charlotte Hornets",
                "TOR": "Toronto Raptors", "GSW": "Golden State Warriors",
                "LAL": "Los Angeles Lakers", "BOS": "Boston Celtics",
                "PHI": "Philadelphia 76ers", "MIA": "Miami Heat",
                "CHI": "Chicago Bulls", "DEN": "Denver Nuggets",
                "PHX": "Phoenix Suns", "POR": "Portland Trail Blazers",
                "CLE": "Cleveland Cavaliers", "IND": "Indiana Pacers",
                "DET": "Detroit Pistons", "ORL": "Orlando Magic",
                "BKN": "Brooklyn Nets", "MEM": "Memphis Grizzlies"
            }

            # Equipes des joueurs francais en NBA (saison 2025-26)
            french_players_teams = {
                "Victor Wembanyama": "San Antonio Spurs",
                "Rudy Gobert": "Minnesota Timberwolves",
                "Nicolas Batum": "Los Angeles Clippers",
                "Bilal Coulibaly": "Washington Wizards",
                "Alexandre Sarr": "Washington Wizards",
                "Zaccharie Risacher": "Atlanta Hawks",
                "Guerschon Yabusele": "New York Knicks",
                "Ousmane Dieng": "Oklahoma City Thunder",
                "Tidjane Salaun": "Charlotte Hornets",
                "Evan Fournier": "Detroit Pistons",
                "Killian Hayes": "Brooklyn Nets",
                "Sidy Cissoko": "San Antonio Spurs",
                "Armel Traore": "Los Angeles Lakers",
                "Pacôme Dadiet": "New York Knicks",
                "Moussa Diabate": "Charlotte Hornets",
                "Olivier Sarr": "Oklahoma City Thunder"
            }

            # Grouper par joueur et garder le plus recent
            players_last_game = {}
            for stat in player_stats:
                player = stat.get('player', '')
                # Recuperer la date (peut etre 'game_date' ou 'date' selon la source)
                game_date = stat.get('game_date', stat.get('date', ''))

                if player not in players_last_game:
                    players_last_game[player] = stat
                else:
                    # Comparer avec la date du match deja stocke
                    existing_date = players_last_game[player].get('game_date',
                                   players_last_game[player].get('date', ''))
                    if game_date > existing_date:
                        players_last_game[player] = stat

            prompt_parts.append("\nJoueurs francais en NBA (matchs de la veille):")
            prompt_parts.append("Format: Joueur (EQUIPE) | Date | vs Adversaire | Resultat | Points | Rebonds | Passes")
            for player, stat in players_last_game.items():
                game_date = stat.get('game_date', stat.get('date', 'date inconnue'))
                matchup = stat.get('matchup', '')
                result = "Victoire" if stat.get('result') == 'W' else "Defaite"

                # Recuperer l'equipe du joueur
                player_team = french_players_teams.get(player, "")

                # Decoder l'adversaire depuis le matchup
                # Format: "TEAM @ OPP" (away) ou "TEAM vs. OPP" (home)
                # La premiere equipe est celle du joueur, la seconde est l'adversaire
                opponent = matchup  # fallback
                if matchup:
                    # Normaliser le separateur
                    if ' @ ' in matchup:
                        parts = matchup.split(' @ ')
                    elif ' vs. ' in matchup:
                        parts = matchup.split(' vs. ')
                    elif ' vs ' in matchup:
                        parts = matchup.split(' vs ')
                    else:
                        parts = []

                    if len(parts) == 2:
                        # L'adversaire est la SECONDE partie
                        opp_abbr = parts[1].strip()
                        opponent = nba_teams.get(opp_abbr, opp_abbr)

                # Format avec equipe du joueur entre parentheses
                team_info = f" ({player_team})" if player_team else ""
                prompt_parts.append(
                    f"  - {player}{team_info} | {game_date} | vs {opponent} | {result} | "
                    f"{stat.get('points')} points | {stat.get('rebounds')} rebonds | {stat.get('assists')} passes"
                )

        # Tous les resultats de matchs RECENTS (moins de 7 jours) avec DATE
        match_results = [i for i in sport_items if i.get("type") == "match_result" and is_recent_match(i)]
        if match_results:
            if sport == "basketball":
                prompt_parts.append("\nMatchs NBA de la veille:")
            else:
                prompt_parts.append("\nResultats:")
            for match in match_results:
                match_date = match.get('date', '')[:10] if match.get('date') else ''
                home_team = match.get('home_team', '')
                away_team = match.get('away_team', '')
                competition = match.get('competition', match.get('league', ''))

                # Format avec home_score/away_score (football, basket)
                if match.get("home_score") is not None:
                    prompt_parts.append(
                        f"  - [{match_date}] {home_team} {match.get('home_score')} - "
                        f"{match.get('away_score')} {away_team} ({competition})"
                    )
                # Format avec score unique (volleyball LNV: "3-2")
                elif match.get("score"):
                    score = match.get('score')
                    journee = match.get('journee', '')
                    journee_info = f" J{journee}" if journee else ""
                    prompt_parts.append(
                        f"  - [{match_date}] {home_team} {score} {away_team} ({competition}{journee_info})"
                    )

        # Classements NBA - Tous les standings (pas seulement priorite 1)
        if sport == "basketball":
            all_standings = [i for i in sport_items if i.get("type") == "standing"]
            if all_standings:
                # Separer par conference
                east_standings = sorted(
                    [s for s in all_standings if s.get("conference") == "EAST"],
                    key=lambda x: x.get("rank", 99)
                )
                west_standings = sorted(
                    [s for s in all_standings if s.get("conference") == "WEST"],
                    key=lambda x: x.get("rank", 99)
                )

                prompt_parts.append("\nClassement NBA - Conference Est (Top 5):")
                for standing in east_standings[:5]:
                    team_name = f"{standing.get('team_city', '')} {standing.get('team', '')}".strip()
                    if not team_name:
                        team_name = standing.get('team', '')
                    prompt_parts.append(
                        f"  {standing.get('rank')}. {team_name} - "
                        f"{standing.get('wins')}V/{standing.get('losses')}D "
                        f"(Serie: {standing.get('streak', 'N/A')}, 10 derniers: {standing.get('last_10', 'N/A')})"
                    )

                prompt_parts.append("\nClassement NBA - Conference Ouest (Top 5):")
                for standing in west_standings[:5]:
                    team_name = f"{standing.get('team_city', '')} {standing.get('team', '')}".strip()
                    if not team_name:
                        team_name = standing.get('team', '')
                    prompt_parts.append(
                        f"  {standing.get('rank')}. {team_name} - "
                        f"{standing.get('wins')}V/{standing.get('losses')}D "
                        f"(Serie: {standing.get('streak', 'N/A')}, 10 derniers: {standing.get('last_10', 'N/A')})"
                    )

        # Classements des equipes favorites (football, volleyball)
        standings = [i for i in sport_items if i.get("type") == "standing" and i.get("priority") == 1]
        if standings and sport in ["football", "volleyball"]:
            prompt_parts.append("\nClassement equipes favorites:")
            for standing in standings:
                if sport == "football":
                    prompt_parts.append(
                        f"  {standing.get('position')}. {standing.get('team')} - "
                        f"{standing.get('points')} pts ({standing.get('competition')})"
                    )
                elif sport == "volleyball":
                    prompt_parts.append(
                        f"  {standing.get('position')}. {standing.get('team')} - "
                        f"{standing.get('points')} pts, {standing.get('won')}V/{standing.get('lost')}D "
                        f"({standing.get('league', '')})"
                    )

        # Matchs a venir avec DATE
        match_upcoming = [i for i in sport_items if i.get("type") == "match_upcoming"]
        if match_upcoming:
            prompt_parts.append("\nMatchs a venir:")
            for match in match_upcoming:
                match_date = match.get('date', '')[:10] if match.get('date') else 'date inconnue'
                prompt_parts.append(
                    f"  - [{match_date}] {match.get('home_team')} vs {match.get('away_team')} "
                    f"({match.get('competition', '')})"
                )

        # Resultats courses (F1, biathlon) RECENTS (moins de 7 jours) avec DATE
        race_results = [i for i in sport_items if i.get("type") == "race_result" and is_recent_match(i)]
        if race_results:
            prompt_parts.append("\nResultats courses:")
            for result in race_results:
                race_date = result.get('date', '')[:10] if result.get('date') else ''
                if result.get("athlete"):  # Biathlon
                    prompt_parts.append(
                        f"  - [{race_date}] {result.get('athlete')} ({result.get('nation')}): "
                        f"{result.get('rank')}e - {result.get('race')}"
                    )
                else:  # F1
                    prompt_parts.append(
                        f"  - [{race_date}] P{result.get('position')}: #{result.get('driver_number')} "
                        f"({result.get('meeting')})"
                    )

    prompt_parts.append("\n=== FIN DES DONNEES ===")
    prompt_parts.append("\nGenere maintenant le script audio du briefing sportif.")

    return "\n".join(prompt_parts)


def call_openai(system_prompt: str, user_prompt: str, config: dict) -> str:
    """Appelle l'API OpenAI"""
    try:
        from openai import OpenAI

        client = OpenAI()  # Utilise OPENAI_API_KEY

        response = client.chat.completions.create(
            model=config.get("model", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=config.get("max_tokens", 1500),
            temperature=0.7,
        )

        return response.choices[0].message.content

    except ImportError:
        print("[ERROR] Package openai non installe. Installez-le avec: pip install openai")
        return ""
    except Exception as e:
        print(f"[ERROR] Erreur OpenAI: {e}")
        return ""


def call_anthropic(system_prompt: str, user_prompt: str, config: dict) -> str:
    """Appelle l'API Anthropic"""
    try:
        import anthropic

        client = anthropic.Anthropic()  # Utilise ANTHROPIC_API_KEY

        response = client.messages.create(
            model=config.get("model", "claude-3-haiku-20240307"),
            max_tokens=config.get("max_tokens", 1500),
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )

        return response.content[0].text

    except ImportError:
        print("[ERROR] Package anthropic non installe. Installez-le avec: pip install anthropic")
        return ""
    except Exception as e:
        print(f"[ERROR] Erreur Anthropic: {e}")
        return ""


def call_ollama(system_prompt: str, user_prompt: str, config: dict) -> str:
    """Appelle Ollama (LLM local gratuit)"""
    try:
        import requests

        model = config.get("model", "llama3.2")
        base_url = config.get("ollama_url", "http://localhost:11434")

        response = requests.post(
            f"{base_url}/api/generate",
            json={
                "model": model,
                "prompt": f"{system_prompt}\n\n{user_prompt}",
                "stream": False,
            },
            timeout=120
        )

        if response.status_code == 200:
            return response.json().get("response", "")
        else:
            print(f"[ERROR] Ollama erreur {response.status_code}: {response.text[:200]}")
            return ""

    except requests.exceptions.ConnectionError:
        print("[ERROR] Ollama non accessible. Lancez: ollama serve")
        print("        Puis: ollama pull llama3.2")
        return ""
    except Exception as e:
        print(f"[ERROR] Erreur Ollama: {e}")
        return ""


def call_groq(system_prompt: str, user_prompt: str, config: dict) -> str:
    """Appelle Groq (gratuit avec limites)"""
    try:
        from groq import Groq

        client = Groq()  # Utilise GROQ_API_KEY

        response = client.chat.completions.create(
            model=config.get("model", "llama-3.3-70b-versatile"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=config.get("max_tokens", 1500),
            temperature=0.7,
        )

        return response.choices[0].message.content

    except ImportError:
        print("[ERROR] Package groq non installe. Installez-le avec: pip install groq")
        return ""
    except Exception as e:
        print(f"[ERROR] Erreur Groq: {e}")
        return ""


def call_gemini(system_prompt: str, user_prompt: str, config: dict) -> str:
    """Appelle Google Gemini (gratuit)"""
    try:
        import google.generativeai as genai

        # Configurer avec la cle API
        api_key = config.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("[ERROR] Cle API Gemini non configuree")
            print("        Ajoutez 'gemini_api_key' dans api_keys de user_preferences.json")
            print("        Ou definissez GEMINI_API_KEY dans l'environnement")
            return ""

        genai.configure(api_key=api_key)

        model = genai.GenerativeModel(
            model_name=config.get("model", "gemini-2.0-flash"),
            system_instruction=system_prompt
        )

        response = model.generate_content(user_prompt)

        return response.text

    except ImportError:
        print("[ERROR] Package google-generativeai non installe")
        print("        Installez-le avec: pip install google-generativeai")
        return ""
    except Exception as e:
        print(f"[ERROR] Erreur Gemini: {e}")
        return ""


def generate_briefing(provider: str = None, debug: bool = False) -> str:
    """
    Genere le briefing sportif

    Args:
        provider: "openai" ou "anthropic" (utilise config si None)
        debug: Si True, sauvegarde le prompt dans debug_prompt.txt

    Returns:
        Texte du briefing genere
    """
    print("=" * 50)
    print("SPORTBRIEF - GENERATION DU BRIEFING")
    print("=" * 50)

    # Charger les donnees
    print("\n[INFO] Chargement des donnees...")
    data = load_aggregated_data()
    if not data:
        return ""

    prefs = load_preferences()
    config = get_llm_config(prefs)

    # Provider
    if provider:
        config["provider"] = provider

    print(f"[INFO] Provider: {config['provider']}")
    print(f"[INFO] Model: {config.get('model', 'default')}")
    print(f"[INFO] Items a traiter: {data.get('total_items', 0)}")

    # Construire les prompts
    print("\n[INFO] Construction du prompt...")
    system_prompt = build_system_prompt(prefs)
    user_prompt = build_user_prompt(data, prefs)

    # Debug: sauvegarder le prompt si demande
    if debug:
        prompt_file = OUTPUT_DIR / "debug_prompt.txt"
        with open(prompt_file, "w", encoding="utf-8") as f:
            f.write("=== SYSTEM PROMPT ===\n")
            f.write(system_prompt)
            f.write("\n\n=== USER PROMPT ===\n")
            f.write(user_prompt)
        print(f"[DEBUG] Prompt sauvegarde dans {prompt_file}")

    # Appeler le LLM
    print(f"\n[INFO] Appel {config['provider'].upper()}...")

    if config["provider"] == "openai":
        briefing = call_openai(system_prompt, user_prompt, config)
    elif config["provider"] == "anthropic":
        briefing = call_anthropic(system_prompt, user_prompt, config)
    elif config["provider"] == "ollama":
        briefing = call_ollama(system_prompt, user_prompt, config)
    elif config["provider"] == "groq":
        briefing = call_groq(system_prompt, user_prompt, config)
    elif config["provider"] == "gemini":
        briefing = call_gemini(system_prompt, user_prompt, config)
    else:
        print(f"[ERROR] Provider inconnu: {config['provider']}")
        return ""

    if not briefing:
        print("[ERROR] Aucun briefing genere")
        return ""

    # Nettoyer le markdown pour l'audio
    briefing_raw = briefing
    briefing = clean_markdown_for_audio(briefing)
    if briefing != briefing_raw:
        print("[INFO] Markdown nettoye pour format audio")

    # Sauvegarder le briefing (uniquement latest, pas de fichiers horodates)
    output_file = OUTPUT_DIR / "briefing_latest.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(briefing)

    # Stats
    word_count = len(briefing.split())
    estimated_duration = word_count / 150  # ~150 mots/minute

    print(f"\n{'=' * 50}")
    print("BRIEFING GENERE")
    print("=" * 50)
    print(f"Mots: {word_count}")
    print(f"Duree estimee: {estimated_duration:.1f} minutes")
    print(f"\n[OK] Sauvegarde dans {output_file}")

    return briefing


def main():
    """Fonction principale"""
    import argparse

    parser = argparse.ArgumentParser(description="SportBrief - Generation du briefing")
    parser.add_argument("provider", nargs="?", help="Provider LLM (openai, anthropic, gemini, ollama, groq)")
    parser.add_argument("-d", "--debug", action="store_true", help="Sauvegarder le prompt dans debug_prompt.txt")
    args = parser.parse_args()

    briefing = generate_briefing(provider=args.provider, debug=args.debug)

    if briefing:
        print("\n" + "-" * 50)
        print("APERCU DU BRIEFING:")
        print("-" * 50)
        print(briefing[:500] + "..." if len(briefing) > 500 else briefing)


if __name__ == "__main__":
    main()
