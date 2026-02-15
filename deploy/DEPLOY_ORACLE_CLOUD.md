# Déploiement SportBrief sur Oracle Cloud Free Tier

## 1. Créer un compte Oracle Cloud

1. Aller sur https://cloud.oracle.com/
2. Cliquer sur "Start for free"
3. Créer un compte (carte bancaire requise mais aucun prélèvement)
4. Choisir une région proche (ex: Frankfurt, eu-frankfurt-1)

## 2. Créer une VM ARM gratuite

### Via la console Oracle Cloud :

1. **Compute > Instances > Create Instance**
2. Configuration :
   - **Name**: `sportbrief-server`
   - **Image**: Ubuntu 22.04 (ou Oracle Linux 8)
   - **Shape**: VM.Standard.A1.Flex (ARM)
     - OCPUs: 2 (gratuit jusqu'à 4)
     - Memory: 12 GB (gratuit jusqu'à 24 GB)
   - **Networking**: Créer un nouveau VCN ou utiliser existant
   - **SSH Keys**: Ajouter votre clé publique SSH

3. **Security List** - Ouvrir les ports :
   - 22 (SSH)
   - 5678 (n8n)
   - 8501 (Streamlit - optionnel)

### Commande OCI CLI (alternative) :
```bash
oci compute instance launch \
  --availability-domain "AD-1" \
  --compartment-id $COMPARTMENT_ID \
  --shape "VM.Standard.A1.Flex" \
  --shape-config '{"ocpus":2,"memoryInGBs":12}' \
  --image-id $UBUNTU_IMAGE_ID \
  --subnet-id $SUBNET_ID \
  --ssh-authorized-keys-file ~/.ssh/id_rsa.pub \
  --display-name "sportbrief-server"
```

## 3. Se connecter à la VM

```bash
ssh ubuntu@<IP_PUBLIQUE>
```

## 4. Installer SportBrief

```bash
# Télécharger et exécuter le script d'installation
curl -fsSL https://raw.githubusercontent.com/VOTRE_REPO/sportbrief/main/deploy/install.sh | bash

# OU manuellement :
git clone https://github.com/VOTRE_REPO/sportbrief.git
cd sportbrief
chmod +x deploy/install.sh
./deploy/install.sh
```

## 5. Configurer les variables d'environnement

```bash
cd ~/sportbrief
cp .env.example .env
nano .env
```

Ajouter vos clés API :
```
GEMINI_API_KEY=votre_cle_gemini
API_SPORTS_KEY=votre_cle_api_sports
FOOTBALL_DATA_ORG_KEY=votre_cle_football_data
```

## 6. Tester le pipeline

```bash
cd ~/sportbrief
python sportbrief.py -a
```

Vérifier que les fichiers sont générés dans `data/output/`.

## 7. Accéder à n8n

- URL: `http://<IP_PUBLIQUE>:5678`
- Premier accès : créer un compte admin

## 8. Importer le workflow n8n

1. Dans n8n, aller dans **Workflows > Import from file**
2. Sélectionner `deploy/n8n_workflow.json`
3. Activer le workflow

## 9. Configurer le Webhook (optionnel)

Si vous voulez déclencher manuellement depuis Streamlit :
- URL du webhook : `http://<IP_PUBLIQUE>:5678/webhook/sportbrief-trigger`

## Maintenance

### Logs n8n
```bash
docker logs -f n8n
```

### Logs SportBrief
```bash
cat ~/sportbrief/data/output/debug_prompt.txt
```

### Redémarrer n8n
```bash
cd ~/sportbrief/deploy
docker-compose restart n8n
```

### Mettre à jour SportBrief
```bash
cd ~/sportbrief
git pull
pip install -r requirements.txt
```

## Coûts

Oracle Cloud Free Tier inclut gratuitement :
- 4 OCPUs ARM + 24 GB RAM (à vie)
- 200 GB de stockage bloc
- 10 TB de transfert sortant/mois

**Aucun coût tant que vous restez dans ces limites.**
