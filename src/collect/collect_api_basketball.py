import json
import sys
from datetime import datetime
from pathlib import Path

import requests

# Ajouter le répertoire parent au path pour importer config
sys.path.append(str(Path(__file__).parent.parent))
from config import get_sport_config, get_api_key, get_api_url, get_best_season


# Configuration
OUTPUT_DIR = Path("data/raw/api/basketball")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CONFIG = get_sport_config("basketball")
API_KEY = get_api_key("basketball")
BASE_URL = get_api_url("basketball")

TEAMS = CONFIG.get("teams", [])
LEAGUES = CONFIG.get("leagues", [])
# Utiliser la meilleure saison disponible (avec fallback si API trial en retard)
SEASON = get_best_season("basketball")
MAX_GAMES_PER_TEAM = CONFIG.get("max_games_per_team", 10)


# Helpers

def make_api_request(endpoint: str, params: dict | None = None) -> dict:
    """
    Effectue une requête à l'API Basketball

    Args:
        endpoint: Endpoint de l'API
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

def collect_team_games(team_id: int, team_name: str, league_id: int, season: str, max_games: int = 10) -> list[dict]:
    """
    Collecte les matchs d'une équipe

    Args:
        team_id: ID de l'équipe
        team_name: Nom de l'équipe
        league_id: ID de la ligue
        season: Saison (ex: "2024-2025")
        max_games: Nombre maximum de matchs à récupérer

    Returns:
        Liste des matchs
    """
    data = []

    try:
        # Récupérer les matchs de l'équipe pour la saison
        response = make_api_request("/games", {"team": team_id, "season": season, "league": league_id})

        games = response.get("response", [])
        # Prendre les derniers matchs
        recent_games = games[-max_games:] if len(games) > max_games else games

        for game in recent_games:
            data.append({
                "sport": "basketball",
                "source": "api-basketball",
                "team_tracked": team_name,
                "game_id": game.get("id"),
                "date": game.get("date"),
                "status": game.get("status", {}).get("long"),
                "league": game.get("league", {}).get("name"),
                "home_team": game.get("teams", {}).get("home", {}).get("name"),
                "away_team": game.get("teams", {}).get("away", {}).get("name"),
                "home_score": game.get("scores", {}).get("home", {}).get("total"),
                "away_score": game.get("scores", {}).get("away", {}).get("total"),
            })

    except Exception as e:
        print(f"[WARNING] Erreur sur les matchs de {team_name}: {e}")

    return data


def collect_league_standings(league_id: int, league_name: str, season: str) -> list[dict]:
    """
    Collecte le classement d'une ligue

    Args:
        league_id: ID de la ligue
        league_name: Nom de la ligue
        season: Saison (ex: "2024-2025")

    Returns:
        Liste des positions au classement
    """
    data = []

    try:
        response = make_api_request("/standings", {"league": league_id, "season": season})

        for standing_group in response.get("response", []):
            for standing in standing_group:
                if isinstance(standing, dict):
                    data.append({
                        "sport": "basketball",
                        "source": "api-basketball",
                        "league": league_name,
                        "season": season,
                        "position": standing.get("position"),
                        "team": standing.get("team", {}).get("name"),
                        "conference": standing.get("group", {}).get("name"),
                        "games_played": standing.get("games", {}).get("played"),
                        "wins": standing.get("games", {}).get("win", {}).get("total"),
                        "losses": standing.get("games", {}).get("lose", {}).get("total"),
                        "win_percentage": standing.get("games", {}).get("win", {}).get("percentage"),
                    })

    except Exception as e:
        print(f"[WARNING] Erreur sur le classement de {league_name}: {e}")

    return data


# Main

def main():
    all_data = {
        "games": [],
        "standings": []
    }

    # Collecter les matchs des équipes favorites
    print("[INFO] Collecte des matchs des equipes...")
    for team in TEAMS:
        team_id = team.get("id")
        team_name = team.get("name")
        league_id = team.get("league_id")

        if not team_id or not league_id:
            print(f"[WARNING] ID manquant pour {team_name}, skip")
            continue

        games = collect_team_games(team_id, team_name, league_id, SEASON, MAX_GAMES_PER_TEAM)
        all_data["games"].extend(games)
        print(f"[OK] {team_name}: {len(games)} matchs collectes")

    # Collecter les classements des ligues
    print("[INFO] Collecte des classements...")
    for league in LEAGUES:
        league_id = league.get("id")
        league_name = league.get("name")

        if not league_id:
            print(f"[WARNING] Pas d'ID pour {league_name}, skip")
            continue

        standings = collect_league_standings(league_id, league_name, SEASON)
        all_data["standings"].extend(standings)
        print(f"[OK] {league_name}: {len(standings)} positions collectees")

    # Sauvegarder
    payload = {
        "source": "api-basketball",
        "sport": "basketball",
        "season": SEASON,
        "fetched_at": datetime.utcnow().isoformat(),
        "teams_tracked": [t.get("name") for t in TEAMS],
        "leagues_tracked": [l.get("name") for l in LEAGUES],
        "total_games": len(all_data["games"]),
        "total_standings": len(all_data["standings"]),
        "data": all_data
    }

    output_file = OUTPUT_DIR / "basketball_data.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"[OK] Basketball : {payload['total_games']} matchs + {payload['total_standings']} classements collectes")


if __name__ == "__main__":
    main()
