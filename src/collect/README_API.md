# Collecteurs API SportBrief

## Architecture

Chaque sport a son propre script de collecte dans `src/collect/`.

```
src/collect/
├── collect_rss.py              # Flux RSS (RMC, L'Équipe, Dailysport)
├── collect_api_football.py     # Football (API-SPORTS v3)
├── collect_api_nba.py          # NBA (API-Basketball)
├── collect_api_basketball.py   # Basketball générique
├── collect_api_rugby.py        # Rugby (API-SPORTS)
├── collect_api_handball.py     # Handball (API-SPORTS)
├── collect_api_volleyball.py   # Volleyball (API-SPORTS)
├── collect_api_formule1.py     # F1 (API-SPORTS)
├── collect_api_mma.py          # MMA/UFC (API-SPORTS)
├── collect_api_tennis.py       # Tennis
├── collect_api_pingpong.py     # Tennis de table
├── collect_api_biathlon.py     # Biathlon (biathlonresults)
├── collect_footballdata.py     # Football-data.org (alternatif)
├── collect_nba.py              # NBA détaillé
├── collect_f1.py               # F1 détaillé
└── collect_lnv.py              # Volleyball LNV
```

## Configuration

- Clés API dans `.env` (voir `.env.example`)
- Préférences utilisateur dans `user_preferences.json`
- Config des IDs et ligues dans `src/config/`

## Quota API-SPORTS

Le plan gratuit donne 100 requêtes/jour. Le pipeline utilise environ 16 requêtes par exécution.

Stratégies d'économie :
- Filtrer par équipes favorites uniquement
- Limiter à 5 derniers matchs par équipe
- Préférer les classements aux listes complètes

## Données générées

Chaque collecteur écrit dans `data/raw/api/<sport>/` au format JSON.
