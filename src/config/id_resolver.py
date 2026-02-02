"""
Résolveur automatique d'IDs pour les équipes, ligues et joueurs
Recherche les IDs manquants via les APIs et les met en cache
"""
import json
import requests
from pathlib import Path
from typing import Dict, Any, Optional


# Fichier de cache des IDs trouvés
CACHE_FILE = Path(__file__).parent.parent.parent / "id_cache.json"


class IDResolver:
    """Résout automatiquement les IDs manquants en interrogeant les APIs"""

    def __init__(self):
        self.cache = self._load_cache()
        self.api_key = None

    def _load_cache(self) -> Dict:
        """Charge le cache d'IDs depuis le fichier"""
        if CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[WARNING] Erreur lecture cache: {e}")

        return {
            "football": {"teams": {}, "leagues": {}},
            "basketball": {"teams": {}, "players": {}},
            "rugby": {"teams": {}, "leagues": {}},
            "handball": {"teams": {}, "leagues": {}},
            "volleyball": {"teams": {}, "leagues": {}},
            "mma": {"fighters": {}},
        }

    def _save_cache(self):
        """Sauvegarde le cache d'IDs"""
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
            print(f"[OK] Cache sauvegardé: {CACHE_FILE}")
        except Exception as e:
            print(f"[ERROR] Erreur sauvegarde cache: {e}")

    def set_api_key(self, api_key: str):
        """Définit la clé API pour les recherches"""
        self.api_key = api_key

    def search_team(self, sport: str, team_name: str, api_url: str) -> Optional[Dict]:
        """
        Recherche l'ID d'une équipe via l'API

        Args:
            sport: Nom du sport (football, basketball, etc.)
            team_name: Nom de l'équipe à rechercher
            api_url: URL de base de l'API

        Returns:
            Dict avec les infos de l'équipe ou None
        """
        # Vérifier le cache d'abord
        if team_name in self.cache.get(sport, {}).get("teams", {}):
            print(f"[CACHE] {team_name} trouvé dans le cache")
            return self.cache[sport]["teams"][team_name]

        if not self.api_key:
            print(f"[ERROR] Clé API manquante pour rechercher {team_name}")
            return None

        print(f"[SEARCH] Recherche de '{team_name}' dans l'API {sport}...")

        try:
            headers = {"x-apisports-key": self.api_key}
            response = requests.get(
                f"{api_url}/teams",
                headers=headers,
                params={"search": team_name},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            teams = data.get("response", [])
            if not teams:
                print(f"[NOT FOUND] Aucune équipe trouvée pour '{team_name}'")
                return None

            # Prendre le premier résultat (meilleure correspondance)
            team_data = teams[0]
            team_info = team_data.get("team", team_data)

            result = {
                "id": team_info.get("id"),
                "name": team_info.get("name"),
                "country": team_info.get("country"),
            }

            # Ajouter au cache
            if sport not in self.cache:
                self.cache[sport] = {"teams": {}, "leagues": {}}
            if "teams" not in self.cache[sport]:
                self.cache[sport]["teams"] = {}

            self.cache[sport]["teams"][team_name] = result
            self._save_cache()

            print(f"[FOUND] {team_name} → ID: {result['id']}")
            return result

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                print(f"[ERROR] Limite de requêtes API atteinte")
            else:
                print(f"[ERROR] Erreur HTTP {e.response.status_code}: {e}")
        except Exception as e:
            print(f"[ERROR] Erreur recherche {team_name}: {e}")

        return None

    def search_league(self, sport: str, league_name: str, api_url: str) -> Optional[Dict]:
        """
        Recherche l'ID d'une ligue via l'API

        Args:
            sport: Nom du sport
            league_name: Nom de la ligue
            api_url: URL de base de l'API

        Returns:
            Dict avec les infos de la ligue ou None
        """
        # Vérifier le cache
        if league_name in self.cache.get(sport, {}).get("leagues", {}):
            print(f"[CACHE] {league_name} trouvé dans le cache")
            return self.cache[sport]["leagues"][league_name]

        if not self.api_key:
            print(f"[ERROR] Clé API manquante pour rechercher {league_name}")
            return None

        print(f"[SEARCH] Recherche de '{league_name}' dans l'API {sport}...")

        try:
            headers = {"x-apisports-key": self.api_key}
            response = requests.get(
                f"{api_url}/leagues",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            leagues = data.get("response", [])

            # Rechercher par nom
            for league in leagues:
                league_info = league.get("league", league)
                name = league_info.get("name", "")

                if league_name.lower() in name.lower():
                    result = {
                        "id": league_info.get("id"),
                        "name": name,
                        "country": league_info.get("country", {}).get("name")
                                   if isinstance(league_info.get("country"), dict)
                                   else league_info.get("country")
                    }

                    # Ajouter au cache
                    if sport not in self.cache:
                        self.cache[sport] = {"teams": {}, "leagues": {}}
                    if "leagues" not in self.cache[sport]:
                        self.cache[sport]["leagues"] = {}

                    self.cache[sport]["leagues"][league_name] = result
                    self._save_cache()

                    print(f"[FOUND] {league_name} → ID: {result['id']}")
                    return result

            print(f"[NOT FOUND] Aucune ligue trouvée pour '{league_name}'")
            return None

        except Exception as e:
            print(f"[ERROR] Erreur recherche {league_name}: {e}")

        return None

    def get_cached_team(self, sport: str, team_name: str) -> Optional[Dict]:
        """Récupère un ID d'équipe depuis le cache uniquement"""
        return self.cache.get(sport, {}).get("teams", {}).get(team_name)

    def get_cached_league(self, sport: str, league_name: str) -> Optional[Dict]:
        """Récupère un ID de ligue depuis le cache uniquement"""
        return self.cache.get(sport, {}).get("leagues", {}).get(league_name)


# Instance globale
_resolver_instance = None


def get_id_resolver() -> IDResolver:
    """
    Récupère l'instance unique du résolveur

    Returns:
        Instance de IDResolver
    """
    global _resolver_instance
    if _resolver_instance is None:
        _resolver_instance = IDResolver()
    return _resolver_instance
