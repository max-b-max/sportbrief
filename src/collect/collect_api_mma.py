import json
import sys
from datetime import datetime
from pathlib import Path

import requests

# Ajouter le répertoire parent au path pour importer config
sys.path.append(str(Path(__file__).parent.parent))
from config import get_sport_config, get_api_key, get_api_url, get_best_season


# Configuration
OUTPUT_DIR = Path("data/raw/api/mma")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CONFIG = get_sport_config("mma")
API_KEY = get_api_key("mma")
BASE_URL = get_api_url("mma")

FIGHTERS = CONFIG.get("fighters", [])
ORGANIZATIONS = CONFIG.get("organizations", ["UFC"])
# Utiliser la meilleure saison disponible (avec fallback si API trial en retard, converti en string)
SEASON = str(get_best_season("mma"))
MAX_FIGHTS_PER_FIGHTER = CONFIG.get("max_fights_per_fighter", 5)
MAX_RECENT_FIGHTS = CONFIG.get("max_recent_fights", 20)


# Helpers

def make_api_request(endpoint: str, params: dict | None = None) -> dict:
    """
    Effectue une requête à l'API MMA

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

def collect_recent_ufc_fights(season: str = "2024", max_fights: int = 20) -> list[dict]:
    """
    Collecte les combats récents

    Args:
        season: Saison à récupérer (ex: "2024")
        max_fights: Nombre maximum de combats à récupérer

    Returns:
        Liste des combats
    """
    data = []

    try:
        # Récupérer les combats de la saison
        response = make_api_request("/fights", {"season": season})

        fights = response.get("response", [])
        # Prendre les derniers combats
        recent_fights = fights[-max_fights:] if len(fights) > max_fights else fights

        for fight in recent_fights:
            data.append({
                "sport": "mma",
                "source": "api-mma",
                "fight_id": fight.get("id"),
                "date": fight.get("date"),
                "status": fight.get("status"),
                "event": fight.get("event", {}).get("name"),
                "fighter1": fight.get("fighters", {}).get("fighter_1", {}).get("name"),
                "fighter2": fight.get("fighters", {}).get("fighter_2", {}).get("name"),
                "winner": fight.get("winner"),
                "method": fight.get("method"),
                "round": fight.get("round"),
                "time": fight.get("time"),
            })

    except Exception as e:
        print(f"[WARNING] Erreur sur les combats: {e}")

    return data


def search_fighter(fighter_name: str) -> dict | None:
    """
    Recherche un combattant par nom

    Args:
        fighter_name: Nom du combattant

    Returns:
        Informations du combattant ou None
    """
    try:
        response = make_api_request("/fighters", {"search": fighter_name})
        fighters = response.get("response", [])

        if fighters:
            return fighters[0]  # Premier résultat

    except Exception as e:
        print(f"[WARNING] Erreur recherche {fighter_name}: {e}")

    return None


def collect_fighter_fights(fighter_name: str, fighter_id: int | None = None, max_fights: int = 5) -> list[dict]:
    """
    Collecte les combats d'un combattant spécifique

    Args:
        fighter_name: Nom du combattant
        fighter_id: ID du combattant (optionnel, sinon recherche par nom)
        max_fights: Nombre maximum de combats à récupérer

    Returns:
        Liste des combats
    """
    data = []

    try:
        # Si pas d'ID fourni, chercher le combattant par nom
        if not fighter_id:
            fighter = search_fighter(fighter_name)

            if not fighter:
                print(f"[WARNING] Combattant {fighter_name} non trouve")
                return data

            fighter_id = fighter.get("id")

        # Récupérer les combats du combattant
        response = make_api_request("/fights", {"fighter": fighter_id, "season": SEASON})

        fights = response.get("response", [])
        # Prendre les derniers combats
        recent_fights = fights[-max_fights:] if len(fights) > max_fights else fights

        for fight in recent_fights:
            data.append({
                "sport": "mma",
                "source": "api-mma",
                "fighter_tracked": fighter_name,
                "fight_id": fight.get("id"),
                "date": fight.get("date"),
                "status": fight.get("status"),
                "event": fight.get("event", {}).get("name"),
                "opponent": fight.get("opponent", {}).get("name"),
                "result": fight.get("result"),
                "method": fight.get("method"),
            })

    except Exception as e:
        print(f"[WARNING] Erreur sur les combats de {fighter_name}: {e}")

    return data


# Main

def main():
    all_data = {
        "recent_fights": [],
        "fighters_fights": []
    }

    # Collecter les derniers combats de la saison
    print(f"[INFO] Collecte des combats recents (saison {SEASON})...")
    recent_fights = collect_recent_ufc_fights(SEASON, MAX_RECENT_FIGHTS)
    all_data["recent_fights"].extend(recent_fights)
    print(f"[OK] {len(recent_fights)} combats collectes")

    # Collecter les combats des combattants suivis
    if FIGHTERS:
        print("[INFO] Collecte des combats des combattants suivis...")
        for fighter in FIGHTERS:
            fighter_name = fighter.get("name")
            fighter_id = fighter.get("id")
            if not fighter_name:
                continue

            fights = collect_fighter_fights(fighter_name, fighter_id, MAX_FIGHTS_PER_FIGHTER)
            all_data["fighters_fights"].extend(fights)
            print(f"[OK] {fighter_name}: {len(fights)} combats collectes")

    # Sauvegarder
    payload = {
        "source": "api-mma",
        "sport": "mma",
        "season": SEASON,
        "fetched_at": datetime.utcnow().isoformat(),
        "fighters_tracked": [f.get("name") for f in FIGHTERS],
        "total_recent_fights": len(all_data["recent_fights"]),
        "total_fighters_fights": len(all_data["fighters_fights"]),
        "data": all_data
    }

    output_file = OUTPUT_DIR / "mma_data.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"[OK] MMA : {payload['total_recent_fights']} combats recents + {payload['total_fighters_fights']} combats de combattants suivis collectes")


if __name__ == "__main__":
    main()
