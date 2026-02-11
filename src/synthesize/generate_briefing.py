"""
Module LLM SportBrief
Genere le briefing sportif a partir des donnees agregees
"""

import json
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

try:
    import google.generativeai as genai
except ImportError:
    print("[ERROR] google-generativeai non installe")
    exit(1)

INPUT_FILE = Path("data/processed/aggregated_data.json")
OUTPUT_DIR = Path("data/output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SYSTEM_PROMPT = """Tu es un journaliste sportif francais qui presente un briefing audio quotidien.

Ton style:
- Ton dynamique et professionnel
- Phrases courtes adaptees a l'audio
- Transitions fluides entre les sports

Structure:
1. Introduction (date, accroche)
2. Résultats des matchs
3. Actualités par sport
4. Conclusion

Contrainte: le briefing doit faire environ 450 mots (3 minutes de lecture).
Utilise UNIQUEMENT les données fournies, ne jamais inventer de scores.
"""

def load_data():
    if not INPUT_FILE.exists():
        print(f"[ERROR] {INPUT_FILE} introuvable")
        return None
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def generate(data):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[ERROR] GEMINI_API_KEY non configurée dans .env")
        return None

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash-lite")

    prompt = f"""{SYSTEM_PROMPT}

Voici les données sportives du jour:

{json.dumps(data, indent=2, ensure_ascii=False)[:15000]}
"""

    response = model.generate_content(prompt)
    return response.text

def main():
    print("=" * 50)
    print("SPORTBRIEF - GENERATION BRIEFING")
    print("=" * 50)

    data = load_data()
    if not data:
        return

    print("[INFO] Appel Gemini en cours...")
    briefing = generate(data)

    if not briefing:
        print("[ERROR] Pas de réponse du LLM")
        return

    output_file = OUTPUT_DIR / "briefing_latest.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(briefing)

    word_count = len(briefing.split())
    print(f"[OK] Briefing généré: {word_count} mots")
    print(f"     Durée estimée: {word_count / 150:.1f} min")
    print(f"     Fichier: {output_file}")

if __name__ == "__main__":
    main()
