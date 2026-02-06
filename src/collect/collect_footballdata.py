"""
Collector Football utilisant Football-Data.org API (v4)
API gratuite avec accès aux principales ligues européennes + Ligue 1

Compétitions disponibles (FREE tier):
- FL1: Ligue 1 (France)
- PL: Premier League (England)
- BL1: Bundesliga (Germany)
- SA: Serie A (Italy)
- PD: La Liga (Spain)
- CL: Champions League
- EC: European Championship
- WC: World Cup
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()
from typing import Optional

import requests

# Rate limiting: 10 requests/minute = 1 request every 6 seconds minimum
REQUEST_DELAY = 7  # secondes entre chaque requête (marge de sécurité)

# Ajouter le répertoire parent au path pour importer config
sys.path.append(str(Path(__file__).parent.parent))

# Configuration
OUTPUT_DIR = Path("data/raw/api/football")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://api.football-data.org/v4"

# Mapping des compétitions Football-Data.org
# FREE tier: FL1, PL, BL1, SA, PD, CL, EC, WC, ELC (Championship), PPL, DED, BSA
COMPETITIONS = {
    "Ligue 1": "FL1",
    "Premier League": "PL",
    "Bundesliga": "BL1",
    "Serie A": "SA",
    "La Liga": "PD",
    "Champions League": "CL",
    "Europa League": "EL",  # Peut nécessiter tier payant
    "Conference League": None,  # Non disponible dans API
    "Euro": "EC",
    "European Championship": "EC",
    "Coupe du Monde": "WC",
    "World Cup": "WC",
    "Championship": "ELC",  # England Championship (bonus)
}

# Charger les préférences utilisateur
def load_preferences() -> dict:
    """Charge les préférences utilisateur depuis le fichier JSON"""
    prefs_file = Path("user_preferences.json")
    if prefs_file.exists():
        with open(prefs_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def get_api_key() -> str:
    """Récupère la clé API Football-Data.org depuis .env ou preferences"""
    # Priorité: variable d'environnement
    key = os.getenv("FOOTBALL_DATA_ORG_KEY", "")
    if key:
        return key
    # Fallback: preferences (deprecated)
    prefs = load_preferences()
    return prefs.get("api_keys", {}).get("football_data_org", "")


def get_configured_leagues() -> list[str]:
    """Récupère les ligues configurées dans les préférences"""
    prefs = load_preferences()
    football_prefs = prefs.get("sports", {}).get("football", {})
    return football_prefs.get("leagues", [])


def get_configured_teams() -> list[dict]:
    """Récupère les équipes favorites configurées"""
    prefs = load_preferences()
    football_prefs = prefs.get("sports", {}).get("football", {})
    return football_prefs.get("teams", [])


# API Helpers

_last_request_time = 0


def make_api_request(endpoint: str, params: Optional[dict] = None) -> dict:
    """
    Effectue une requête à l'API Football-Data.org avec rate limiting

    Args:
        endpoint: Endpoint de l'API (ex: "/competitions/FL1/standings")
        params: Paramètres de la requête

    Returns:
        Réponse JSON de l'API
    """
    global _last_request_time

    api_key = get_api_key()
    if not api_key:
        print("[ERROR] Cle API Football-Data.org non configuree")
        return {}

    # Rate limiting
    elapsed = time.time() - _last_request_time
    if elapsed < REQUEST_DELAY:
        wait_time = REQUEST_DELAY - elapsed
        print(f"      [WAIT] Attente {wait_time:.1f}s (rate limit)...")
        time.sleep(wait_time)

    url = f"{BASE_URL}{endpoint}"
    headers = {"X-Auth-Token": api_key}

    try:
        _last_request_time = time.time()
        response = requests.get(url, headers=headers, params=params, timeout=15)

        if response.status_code == 429:
            print("[WARNING] Rate limit atteint, attente 60s...")
            time.sleep(60)
            # Retry une fois
            response = requests.get(url, headers=headers, params=params, timeout=15)

        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Erreur API sur {endpoint}: {e}")
        return {}


# Collecteurs

def collect_standings(competition_code: str, competition_name: str) -> list[dict]:
    """
    Collecte le classement d'une compétition

    Args:
        competition_code: Code de la compétition (ex: "FL1")
        competition_name: Nom de la compétition (ex: "Ligue 1")

    Returns:
        Liste des positions au classement
    """
    data = []

    response = make_api_request(f"/competitions/{competition_code}/standings")

    if not response:
        return data

    season = response.get("season", {})
    season_display = f"{season.get('startDate', '')[:4]}/{season.get('endDate', '')[:4]}"

    for standing_group in response.get("standings", []):
        standing_type = standing_group.get("type", "TOTAL")

        # On ne prend que le classement total
        if standing_type != "TOTAL":
            continue

        for team_standing in standing_group.get("table", []):
            team_info = team_standing.get("team", {})

            data.append({
                "sport": "football",
                "source": "football-data.org",
                "type": "standing",
                "competition": competition_name,
                "competition_code": competition_code,
                "season": season_display,
                "position": team_standing.get("position"),
                "team_id": team_info.get("id"),
                "team": team_info.get("name"),
                "team_short": team_info.get("shortName"),
                "team_crest": team_info.get("crest"),
                "played": team_standing.get("playedGames"),
                "won": team_standing.get("won"),
                "draw": team_standing.get("draw"),
                "lost": team_standing.get("lost"),
                "goals_for": team_standing.get("goalsFor"),
                "goals_against": team_standing.get("goalsAgainst"),
                "goal_difference": team_standing.get("goalDifference"),
                "points": team_standing.get("points"),
                "form": team_standing.get("form"),
            })

    return data


def collect_recent_matches(competition_code: str, competition_name: str, limit: int = 10) -> list[dict]:
    """
    Collecte les matchs récents terminés d'une compétition

    Args:
        competition_code: Code de la compétition
        competition_name: Nom de la compétition
        limit: Nombre de matchs à récupérer

    Returns:
        Liste des matchs terminés
    """
    data = []

    # Récupérer les matchs terminés
    response = make_api_request(
        f"/competitions/{competition_code}/matches",
        params={"status": "FINISHED", "limit": limit}
    )

    if not response:
        return data

    for match in response.get("matches", []):
        home_team = match.get("homeTeam", {})
        away_team = match.get("awayTeam", {})
        score = match.get("score", {})
        full_time = score.get("fullTime", {})

        data.append({
            "sport": "football",
            "source": "football-data.org",
            "type": "match_result",
            "competition": competition_name,
            "competition_code": competition_code,
            "match_id": match.get("id"),
            "matchday": match.get("matchday"),
            "date": match.get("utcDate"),
            "status": match.get("status"),
            "home_team_id": home_team.get("id"),
            "home_team": home_team.get("name"),
            "home_team_short": home_team.get("shortName"),
            "away_team_id": away_team.get("id"),
            "away_team": away_team.get("name"),
            "away_team_short": away_team.get("shortName"),
            "home_score": full_time.get("home"),
            "away_score": full_time.get("away"),
            "winner": score.get("winner"),
        })

    return data


def collect_upcoming_matches(competition_code: str, competition_name: str, limit: int = 10) -> list[dict]:
    """
    Collecte les prochains matchs programmés d'une compétition

    Args:
        competition_code: Code de la compétition
        competition_name: Nom de la compétition
        limit: Nombre de matchs à récupérer

    Returns:
        Liste des matchs à venir
    """
    data = []

    response = make_api_request(
        f"/competitions/{competition_code}/matches",
        params={"status": "SCHEDULED,TIMED", "limit": limit}
    )

    if not response:
        return data

    for match in response.get("matches", []):
        home_team = match.get("homeTeam", {})
        away_team = match.get("awayTeam", {})

        data.append({
            "sport": "football",
            "source": "football-data.org",
            "type": "match_scheduled",
            "competition": competition_name,
            "competition_code": competition_code,
            "match_id": match.get("id"),
            "matchday": match.get("matchday"),
            "date": match.get("utcDate"),
            "status": match.get("status"),
            "home_team_id": home_team.get("id"),
            "home_team": home_team.get("name"),
            "home_team_short": home_team.get("shortName"),
            "away_team_id": away_team.get("id"),
            "away_team": away_team.get("name"),
            "away_team_short": away_team.get("shortName"),
        })

    return data


def collect_team_matches(team_name: str, limit: int = 5) -> list[dict]:
    """
    Collecte les matchs récents d'une équipe spécifique

    Note: Football-Data.org permet de chercher par ID d'équipe
    Pour le MVP, on filtre les matchs des compétitions

    Args:
        team_name: Nom de l'équipe
        limit: Nombre de matchs

    Returns:
        Liste des matchs de l'équipe
    """
    # Pour le MVP, cette fonction sera appelée après avoir collecté
    # les matchs des compétitions, et on filtrera par équipe
    return []


# Main

def main():
    """Fonction principale de collecte"""

    print("=" * 50)
    print("FOOTBALL-DATA.ORG COLLECTOR")
    print("=" * 50)

    # Verifier la cle API
    api_key = get_api_key()
    if not api_key:
        print("[ERROR] Cle API non trouvee dans user_preferences.json")
        print("        Ajoute 'football_data_org' dans api_keys")
        return

    all_data = {
        "standings": [],
        "recent_matches": [],
        "upcoming_matches": [],
    }

    # Recuperer les ligues configurees
    configured_leagues = get_configured_leagues()
    print(f"\n[INFO] Ligues configurees: {configured_leagues}")

    # Collecter les données pour chaque ligue
    for league_name in configured_leagues:
        competition_code = COMPETITIONS.get(league_name)

        if competition_code is None:
            print(f"[SKIP] {league_name}: non disponible dans l'API gratuite")
            continue

        if not competition_code:
            print(f"[WARNING] {league_name}: pas de code competition trouve, skip")
            continue

        print(f"\n[INFO] Collecte {league_name} ({competition_code})...")

        # Classement
        standings = collect_standings(competition_code, league_name)
        all_data["standings"].extend(standings)
        if standings:
            print(f"  [OK] Classement: {len(standings)} equipes")

        # Matchs recents
        recent = collect_recent_matches(competition_code, league_name, limit=10)
        all_data["recent_matches"].extend(recent)
        if recent:
            print(f"  [OK] Matchs recents: {len(recent)}")

        # Prochains matchs
        upcoming = collect_upcoming_matches(competition_code, league_name, limit=10)
        all_data["upcoming_matches"].extend(upcoming)
        if upcoming:
            print(f"  [OK] Matchs a venir: {len(upcoming)}")

    # Résumé
    total_standings = len(all_data["standings"])
    total_recent = len(all_data["recent_matches"])
    total_upcoming = len(all_data["upcoming_matches"])

    print(f"\n{'=' * 50}")
    print(f"RESUME:")
    print(f"  - Classements: {total_standings} positions")
    print(f"  - Matchs termines: {total_recent}")
    print(f"  - Matchs a venir: {total_upcoming}")

    # Construire le payload final
    payload = {
        "source": "football-data.org",
        "sport": "football",
        "api_version": "v4",
        "fetched_at": datetime.utcnow().isoformat(),
        "leagues_collected": configured_leagues,
        "stats": {
            "total_standings": total_standings,
            "total_recent_matches": total_recent,
            "total_upcoming_matches": total_upcoming,
        },
        "data": all_data,
    }

    # Sauvegarder
    output_file = OUTPUT_DIR / "football_data.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Donnees sauvegardees dans {output_file}")


if __name__ == "__main__":
    main()
