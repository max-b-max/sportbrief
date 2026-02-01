"""
Gestion des préférences utilisateur pour SportBrief
Charge et interprète les préférences depuis user_preferences.json
"""
import json
from pathlib import Path
from typing import Any


# Chemin vers le fichier de préférences
PREFERENCES_FILE = Path(__file__).parent.parent.parent / "user_preferences.json"


class UserPreferences:
    """Classe pour gérer les préférences utilisateur"""

    def __init__(self, preferences_file: Path = PREFERENCES_FILE):
        """
        Initialise les préférences utilisateur

        Args:
            preferences_file: Chemin vers le fichier de préférences JSON
        """
        self.preferences_file = preferences_file
        self._preferences = None
        self._load_preferences()

    def _load_preferences(self):
        """Charge les préférences depuis le fichier JSON"""
        try:
            with open(self.preferences_file, "r", encoding="utf-8") as f:
                self._preferences = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Fichier de préférences non trouvé: {self.preferences_file}\n"
                "Créez un fichier user_preferences.json à la racine du projet."
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"Erreur de format JSON dans {self.preferences_file}: {e}")

    def reload(self):
        """Recharge les préférences depuis le fichier"""
        self._load_preferences()

    def get(self, key: str, default: Any = None) -> Any:
        """
        Récupère une valeur de préférence

        Args:
            key: Clé au format "section.subsection.key" (ex: "sports.football.enabled")
            default: Valeur par défaut si la clé n'existe pas

        Returns:
            Valeur de la préférence ou default
        """
        keys = key.split(".")
        value = self._preferences

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def is_sport_enabled(self, sport: str) -> bool:
        """
        Vérifie si un sport est activé

        Args:
            sport: Nom du sport (ex: "football", "basketball")

        Returns:
            True si le sport est activé
        """
        return self.get(f"sports.{sport}.enabled", False)

    def get_sport_config(self, sport: str) -> dict:
        """
        Récupère la configuration complète d'un sport

        Args:
            sport: Nom du sport

        Returns:
            Dictionnaire de configuration du sport
        """
        return self.get(f"sports.{sport}", {})

    def get_teams(self, sport: str) -> list[dict]:
        """
        Récupère la liste des équipes suivies pour un sport

        Args:
            sport: Nom du sport

        Returns:
            Liste des équipes avec leurs informations
        """
        return self.get(f"sports.{sport}.teams", [])

    def get_leagues(self, sport: str) -> list[str]:
        """
        Récupère la liste des ligues/compétitions suivies pour un sport

        Args:
            sport: Nom du sport

        Returns:
            Liste des noms de ligues
        """
        return self.get(f"sports.{sport}.leagues", [])

    def get_players(self, sport: str) -> str | list:
        """
        Récupère la configuration des joueurs suivis

        Args:
            sport: Nom du sport

        Returns:
            Configuration des joueurs (peut être "all", "all_french", liste de noms, etc.)
        """
        return self.get(f"sports.{sport}.players", [])

    def get_api_key(self, api_name: str) -> str | None:
        """
        Récupère une clé API

        Args:
            api_name: Nom de l'API (ex: "api_sports", "sportradar")

        Returns:
            Clé API ou None
        """
        return self.get(f"api_keys.{api_name}")

    def get_country(self) -> str:
        """
        Récupère le pays de l'utilisateur

        Returns:
            Code ou nom du pays
        """
        return self.get("general.country", "France")

    def get_max_items(self, item_type: str) -> int:
        """
        Récupère le nombre maximum d'éléments à collecter

        Args:
            item_type: Type d'élément (ex: "games_per_team", "events")

        Returns:
            Nombre maximum
        """
        key_map = {
            "games_per_team": "max_games_per_team",
            "games_per_league": "max_games_per_league",
            "games_per_player": "max_games_per_player",
            "events": "max_events"
        }

        key = key_map.get(item_type, item_type)
        return self.get(f"data_collection.{key}", 5)

    def should_include_womens(self) -> bool:
        """
        Vérifie si les compétitions féminines doivent être incluses

        Returns:
            True si les compétitions féminines doivent être incluses
        """
        return self.get("filters.include_womens_competitions", True)

    def should_include_world_championships(self) -> bool:
        """
        Vérifie si les championnats du monde doivent être inclus

        Returns:
            True si les championnats du monde doivent être inclus
        """
        return self.get("filters.include_world_championships", True)

    def get_nationality_priority(self) -> list[str]:
        """
        Récupère la liste des nationalités prioritaires

        Returns:
            Liste des nationalités (ex: ["France", "French"])
        """
        return self.get("filters.nationality_priority", ["France"])

    def export_to_dict(self) -> dict:
        """
        Exporte toutes les préférences sous forme de dictionnaire

        Returns:
            Dictionnaire complet des préférences
        """
        return self._preferences.copy()


# Instance globale des préférences
_preferences_instance = None


def get_preferences() -> UserPreferences:
    """
    Récupère l'instance unique des préférences utilisateur

    Returns:
        Instance de UserPreferences
    """
    global _preferences_instance
    if _preferences_instance is None:
        _preferences_instance = UserPreferences()
    return _preferences_instance


def reload_preferences():
    """Recharge les préférences depuis le fichier"""
    global _preferences_instance
    if _preferences_instance is not None:
        _preferences_instance.reload()
    else:
        _preferences_instance = UserPreferences()
