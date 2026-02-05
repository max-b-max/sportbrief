import json
import sys
from datetime import datetime
from pathlib import Path
import requests

sys.path.append(str(Path(__file__).parent.parent))
from config import get_sport_config, get_api_key, get_api_url, get_best_season, get_current_season_from_api

OUTPUT_DIR = Path("data/raw/api/nba")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CONFIG = get_sport_config("basketball")
API_KEY = get_api_key("basketball")
BASE_URL = get_api_url("basketball")

FRENCH_PLAYERS = CONFIG.get("french_players", [])
LEAGUES = CONFIG.get("leagues", [])

# Récupérer la saison en cours depuis l'API (current=true basé sur les dates)
NBA_LEAGUE_ID = 12
SEASON = get_current_season_from_api("basketball", NBA_LEAGUE_ID, "NBA", BASE_URL, API_KEY)

# Fallback si l'API ne retourne pas de saison
if not SEASON:
    print("[WARNING] Impossible de trouver la saison en cours via l'API, utilisation du fallback")
    SEASON = get_best_season("basketball")

print(f"[INFO] Utilisation de la saison: {SEASON}")

MAX_GAMES_PER_PLAYER = CONFIG.get("max_games_per_player", 5)


# Helpers

def make_api_request(endpoint: str, params: dict | None = None) -> dict:
    """Effectue une requête API"""
    headers = {"x-apisports-key": API_KEY}

    try:
        response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    except Exception as e:
        print(f"[WARNING] Erreur API {endpoint}: {e}")
        return {"response": [], "results": 0}


# Collection functions

def collect_nba_standings() -> list[dict]:
    """
    Collecte le classement NBA complet

    Returns:
        Liste des positions au classement
    """
    data = []

    try:
        response = make_api_request("/standings", {"league": 12, "season": SEASON})

        for standing_group in response.get("response", []):
            for standing in standing_group:
                if isinstance(standing, dict):
                    data.append({
                        "sport": "basketball",
                        "league": "NBA",
                        "rank": standing.get("position"),
                        "team": standing.get("team", {}).get("name"),
                        "team_id": standing.get("team", {}).get("id"),
                        "conference": standing.get("group", {}).get("name"),  # Eastern/Western
                        "games_played": standing.get("games", {}).get("played"),
                        "wins": standing.get("games", {}).get("win", {}).get("total"),
                        "losses": standing.get("games", {}).get("lose", {}).get("total"),
                        "win_percentage": standing.get("games", {}).get("win", {}).get("percentage"),
                        "points_for": standing.get("points", {}).get("for"),
                        "points_against": standing.get("points", {}).get("against"),
                    })

    except Exception as e:
        print(f"[WARNING] Erreur sur le classement NBA: {e}")

    return data


def collect_player_games(player_id: int, player_name: str, team_id: int, max_games: int = 5) -> list[dict]:
    """
    Collecte les derniers matchs d'un joueur

    Args:
        player_id: ID du joueur
        player_name: Nom du joueur
        team_id: ID de l'équipe du joueur
        max_games: Nombre de matchs à récupérer

    Returns:
        Liste des matchs
    """
    data = []

    try:
        # Récupérer les matchs de l'équipe du joueur
        response = make_api_request("/games", {
            "team": team_id,
            "season": SEASON,
            "league": 12
        })

        games = response.get("response", [])
        # Prendre les derniers matchs
        recent_games = games[-max_games:] if len(games) > max_games else games

        for game in recent_games:
            teams = game.get("teams", {})
            scores = game.get("scores", {})
            home_team = teams.get("home", {})
            away_team = teams.get("away", {})

            # Déterminer si le joueur était à domicile ou à l'extérieur
            is_home = home_team.get("id") == team_id

            # Calculer le résultat
            home_score = scores.get("home", {}).get("total", 0)
            away_score = scores.get("away", {}).get("total", 0)

            if is_home:
                result = "W" if home_score > away_score else "L" if home_score < away_score else "D"
            else:
                result = "W" if away_score > home_score else "L" if away_score < home_score else "D"

            data.append({
                "sport": "basketball",
                "player_tracked": player_name,
                "player_id": player_id,
                "game_id": game.get("id"),
                "date": game.get("date"),
                "status": game.get("status", {}).get("long"),
                "home_team": home_team.get("name"),
                "away_team": away_team.get("name"),
                "home_score": home_score,
                "away_score": away_score,
                "player_team": home_team.get("name") if is_home else away_team.get("name"),
                "opponent": away_team.get("name") if is_home else home_team.get("name"),
                "result": result,
            })

    except Exception as e:
        print(f"[WARNING] Erreur sur les matchs de {player_name}: {e}")

    return data


# Main

def main():
    all_data = {
        "standings": [],
        "french_players_games": []
    }

    # Collecter le classement NBA
    print("[INFO] Collecte du classement NBA...")
    standings = collect_nba_standings()
    all_data["standings"].extend(standings)
    print(f"[OK] NBA: {len(standings)} positions collectees")

    # Collecter les matchs des joueurs français
    if FRENCH_PLAYERS:
        print(f"[INFO] Collecte des matchs de {len(FRENCH_PLAYERS)} joueurs francais...")
        total_games = 0

        for player in FRENCH_PLAYERS:
            player_id = player.get("id")
            player_name = player.get("name")
            team_id = player.get("team_id")

            if not player_id or not team_id:
                continue

            games = collect_player_games(player_id, player_name, team_id, MAX_GAMES_PER_PLAYER)
            all_data["french_players_games"].extend(games)
            total_games += len(games)

            if len(games) > 0:
                print(f"[OK] {player_name}: {len(games)} matchs collectes")

        print(f"[OK] Total: {total_games} matchs de joueurs francais collectes")

    # Sauvegarder
    payload = {
        "source": "api-basketball",
        "sport": "basketball",
        "league": "NBA",
        "season": SEASON,
        "fetched_at": datetime.utcnow().isoformat(),
        "french_players_tracked": [p.get("name") for p in FRENCH_PLAYERS],
        "total_standings": len(all_data["standings"]),
        "total_french_games": len(all_data["french_players_games"]),
        "data": all_data
    }

    output_file = OUTPUT_DIR / "nba_data.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"[OK] NBA : {payload['total_standings']} classements + {payload['total_french_games']} matchs de francais collectes")


if __name__ == "__main__":
    main()
