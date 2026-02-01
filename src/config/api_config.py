"""
Configuration centrale pour les APIs sportives
Preferences utilisateur hardcodees pour le MVP
"""

import os
from dotenv import load_dotenv

load_dotenv()

# API-SPORTS (multi-sports) - depuis .env
API_SPORTS_KEY = os.getenv("API_SPORTS_KEY", "")

# URLs par sport (versions différentes selon le sport)
API_URLS = {
    "football": "https://v3.football.api-sports.io",
    "basketball": "https://v1.basketball.api-sports.io",
    "volleyball": "https://v1.volleyball.api-sports.io",
    "handball": "https://v1.handball.api-sports.io",
    "rugby": "https://v1.rugby.api-sports.io",
    "formula1": "https://v1.formula-1.api-sports.io",
    "mma": "https://v1.mma.api-sports.io",
}

# Configuration par sport
SPORTS_CONFIG = {
    "biathlon": {
        "source": "biathlonresults",
        "nations": ["FRA"],  # Filtrer uniquement athlètes français
        "max_events": 3,  # Limiter le nombre d'événements
    },

    "football": {
        "source": "api-football",
        "api_key": API_SPORTS_KEY,
        "teams": [
            {"name": "Olympique Marseille", "id": 119, "league_id": 61, "league_name": "Ligue 1"},
            {"name": "Liverpool FC", "id": 40, "league_id": 39, "league_name": "Premier League"},
        ],
        "leagues": [
            {"name": "Ligue 1", "id": 61, "country": "France"},
            {"name": "Premier League", "id": 39, "country": "England"},
            {"name": "La Liga", "id": 140, "country": "Spain"},
            {"name": "Bundesliga", "id": 78, "country": "Germany"},
            {"name": "Serie A", "id": 135, "country": "Italy"},
            {"name": "Champions League", "id": 2, "country": "World"},
            {"name": "Europa League", "id": 3, "country": "World"},
            {"name": "Conference League", "id": 848, "country": "World"},
            {"name": "Euro", "id": 4, "country": "World"},
            {"name": "Coupe du Monde", "id": 1, "country": "World"},
        ],
        "max_games_per_team": 5,  # Derniers 5 matchs par équipe
        "max_games_per_league": 10,  # Derniers résultats par compétition
        "season": 2024,  # Saison en cours
    },

    "basketball": {
        "source": "api-basketball",
        "api_key": API_SPORTS_KEY,
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
            {"id": 189, "name": "Salaun Tidjane", "team_id": 135, "team_name": "Charlotte Hornets"},
        ],
        "leagues": [
            {"name": "NBA", "id": 12, "country": "USA"}
        ],
        "season": "2024-2025",  # Saison en cours
        "max_games_per_player": 5,  # Derniers matchs par joueur français
    },

    "volleyball": {
        "source": "api-volleyball",
        "api_key": API_SPORTS_KEY,
        "season": 2024,  # Saison en cours
        "teams": [
            {"name": "Chaumont", "id": 470, "league_id": 63, "league_name": "Ligue A"},
            {"name": "France", "id": 2201, "is_national_team": True},
        ],
        "leagues": [
            {"name": "Ligue A", "id": 63, "country": "France"},
            {"name": "World Championship", "id": 185, "country": "World"},
            {"name": "World Championship Women", "id": 186, "country": "World"},
            {"name": "Olympic Games", "id": 189, "country": "World"},
        ],
        "max_games_per_team": 5,
        "max_games_per_league": 10,  # Derniers résultats par compétition
    },

    "handball": {
        "source": "api-handball",
        "api_key": API_SPORTS_KEY,
        "season": 2024,  # Saison en cours
        "teams": [
            {"name": "France", "id": 2662, "is_national_team": True}
        ],
        "leagues": [
            {"name": "Starligue", "id": 34, "country": "France"},  # Championnat masculin
            {"name": "Division 1 Women", "id": 29, "country": "France"},  # Championnat féminin
            {"name": "World Championship", "id": 153, "country": "World"},
            {"name": "World Championship Women", "id": 154, "country": "World"},
            {"name": "Olympic Games", "id": 155, "country": "World"},
        ],
        "max_games_per_team": 5,
        "max_games_per_league": 10,  # Derniers résultats par compétition
    },

    "rugby": {
        "source": "api-rugby",
        "api_key": API_SPORTS_KEY,
        "season": 2024,  # Saison en cours
        "teams": [
            {"name": "France", "id": 387, "is_national_team": True},
            # Équipes françaises en Champions Cup
            {"name": "Stade Toulousain", "id": 107, "league_id": 54},
            {"name": "Bordeaux Begles", "id": 96, "league_id": 54},
        ],
        "leagues": [
            {"name": "Top 14", "id": 16, "country": "France"},
            {"name": "Champions Cup", "id": 54, "country": "Europe"},
            {"name": "Six Nations", "id": 51, "country": "Europe"},
            {"name": "Coupe du Monde", "id": 69, "country": "World"},
            {"name": "Coupe du Monde Feminine", "id": 70, "country": "World"}
        ],
        "max_games_per_team": 5,
        "max_games_per_league": 10,  # Derniers résultats par compétition
    },

    "formula1": {
        "source": "api-formula1",
        "api_key": API_SPORTS_KEY,
        "drivers": [],  # Tous les pilotes
        "max_races": 3,  # 3 dernières courses
    },

    "mma": {
        "source": "api-mma",
        "api_key": API_SPORTS_KEY,
        "season": "2024",  # Saison pour récupérer les combats récents
        "fighters": [
            # Combattants français majeurs UFC
            {"name": "Ciryl Gane", "id": 545},  # Heavyweight - Top 5 UFC
            {"name": "Nassourdine Imavov", "id": 831},  # Middleweight - Top 10 UFC
            {"name": "Benoît Saint Denis", "id": 2466},  # Lightweight - Top 15 UFC
            {"name": "Manon Fiorot", "id": 900},  # Women's Flyweight - Top 5 UFC
            # Autres combattants français UFC
            {"name": "Taylor Lapilus", "id": 2145},  # Bantamweight
            {"name": "William Gomis", "id": 2522},  # Featherweight
            {"name": "Farés Ziam", "id": 591},  # Lightweight
            {"name": "Alan Baudot", "id": 857},  # Light Heavyweight
            {"name": "Gadzhi Omargadzhiev", "id": 2490},  # Middleweight
            {"name": "Daria Zhelezniakova", "id": 2627},  # Women's Bantamweight
            {"name": "Stephanie Egger", "id": 858},  # Women's category
            {"name": "Joanne Wood", "id": 18},  # Women's category
        ],
        "organizations": ["UFC"],
        "max_fights_per_fighter": 5,
        "max_recent_fights": 20,  # Nombre de combats récents à collecter
    },

    "tennis": {
        "source": "custom",  # API à déterminer
        "tournaments": [
            "Australian Open",
            "Roland Garros",
            "Wimbledon",
            "US Open",
            "Masters 1000"
        ],
    },

    "pingpong": {
        "source": "custom",  # API à déterminer
        "players": [
            {"name": "Felix Lebrun", "id": None},
            {"name": "Alexis Lebrun", "id": None}
        ],
    }
}


def get_sport_config(sport: str) -> dict:
    """
    Récupère la configuration pour un sport donné

    Args:
        sport: Nom du sport (ex: "football", "basketball", etc.)

    Returns:
        Configuration du sport ou dictionnaire vide si non trouvé
    """
    return SPORTS_CONFIG.get(sport, {})


def get_api_key(sport: str) -> str | None:
    """
    Récupère la clé API pour un sport donné

    Args:
        sport: Nom du sport

    Returns:
        Clé API ou None si non applicable
    """
    config = get_sport_config(sport)
    return config.get("api_key")


def get_api_url(sport: str) -> str | None:
    """
    Récupère l'URL de base de l'API pour un sport

    Args:
        sport: Nom du sport (ex: "football", "basketball")

    Returns:
        URL de base de l'API ou None si non applicable
    """
    return API_URLS.get(sport)
