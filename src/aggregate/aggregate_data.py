"""
Agregateur de donnees SportBrief
Fusionne les donnees RSS et API en un format unifie
"""

import json
from datetime import datetime
from pathlib import Path

RAW_DATA_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def load_rss_data():
    """Charge les données RSS dédupliquées"""
    rss_file = PROCESSED_DIR / "deduplicated_rss.json"
    if not rss_file.exists():
        return []
    with open(rss_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("articles", [])

def load_api_data():
    """Charge toutes les données API disponibles"""
    api_dir = RAW_DATA_DIR / "api"
    all_data = {}
    if not api_dir.exists():
        return all_data
    for sport_dir in api_dir.iterdir():
        if sport_dir.is_dir():
            for json_file in sport_dir.glob("*.json"):
                with open(json_file, "r", encoding="utf-8") as f:
                    all_data[f"{sport_dir.name}/{json_file.name}"] = json.load(f)
    return all_data

def main():
    print("[INFO] Chargement des données RSS...")
    rss_articles = load_rss_data()
    print(f"  {len(rss_articles)} articles RSS")

    print("[INFO] Chargement des données API...")
    api_data = load_api_data()
    print(f"  {len(api_data)} sources API")

    aggregated = {
        "aggregated_at": datetime.utcnow().isoformat(),
        "rss": {"total": len(rss_articles), "articles": rss_articles},
        "api": api_data,
    }

    output_file = PROCESSED_DIR / "aggregated_data.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(aggregated, f, indent=2, ensure_ascii=False)

    print(f"[OK] Données agrégées dans {output_file}")

if __name__ == "__main__":
    main()
