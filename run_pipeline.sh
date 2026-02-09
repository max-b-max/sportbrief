#!/bin/bash
# SportBrief - Script d'exécution du pipeline
# Utilisé par n8n ou cron pour l'exécution quotidienne

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

LOG_FILE="data/output/pipeline.log"
mkdir -p data/output

echo "$(date '+%Y-%m-%d %H:%M:%S') - Début du pipeline SportBrief" >> "$LOG_FILE"

# Activer le virtualenv si présent
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Charger les variables d'environnement
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Exécuter le pipeline complet avec audio
python sportbrief.py -a 2>&1 | tee -a "$LOG_FILE"

EXIT_CODE=${PIPESTATUS[0]}

echo "$(date '+%Y-%m-%d %H:%M:%S') - Pipeline terminé (exit: $EXIT_CODE)" >> "$LOG_FILE"

exit $EXIT_CODE
