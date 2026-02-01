import json
import sys
from datetime import datetime
from pathlib import Path

import requests

# Ajouter le répertoire parent au path pour importer config
sys.path.append(str(Path(__file__).parent.parent))
from config import get_sport_config, get_api_key, get_api_url, get_best_season, get_current_season_from_api
from config.league_ids import FOOTBALL_LEAGUES


# Configuration
OUTPUT_DIR = Path("data/raw/api/football")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CONFIG = get_sport_config("football")
API_KEY = get_api_key("football")
BASE_URL = get_api_url("football")

TEAMS = CONFIG.get("teams", [])
LEAGUES = CONFIG.get("leagues", [])
MAX_GAMES_PER_TEAM = CONFIG.get("max_games_per_team", 5)
MAX_GAMES_PER_LEAGUE = CONFIG.get("max_games_per_league", 10)

# Récupérer les saisons en cours pour toutes les ligues
print("[INFO] Detection des saisons en cours pour les ligues...")
LEAGUE_SEASONS = {}
for league in LEAGUES:
    league_id = league.get("id")
    league_name = league.get("name")

    if not league_id:
        # Essayer de trouver l'ID depuis le mapping
        league_id = FOOTBALL_LEAGUES.get(league_name)

    if league_id:
        season = get_current_season_from_api("football", league_id, league_name, BASE_URL, API_KEY)
        if season:
            LEAGUE_SEASONS[league_id] = season
        else:
            # Fallback
            LEAGUE_SEASONS[league_id] = get_best_season("football")
            print(f"[WARNING] {league_name}: utilisation du fallback")

# Saison par défaut si aucune ligue configurée
DEFAULT_SEASON = get_best_season("football")


# Helpers

def make_api_request(endpoint: str, params: dict | None = None) -> dict:
    """
    Effectue une requête à l'API Football

    Args:
        endpoint: Endpoint de l'API (ex: "/games", "/standings")
        params: Paramètres de la requête

    Returns:
        Réponse JSON de l'API
    """
    url = f"{BASE_URL}{endpoint}"
    headers = {
        "x-apisports-key": API_KEY
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Erreur API sur {endpoint}: {e}")
        return {"response": []}


# Collecte

def collect_team_games(team_id: int, team_name: str, max_games: int = 5) -> list[dict]:
    """
    Collecte les derniers matchs d'une équipe

    Args:
        team_id: ID de l'équipe
        team_name: Nom de l'équipe
        max_games: Nombre maximum de matchs à récupérer

    Returns:
        Liste des matchs
    """
    data = []

    try:
        # Récupérer les derniers matchs (last parameter)
        response = make_api_request("/games", {"team": team_id, "last": max_games})

        for game in response.get("response", []):
            data.append({
                "sport": "football",
                "source": "api-football",
                "team_tracked": team_name,
                "game_id": game.get("game", {}).get("id"),
                "date": game.get("game", {}).get("date"),
                "status": game.get("game", {}).get("status", {}).get("long"),
                "league": game.get("league", {}).get("name"),
                "home_team": game.get("teams", {}).get("home", {}).get("name"),
                "away_team": game.get("teams", {}).get("away", {}).get("name"),
                "home_score": game.get("goals", {}).get("home"),
                "away_score": game.get("goals", {}).get("away"),
            })

    except Exception as e:
        print(f"[WARNING] Erreur sur les matchs de {team_name}: {e}")

    return data


def collect_league_standings(league_id: int, league_name: str, season: int = 2024) -> list[dict]:
    """
    Collecte le classement d'une ligue

    Args:
        league_id: ID de la ligue
        league_name: Nom de la ligue
        season: Saison (année)

    Returns:
        Liste des positions au classement
    """
    data = []

    try:
        response = make_api_request("/standings", {"league": league_id, "season": season})

        for league_data in response.get("response", []):
            for standing in league_data.get("league", {}).get("standings", [[]])[0]:
                data.append({
                    "sport": "football",
                    "source": "api-football",
                    "league": league_name,
                    "season": season,
                    "rank": standing.get("rank"),
                    "team": standing.get("team", {}).get("name"),
                    "points": standing.get("points"),
                    "played": standing.get("all", {}).get("played"),
                    "win": standing.get("all", {}).get("win"),
                    "draw": standing.get("all", {}).get("draw"),
                    "lose": standing.get("all", {}).get("lose"),
                    "goals_for": standing.get("all", {}).get("goals", {}).get("for"),
                    "goals_against": standing.get("all", {}).get("goals", {}).get("against"),
                })

    except Exception as e:
        print(f"[WARNING] Erreur sur le classement de {league_name}: {e}")

    return data


def collect_league_recent_games(league_id: int, league_name: str, season: int, max_games: int = 10) -> list[dict]:
    """
    Collecte les matchs récents d'une ligue

    Args:
        league_id: ID de la ligue
        league_name: Nom de la ligue
        season: Saison (année)
        max_games: Nombre de matchs récents à récupérer

    Returns:
        Liste des matchs
    """
    data = []

    try:
        # Pour football, on collecte les derniers matchs terminés
        response = make_api_request("/fixtures", {
            "league": league_id,
            "season": season,
            "status": "FT"  # Match terminé (Full Time)
        })

        games = response.get("response", [])
        # Prendre les derniers matchs
        recent_games = games[-max_games:] if len(games) > max_games else games

        for game in recent_games:
            fixture = game.get("fixture", {})
            teams = game.get("teams", {})
            goals = game.get("goals", {})

            data.append({
                "sport": "football",
                "league": league_name,
                "game_id": fixture.get("id"),
                "date": fixture.get("date"),
                "status": fixture.get("status", {}).get("long"),
                "home_team": teams.get("home", {}).get("name"),
                "away_team": teams.get("away", {}).get("name"),
                "home_score": goals.get("home"),
                "away_score": goals.get("away"),
            })

    except Exception as e:
        print(f"[WARNING] Erreur sur les matchs récents de {league_name}: {e}")

    return data


# Main

def main():
    all_data = {
        "teams_games": [],
        "league_games": [],
        "standings": []
    }

    # Collecter les matchs des équipes favorites
    print("[INFO] Collecte des matchs des equipes...")
    for team in TEAMS:
        team_id = team.get("id")
        team_name = team.get("name")

        if not team_id:
            print(f"[WARNING] Pas d'ID pour {team_name}, skip")
            continue

        games = collect_team_games(team_id, team_name, MAX_GAMES_PER_TEAM)
        all_data["teams_games"].extend(games)
        print(f"[OK] {team_name}: {len(games)} matchs collectes")

    # Collecter les matchs récents des ligues
    print("[INFO] Collecte des resultats recents des competitions...")
    for league in LEAGUES:
        league_id = league.get("id")
        league_name = league.get("name")

        if not league_id:
            continue

        # Utiliser la saison en cours pour cette ligue
        season = LEAGUE_SEASONS.get(league_id, DEFAULT_SEASON)

        league_games = collect_league_recent_games(league_id, league_name, season, MAX_GAMES_PER_LEAGUE)
        all_data["league_games"].extend(league_games)
        if len(league_games) > 0:
            print(f"[OK] {league_name}: {len(league_games)} resultats collectes")

    # Collecter les classements des ligues
    print("[INFO] Collecte des classements...")
    for league in LEAGUES:
        league_id = league.get("id")
        league_name = league.get("name")

        if not league_id:
            print(f"[WARNING] Pas d'ID pour {league_name}, skip")
            continue

        # Utiliser la saison en cours pour cette ligue
        season = LEAGUE_SEASONS.get(league_id, DEFAULT_SEASON)

        standings = collect_league_standings(league_id, league_name, season)
        all_data["standings"].extend(standings)
        print(f"[OK] {league_name}: {len(standings)} positions collectees")

    # Sauvegarder
    total_games = len(all_data["teams_games"]) + len(all_data["league_games"])

    payload = {
        "source": "api-football",
        "sport": "football",
        "seasons": LEAGUE_SEASONS,  # Saisons par ligue (détectées automatiquement via API)
        "fetched_at": datetime.utcnow().isoformat(),
        "teams_tracked": [t.get("name") for t in TEAMS],
        "leagues_tracked": [l.get("name") for l in LEAGUES],
        "total_teams_games": len(all_data["teams_games"]),
        "total_league_games": len(all_data["league_games"]),
        "total_games": total_games,
        "total_standings": len(all_data["standings"]),
        "data": all_data
    }

    output_file = OUTPUT_DIR / "football_data.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"[OK] Football : {payload['total_games']} matchs ({payload['total_teams_games']} equipes + {payload['total_league_games']} ligues) + {payload['total_standings']} classements collectes")


if __name__ == "__main__":
    main()
