#!/bin/bash
# Script d'installation SportBrief pour Ubuntu/Debian (ARM ou x86)
# Usage: curl -fsSL <url>/install.sh | bash

set -e

echo "=========================================="
echo "  SportBrief - Installation automatique"
echo "=========================================="

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Variables
INSTALL_DIR="$HOME/sportbrief"
N8N_PORT=5678

# 1. Mise à jour système
log_info "Mise a jour du systeme..."
sudo apt update && sudo apt upgrade -y

# 2. Installation des dépendances
log_info "Installation des dependances..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    docker.io \
    docker-compose

# 3. Configurer Docker pour l'utilisateur courant
log_info "Configuration de Docker..."
sudo usermod -aG docker $USER

# 4. Cloner le repo (si pas déjà fait)
if [ -d "$INSTALL_DIR" ]; then
    log_warn "Le dossier $INSTALL_DIR existe deja. Mise a jour..."
    cd "$INSTALL_DIR"
    git pull || true
else
    log_info "Clonage du projet..."
    # Remplacer par votre repo
    # git clone https://github.com/VOTRE_REPO/sportbrief.git "$INSTALL_DIR"

    # Pour l'instant, on suppose que les fichiers sont copiés manuellement
    mkdir -p "$INSTALL_DIR"
    log_warn "Copiez vos fichiers SportBrief dans $INSTALL_DIR"
fi

cd "$INSTALL_DIR"

# 5. Créer l'environnement virtuel Python
log_info "Creation de l'environnement Python..."
python3 -m venv venv
source venv/bin/activate

# 6. Installer les dépendances Python
log_info "Installation des dependances Python..."
pip install --upgrade pip
pip install -r requirements.txt

# 7. Créer les dossiers nécessaires
log_info "Creation des dossiers..."
mkdir -p data/output
mkdir -p data/cache

# 8. Configurer n8n avec Docker
log_info "Configuration de n8n..."
mkdir -p "$INSTALL_DIR/deploy/n8n_data"

# Créer docker-compose.yml si pas présent
if [ ! -f "$INSTALL_DIR/deploy/docker-compose.yml" ]; then
    log_info "Creation de docker-compose.yml..."
    cat > "$INSTALL_DIR/deploy/docker-compose.yml" << 'EOF'
version: '3.8'

services:
  n8n:
    image: n8nio/n8n:latest
    container_name: n8n
    restart: unless-stopped
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=sportbrief2024
      - GENERIC_TIMEZONE=Europe/Paris
      - TZ=Europe/Paris
      - N8N_HOST=0.0.0.0
      - WEBHOOK_URL=http://localhost:5678/
    volumes:
      - ./n8n_data:/home/node/.n8n
      - /home/ubuntu/sportbrief:/home/node/sportbrief:ro
    user: root
EOF
fi

# 9. Démarrer n8n
log_info "Demarrage de n8n..."
cd "$INSTALL_DIR/deploy"
sudo docker-compose up -d

# 10. Créer le script d'exécution du pipeline
log_info "Creation du script runner..."
cat > "$INSTALL_DIR/run_pipeline.sh" << 'EOF'
#!/bin/bash
# Script pour exécuter le pipeline SportBrief
cd /home/ubuntu/sportbrief
source venv/bin/activate
python sportbrief.py -a
echo "Pipeline termine: $(date)"
EOF
chmod +x "$INSTALL_DIR/run_pipeline.sh"

# 11. Vérification
log_info "Verification de l'installation..."
echo ""
echo "=========================================="
echo "  Installation terminee!"
echo "=========================================="
echo ""
echo "Prochaines etapes:"
echo "  1. Configurer .env avec vos cles API:"
echo "     cd $INSTALL_DIR && cp .env.example .env && nano .env"
echo ""
echo "  2. Tester le pipeline:"
echo "     cd $INSTALL_DIR && source venv/bin/activate && python sportbrief.py -a"
echo ""
echo "  3. Acceder a n8n:"
echo "     URL: http://$(curl -s ifconfig.me):5678"
echo "     User: admin"
echo "     Pass: sportbrief2024"
echo ""
echo "  4. Importer le workflow n8n:"
echo "     deploy/n8n_workflow.json"
echo ""
log_warn "IMPORTANT: Reconnectez-vous pour appliquer les permissions Docker"
log_info "Ou executez: newgrp docker"
