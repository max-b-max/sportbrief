"""
Config Manager pour SportBrief Streamlit App
Gère le chargement/sauvegarde des préférences et de la base d'équipes
"""

import json
import os
from pathlib import Path
from typing import Any, Optional


# Chemins par défaut
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
PREFERENCES_FILE = PROJECT_ROOT / "user_preferences.json"
TEAMS_DATABASE_FILE = PROJECT_ROOT / "src" / "config" / "teams_database.json"


class ConfigManager:
    """Gestionnaire de configuration pour l'app Streamlit"""

    def __init__(
        self,
        preferences_path: Path = PREFERENCES_FILE,
        teams_db_path: Path = TEAMS_DATABASE_FILE
    ):
        self.preferences_path = preferences_path
        self.teams_db_path = teams_db_path
        self._preferences: Optional[dict] = None
        self._teams_db: Optional[dict] = None

    def load_preferences(self) -> dict:
        """Charge les préférences utilisateur depuis le fichier JSON"""
        if self._preferences is None:
            try:
                with open(self.preferences_path, "r", encoding="utf-8") as f:
                    self._preferences = json.load(f)
            except FileNotFoundError:
                self._preferences = self._get_default_preferences()
            except json.JSONDecodeError as e:
                raise ValueError(f"Erreur JSON dans {self.preferences_path}: {e}")
        return self._preferences

    def save_preferences(self, prefs: dict) -> bool:
        """
        Sauvegarde les préférences de manière atomique.
        Écrit dans un fichier temporaire puis renomme.
        """
        tmp_path = self.preferences_path.with_suffix(".json.tmp")

        try:
            # Écrire dans le fichier temporaire
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(prefs, f, indent=2, ensure_ascii=False)

            # Renommer atomiquement (remplace le fichier existant)
            os.replace(tmp_path, self.preferences_path)

            # Mettre à jour le cache
            self._preferences = prefs
            return True

        except Exception as e:
            # Nettoyer le fichier temporaire si erreur
            if tmp_path.exists():
                tmp_path.unlink()
            raise RuntimeError(f"Erreur sauvegarde préférences: {e}")

    def reload_preferences(self) -> dict:
        """Force le rechargement des préférences depuis le fichier"""
        self._preferences = None
        return self.load_preferences()

    def load_teams_database(self) -> dict:
        """Charge la base de données des équipes"""
        if self._teams_db is None:
            try:
                with open(self.teams_db_path, "r", encoding="utf-8") as f:
                    self._teams_db = json.load(f)
            except FileNotFoundError:
                self._teams_db = {}
            except json.JSONDecodeError as e:
                raise ValueError(f"Erreur JSON dans {self.teams_db_path}: {e}")
        return self._teams_db

    def get_teams_for_sport(self, sport: str) -> list[dict]:
        """Retourne la liste des équipes disponibles pour un sport"""
        teams_db = self.load_teams_database()
        sport_data = teams_db.get(sport, {})
        return sport_data.get("teams", [])

    def get_sport_icon(self, sport: str) -> str:
        """Retourne l'icône d'un sport"""
        teams_db = self.load_teams_database()
        sport_data = teams_db.get(sport, {})
        return sport_data.get("icon", "🏅")

    def lookup_team_by_name(self, sport: str, name: str) -> Optional[dict]:
        """
        Recherche une équipe par son nom ou un de ses aliases.
        Retourne le dict complet de l'équipe avec tous ses aliases.
        """
        teams = self.get_teams_for_sport(sport)
        name_lower = name.lower()

        for team in teams:
            # Vérifier le nom principal
            if team.get("name", "").lower() == name_lower:
                return team
            # Vérifier les aliases
            for alias in team.get("aliases", []):
                if alias.lower() == name_lower:
                    return team

        return None

    def get_available_sports(self) -> list[str]:
        """Retourne la liste des sports disponibles dans la base"""
        teams_db = self.load_teams_database()
        return list(teams_db.keys())

    def get_all_sports_from_preferences(self) -> dict:
        """Retourne tous les sports des préférences (même ceux sans teams_db)"""
        prefs = self.load_preferences()
        return prefs.get("sports", {})

    def is_sport_enabled(self, sport: str) -> bool:
        """Vérifie si un sport est activé dans les préférences"""
        prefs = self.load_preferences()
        return prefs.get("sports", {}).get(sport, {}).get("enabled", False)

    def get_selected_teams(self, sport: str) -> list[dict]:
        """Retourne les équipes sélectionnées par l'utilisateur pour un sport"""
        prefs = self.load_preferences()
        return prefs.get("sports", {}).get(sport, {}).get("teams", [])

    def get_briefing_duration(self) -> str:
        """Retourne le mode de durée du briefing (short/medium/long)"""
        prefs = self.load_preferences()
        return prefs.get("briefing_duration", {}).get("mode", "medium")

    def get_top3_priorities(self) -> list[str]:
        """Retourne les 3 équipes prioritaires"""
        prefs = self.load_preferences()
        priorities = prefs.get("briefing_priorities", {}).get("teams_priorities", {})

        # Filtrer les équipes avec niveau "maximum" ou "high"
        top_teams = []
        for team, config in priorities.items():
            if config.get("level") in ["maximum", "high"]:
                top_teams.append(team)

        return top_teams[:3]

    def _get_default_preferences(self) -> dict:
        """Retourne les préférences par défaut"""
        return {
            "metadata": {"version": "1.0"},
            "general": {"country": "France", "languages": ["fr"]},
            "sports": {},
            "briefing_duration": {"mode": "medium"},
            "briefing_priorities": {"teams_priorities": {}}
        }


# Instance globale (singleton)
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Retourne l'instance unique du ConfigManager"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
