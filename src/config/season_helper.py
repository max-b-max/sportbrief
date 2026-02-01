"""
Helper pour déterminer automatiquement la saison actuelle
selon le sport et la date
"""
from datetime import datetime


def get_current_season(sport: str) -> str | int:
    """
    Retourne la saison actuelle en fonction du sport

    Args:
        sport: Nom du sport (football, basketball, rugby, etc.)

    Returns:
        Saison actuelle (format dépend du sport)

    Examples:
        En janvier 2026:
        - basketball/nba: "2025-2026"
        - football: 2025
        - rugby: 2025
    """
    now = datetime.now()
    current_year = now.year
    current_month = now.month

    # Sports avec saison sur 2 années (format "YYYY-YYYY")
    # Basketball: Octobre à Juin
    if sport.lower() in ["basketball", "nba"]:
        if current_month >= 10:
            # Oct-Déc: saison YYYY-(YYYY+1)
            return f"{current_year}-{current_year + 1}"
        else:
            # Jan-Sep: saison (YYYY-1)-YYYY
            return f"{current_year - 1}-{current_year}"

    # Football européen: Août à Mai (format YYYY-YYYY)
    elif sport.lower() in ["football", "soccer"]:
        if current_month >= 8:
            # Août-Déc: saison YYYY-(YYYY+1)
            return f"{current_year}-{current_year + 1}"
        else:
            # Jan-Juil: saison (YYYY-1)-YYYY (commencée en août YYYY-1)
            return f"{current_year - 1}-{current_year}"

    # Rugby (hémisphère nord): Septembre à Juin (format YYYY-YYYY)
    elif sport.lower() in ["rugby"]:
        if current_month >= 9:
            # Sep-Déc: saison YYYY-(YYYY+1)
            return f"{current_year}-{current_year + 1}"
        else:
            # Jan-Août: saison (YYYY-1)-YYYY (commencée en sep YYYY-1)
            return f"{current_year - 1}-{current_year}"

    # Handball européen: Septembre à Juin (format YYYY-YYYY)
    elif sport.lower() in ["handball"]:
        if current_month >= 9:
            # Sep-Déc: saison YYYY-(YYYY+1)
            return f"{current_year}-{current_year + 1}"
        else:
            # Jan-Août: saison (YYYY-1)-YYYY
            return f"{current_year - 1}-{current_year}"

    # Volleyball: Octobre à Mai (format YYYY-YYYY)
    elif sport.lower() in ["volleyball", "volley"]:
        if current_month >= 10:
            # Oct-Déc: saison YYYY-(YYYY+1)
            return f"{current_year}-{current_year + 1}"
        else:
            # Jan-Sep: saison (YYYY-1)-YYYY
            return f"{current_year - 1}-{current_year}"

    # Sports avec saison calendaire (Jan-Déc)
    # MMA, F1, Tennis, etc.
    else:
        return current_year


def format_season_display(sport: str, season: str | int) -> str:
    """
    Formate l'affichage de la saison pour les logs

    Args:
        sport: Nom du sport
        season: Saison (int ou str)

    Returns:
        Chaîne formatée pour affichage

    Examples:
        - "2025-2026" (basketball)
        - "2025/2026" (football)
        - "2025" (autres)
    """
    if isinstance(season, str) and "-" in season:
        # Format YYYY-YYYY
        parts = season.split("-")
        if len(parts) == 2:
            return f"{parts[0]}/{parts[1]}"

    return str(season)


# Export des saisons actuelles pour utilisation directe
CURRENT_BASKETBALL_SEASON = get_current_season("basketball")
CURRENT_FOOTBALL_SEASON = get_current_season("football")
CURRENT_RUGBY_SEASON = get_current_season("rugby")
CURRENT_HANDBALL_SEASON = get_current_season("handball")
CURRENT_VOLLEYBALL_SEASON = get_current_season("volleyball")
CURRENT_MMA_SEASON = get_current_season("mma")


if __name__ == "__main__":
    # Test et affichage des saisons actuelles
    print("=== SAISONS ACTUELLES ===")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
    print()

    sports = ["basketball", "football", "rugby", "handball", "volleyball", "mma", "tennis"]

    for sport in sports:
        season = get_current_season(sport)
        display = format_season_display(sport, season)
        print(f"{sport.capitalize():15} : {season:15} (affichage: {display})")
