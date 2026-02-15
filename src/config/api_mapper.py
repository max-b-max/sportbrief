"""
Mapper entre préférences utilisateur et configurations API
Traduit les préférences en configurations concrètes pour chaque API
"""
from typing import Dict, List, Any
from .preferences import get_preferences
from .id_resolver import get_id_resolver


# IDs mapping - À remplir progressivement via recherche API
# Ce mapping sera éventuellement externalisé dans un fichier JSON
API_IDS = {
    "football": {
        "teams": {
            "Olympique Marseille": {"id": 119, "league_id": 61},
            "Liverpool FC": {"id": 40, "league_id": 39}
        },
        "leagues": {
            "Ligue 1": {"id": 61, "country": "France"},
            "Premier League": {"id": 39, "country": "England"},
            "La Liga": {"id": 140, "country": "Spain"},
            "Bundesliga": {"id": 78, "country": "Germany"},
            "Serie A": {"id": 135, "country": "Italy"},
            "Champions League": {"id": 2, "country": "World"},
            "Europa League": {"id": 3, "country": "World"},
            "Conference League": {"id": 848, "country": "World"},
            "Euro": {"id": 4, "country": "World"},
            "Coupe du Monde": {"id": 1, "country": "World"}
        }
    },
    "basketball": {
        "french_players": [
            {"id": 985, "name": "Wembanyama Victor", "team_id": 158, "team_name": "San Antonio Spurs"},
            {"id": 815, "name": "Gobert Rudy", "team_id": 149, "team_name": "Minnesota Timberwolves"},
            {"id": 919, "name": "Batum Nicolas", "team_id": 144, "team_name": "Los Angeles Clippers"},
            {"id": 1052, "name": "Coulibaly Bilal", "team_id": 161, "team_name": "Washington Wizards"},
            {"id": 11642, "name": "Sarr Alexandre", "team_id": 161, "team_name": "Washington Wizards"},
            {"id": 264, "name": "Risacher Zaccharie", "team_id": 132, "team_name": "Atlanta Hawks"},
            {"id": 7818, "name": "Yabusele Guerschon", "team_id": 154, "team_name": "Philadelphia 76ers"},
            {"id": 885, "name": "Dieng Ousmane", "team_id": 152, "team_name": "Oklahoma City Thunder"},
            {"id": 987, "name": "Cissoko Sidy", "team_id": 158, "team_name": "San Antonio Spurs"},
            {"id": 647, "name": "Hayes Killian", "team_id": 134, "team_name": "Brooklyn Nets"},
            {"id": 715, "name": "Diabate Moussa", "team_id": 135, "team_name": "Charlotte Hornets"},
            {"id": 189, "name": "Salaun Tidjane", "team_id": 135, "team_name": "Charlotte Hornets"}
        ],
        "leagues": {
            "NBA": {"id": 12, "country": "USA"}
        }
    },
    "rugby": {
        "teams": {
            "France": {"id": 387, "is_national_team": True},
            "Stade Toulousain": {"id": 107, "league_id": 54},
            "Bordeaux Begles": {"id": 96, "league_id": 54}
        },
        "leagues": {
            "Top 14": {"id": 16, "country": "France"},
            "Champions Cup": {"id": 54, "country": "Europe"},
            "Six Nations": {"id": 51, "country": "Europe"},
            "Coupe du Monde": {"id": 69, "country": "World"},
            "Coupe du Monde Feminine": {"id": 70, "country": "World"}
        }
    },
    "handball": {
        "teams": {
            "France": {"id": 2662, "is_national_team": True}
        },
        "leagues": {
            "Starligue": {"id": 34, "country": "France"},
            "Division 1 Women": {"id": 29, "country": "France"},
            "World Championship": {"id": 153, "country": "World"},
            "World Championship Women": {"id": 154, "country": "World"},
            "Olympic Games": {"id": 155, "country": "World"}
        }
    },
    "volleyball": {
        "teams": {
            "Chaumont": {"id": 470, "league_id": 63},
            "France": {"id": 2201, "is_national_team": True}
        },
        "leagues": {
            "Ligue A": {"id": 63, "country": "France"},
            "World Championship": {"id": 185, "country": "World"},
            "World Championship Women": {"id": 186, "country": "World"},
            "Olympic Games": {"id": 189, "country": "World"}
        }
    },
    "mma": {
        "french_fighters": [
            {"name": "Ciryl Gane", "id": 545},
            {"name": "Nassourdine Imavov", "id": 831},
            {"name": "Benoît Saint Denis", "id": 2466},
            {"name": "Manon Fiorot", "id": 900},
            {"name": "Taylor Lapilus", "id": 2145},
            {"name": "William Gomis", "id": 2522},
            {"name": "Farés Ziam", "id": 591},
            {"name": "Alan Baudot", "id": 857},
            {"name": "Gadzhi Omargadzhiev", "id": 2490},
            {"name": "Daria Zhelezniakova", "id": 2627},
            {"name": "Stephanie Egger", "id": 858},
            {"name": "Joanne Wood", "id": 18}
        ]
    }
}


class APIMapper:
    """Mapper entre préférences et configurations API"""

    def __init__(self):
        self.prefs = get_preferences()
        self.resolver = get_id_resolver()

        # Configurer le résolveur avec la clé API
        api_key = self.prefs.get_api_key("football_data")
        if api_key:
            self.resolver.set_api_key(api_key)

    def get_sport_api_config(self, sport: str) -> Dict[str, Any]:
        """
        Génère la configuration API pour un sport basée sur les préférences

        Args:
            sport: Nom du sport

        Returns:
            Configuration API complète pour le sport
        """
        if not self.prefs.is_sport_enabled(sport):
            return {}

        sport_config = self.prefs.get_sport_config(sport)

        # Configuration de base
        config = {
            "enabled": True,
            "season": 2024,
            "max_games_per_team": self.prefs.get_max_items("games_per_team"),
            "max_games_per_league": self.prefs.get_max_items("games_per_league"),
            "max_games_per_player": self.prefs.get_max_items("games_per_player"),
        }

        # Mapper les équipes
        if "teams" in sport_config:
            config["teams"] = self._map_teams(sport, sport_config["teams"])

        # Mapper les ligues
        if "leagues" in sport_config:
            config["leagues"] = self._map_leagues(sport, sport_config["leagues"])

        # Mapper les joueurs
        if "players" in sport_config:
            config["players"] = self._map_players(sport, sport_config["players"])

        # Mapper les combattants (MMA)
        if "fighters" in sport_config:
            config["fighters"] = self._map_fighters(sport, sport_config["fighters"])

        return config

    def _map_teams(self, sport: str, team_prefs: List[Dict]) -> List[Dict]:
        """
        Mappe les préférences d'équipes vers les IDs API
        Recherche automatiquement les IDs manquants

        Args:
            sport: Nom du sport
            team_prefs: Liste des équipes des préférences

        Returns:
            Liste des équipes avec IDs
        """
        teams = []
        team_mapping = API_IDS.get(sport, {}).get("teams", {})

        # Mapping des sports vers leurs URLs API
        api_urls = {
            "football": "https://api.football-data.org/v4",
        }

        for team_pref in team_prefs:
            team_name = team_pref.get("name")

            # 1. Chercher dans le mapping hardcodé
            if team_name in team_mapping:
                team_data = team_mapping[team_name].copy()
                team_data["name"] = team_name
                teams.append(team_data)

            # 2. Chercher dans le cache
            elif cached := self.resolver.get_cached_team(sport, team_name):
                team_data = cached.copy()
                team_data["name"] = team_name
                teams.append(team_data)
                print(f"[CACHE] {team_name} récupéré du cache")

            # 3. Rechercher automatiquement via l'API
            elif sport in api_urls:
                print(f"[AUTO-RESOLVE] Recherche automatique de '{team_name}'...")
                found = self.resolver.search_team(sport, team_name, api_urls[sport])

                if found:
                    team_data = found.copy()
                    team_data["name"] = team_name
                    teams.append(team_data)
                else:
                    print(f"[WARNING] Équipe '{team_name}' non trouvée - ignorée")

            else:
                print(f"[WARNING] Sport '{sport}' non supporté pour recherche auto - équipe '{team_name}' ignorée")

        return teams

    def _map_leagues(self, sport: str, league_names: List[str]) -> List[Dict]:
        """
        Mappe les préférences de ligues vers les IDs API
        Recherche automatiquement les IDs manquants

        Args:
            sport: Nom du sport
            league_names: Liste des noms de ligues

        Returns:
            Liste des ligues avec IDs
        """
        leagues = []
        league_mapping = API_IDS.get(sport, {}).get("leagues", {})

        # Mapping des sports vers leurs URLs API
        api_urls = {
            "football": "https://api.football-data.org/v4",
        }

        for league_name in league_names:

            # 1. Chercher dans le mapping hardcodé
            if league_name in league_mapping:
                league_data = league_mapping[league_name].copy()
                league_data["name"] = league_name
                leagues.append(league_data)

            # 2. Chercher dans le cache
            elif cached := self.resolver.get_cached_league(sport, league_name):
                league_data = cached.copy()
                league_data["name"] = league_name
                leagues.append(league_data)
                print(f"[CACHE] {league_name} récupéré du cache")

            # 3. Rechercher automatiquement via l'API
            elif sport in api_urls:
                print(f"[AUTO-RESOLVE] Recherche automatique de '{league_name}'...")
                found = self.resolver.search_league(sport, league_name, api_urls[sport])

                if found:
                    league_data = found.copy()
                    league_data["name"] = league_name
                    leagues.append(league_data)
                else:
                    print(f"[WARNING] Ligue '{league_name}' non trouvée - ignorée")

            else:
                print(f"[WARNING] Sport '{sport}' non supporté pour recherche auto - ligue '{league_name}' ignorée")

        return leagues

    def _map_players(self, sport: str, player_pref: Any) -> List[Dict] | str:
        """
        Mappe les préférences de joueurs vers les IDs API

        Args:
            sport: Nom du sport
            player_pref: Préférence joueurs ("all_french", liste, etc.)

        Returns:
            Liste des joueurs ou configuration
        """
        if player_pref == "all_french":
            # Retourner tous les joueurs français du mapping
            return API_IDS.get(sport, {}).get("french_players", [])
        elif isinstance(player_pref, list):
            # Liste spécifique de joueurs
            return player_pref
        else:
            return player_pref

    def _map_fighters(self, sport: str, fighter_pref: str) -> List[Dict]:
        """
        Mappe les préférences de combattants vers les IDs API

        Args:
            sport: Nom du sport
            fighter_pref: Préférence combattants

        Returns:
            Liste des combattants
        """
        if fighter_pref == "all_french":
            return API_IDS.get(sport, {}).get("french_fighters", [])
        return []


# Instance globale
_mapper_instance = None


def get_api_mapper() -> APIMapper:
    """
    Récupère l'instance unique du mapper

    Returns:
        Instance de APIMapper
    """
    global _mapper_instance
    if _mapper_instance is None:
        _mapper_instance = APIMapper()
    return _mapper_instance


def get_sport_api_config(sport: str) -> Dict[str, Any]:
    """
    Fonction helper pour récupérer la config d'un sport

    Args:
        sport: Nom du sport

    Returns:
        Configuration API du sport
    """
    mapper = get_api_mapper()
    return mapper.get_sport_api_config(sport)
