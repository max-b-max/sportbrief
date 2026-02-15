"""
Résolveur automatique de saisons en cours via l'API
Interroge les APIs pour trouver quelle saison est en cours (via les dates start/end)
"""
import json
from pathlib import Path
from typing import Optional
from datetime import datetime
import requests


# Cache pour éviter de réinterroger l'API à chaque fois
CACHE_FILE = Path("current_seasons_cache.json")
_cache = {}


def load_cache() -> dict:
    """Charge le cache des saisons en cours depuis le fichier"""
    global _cache

    if not CACHE_FILE.exists():
        return {}

    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            _cache = json.load(f)
            return _cache
    except Exception as e:
        print(f"[WARNING] Erreur chargement cache saisons: {e}")
        return {}


def save_cache():
    """Sauvegarde le cache des saisons en cours"""
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(_cache, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[WARNING] Erreur sauvegarde cache saisons: {e}")


def get_current_season_from_api(
    sport: str,
    league_id: int,
    league_name: str,
    api_url: str,
    api_key: str
) -> Optional[str | int]:
    """
    Interroge l'API pour trouver la saison marquée current=true

    Args:
        sport: Nom du sport (football, basketball, etc.)
        league_id: ID de la ligue
        league_name: Nom de la ligue (pour les logs)
        api_url: URL de base de l'API
        api_key: Clé API

    Returns:
        Saison marquée comme current, ou None si non trouvée
    """
    # Vérifier le cache d'abord
    cache_key = f"{sport}_{league_id}"
    if cache_key in _cache:
        print(f"[CACHE] {league_name}: saison {_cache[cache_key]} (depuis cache)")
        return _cache[cache_key]

    # Interroger l'API
    headers = {"x-apisports-key": api_key}

    try:
        # Endpoint differ selon le sport
        if sport in ["basketball", "nba"]:
            endpoint = f"{api_url}/leagues"
        elif sport == "football":
            endpoint = f"{api_url}/leagues"
        elif sport in ["rugby", "handball", "volleyball"]:
            endpoint = f"{api_url}/leagues"
        elif sport == "mma":
            # MMA n'a pas de concept de ligue avec saisons
            return None
        elif sport == "formula1":
            # F1 n'a pas de concept de ligue avec saisons
            return None
        else:
            return None

        response = requests.get(
            endpoint,
            headers=headers,
            params={"id": league_id} if league_id else None,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        # Parser la réponse pour trouver la saison en cours (via dates)
        now = datetime.now()

        for league_data in data.get("response", []):
            # Vérifier que c'est la bonne ligue
            if isinstance(league_data, dict):
                # Format avec clé "league"
                league = league_data.get("league", league_data)
                if league.get("id") != league_id:
                    continue
                seasons = league_data.get("seasons", [])
            else:
                # Format direct
                if league_data.get("id") != league_id:
                    continue
                seasons = league_data.get("seasons", [])

            # Chercher la saison dont les dates incluent aujourd'hui
            for season in seasons:
                # Le champ peut être "season" (basketball) ou "year" (football)
                season_value = season.get("season") or season.get("year")
                start_str = season.get("start")
                end_str = season.get("end")

                if not season_value or not start_str or not end_str:
                    continue

                try:
                    start_date = datetime.strptime(start_str, "%Y-%m-%d")
                    end_date = datetime.strptime(end_str, "%Y-%m-%d")

                    # Vérifier si la date actuelle est dans la période
                    if start_date <= now <= end_date:
                        # Sauvegarder dans le cache
                        _cache[cache_key] = season_value
                        save_cache()

                        print(f"[API] {league_name}: saison {season_value} (en cours)")
                        return season_value

                except ValueError:
                    continue

        print(f"[WARNING] {league_name}: aucune saison en cours trouvee")
        return None

    except Exception as e:
        print(f"[ERROR] Erreur API pour {league_name}: {e}")
        return None


def get_current_seasons_for_sport(
    sport: str,
    api_url: str,
    api_key: str,
    league_ids: list[int] = None
) -> dict[int, str | int]:
    """
    Récupère toutes les saisons en cours pour un sport donné

    Args:
        sport: Nom du sport
        api_url: URL de base de l'API
        api_key: Clé API
        league_ids: Liste optionnelle d'IDs de ligues à interroger

    Returns:
        Dictionnaire {league_id: current_season}
    """
    results = {}

    headers = {"x-apisports-key": api_key}

    try:
        # Obtenir toutes les ligues
        endpoint = f"{api_url}/leagues"
        response = requests.get(endpoint, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        now = datetime.now()

        for league_data in data.get("response", []):
            if isinstance(league_data, dict):
                league = league_data.get("league", league_data)
                league_id = league.get("id")
                league_name = league.get("name", "Unknown")
                seasons = league_data.get("seasons", [])
            else:
                league_id = league_data.get("id")
                league_name = league_data.get("name", "Unknown")
                seasons = league_data.get("seasons", [])

            # Si une liste d'IDs est fournie, filtrer
            if league_ids and league_id not in league_ids:
                continue

            # Chercher la saison en cours (via dates)
            for season in seasons:
                # Le champ peut être "season" (basketball) ou "year" (football)
                season_value = season.get("season") or season.get("year")
                start_str = season.get("start")
                end_str = season.get("end")

                if not season_value or not start_str or not end_str:
                    continue

                try:
                    start_date = datetime.strptime(start_str, "%Y-%m-%d")
                    end_date = datetime.strptime(end_str, "%Y-%m-%d")

                    if start_date <= now <= end_date:
                        results[league_id] = season_value

                        # Sauvegarder dans le cache
                        cache_key = f"{sport}_{league_id}"
                        _cache[cache_key] = season_value

                        print(f"[OK] {league_name} (ID {league_id}): saison {season_value}")
                        break

                except ValueError:
                    continue

        # Sauvegarder le cache
        save_cache()

        return results

    except Exception as e:
        print(f"[ERROR] Erreur récupération saisons pour {sport}: {e}")
        return {}


def clear_cache():
    """Efface le cache des saisons"""
    global _cache
    _cache = {}
    if CACHE_FILE.exists():
        CACHE_FILE.unlink()
    print("[INFO] Cache des saisons effacé")


# Charger le cache au démarrage
_cache = load_cache()


if __name__ == "__main__":
    # Test du système
    try:
        from api_config import get_api_key
    except ImportError:
        from src.config import get_api_key

    print("=== TEST RESOLVEUR DE SAISONS COURANTES ===\n")

    # Test Basketball
    api_key = get_api_key("basketball")
    api_url = "https://api.football-data.org/v4"

    print("Basketball - NBA (league_id=12):")
    season = get_current_season_from_api("basketball", 12, "NBA", api_url, api_key)
    print(f"Resultat: {season}\n")

    # Test Football
    api_key = get_api_key("football")
    api_url = "https://api.football-data.org/v4"

    print("Football - Ligue 1 (league_id=61):")
    season = get_current_season_from_api("football", 61, "Ligue 1", api_url, api_key)
    print(f"Resultat: {season}\n")
