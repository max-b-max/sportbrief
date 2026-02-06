import json
import sys
from datetime import datetime
from pathlib import Path
import requests

sys.path.append(str(Path(__file__).parent.parent))
from config import get_sport_config, get_api_key, get_api_url, get_best_season, get_current_season_from_api
from config.league_ids import RUGBY_LEAGUES

OUTPUT_DIR = Path("data/raw/api/rugby")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CONFIG = get_sport_config("rugby")
API_KEY = get_api_key("rugby")
BASE_URL = get_api_url("rugby")

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
        league_id = RUGBY_LEAGUES.get(league_name)

    if league_id:
        season = get_current_season_from_api("rugby", league_id, league_name, BASE_URL, API_KEY)
        if season:
            LEAGUE_SEASONS[league_id] = season
        else:
            LEAGUE_SEASONS[league_id] = get_best_season("rugby")
            print(f"[WARNING] {league_name}: utilisation du fallback")

DEFAULT_SEASON = get_best_season("rugby")


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

def collect_league_standings(league_id: int, league_name: str, season: int | str) -> list[dict]:
    """
    Collecte le classement d'une ligue

    Args:
        league_id: ID de la ligue
        league_name: Nom de la ligue
        season: Saison à collecter

    Returns:
        Liste des positions au classement
    """
    data = []

    try:
        response = make_api_request("/standings", {"league": league_id, "season": season})

        standings_list = response.get("response", [[]])
        # Les standings sont dans une liste imbriquée
        if standings_list and isinstance(standings_list[0], list):
            standings = standings_list[0]
        else:
            standings = standings_list

        for standing in standings:
            if not isinstance(standing, dict):
                continue

            team = standing.get('team', {})
            if not isinstance(team, dict):
                continue

            games = standing.get('games', {})
            points_data = standing.get('points', {})

            # S'assurer que games et points_data sont des dictionnaires
            if not isinstance(games, dict):
                games = {}
            if not isinstance(points_data, dict):
                points_data = {}

            data.append({
                "sport": "rugby",
                "league": league_name,
                "season": season,
                "position": standing.get("position"),
                "team": team.get("name"),
                "team_id": team.get("id"),
                "games_played": games.get("played"),
                "wins": games.get("win"),
                "draws": games.get("draw"),
                "losses": games.get("lose"),
                "points_for": points_data.get("for"),
                "points_against": points_data.get("against"),
                "points": points_data.get("total"),
            })

    except Exception as e:
        print(f"[WARNING] Erreur sur le classement de {league_name}: {e}")

    return data


def collect_team_games(team_id: int, team_name: str, season: int | str, max_games: int = 5) -> list[dict]:
    """
    Collecte les derniers matchs d'une équipe

    Args:
        team_id: ID de l'équipe
        team_name: Nom de l'équipe
        season: Saison à collecter
        max_games: Nombre de matchs à récupérer

    Returns:
        Liste des matchs
    """
    data = []

    try:
        response = make_api_request("/games", {
            "team": team_id,
            "season": season
        })

        games = response.get("response", [])
        # Prendre les derniers matchs
        recent_games = games[-max_games:] if len(games) > max_games else games

        for game in recent_games:
            teams = game.get("teams", {})
            scores = game.get("scores", {})
            home_team = teams.get("home", {})
            away_team = teams.get("away", {})

            data.append({
                "sport": "rugby",
                "team_tracked": team_name,
                "game_id": game.get("id"),
                "date": game.get("date"),
                "status": game.get("status"),
                "league": game.get("league", {}).get("name"),
                "home_team": home_team.get("name"),
                "away_team": away_team.get("name"),
                "home_score": scores.get("home"),
                "away_score": scores.get("away"),
            })

    except Exception as e:
        print(f"[WARNING] Erreur sur les matchs de {team_name}: {e}")

    return data


def collect_league_recent_games(league_id: int, league_name: str, season: int | str, max_games: int = 10) -> list[dict]:
    """
    Collecte les matchs récents d'une ligue

    Args:
        league_id: ID de la ligue
        league_name: Nom de la ligue
        season: Saison à collecter
        max_games: Nombre de matchs récents à récupérer

    Returns:
        Liste des matchs
    """
    data = []

    try:
        response = make_api_request("/games", {
            "league": league_id,
            "season": season
        })

        games = response.get("response", [])
        # Prendre les derniers matchs
        recent_games = games[-max_games:] if len(games) > max_games else games

        for game in recent_games:
            teams = game.get("teams", {})
            scores = game.get("scores", {})
            home_team = teams.get("home", {})
            away_team = teams.get("away", {})

            data.append({
                "sport": "rugby",
                "league": league_name,
                "game_id": game.get("id"),
                "date": game.get("date"),
                "status": game.get("status"),
                "week": game.get("week"),
                "home_team": home_team.get("name"),
                "away_team": away_team.get("name"),
                "home_score": scores.get("home"),
                "away_score": scores.get("away"),
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

    # Collecter les matchs des équipes suivies
    print("[INFO] Collecte des matchs des equipes...")
    for team in TEAMS:
        team_id = team.get("id")
        team_name = team.get("name")

        if not team_id:
            print(f"[WARNING] ID manquant pour {team_name}, skip")
            continue

        # Utiliser DEFAULT_SEASON pour les équipes (ou récupérer depuis la config si disponible)
        team_season = DEFAULT_SEASON
        games = collect_team_games(team_id, team_name, team_season, MAX_GAMES_PER_TEAM)
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
        "source": "api-rugby",
        "sport": "rugby",
        "seasons": LEAGUE_SEASONS,
        "fetched_at": datetime.utcnow().isoformat(),
        "teams_tracked": [t.get("name") for t in TEAMS],
        "leagues_tracked": [l.get("name") for l in LEAGUES],
        "total_teams_games": len(all_data["teams_games"]),
        "total_league_games": len(all_data["league_games"]),
        "total_games": total_games,
        "total_standings": len(all_data["standings"]),
        "data": all_data
    }

    output_file = OUTPUT_DIR / "rugby_data.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"[OK] Rugby : {payload['total_games']} matchs ({payload['total_teams_games']} equipes + {payload['total_league_games']} ligues) + {payload['total_standings']} classements collectes")


if __name__ == "__main__":
    main()
