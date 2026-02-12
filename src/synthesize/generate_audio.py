"""
Module TTS SportBrief
Convertit le briefing texte en audio MP3 avec Edge TTS
"""

import asyncio
import sys
from pathlib import Path

try:
    import edge_tts
except ImportError:
    print("[ERROR] edge-tts non installe. Installez avec: pip install edge-tts")
    sys.exit(1)


# Configuration
INPUT_FILE = Path("data/output/briefing_latest.txt")
OUTPUT_DIR = Path("data/output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Voix francaise - Henri (homme)
VOICE = "fr-FR-HenriNeural"

# Vitesse de lecture (1.0 = normal, 1.1 = legèrement plus rapide)
RATE = "+0%"


async def text_to_speech(text: str, output_path: Path, voice: str = VOICE, rate: str = RATE, max_retries: int = 3) -> bool:
    """
    Convertit le texte en audio MP3 avec retry en cas d'erreur reseau

    Args:
        text: Texte a convertir
        output_path: Chemin du fichier MP3 de sortie
        voice: Voix Edge TTS a utiliser
        rate: Vitesse de lecture (+X% ou -X%)
        max_retries: Nombre de tentatives en cas d'erreur

    Returns:
        True si succes, False sinon
    """
    for attempt in range(max_retries):
        try:
            communicate = edge_tts.Communicate(text, voice, rate=rate)
            await communicate.save(str(output_path))
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                print(f"[WARN] Tentative {attempt + 1}/{max_retries} echouee, retry dans {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                print(f"[ERROR] Erreur TTS apres {max_retries} tentatives: {e}")
                return False
    return False


def load_briefing() -> str:
    """Charge le briefing texte"""
    if not INPUT_FILE.exists():
        print(f"[ERROR] Fichier {INPUT_FILE} introuvable")
        print("        Lancez d'abord: python src/synthesize/generate_briefing.py")
        return ""

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        return f.read()


def generate_audio(voice: str = None, rate: str = None) -> Path | None:
    """
    Genere l'audio du briefing

    Args:
        voice: Voix a utiliser (defaut: fr-FR-HenriNeural)
        rate: Vitesse de lecture (defaut: +0%)

    Returns:
        Chemin du fichier MP3 genere ou None si erreur
    """
    print("=" * 50)
    print("SPORTBRIEF - GENERATION AUDIO")
    print("=" * 50)

    # Charger le briefing
    print("\n[INFO] Chargement du briefing...")
    text = load_briefing()
    if not text:
        return None

    word_count = len(text.split())
    print(f"[INFO] Mots: {word_count}")
    print(f"[INFO] Duree estimee: {word_count / 150:.1f} minutes")

    # Configuration
    use_voice = voice or VOICE
    use_rate = rate or RATE
    print(f"[INFO] Voix: {use_voice}")
    print(f"[INFO] Vitesse: {use_rate}")

    # Generer l'audio (uniquement latest, pas de fichiers horodates)
    print("\n[INFO] Generation audio en cours...")

    output_file = OUTPUT_DIR / "briefing_latest.mp3"

    # Executer la conversion async
    success = asyncio.run(text_to_speech(text, output_file, use_voice, use_rate))

    if not success:
        print("[ERROR] Echec de la generation audio")
        return None

    # Stats
    file_size = output_file.stat().st_size / 1024 / 1024  # MB

    print(f"\n{'=' * 50}")
    print("AUDIO GENERE")
    print("=" * 50)
    print(f"Taille: {file_size:.2f} MB")
    print(f"\n[OK] Sauvegarde dans {output_file}")

    return output_file


def list_voices():
    """Liste les voix francaises disponibles"""
    async def get_voices():
        voices = await edge_tts.list_voices()
        french_voices = [v for v in voices if v["Locale"].startswith("fr-")]
        return french_voices

    voices = asyncio.run(get_voices())

    print("Voix francaises disponibles:")
    print("-" * 60)
    for v in voices:
        gender = "Homme" if v["Gender"] == "Male" else "Femme"
        print(f"  {v['ShortName']:30} ({gender})")


def main():
    """Fonction principale"""
    import argparse

    parser = argparse.ArgumentParser(description="SportBrief TTS - Generation audio")
    parser.add_argument("--voice", "-v", help="Voix Edge TTS (defaut: fr-FR-HenriNeural)")
    parser.add_argument("--rate", "-r", help="Vitesse: +10%%, -10%%, etc. (defaut: +0%%)")
    parser.add_argument("--list-voices", "-l", action="store_true", help="Liste les voix FR disponibles")

    args = parser.parse_args()

    if args.list_voices:
        list_voices()
        return

    output = generate_audio(voice=args.voice, rate=args.rate)

    if output:
        print(f"\n[OK] Audio disponible: {output}")


if __name__ == "__main__":
    main()
