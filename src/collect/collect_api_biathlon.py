import json
import sys
from datetime import datetime, date
from pathlib import Path

import biathlonresults

# Ajouter le répertoire parent au path pour importer config
sys.path.append(str(Path(__file__).parent.parent))
from config import get_sport_config


# Saison

def get_current_biathlon_season(today: date | None = None) -> str:
    """
    Retourne la saison de biathlon courante au format 'YYZZ'
    Ex : '2425' pour la saison 2024-2025
    """
    if today is None:
        today = date.today()

    year = today.year

    # Saison de biathlon : automne -> printemps
    if today.month >= 8:  # août à décembre
        start_year = year
        end_year = year + 1
    else:  # janvier à juillet
        start_year = year - 1
        end_year = year

    return f"{str(start_year)[-2:]}{str(end_year)[-2:]}"


# Configuration

OUTPUT_DIR = Path("data/raw/api/biathlon")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Charger la configuration depuis le fichier central
CONFIG = get_sport_config("biathlon")
NATIONS_FILTER = CONFIG.get("nations", [])  # ["FRA"]
MAX_EVENTS = CONFIG.get("max_events", 3)

SEASON = get_current_biathlon_season()
LEVEL = biathlonresults.consts.LevelType.BMW_IBU_WC


# Collecte

def collect_biathlon_results(
    season: str,
    level,
    max_events: int | None = None,
    nations_filter: list[str] | None = None
) -> list[dict]:
    """
    Collecte les résultats de biathlon pour une saison et un niveau donnés.

    Args:
        season: Saison au format 'YYZZ' (ex: '2425')
        level: Niveau de compétition
        max_events: Nombre maximum d'événements à collecter
        nations_filter: Liste des codes pays à filtrer (ex: ["FRA", "NOR"])
                       Si None, collecte toutes les nations

    Returns:
        Liste des résultats filtrés
    """
    data: list[dict] = []

    try:
        events = biathlonresults.events(season, level=level)
        if max_events:
            events = events[:max_events]

        for event in events:
            try:
                competitions = biathlonresults.competitions(event["EventId"])

                for race in competitions:
                    try:
                        results = biathlonresults.results(race_id=race["RaceId"])

                        for result in results.get("Results", []):
                            nation = result.get("Nat")

                            # Filtrer par nations si spécifié
                            if nations_filter and nation not in nations_filter:
                                continue

                            data.append({
                                "sport": "biathlon",
                                "season": season,
                                "event": event.get("ShortDescription"),
                                "race": race.get("ShortDescription"),
                                "race_date": race.get("StartTime"),
                                "athlete": result.get("ShortName"),
                                "nation": nation,
                                "rank": result.get("Rank"),
                                "shooting": result.get("Shootings"),
                                "time": result.get("TotalTime") or result.get("Behind"),
                            })

                    except Exception as e:
                        print(f"[WARNING] Erreur sur la course {race.get('ShortDescription', 'unknown')}: {e}")
                        continue

            except Exception as e:
                print(f"[WARNING] Erreur sur l'evenement {event.get('ShortDescription', 'unknown')}: {e}")
                continue

    except Exception as e:
        print(f"[ERROR] Erreur lors de la collecte biathlon: {e}")

    return data


# Main

def main():
    results = collect_biathlon_results(
        season=SEASON,
        level=LEVEL,
        max_events=MAX_EVENTS,
        nations_filter=NATIONS_FILTER
    )

    payload = {
        "source": "biathlonresults",
        "sport": "biathlon",
        "season": SEASON,
        "level": "BMW IBU World Cup",
        "fetched_at": datetime.utcnow().isoformat(),
        "count": len(results),
        "data": results,
    }

    output_file = OUTPUT_DIR / "biathlon_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    nations_info = f" (nations: {', '.join(NATIONS_FILTER)})" if NATIONS_FILTER else ""
    print(f"[OK] Biathlon : {payload['count']} resultats collectes pour la saison {SEASON}{nations_info}")


if __name__ == "__main__":
    main()