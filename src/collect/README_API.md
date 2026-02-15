# Guide de collecte des APIs sportives

## Architecture

```
src/
├── config/
│   ├── __init__.py
│   └── api_config.py          # Configuration centrale de toutes les APIs
├── collect/
│   ├── collect_rss.py         # Collecte RSS (gratuit)
│   ├── collect_api_biathlon.py    # ✅ Biathlon (gratuit)
│   ├── collect_api_football.py    # ✅ Football (API-SPORTS)
│   ├── _template_api_sport.py     # Template pour nouveaux sports
│   └── collect_api_*.py           # Autres sports (à créer)
```

## Configuration centrale

Toutes les préférences utilisateur sont dans **src/config/api_config.py**:

- API-KEY pour API-SPORTS
- Équipes favorites par sport
- Ligues suivies
- Joueurs/athlètes suivis
- Limites de collecte (économie de quota)

## Sports couverts

| Sport | Script | Source | Statut | Quota/jour |
|-------|--------|--------|--------|------------|
| **Biathlon** | `collect_api_biathlon.py` | biathlonresults | ✅ Opérationnel | Gratuit |
| **Football** | `collect_api_football.py` | API-SPORTS v3 | ✅ Opérationnel | ~4 requêtes |
| **Basketball** | À créer | API-SPORTS v1 | ⏳ Template dispo | ~2 requêtes |
| **Volleyball** | À créer | API-SPORTS v1 | ⏳ Template dispo | ~2 requêtes |
| **Handball** | À créer | API-SPORTS v1 | ⏳ Template dispo | ~2 requêtes |
| **Rugby** | À créer | API-SPORTS v1 | ⏳ Template dispo | ~2 requêtes |
| **Formule 1** | À créer | API-SPORTS v1 | ⏳ Template dispo | ~2 requêtes |
| **MMA** | À créer | API-SPORTS v1 | ⏳ Template dispo | ~2 requêtes |
| **Tennis** | À créer | API à définir | ❌ Pas d'API | - |
| **Ping-pong** | À créer | API à définir | ❌ Pas d'API | - |

**Total estimé**: 16 requêtes/jour (sur 100 disponibles en Free)

## Ajouter un nouveau sport

### 1. Copier le template

```bash
cp src/collect/_template_api_sport.py src/collect/collect_api_<sport>.py
```

### 2. Configurer le sport dans api_config.py

Ajouter l'entrée dans `SPORTS_CONFIG`:

```python
"volleyball": {
    "source": "api-volleyball",
    "api_key": API_SPORTS_KEY,
    "teams": [
        {"name": "CVB 52 Chaumont", "id": None, "league_id": None}
    ],
    "leagues": [
        {"name": "Ligue A", "id": None, "country": "France"}
    ],
    "max_games_per_team": 5,
}
```

Ajouter l'URL dans `API_URLS`:

```python
API_URLS = {
    # ...
    "volleyball": "https://v1.volleyball.api-sports.io",
}
```

### 3. Trouver les IDs

Utiliser l'API pour trouver les IDs:

```python
# Exemple: Trouver l'ID d'une équipe
import requests

response = requests.get(
    "https://v1.volleyball.api-sports.io/teams",
    headers={"x-apisports-key": "VOTRE_CLE"},
    params={"search": "Chaumont"}
)

print(response.json())
```

Ou utiliser le dashboard: https://dashboard.api-football.com

### 4. Adapter le template

- Remplacer `SPORT_NAME` par le nom du sport
- Adapter les endpoints selon la documentation
- Adapter la structure des données retournées

### 5. Tester

```bash
python src/collect/collect_api_<sport>.py
```

Vérifier le fichier généré dans `data/raw/api/<sport>/`.

## Optimisation du quota

### Stratégies actuelles

1. **Filtrage par préférences utilisateur**
   - Biathlon: uniquement athlètes français (1917 → 128 résultats)
   - Football: uniquement 2 équipes + 3 ligues

2. **Limitation des résultats**
   - `max_games_per_team`: 5 derniers matchs max
   - `max_events`: 3 événements max (biathlon)

3. **Choix des données**
   - Classements au lieu de tous les matchs
   - Données déjà agrégées quand possible

### Recommandations

- **Ne pas** collecter toutes les compétitions
- **Ne pas** récupérer l'historique complet
- **Privilégier** les données agrégées (standings vs tous les games)
- **Cacher** les résultats côté serveur si possible

## Erreurs fréquentes

### Erreur: "Failed to resolve API URL"

➡️ Vérifier que l'URL est dans `API_URLS` dans `api_config.py`

### Erreur: "Quota exceeded"

➡️ Vous avez dépassé les 100 requêtes/jour
- Attendre le reset (minuit UTC)
- Réduire `max_games_per_team`
- Filtrer davantage les données

### Warning: "Pas d'ID pour X, skip"

➡️ L'ID de l'équipe/ligue n'est pas configuré
- Utiliser l'API ou le dashboard pour trouver l'ID
- Mettre à jour `api_config.py`

## Données générées

Chaque script génère un fichier JSON:

```
data/raw/api/<sport>/<sport>_data.json
```

Structure:

```json
{
  "source": "api-football",
  "sport": "football",
  "fetched_at": "2026-01-22T21:00:00",
  "teams_tracked": ["OM", "Liverpool"],
  "leagues_tracked": ["Ligue 1", "Premier League"],
  "total_games": 10,
  "total_standings": 74,
  "data": {
    "games": [...],
    "standings": [...]
  }
}
```

## Prochaines étapes

Au **Jour 5**, ces données seront:
1. Fusionnées avec les articles RSS
2. Enrichies (contexte sportif)
3. Filtrées selon pertinence

Au **Jour 6**, un système de scoring/priorisation sera ajouté.
