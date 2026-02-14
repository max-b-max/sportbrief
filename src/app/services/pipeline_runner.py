"""
Pipeline Runner pour SportBrief Streamlit App
Gère l'exécution du pipeline et la récupération des résultats
"""

import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional
import time


# Chemin vers le script principal
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
SPORTBRIEF_SCRIPT = PROJECT_ROOT / "sportbrief.py"
OUTPUT_DIR = PROJECT_ROOT / "data" / "output"


@dataclass
class PipelineResult:
    """Résultat de l'exécution du pipeline"""
    success: bool
    error: Optional[str] = None
    duration: float = 0.0


class PipelineRunner:
    """Gestionnaire d'exécution du pipeline SportBrief"""

    def __init__(self, output_dir: Path = OUTPUT_DIR):
        self.output_dir = output_dir
        self.script_path = SPORTBRIEF_SCRIPT

    def run_pipeline(self, with_audio: bool = True) -> PipelineResult:
        """
        Exécute le pipeline SportBrief.

        Args:
            with_audio: Si True, génère aussi l'audio (-a flag)

        Returns:
            PipelineResult avec success, error et duration
        """
        start_time = time.time()

        # Construire la commande
        cmd = [sys.executable, str(self.script_path)]
        if with_audio:
            cmd.append("-a")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(PROJECT_ROOT),
                timeout=300  # 5 minutes max
            )

            duration = time.time() - start_time

            if result.returncode == 0:
                return PipelineResult(
                    success=True,
                    duration=duration
                )
            else:
                error_msg = result.stderr or result.stdout or "Erreur inconnue"
                return PipelineResult(
                    success=False,
                    error=error_msg,
                    duration=duration
                )

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return PipelineResult(
                success=False,
                error="Timeout: le pipeline a dépassé 5 minutes",
                duration=duration
            )
        except Exception as e:
            duration = time.time() - start_time
            return PipelineResult(
                success=False,
                error=str(e),
                duration=duration
            )

    def get_last_update_time(self) -> Optional[datetime]:
        """
        Retourne la date de dernière mise à jour du briefing.
        Basé sur la date de modification du fichier texte.
        """
        text_file = self._find_latest_briefing_file("txt")
        if text_file and text_file.exists():
            mtime = text_file.stat().st_mtime
            return datetime.fromtimestamp(mtime)
        return None

    def get_briefing_text(self) -> Optional[str]:
        """Retourne le contenu du dernier briefing texte"""
        text_file = self._find_latest_briefing_file("txt")
        if text_file and text_file.exists():
            try:
                with open(text_file, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception:
                return None
        return None

    def get_audio_path(self) -> Optional[Path]:
        """Retourne le chemin vers le dernier fichier audio"""
        audio_file = self._find_latest_briefing_file("mp3")
        if audio_file and audio_file.exists():
            return audio_file
        return None

    def _find_latest_briefing_file(self, extension: str) -> Optional[Path]:
        """
        Trouve le fichier de briefing le plus récent avec l'extension donnée.
        Les fichiers sont nommés: briefing_YYYYMMDD_HHMMSS.{ext}
        """
        if not self.output_dir.exists():
            return None

        pattern = f"briefing_*.{extension}"
        files = list(self.output_dir.glob(pattern))

        if not files:
            return None

        # Trier par date de modification (le plus récent en premier)
        files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        return files[0]

    def has_briefing(self) -> bool:
        """Vérifie si un briefing existe"""
        return self.get_briefing_text() is not None

    def has_audio(self) -> bool:
        """Vérifie si un fichier audio existe"""
        return self.get_audio_path() is not None


# Instance globale (singleton)
_pipeline_runner: Optional[PipelineRunner] = None


def get_pipeline_runner() -> PipelineRunner:
    """Retourne l'instance unique du PipelineRunner"""
    global _pipeline_runner
    if _pipeline_runner is None:
        _pipeline_runner = PipelineRunner()
    return _pipeline_runner
