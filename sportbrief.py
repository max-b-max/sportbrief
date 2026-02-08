#!/usr/bin/env python3
"""
SportBrief - Pipeline unifie
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

# Collectors API par sport
API_COLLECTORS = {
    "football": "src/collect/collect_footballdata.py",
    "basketball": "src/collect/collect_nba.py",
    "formule1": "src/collect/collect_f1.py",
    "biathlon": "src/collect/collect_api_biathlon.py",
    "volleyball": "src/collect/collect_lnv.py",
}

# Pipeline RSS
RSS_PIPELINE = [
    ("Collecte RSS", "src/collect/collect_rss.py"),
    ("Fusion RSS", "src/process/merge_rss.py"),
    ("Normalisation RSS", "src/process/normalize_rss.py"),
    ("Deduplication RSS", "src/process/deduplicate_rss.py"),
]

AGGREGATOR = "src/aggregate/aggregate_data.py"

def load_preferences():
    prefs_file = Path("user_preferences.json")
    if not prefs_file.exists():
        print("[ERREUR] Fichier user_preferences.json introuvable")
        sys.exit(1)
    with open(prefs_file, "r", encoding="utf-8") as f:
        return json.load(f)

def get_enabled_sports(prefs):
    sports = prefs.get("sports", {})
    return [name for name, config in sports.items() if config.get("enabled", False)]

def run_script(name, script_path):
    script = Path(script_path)
    if not script.exists():
        print(f"  [SKIP] {name}: script introuvable")
        return False
    try:
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        if result.returncode != 0:
            print(f"  [ERREUR] {name}")
            if result.stderr:
                for line in result.stderr.strip().split("\n")[:2]:
                    print(f"    {line}")
            return False
        print(f"  [OK] {name}")
        return True
    except Exception as e:
        print(f"  [ERREUR] {name}: {e}")
        return False

def main():
    print("=" * 50)
    print(" SPORTBRIEF")
    print("=" * 50)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    prefs = load_preferences()
    enabled_sports = get_enabled_sports(prefs)
    print(f"Sports: {', '.join(enabled_sports)}")

    # Collecte API
    print("\n--- Collecte API ---")
    for sport in enabled_sports:
        if sport in API_COLLECTORS:
            run_script(sport.capitalize(), API_COLLECTORS[sport])

    # Pipeline RSS
    print("\n--- Pipeline RSS ---")
    for name, script in RSS_PIPELINE:
        run_script(name, script)

    # Agrégation
    print("\n--- Agregation ---")
    run_script("Agregateur", AGGREGATOR)

    print("\n[OK] Pipeline terminé")
    print("  data/processed/aggregated_data.json")

if __name__ == "__main__":
    main()
