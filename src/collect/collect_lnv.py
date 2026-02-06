#!/usr/bin/env python3
"""
Collecteur LNV - Calendriers et classements volleyball français
"""

import json
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path("data/raw/lnv")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LNV_FEEDS = {
    "calendrier_lam": "https://www.lnv.fr/xml/calendrier-LAM.xml",
    "calendrier_laf": "https://www.lnv.fr/xml/calendrier-LAF.xml",
    "calendrier_lbm": "https://www.lnv.fr/xml/calendrier-LBM.xml",
    "classement_lam": "https://www.lnv.fr/xml/classement-LAM.xml",
    "classement_laf": "https://www.lnv.fr/xml/classement-LAF.xml",
    "classement_lbm": "https://www.lnv.fr/xml/classement-LBM.xml",
}

LEAGUE_NAMES = {
    "lam": "Ligue A Masculine",
    "laf": "Ligue A Féminine",
    "lbm": "Ligue B Masculine",
}


def parse_calendrier(xml_content: str, league: str) -> dict:
    """Parse le XML calendrier LNV"""
    root = ET.fromstring(xml_content)
    matches = []

    for journee in root.findall(".//Journee"):
        num_journee = journee.get("NumJournee", "")

        for match in journee.findall("Match"):
            # Convertir date DD-MM-YYYY vers YYYY-MM-DD
            raw_date = match.findtext("Date", "")
            formatted_date = raw_date
            if raw_date and "-" in raw_date:
                parts = raw_date.split("-")
                if len(parts) == 3 and len(parts[2]) == 4:  # DD-MM-YYYY
                    formatted_date = f"{parts[2]}-{parts[1]}-{parts[0]}"

            match_data = {
                "journee": num_journee,
                "code": match.findtext("CodeMatch", ""),
                "date": formatted_date,
                "heure": match.findtext("Heure", ""),
                "domicile": match.findtext("EquipeDomicile", ""),
                "exterieur": match.findtext("EquipeExterieur", ""),
                "score": match.findtext("Score", ""),
                "sets": [
                    match.findtext("Set1", ""),
                    match.findtext("Set2", ""),
                    match.findtext("Set3", ""),
                    match.findtext("Set4", ""),
                    match.findtext("Set5", ""),
                ],
                "points_domicile": match.findtext("PointsEquipeDomicile", ""),
                "points_exterieur": match.findtext("PointsEquipeExterieur", ""),
            }
            matches.append(match_data)

    return {
        "type": "calendrier",
        "league": LEAGUE_NAMES.get(league, league),
        "league_code": league.upper(),
        "fetched_at": datetime.utcnow().isoformat(),
        "matches": matches,
    }


def parse_classement(xml_content: str, league: str) -> dict:
    """Parse le XML classement LNV"""
    root = ET.fromstring(xml_content)
    teams = []

    for equipe in root.findall(".//Equipe"):
        team_data = {
            "rang": int(equipe.findtext("Rang", "0")),
            "nom": equipe.get("NomClub", ""),
            "code": equipe.get("NumClub", ""),
            "points": int(equipe.findtext("Points", "0")),
            "matchs_joues": int(equipe.findtext("MatchsJoues", "0")),
            "matchs_gagnes": int(equipe.findtext("MatchsGagnes", "0")),
            "matchs_perdus": int(equipe.findtext("MatchsPerdus", "0")),
            "sets_pour": int(equipe.findtext("SetPour", "0")),
            "sets_contre": int(equipe.findtext("SetContre", "0")),
            "points_pour": int(equipe.findtext("PointsPour", "0")),
            "points_contre": int(equipe.findtext("PointsContre", "0")),
        }
        teams.append(team_data)

    # Trier par rang
    teams.sort(key=lambda x: x["rang"])

    return {
        "type": "classement",
        "league": LEAGUE_NAMES.get(league, league),
        "league_code": league.upper(),
        "fetched_at": datetime.utcnow().isoformat(),
        "teams": teams,
    }


def collect_lnv(name: str, url: str) -> dict:
    """Collecte et parse un flux LNV"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # Déterminer le type (calendrier ou classement) et la ligue
        parts = name.split("_")
        feed_type = parts[0]  # calendrier ou classement
        league = parts[1]  # lam, laf, lbm

        if feed_type == "calendrier":
            return parse_calendrier(response.text, league)
        else:
            return parse_classement(response.text, league)

    except Exception as e:
        print(f"[ERREUR] {name}: {e}")
        return {"error": str(e), "fetched_at": datetime.utcnow().isoformat()}


def main():
    print("=== Collecte LNV Volleyball ===")

    for name, url in LNV_FEEDS.items():
        data = collect_lnv(name, url)

        output_file = OUTPUT_DIR / f"{name}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        if "error" not in data:
            if data["type"] == "calendrier":
                print(f"[OK] {name}: {len(data['matches'])} matchs")
            else:
                print(f"[OK] {name}: {len(data['teams'])} équipes")
        else:
            print(f"[ERREUR] {name}")


if __name__ == "__main__":
    main()
