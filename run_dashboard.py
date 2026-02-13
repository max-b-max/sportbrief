#!/usr/bin/env python
"""
Script de lancement du dashboard SportBrief
Usage: python run_dashboard.py
"""

import subprocess
import sys
from pathlib import Path


def main():
    # Chemin vers l'application Streamlit
    app_path = Path(__file__).parent / "src" / "app" / "app.py"

    if not app_path.exists():
        print(f"Erreur: {app_path} non trouvé")
        sys.exit(1)

    # Lancer Streamlit
    cmd = [sys.executable, "-m", "streamlit", "run", str(app_path)]

    print("[SportBrief] Demarrage du Dashboard...")
    print(f"   Commande: {' '.join(cmd)}")
    print()

    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n[SportBrief] Dashboard arrete.")
    except Exception as e:
        print(f"Erreur: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
