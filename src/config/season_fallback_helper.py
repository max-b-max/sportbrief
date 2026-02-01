"""
Helper pour gérer le fallback de saison quand les APIs n'ont pas encore les données
"""
try:
    from .season_helper import get_current_season
except ImportError:
    from season_helper import get_current_season


def get_previous_season(sport: str) -> str | int:
    """
    Retourne la saison précédente en fonction du sport

    Args:
        sport: Nom du sport

    Returns:
        Saison précédente
    """
    current = get_current_season(sport)

    # Sports avec format "YYYY-YYYY"
    if isinstance(current, str) and "-" in current:
        years = current.split("-")
        prev_start = int(years[0]) - 1
        prev_end = int(years[1]) - 1
        return f"{prev_start}-{prev_end}"

    # Sports avec format année unique
    return current - 1


def get_season_with_fallback(sport: str, prefer_current: bool = True) -> tuple[str | int, str | int]:
    """
    Retourne (saison_préférée, saison_fallback)

    Args:
        sport: Nom du sport
        prefer_current: Si True, préfère la saison actuelle, sinon la précédente

    Returns:
        Tuple (saison primaire, saison fallback)

    Example:
        En janvier 2026 pour basketball:
        - prefer_current=True: ("2025-2026", "2024-2025")
        - prefer_current=False: ("2024-2025", "2025-2026")
    """
    current = get_current_season(sport)
    previous = get_previous_season(sport)

    if prefer_current:
        return (current, previous)
    else:
        return (previous, current)


# Configuration par sport
# True = préférer saison actuelle, False = préférer saison précédente
# TOUS LES SPORTS UTILISENT LA SAISON ACTUELLE
SEASON_PREFERENCES = {
    "basketball": True,   # Utiliser 2025-2026 (saison en cours)
    "football": True,     # Utiliser 2025-2026 (saison en cours)
    "rugby": True,        # Utiliser 2025-2026 (saison en cours)
    "handball": True,     # Utiliser 2025-2026 (saison en cours)
    "volleyball": True,   # Utiliser 2025-2026 (saison en cours)
    "mma": True,          # Utiliser 2026 (saison en cours)
    "formula1": True,     # Utiliser 2026 (saison en cours)
}


def get_best_season(sport: str) -> str | int:
    """
    Retourne la meilleure saison à utiliser pour un sport donné
    en tenant compte des limitations des APIs trial

    Args:
        sport: Nom du sport

    Returns:
        Saison recommandée
    """
    prefer_current = SEASON_PREFERENCES.get(sport, True)
    primary, _ = get_season_with_fallback(sport, prefer_current)
    return primary


if __name__ == "__main__":
    from datetime import datetime

    print("=== SAISONS AVEC FALLBACK ===")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
    print()

    sports = ["basketball", "football", "rugby", "handball", "volleyball", "mma"]

    for sport in sports:
        current = get_current_season(sport)
        previous = get_previous_season(sport)
        best = get_best_season(sport)
        prefer = "actuelle" if SEASON_PREFERENCES.get(sport, True) else "precedente"

        print(f"{sport.capitalize():15} :")
        print(f"  Actuelle:  {current}")
        print(f"  Precedente: {previous}")
        print(f"  Utilisee:  {best} (preference: {prefer})")
        print()
