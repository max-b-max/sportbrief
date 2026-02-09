#!/usr/bin/env python3
"""
SportBrief - Pipeline unifie
Usage:
    python sportbrief.py              # Collecte + Agregation seulement
    python sportbrief.py --briefing   # + Generation briefing texte
    python sportbrief.py --audio      # + Generation audio (implique --briefing)
    python sportbrief.py -a           # Raccourci pour --audio
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Charger les variables d'environnement depuis .env
from dotenv import load_dotenv
load_dotenv()


# =============================================================================
# CONFIGURATION
# =============================================================================

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

# Agregation et synthese
AGGREGATOR = "src/aggregate/aggregate_data.py"
BRIEFING_GENERATOR = "src/synthesize/generate_briefing.py"
AUDIO_GENERATOR = "src/synthesize/generate_audio.py"


# =============================================================================
# UTILS
# =============================================================================

def load_preferences() -> dict:
    """Charge les preferences utilisateur"""
    prefs_file = Path("user_preferences.json")
    if not prefs_file.exists():
        print("[ERREUR] Fichier user_preferences.json introuvable")
        sys.exit(1)
    with open(prefs_file, "r", encoding="utf-8") as f:
        return json.load(f)


def get_enabled_sports(prefs: dict) -> list[str]:
    """Retourne les sports actives"""
    sports = prefs.get("sports", {})
    return [name for name, config in sports.items() if config.get("enabled", False)]


def run_script(name: str, script_path: str, quiet: bool = False) -> bool:
    """Execute un script Python"""
    script = Path(script_path)
    if not script.exists():
        if not quiet:
            print(f"  [SKIP] {name}: script introuvable")
        return False

    try:
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

        if result.returncode != 0:
            print(f"  [ERREUR] {name}")
            if result.stderr:
                # Afficher seulement les 2 premieres lignes d'erreur
                for line in result.stderr.strip().split("\n")[:2]:
                    print(f"    {line}")
            return False

        print(f"  [OK] {name}")
        return True

    except Exception as e:
        print(f"  [ERREUR] {name}: {e}")
        return False


def print_header(title: str):
    """Affiche un header de section"""
    print()
    print("=" * 50)
    print(f" {title}")
    print("=" * 50)


def print_section(title: str):
    """Affiche un titre de sous-section"""
    print()
    print(f"--- {title} ---")


# =============================================================================
# PIPELINE STEPS
# =============================================================================

def step_collect_api(enabled_sports: list[str]) -> dict:
    """Etape 1: Collecte des donnees API"""
    print_section("Collecte API")

    stats = {"success": 0, "failed": 0, "skipped": 0}

    for sport in enabled_sports:
        if sport in API_COLLECTORS:
            if run_script(sport.capitalize(), API_COLLECTORS[sport]):
                stats["success"] += 1
            else:
                stats["failed"] += 1
        else:
            stats["skipped"] += 1

    return stats


def step_collect_rss() -> bool:
    """Etape 2: Pipeline RSS complet"""
    print_section("Pipeline RSS")

    for name, script in RSS_PIPELINE:
        if not run_script(name, script):
            return False
    return True


def step_aggregate() -> bool:
    """Etape 3: Agregation des donnees"""
    print_section("Agregation")
    return run_script("Agregateur", AGGREGATOR)


def step_briefing(debug: bool = False) -> bool:
    """Etape 4: Generation du briefing LLM"""
    print_section("Briefing LLM")
    script = Path(BRIEFING_GENERATOR)
    if not script.exists():
        print(f"  [SKIP] Briefing: script introuvable")
        return False

    try:
        cmd = [sys.executable, str(script)]
        if debug:
            cmd.append("--debug")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

        if result.returncode != 0:
            print(f"  [ERREUR] Briefing LLM")
            return False

        print(f"  [OK] Gemini")
        return True

    except Exception as e:
        print(f"  [ERREUR] Briefing: {e}")
        return False


def step_audio() -> bool:
    """Etape 5: Generation audio TTS"""
    print_section("Audio TTS")
    return run_script("Edge TTS", AUDIO_GENERATOR)


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="SportBrief - Pipeline unifie",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python sportbrief.py           # Collecte + Agregation
  python sportbrief.py -b        # + Briefing texte
  python sportbrief.py -a        # + Briefing + Audio
  python sportbrief.py -a -d     # + Audio + Debug (sauvegarde prompt)
        """
    )
    parser.add_argument("-b", "--briefing", action="store_true",
                        help="Generer le briefing texte (LLM)")
    parser.add_argument("-a", "--audio", action="store_true",
                        help="Generer l'audio (implique --briefing)")
    parser.add_argument("-d", "--debug", action="store_true",
                        help="Sauvegarder le prompt LLM dans debug_prompt.txt")
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="Mode silencieux")
    args = parser.parse_args()

    # --audio implique --briefing
    if args.audio:
        args.briefing = True

    # Header
    print_header("SPORTBRIEF")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    # Charger preferences
    prefs = load_preferences()
    enabled_sports = get_enabled_sports(prefs)
    print(f"Sports: {', '.join(enabled_sports)}")

    # Stats
    results = {
        "api": None,
        "rss": False,
        "aggregate": False,
        "briefing": False,
        "audio": False,
    }

    # === ETAPE 1: Collecte API ===
    results["api"] = step_collect_api(enabled_sports)

    # === ETAPE 2: Pipeline RSS ===
    results["rss"] = step_collect_rss()

    # === ETAPE 3: Agregation ===
    results["aggregate"] = step_aggregate()

    # === ETAPE 4: Briefing (optionnel) ===
    if args.briefing:
        results["briefing"] = step_briefing(debug=args.debug)

    # === ETAPE 5: Audio (optionnel) ===
    if args.audio and results["briefing"]:
        results["audio"] = step_audio()

    # === RESUME ===
    print_header("RESUME")

    api = results["api"]
    print(f"API:        {api['success']} OK, {api['failed']} erreurs, {api['skipped']} sans API")
    print(f"RSS:        {'OK' if results['rss'] else 'ERREUR'}")
    print(f"Agregation: {'OK' if results['aggregate'] else 'ERREUR'}")

    if args.briefing:
        print(f"Briefing:   {'OK' if results['briefing'] else 'ERREUR'}")
    if args.audio:
        print(f"Audio:      {'OK' if results['audio'] else 'ERREUR'}")

    # Fichiers generes
    print()
    print("Fichiers:")
    print("  data/processed/aggregated_data.json")
    if results["briefing"]:
        print("  data/output/briefing_latest.txt")
    if results["audio"]:
        print("  data/output/briefing_latest.mp3")

    print()


if __name__ == "__main__":
    main()
