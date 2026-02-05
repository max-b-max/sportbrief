import json
import sys
from datetime import datetime
from pathlib import Path

import requests

# Ajouter le répertoire parent au path pour importer config
sys.path.append(str(Path(__file__).parent.parent))
from config import get_sport_config, get_api_key, get_api_url, get_best_season


# Configuration
OUTPUT_DIR = Path("data/raw/api/formula1")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CONFIG = get_sport_config("formula1")
API_KEY = get_api_key("formula1")
BASE_URL = get_api_url("formula1")

MAX_RACES = CONFIG.get("max_races", 3)
# Utiliser la meilleure saison disponible (avec fallback si API trial en retard)
CURRENT_SEASON = get_best_season("formula1")


# Helpers

def make_api_request(endpoint: str, params: dict | None = None) -> dict:
    """
    Effectue une requête à l'API Formula 1

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

def collect_recent_races(season: int, max_races: int = 3) -> list[dict]:
    """
    Collecte les dernières courses de la saison

    Args:
        season: Année de la saison
        max_races: Nombre maximum de courses à récupérer

    Returns:
        Liste des courses
    """
    data = []

    try:
        # Récupérer toutes les courses de la saison
        response = make_api_request("/races", {"season": season})

        races = response.get("response", [])
        # Prendre les dernières courses (triées par date)
        recent_races = races[-max_races:] if len(races) > max_races else races

        for race in recent_races:
            data.append({
                "sport": "formula1",
                "source": "api-formula1",
                "race_id": race.get("id"),
                "competition": race.get("competition", {}).get("name"),
                "circuit": race.get("circuit", {}).get("name"),
                "location": race.get("competition", {}).get("location", {}).get("city"),
                "date": race.get("date"),
                "status": race.get("status"),
            })

    except Exception as e:
        print(f"[WARNING] Erreur sur les courses: {e}")

    return data


def collect_drivers_standings(season: int) -> list[dict]:
    """
    Collecte le classement des pilotes

    Args:
        season: Année de la saison

    Returns:
        Liste des positions au classement
    """
    data = []

    try:
        response = make_api_request("/rankings/drivers", {"season": season})

        for standing in response.get("response", []):
            data.append({
                "sport": "formula1",
                "source": "api-formula1",
                "season": season,
                "position": standing.get("position"),
                "driver": standing.get("driver", {}).get("name"),
                "team": standing.get("team", {}).get("name"),
                "points": standing.get("points"),
                "wins": standing.get("wins"),
                "podiums": standing.get("podiums"),
            })

    except Exception as e:
        print(f"[WARNING] Erreur sur le classement pilotes: {e}")

    return data


def collect_teams_standings(season: int) -> list[dict]:
    """
    Collecte le classement des équipes

    Args:
        season: Année de la saison

    Returns:
        Liste des positions au classement
    """
    data = []

    try:
        response = make_api_request("/rankings/teams", {"season": season})

        for standing in response.get("response", []):
            data.append({
                "sport": "formula1",
                "source": "api-formula1",
                "season": season,
                "position": standing.get("position"),
                "team": standing.get("team", {}).get("name"),
                "points": standing.get("points"),
            })

    except Exception as e:
        print(f"[WARNING] Erreur sur le classement equipes: {e}")

    return data


# Main

def main():
    all_data = {
        "races": [],
        "drivers_standings": [],
        "teams_standings": []
    }

    # Collecter les dernières courses
    print("[INFO] Collecte des dernieres courses...")
    races = collect_recent_races(CURRENT_SEASON, MAX_RACES)
    all_data["races"].extend(races)
    print(f"[OK] {len(races)} courses collectees")

    # Collecter le classement des pilotes
    print("[INFO] Collecte du classement pilotes...")
    drivers = collect_drivers_standings(CURRENT_SEASON)
    all_data["drivers_standings"].extend(drivers)
    print(f"[OK] {len(drivers)} pilotes au classement")

    # Collecter le classement des équipes
    print("[INFO] Collecte du classement equipes...")
    teams = collect_teams_standings(CURRENT_SEASON)
    all_data["teams_standings"].extend(teams)
    print(f"[OK] {len(teams)} equipes au classement")

    # Sauvegarder
    payload = {
        "source": "api-formula1",
        "sport": "formula1",
        "season": CURRENT_SEASON,
        "fetched_at": datetime.utcnow().isoformat(),
        "total_races": len(all_data["races"]),
        "total_drivers": len(all_data["drivers_standings"]),
        "total_teams": len(all_data["teams_standings"]),
        "data": all_data
    }

    output_file = OUTPUT_DIR / "formula1_data.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"[OK] Formula 1 : {payload['total_races']} courses + {payload['total_drivers']} pilotes + {payload['total_teams']} equipes collectes")


if __name__ == "__main__":
    main()
