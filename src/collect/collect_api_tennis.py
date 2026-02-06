"""
Collecte des données Tennis via Sportradar API
Focus sur les joueurs et joueuses françaises
Filtrage automatique basé sur user_preferences.json
"""
import json
import sys
from datetime import datetime
from pathlib import Path
import requests

sys.path.append(str(Path(__file__).parent.parent))
from config import get_preferences

OUTPUT_DIR = Path("data/raw/api/tennis")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Charger les préférences
PREFS = get_preferences()

# Configuration API Sportradar
API_KEY = PREFS.get_api_key("sportradar")
BASE_URL = "https://api.sportradar.com/tennis/trial/v3/en"

# Préférences tennis
PLAYER_FOCUS = PREFS.get("sports.tennis.players", "french_top_ranked")
TOURNAMENTS = PREFS.get("sports.tennis.tournaments", [])
MAX_EVENTS = PREFS.get_max_items("events")

# Filtres joueurs (hommes et femmes)
INCLUDE_MEN = PREFS.get("sports.tennis.players_filter.include_men", True)
INCLUDE_WOMEN = PREFS.get("sports.tennis.players_filter.include_women", True)

# Filtres tournois
FILTER_GRAND_SLAM = PREFS.get("sports.tennis.tournaments_filter.grand_slam", True)
FILTER_MASTERS_1000 = PREFS.get("sports.tennis.tournaments_filter.masters_1000", True)
FILTER_WTA_1000 = PREFS.get("sports.tennis.tournaments_filter.wta_1000", True)

# Nationalités françaises à filtrer
FRENCH_NATIONALITIES = PREFS.get_nationality_priority()


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
        print("Ajoutez votre clé dans: api_keys.sportradar")
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


def is_french_player(competitor: dict) -> bool:
    """
    Vérifie si un joueur est français

    Args:
        competitor: Données du compétiteur

    Returns:
        True si le joueur est français
    """
    nationality = competitor.get("nationality", "")
    country_code = competitor.get("country_code", "")
    country = competitor.get("country", "")

    # Vérifier différents formats possibles
    french_indicators = ["FRA", "FR", "France", "French"]

    return any(
        indicator.upper() in str(field).upper()
        for field in [nationality, country_code, country]
        for indicator in french_indicators
    )


def is_major_tournament(tournament_name: str) -> bool:
    """
    Vérifie si un tournoi est un Grand Chelem ou Masters 1000/WTA 1000

    Args:
        tournament_name: Nom du tournoi

    Returns:
        True si le tournoi est majeur (selon les préférences)
    """
    if not tournament_name:
        return False

    tournament_lower = tournament_name.lower()

    # Grand Slams
    grand_slams = [
        "australian open",
        "roland garros",
        "french open",  # Alias pour Roland Garros
        "wimbledon",
        "us open"
    ]

    # Masters 1000 / WTA 1000 keywords
    masters_keywords = ["masters", "1000"]

    # Vérifier Grand Slam
    if FILTER_GRAND_SLAM:
        if any(slam in tournament_lower for slam in grand_slams):
            return True

    # Vérifier Masters 1000 / WTA 1000
    if FILTER_MASTERS_1000 or FILTER_WTA_1000:
        if any(keyword in tournament_lower for keyword in masters_keywords):
            return True

    return False


def should_include_player_by_gender(competitor: dict) -> bool:
    """
    Vérifie si un joueur doit être inclus selon son genre

    Args:
        competitor: Données du compétiteur

    Returns:
        True si le joueur doit être inclus
    """
    gender = competitor.get("gender", "").lower()

    # Si les deux sont activés, tout inclure
    if INCLUDE_MEN and INCLUDE_WOMEN:
        return True

    # Sinon, filtrer par genre
    if gender in ["male", "m", "men"]:
        return INCLUDE_MEN
    elif gender in ["female", "f", "women"]:
        return INCLUDE_WOMEN

    # Si le genre n'est pas spécifié, inclure par défaut
    return True


# Collection functions

def collect_rankings(category: str = "singles") -> list[dict]:
    """
    Collecte les classements ATP/WTA et filtre les joueurs français

    Args:
        category: "singles" ou "doubles"

    Returns:
        Liste des joueurs français classés
    """
    data = []

    try:
        print(f"[INFO] Collecte des classements {category}...")

        # Endpoint pour les rankings
        endpoint = "rankings" if category == "singles" else "doubles_rankings"
        response = make_api_request(endpoint)

        # Parser la réponse selon la structure Sportradar
        rankings = response.get("rankings", [])

        for ranking_group in rankings:
            # Extraire les compétiteurs du groupe de classement
            competitor_rankings = ranking_group.get("competitor_rankings", [])

            for comp_rank in competitor_rankings:
                competitor = comp_rank.get("competitor", {})

                # FILTRAGE: Ne garder que les joueurs français
                if not is_french_player(competitor):
                    continue

                # FILTRAGE: Vérifier le genre (hommes/femmes)
                if not should_include_player_by_gender(competitor):
                    continue

                player_name = competitor.get("name", "")
                rank = comp_rank.get("rank")

                data.append({
                    "sport": "tennis",
                    "source": "sportradar",
                    "category": category,
                    "player_name": player_name,
                    "player_id": competitor.get("id"),
                    "nationality": competitor.get("country_code", "FRA"),
                    "rank": rank,
                    "points": comp_rank.get("points"),
                    "ranking_type": ranking_group.get("type_name"),
                    "gender": competitor.get("gender", "")
                })

        print(f"[OK] {len(data)} joueurs français trouvés en {category}")

    except Exception as e:
        print(f"[WARNING] Erreur lors de la collecte des classements {category}: {e}")

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
                "sport": "tennis",
                "source": "sportradar",
                "player_name": player_name,
                "player_id": player_id,
                "gender": competitor.get("gender"),
                "date_of_birth": competitor.get("date_of_birth"),
                "nationality": competitor.get("country_code"),
                "height": competitor.get("height"),
                "weight": competitor.get("weight"),
                "handedness": competitor.get("handedness"),
                "turned_pro": competitor.get("turned_pro"),
                "ranking": competitor.get("rank"),
                "career_titles": competitor.get("info", {}).get("titles")
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
            competitors = sport_event.get("competitors", [])

            # Extraire le nom du tournoi
            tournament_name = sport_event.get("tournament", {}).get("name", "")

            # FILTRAGE: Ne garder que les tournois majeurs (Grand Chelem + Masters/WTA 1000)
            if not is_major_tournament(tournament_name):
                continue

            # Extraire les informations du match
            home_competitor = competitors[0] if len(competitors) > 0 else {}
            away_competitor = competitors[1] if len(competitors) > 1 else {}

            data.append({
                "sport": "tennis",
                "source": "sportradar",
                "player_tracked": player_name,
                "event_id": sport_event.get("id"),
                "date": sport_event.get("start_time"),
                "tournament": tournament_name,
                "round": sport_event.get("tournament_round", {}).get("name"),
                "home_player": home_competitor.get("name"),
                "away_player": away_competitor.get("name"),
                "home_score": sport_event_status.get("home_score"),
                "away_score": sport_event_status.get("away_score"),
                "status": sport_event_status.get("status"),
                "winner_id": sport_event_status.get("winner_id")
            })

    except Exception as e:
        print(f"[WARNING] Erreur sur les matchs de {player_name}: {e}")

    return data


# Main

def main():
    all_data = {
        "rankings_singles": [],
        "rankings_doubles": [],
        "profiles": [],
        "matches": []
    }

    print("[INFO] === Collecte Tennis ===")
    print(f"[INFO] Filtrage: Joueurs français uniquement")
    print(f"[INFO] Nationalités recherchées: {', '.join(FRENCH_NATIONALITIES)}")

    # Afficher les filtres de genre
    gender_filters = []
    if INCLUDE_MEN:
        gender_filters.append("hommes")
    if INCLUDE_WOMEN:
        gender_filters.append("femmes")
    print(f"[INFO] Genres inclus: {', '.join(gender_filters) if gender_filters else 'aucun'}")

    # Afficher les filtres de tournois
    tournament_filters = []
    if FILTER_GRAND_SLAM:
        tournament_filters.append("Grand Chelem")
    if FILTER_MASTERS_1000:
        tournament_filters.append("Masters 1000")
    if FILTER_WTA_1000:
        tournament_filters.append("WTA 1000")
    print(f"[INFO] Tournois filtrés: {', '.join(tournament_filters) if tournament_filters else 'tous'}")

    # Collecter les classements français en simple
    singles_rankings = collect_rankings("singles")
    all_data["rankings_singles"].extend(singles_rankings)

    # Collecter les classements français en double
    doubles_rankings = collect_rankings("doubles")
    all_data["rankings_doubles"].extend(doubles_rankings)

    # Collecter les détails des meilleurs joueurs français
    print(f"\n[INFO] Collecte des détails pour les {min(10, len(singles_rankings))} meilleurs joueurs français...")

    # Prendre les 10 meilleurs joueurs français classés
    top_french_players = sorted(
        singles_rankings,
        key=lambda x: x.get("rank", 9999)
    )[:10]

    for ranking in top_french_players:
        player_name = ranking.get("player_name")
        player_id = ranking.get("player_id")

        if not player_id:
            continue

        print(f"[INFO] Collecte de {player_name} (#{ranking.get('rank')})...")

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
        "source": "sportradar-tennis",
        "sport": "tennis",
        "fetched_at": datetime.utcnow().isoformat(),
        "filter": "french_players_only",
        "nationalities_tracked": FRENCH_NATIONALITIES,
        "total_french_singles": len(all_data["rankings_singles"]),
        "total_french_doubles": len(all_data["rankings_doubles"]),
        "total_profiles": len(all_data["profiles"]),
        "total_matches": len(all_data["matches"]),
        "data": all_data
    }

    output_file = OUTPUT_DIR / "tennis_data.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Tennis : {payload['total_french_singles']} joueurs français (simple) + "
          f"{payload['total_french_doubles']} (double) + {payload['total_matches']} matchs collectés")
    print(f"[OK] Fichier sauvegardé : {output_file}")


if __name__ == "__main__":
    main()
