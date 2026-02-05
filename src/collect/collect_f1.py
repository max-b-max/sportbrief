"""
Collector Formula 1 utilisant OpenF1 API
API gratuite - pas de clé nécessaire pour données historiques

Données disponibles:
- Calendrier des courses
- Résultats des sessions (qualifs, courses)
- Pilotes et équipes
- Classements
"""

import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import requests

# Configuration
OUTPUT_DIR = Path("data/raw/api/f1")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://api.openf1.org/v1"
REQUEST_DELAY = 1  # seconde entre requêtes

# Année en cours
CURRENT_YEAR = datetime.now().year


def make_api_request(endpoint: str, params: Optional[dict] = None) -> list:
    """
    Effectue une requête à l'API OpenF1

    Args:
        endpoint: Endpoint (ex: "/meetings")
        params: Paramètres de la requête

    Returns:
        Liste de résultats JSON
    """
    url = f"{BASE_URL}{endpoint}"

    try:
        time.sleep(REQUEST_DELAY)
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"  [ERROR] Erreur API {endpoint}: {e}")
        return []


def collect_calendar(year: int = CURRENT_YEAR) -> list[dict]:
    """
    Collecte le calendrier des Grand Prix

    Args:
        year: Année du calendrier

    Returns:
        Liste des GP
    """
    data = []

    print(f"  [INFO] Calendrier {year}...")
    meetings = make_api_request("/meetings", {"year": year})

    for meeting in meetings:
        # Filtrer les tests (garder uniquement les GP)
        meeting_name = meeting.get("meeting_name", "")
        if "Testing" in meeting_name:
            continue

        gp_data = {
            "sport": "formula1",
            "source": "openf1",
            "type": "calendar",
            "year": year,
            "meeting_key": meeting.get("meeting_key"),
            "meeting_name": meeting_name,
            "country": meeting.get("country_name"),
            "circuit": meeting.get("circuit_short_name"),
            "date_start": meeting.get("date_start"),
            "gmt_offset": meeting.get("gmt_offset"),
        }
        data.append(gp_data)

    print(f"  [OK] {len(data)} Grand Prix")
    return data


def collect_drivers(year: int = CURRENT_YEAR) -> list[dict]:
    """
    Collecte la liste des pilotes

    Args:
        year: Année

    Returns:
        Liste des pilotes
    """
    data = []

    print(f"  [INFO] Pilotes {year}...")

    # Récupérer la dernière session de l'année pour avoir les pilotes actuels
    sessions = make_api_request("/sessions", {"year": year})

    if not sessions:
        print("  [WARNING] Pas de sessions trouvees")
        return data

    # Prendre la dernière session
    last_session = sessions[-1]
    session_key = last_session.get("session_key")

    # Récupérer les pilotes de cette session
    drivers = make_api_request("/drivers", {"session_key": session_key})

    seen_drivers = set()
    for driver in drivers:
        driver_number = driver.get("driver_number")
        if driver_number in seen_drivers:
            continue
        seen_drivers.add(driver_number)

        driver_data = {
            "sport": "formula1",
            "source": "openf1",
            "type": "driver",
            "year": year,
            "driver_number": driver_number,
            "full_name": driver.get("full_name"),
            "name_acronym": driver.get("name_acronym"),
            "team_name": driver.get("team_name"),
            "team_colour": driver.get("team_colour"),
            "country_code": driver.get("country_code"),
            "headshot_url": driver.get("headshot_url"),
        }
        data.append(driver_data)

    # Identifier les pilotes français
    french_drivers = [d for d in data if d.get("country_code") == "FRA"]
    print(f"  [OK] {len(data)} pilotes ({len(french_drivers)} francais)")

    return data


def collect_recent_results(year: int = CURRENT_YEAR, limit: int = 3) -> list[dict]:
    """
    Collecte les résultats des dernières courses

    Args:
        year: Année
        limit: Nombre de courses à récupérer

    Returns:
        Liste des résultats
    """
    data = []

    print(f"  [INFO] Resultats des {limit} dernieres courses...")

    # Récupérer les meetings de l'année
    meetings = make_api_request("/meetings", {"year": year})

    # Filtrer les GP passés (date < aujourd'hui) et exclure les tests
    now = datetime.now()
    past_gps = []
    for m in meetings:
        if "Testing" in m.get("meeting_name", ""):
            continue
        date_str = m.get("date_start", "")
        if date_str:
            try:
                meeting_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                if meeting_date.replace(tzinfo=None) < now:
                    past_gps.append(m)
            except:
                pass

    # Prendre les derniers GP
    recent_gps = past_gps[-limit:] if len(past_gps) > limit else past_gps

    for gp in recent_gps:
        meeting_key = gp.get("meeting_key")
        meeting_name = gp.get("meeting_name")

        # Récupérer les sessions de ce GP
        sessions = make_api_request("/sessions", {"meeting_key": meeting_key})

        # Trouver la session "Race"
        race_session = None
        for s in sessions:
            if s.get("session_name") == "Race":
                race_session = s
                break

        if not race_session:
            continue

        session_key = race_session.get("session_key")

        # Récupérer les positions finales
        # OpenF1 utilise /position pour les positions en temps réel
        # Pour le résultat final, on utilise la dernière position de chaque pilote
        positions = make_api_request("/position", {"session_key": session_key})

        if not positions:
            continue

        # Grouper par pilote et prendre la dernière position
        driver_positions = {}
        for pos in positions:
            driver_num = pos.get("driver_number")
            driver_positions[driver_num] = pos

        # Convertir en liste triée par position
        final_positions = sorted(
            driver_positions.values(),
            key=lambda x: x.get("position", 99)
        )

        for pos in final_positions[:10]:  # Top 10
            result_data = {
                "sport": "formula1",
                "source": "openf1",
                "type": "race_result",
                "year": year,
                "meeting_key": meeting_key,
                "meeting_name": meeting_name,
                "session_key": session_key,
                "date": race_session.get("date_start", "")[:10],
                "position": pos.get("position"),
                "driver_number": pos.get("driver_number"),
            }
            data.append(result_data)

        print(f"    [OK] {meeting_name}: {len(final_positions)} pilotes")

    print(f"  [OK] {len(data)} resultats collectes")
    return data


def collect_upcoming_races(year: int = CURRENT_YEAR) -> list[dict]:
    """
    Collecte les prochaines courses

    Args:
        year: Année

    Returns:
        Liste des prochaines courses
    """
    data = []

    print(f"  [INFO] Prochaines courses {year}...")

    meetings = make_api_request("/meetings", {"year": year})

    now = datetime.now()

    for m in meetings:
        if "Testing" in m.get("meeting_name", ""):
            continue

        date_str = m.get("date_start", "")
        if date_str:
            try:
                meeting_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                if meeting_date.replace(tzinfo=None) > now:
                    race_data = {
                        "sport": "formula1",
                        "source": "openf1",
                        "type": "upcoming_race",
                        "year": year,
                        "meeting_key": m.get("meeting_key"),
                        "meeting_name": m.get("meeting_name"),
                        "country": m.get("country_name"),
                        "circuit": m.get("circuit_short_name"),
                        "date_start": date_str,
                    }
                    data.append(race_data)
            except:
                pass

    print(f"  [OK] {len(data)} courses a venir")
    return data


def main():
    """Fonction principale de collecte F1"""

    print("=" * 50)
    print("FORMULA 1 COLLECTOR (OpenF1)")
    print("=" * 50)
    print(f"Annee: {CURRENT_YEAR}")

    all_data = {
        "calendar": [],
        "drivers": [],
        "recent_results": [],
        "upcoming_races": [],
    }

    # 1. Calendrier
    print("\n[1/4] CALENDRIER")
    all_data["calendar"] = collect_calendar(CURRENT_YEAR)

    # 2. Pilotes
    print("\n[2/4] PILOTES")
    # Essayer l'année en cours, sinon année précédente
    all_data["drivers"] = collect_drivers(CURRENT_YEAR)
    if not all_data["drivers"]:
        print("  [INFO] Pas de pilotes pour 2026, essai avec 2025...")
        all_data["drivers"] = collect_drivers(CURRENT_YEAR - 1)

    # 3. Résultats récents
    print("\n[3/4] RESULTATS RECENTS")
    all_data["recent_results"] = collect_recent_results(CURRENT_YEAR, limit=3)
    if not all_data["recent_results"] and CURRENT_YEAR > 2025:
        print("  [INFO] Pas de resultats 2026, essai avec 2025...")
        all_data["recent_results"] = collect_recent_results(CURRENT_YEAR - 1, limit=3)

    # 4. Prochaines courses
    print("\n[4/4] PROCHAINES COURSES")
    all_data["upcoming_races"] = collect_upcoming_races(CURRENT_YEAR)

    # Résumé
    print(f"\n{'=' * 50}")
    print("RESUME:")
    print(f"  - Calendrier: {len(all_data['calendar'])} GP")
    print(f"  - Pilotes: {len(all_data['drivers'])}")
    print(f"  - Resultats: {len(all_data['recent_results'])}")
    print(f"  - A venir: {len(all_data['upcoming_races'])}")

    # Sauvegarder
    payload = {
        "source": "openf1",
        "sport": "formula1",
        "year": CURRENT_YEAR,
        "fetched_at": datetime.utcnow().isoformat(),
        "stats": {
            "total_gp": len(all_data["calendar"]),
            "total_drivers": len(all_data["drivers"]),
            "total_results": len(all_data["recent_results"]),
            "total_upcoming": len(all_data["upcoming_races"]),
        },
        "data": all_data,
    }

    output_file = OUTPUT_DIR / "f1_data.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Donnees sauvegardees dans {output_file}")


if __name__ == "__main__":
    main()
