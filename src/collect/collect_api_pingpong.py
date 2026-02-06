"""
Collecte des données Tennis de Table via Sportradar API
Focus sur les joueurs et joueuses françaises
"""
import json
import sys
from datetime import datetime
from pathlib import Path
import requests

sys.path.append(str(Path(__file__).parent.parent))
from config import get_preferences

OUTPUT_DIR = Path("data/raw/api/pingpong")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Charger les préférences
PREFS = get_preferences()

# Configuration API Sportradar
API_KEY = PREFS.get_api_key("sportradar")
BASE_URL = "https://api.sportradar.com/tabletennis/trial/v2/en"

# Préférences ping-pong
SPECIAL_PLAYERS = PREFS.get("sports.pingpong.special_attention", [])
FOCUS = PREFS.get("sports.pingpong.focus", "french_players")
MAX_EVENTS = PREFS.get_max_items("events")


# Helpers

def make_api_request(endpoint: str, params: dict | None = None) -> dict:
    """
    Effectue une requête à l'API Sportradar

    Args:
        endpoint: Endpoint de l'API
        params: Paramètres additionnels

    Returns:
        Réponse JSON de l'API
    """
    if not API_KEY or API_KEY == "YOUR_SPORTRADAR_API_KEY_HERE":
        print("[ERROR] Clé API Sportradar manquante dans user_preferences.json")
        return {"rankings": [], "competitors": []}

    url = f"{BASE_URL}/{endpoint}.json"
    if params is None:
        params = {}
    params["api_key"] = API_KEY

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print(f"[ERROR] Authentification échouée - vérifiez votre clé API Sportradar")
        elif e.response.status_code == 403:
            print(f"[ERROR] Accès refusé - vérifiez vos permissions API")
        elif e.response.status_code == 429:
            print(f"[ERROR] Limite de requêtes atteinte")
        else:
            print(f"[ERROR] Erreur HTTP {e.response.status_code}: {e}")
        return {"rankings": [], "competitors": []}

    except Exception as e:
        print(f"[WARNING] Erreur API {endpoint}: {e}")
        return {"rankings": [], "competitors": []}


# Collection functions

def collect_rankings() -> list[dict]:
    """
    Collecte les classements mondiaux de tennis de table

    Returns:
        Liste des classements
    """
    data = []

    try:
        print("[INFO] Collecte des classements mondiaux...")
        # Endpoint pour les rankings
        # Note: L'endpoint exact dépend de la documentation Sportradar
        # Ceci est une implémentation basée sur la structure typique Sportradar
        response = make_api_request("rankings")

        # Parser la réponse selon la structure Sportradar
        rankings = response.get("rankings", [])

        for ranking_group in rankings:
            # Extraire les compétiteurs du groupe de classement
            competitors = ranking_group.get("competitor_rankings", [])

            for comp_rank in competitors:
                competitor = comp_rank.get("competitor", {})
                nationality = competitor.get("country_code", "")

                # Filtrer par nationalité française
                if nationality.upper() in ["FRA", "FR", "FRANCE"]:
                    player_name = competitor.get("name", "")
                    rank = comp_rank.get("rank")

                    data.append({
                        "sport": "pingpong",
                        "source": "sportradar",
                        "player_name": player_name,
                        "player_id": competitor.get("id"),
                        "nationality": nationality,
                        "rank": rank,
                        "points": comp_rank.get("points"),
                        "category": ranking_group.get("name"),
                        "special_attention": player_name in SPECIAL_PLAYERS
                    })

        print(f"[OK] {len(data)} joueurs français trouvés dans les classements")

    except Exception as e:
        print(f"[WARNING] Erreur lors de la collecte des classements: {e}")

    return data


def collect_player_profile(player_id: str, player_name: str) -> dict | None:
    """
    Collecte le profil détaillé d'un joueur

    Args:
        player_id: ID du joueur
        player_name: Nom du joueur

    Returns:
        Profil du joueur ou None
    """
    try:
        response = make_api_request(f"competitors/{player_id}/profile")

        if "competitor" in response:
            competitor = response["competitor"]
            return {
                "sport": "pingpong",
                "source": "sportradar",
                "player_name": player_name,
                "player_id": player_id,
                "gender": competitor.get("gender"),
                "date_of_birth": competitor.get("date_of_birth"),
                "nationality": competitor.get("country_code"),
                "ranking": competitor.get("rank")
            }

    except Exception as e:
        print(f"[WARNING] Erreur sur le profil de {player_name}: {e}")

    return None


def collect_player_summaries(player_id: str, player_name: str) -> list[dict]:
    """
    Collecte les matchs récents d'un joueur

    Args:
        player_id: ID du joueur
        player_name: Nom du joueur

    Returns:
        Liste des matchs
    """
    data = []

    try:
        response = make_api_request(f"competitors/{player_id}/summaries")

        # Parser les matchs récents
        summaries = response.get("summaries", [])

        for summary in summaries[:MAX_EVENTS]:
            sport_event = summary.get("sport_event", {})
            sport_event_status = summary.get("sport_event_status", {})

            # Extraire les informations du match
            home_competitor = sport_event.get("competitors", [{}])[0] if sport_event.get("competitors") else {}
            away_competitor = sport_event.get("competitors", [{}])[1] if len(sport_event.get("competitors", [])) > 1 else {}

            data.append({
                "sport": "pingpong",
                "source": "sportradar",
                "player_tracked": player_name,
                "event_id": sport_event.get("id"),
                "date": sport_event.get("start_time"),
                "tournament": sport_event.get("tournament", {}).get("name"),
                "home_player": home_competitor.get("name"),
                "away_player": away_competitor.get("name"),
                "home_score": sport_event_status.get("home_score"),
                "away_score": sport_event_status.get("away_score"),
                "status": sport_event_status.get("status"),
                "winner": sport_event_status.get("winner_id")
            })

    except Exception as e:
        print(f"[WARNING] Erreur sur les matchs de {player_name}: {e}")

    return data


# Main

def main():
    all_data = {
        "rankings": [],
        "profiles": [],
        "matches": []
    }

    # Collecter les classements français
    print("[INFO] === Collecte Tennis de Table (Ping-Pong) ===")
    rankings = collect_rankings()
    all_data["rankings"].extend(rankings)

    # Collecter les détails des joueurs spéciaux
    if SPECIAL_PLAYERS:
        print(f"\n[INFO] Collecte des détails pour les joueurs prioritaires...")
        for ranking in rankings:
            player_name = ranking.get("player_name")
            player_id = ranking.get("player_id")

            if player_name in SPECIAL_PLAYERS and player_id:
                print(f"[INFO] Collecte de {player_name}...")

                # Profil
                profile = collect_player_profile(player_id, player_name)
                if profile:
                    all_data["profiles"].append(profile)

                # Matchs récents
                matches = collect_player_summaries(player_id, player_name)
                all_data["matches"].extend(matches)
                if len(matches) > 0:
                    print(f"[OK] {player_name}: {len(matches)} matchs collectés")

    # Sauvegarder
    payload = {
        "source": "sportradar-tabletennis",
        "sport": "pingpong",
        "fetched_at": datetime.utcnow().isoformat(),
        "focus": FOCUS,
        "special_players": SPECIAL_PLAYERS,
        "total_french_players": len(all_data["rankings"]),
        "total_profiles": len(all_data["profiles"]),
        "total_matches": len(all_data["matches"]),
        "data": all_data
    }

    output_file = OUTPUT_DIR / "pingpong_data.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Ping-Pong : {payload['total_french_players']} joueurs français + {payload['total_matches']} matchs collectés")
    print(f"[OK] Fichier sauvegardé : {output_file}")


if __name__ == "__main__":
    main()
