"""
Agregateur de donnees SportBrief
Fusionne les donnees RSS et API en un format unifie pour le LLM
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional


# Configuration
RAW_DATA_DIR = Path("data/raw")
OUTPUT_DIR = Path("data/processed")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Mapping des sports vers leurs sources de donnees
SPORT_SOURCES = {
    "football": {
        "api": ["api/football/football_data.json"],
        "rss": ["lequipe_foot", "rmc_foot", "rmc_ligue1", "rmc_LDC", "rmc_mercato",
                "rmc_premier_league", "dailysport_football", "rmc_euro", "rmc_foot_coupe_monde"]
    },
    "basketball": {
        "api": ["api/nba/nba_data.json"],
        "rss": ["lequipe_basket", "rmc_basket", "rmc_nba", "dailysport_basket"]
    },
    "rugby": {
        "api": [],
        "rss": ["lequipe_rugby", "rmc_rugby", "rmc_rugby_6_nations",
                "rmc_rugby_coupe_europe", "rmc_rugby_coupe_monde", "dailysport_rugby"]
    },
    "handball": {
        "api": [],
        "rss": ["lequipe_handball", "rmc_handball"]
    },
    "volleyball": {
        "api": [],
        "lnv": ["lnv/calendrier_lam.json", "lnv/calendrier_laf.json", "lnv/classement_lam.json", "lnv/classement_laf.json"],
        "rss": ["lequipe_volley", "rmc_volley"]
    },
    "formule1": {
        "api": ["api/f1/f1_data.json"],
        "rss": ["lequipe_f1", "rmc_f1", "dailysport_automoto"]
    },
    "tennis": {
        "api": [],
        "rss": ["lequipe_tennis", "rmc_tennis", "dailysport_tennis"]
    },
    "biathlon": {
        "api": ["api/biathlon/biathlon_results.json"],
        "rss": []  # Biathlon specifique, pas de RSS general
    },
    "ski_alpin": {
        "api": [],
        "rss": ["lequipe_ski"]  # Ski alpin: descente, slalom, etc.
    },
    "jeux_olympiques": {
        "api": [],
        "rss": ["rmc_JO"]  # Jeux Olympiques
    },
    "mma": {
        "api": [],
        "rss": ["rmc_combat"]
    },
    "pingpong": {
        "api": [],
        "rss": []  # Pas de source specifique
    },
    "cyclisme": {
        "api": [],
        "rss": ["lequipe_cyclisme", "rmc_cyclisme", "rmc_TDF", "dailysport_cyclisme"]
    }
}


def load_preferences() -> dict:
    """Charge les preferences utilisateur"""
    prefs_file = Path("user_preferences.json")
    if prefs_file.exists():
        with open(prefs_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def get_enabled_sports(prefs: dict) -> list[str]:
    """Retourne les sports actives"""
    sports = prefs.get("sports", {})
    return [name for name, config in sports.items() if config.get("enabled", False)]


def get_favorite_teams(prefs: dict, sport: str) -> list[str]:
    """Retourne les equipes favorites pour un sport (avec aliases)"""
    sport_config = prefs.get("sports", {}).get(sport, {})
    teams = sport_config.get("teams", [])
    result = []
    for t in teams:
        if isinstance(t, dict):
            result.append(t.get("name", ""))
            # Ajouter les aliases
            aliases = t.get("aliases", [])
            result.extend(aliases)
        else:
            result.append(t)
    return [name for name in result if name]


def load_api_data(file_path: str) -> dict:
    """Charge un fichier de donnees API"""
    full_path = RAW_DATA_DIR / file_path
    if full_path.exists():
        with open(full_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def load_rss_data(source_name: str) -> list[dict]:
    """Charge un fichier RSS et retourne les articles"""
    file_path = RAW_DATA_DIR / "rss" / f"{source_name}.json"
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("articles", [])
    return []


def normalize_api_football(data: dict, prefs: dict) -> list[dict]:
    """Normalise les donnees football API"""
    items = []
    favorite_teams = get_favorite_teams(prefs, "football")

    # Classements (top 5 par ligue + equipes favorites)
    for standing in data.get("data", {}).get("standings", []):
        position = standing.get("position", 99)
        team = standing.get("team") or ""

        # Top 5 ou equipe favorite
        is_favorite = any(fav.lower() in team.lower() for fav in favorite_teams) if team else False
        if position <= 5 or is_favorite:
            items.append({
                "type": "standing",
                "sport": "football",
                "priority": 1 if is_favorite else 2,
                "competition": standing.get("competition"),
                "team": team,
                "position": position,
                "points": standing.get("points"),
                "played": standing.get("played"),
                "won": standing.get("won"),
                "draw": standing.get("draw"),
                "lost": standing.get("lost"),
                "goal_difference": standing.get("goal_difference"),
            })

    # Matchs recents (filtrer par equipes favorites)
    for match in data.get("data", {}).get("recent_matches", [])[-30:]:
        home = match.get("home_team") or ""
        away = match.get("away_team") or ""
        is_favorite = any(
            fav.lower() in home.lower() or fav.lower() in away.lower()
            for fav in favorite_teams
        ) if home and away else False

        if is_favorite or len(items) < 20:
            items.append({
                "type": "match_result",
                "sport": "football",
                "priority": 1 if is_favorite else 3,
                "competition": match.get("competition"),
                "date": match.get("date"),
                "home_team": home,
                "away_team": away,
                "home_score": match.get("home_score"),
                "away_score": match.get("away_score"),
            })

    # Matchs a venir
    for match in data.get("data", {}).get("upcoming_matches", [])[:20]:
        home = match.get("home_team") or ""
        away = match.get("away_team") or ""
        is_favorite = any(
            fav.lower() in home.lower() or fav.lower() in away.lower()
            for fav in favorite_teams
        ) if home and away else False

        if is_favorite:
            items.append({
                "type": "match_upcoming",
                "sport": "football",
                "priority": 1,
                "competition": match.get("competition"),
                "date": match.get("date"),
                "home_team": home,
                "away_team": away,
            })

    return items


def normalize_api_nba(data: dict, prefs: dict) -> list[dict]:
    """Normalise les donnees NBA API avec filtrage par preferences"""
    items = []
    from datetime import datetime, timedelta

    # Charger les preferences basketball
    basketball_prefs = prefs.get("sports", {}).get("basketball", {})
    standings_prefs = basketball_prefs.get("standings", {})
    matches_filter = basketball_prefs.get("matches_filter", {})
    extraordinary_prefs = basketball_prefs.get("extraordinary_performances", {})

    # Calculer la date de la veille
    days_back = matches_filter.get("days_back", 1)
    cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

    # Classements - top N par conference selon preferences
    top_count = standings_prefs.get("top_count", 5)
    show_both = standings_prefs.get("show_both_conferences", True)

    for conf in ["east", "west"]:
        if not show_both and conf == "west":
            continue
        standings = data.get("data", {}).get("standings", {}).get(conf, [])
        for standing in standings[:top_count]:
            items.append({
                "type": "standing",
                "sport": "basketball",
                "priority": 2,
                "league": "NBA",
                "conference": conf.upper(),
                "team": standing.get("team"),
                "team_city": standing.get("team_city"),
                "rank": standing.get("rank"),
                "wins": standing.get("wins"),
                "losses": standing.get("losses"),
                "win_pct": standing.get("win_pct"),
                "streak": standing.get("streak"),
                "last_10": standing.get("last_10"),
            })

    # Matchs de la veille uniquement
    for game in data.get("data", {}).get("recent_games", []):
        game_date = game.get("date", "")
        if game_date >= cutoff_date:
            items.append({
                "type": "match_result",
                "sport": "basketball",
                "priority": 2,
                "league": "NBA",
                "date": game_date,
                "home_team": game.get("home_team"),
                "visitor_team": game.get("visitor_team"),
                "home_score": game.get("home_score"),
                "visitor_score": game.get("visitor_score"),
            })

    # Stats joueurs francais - uniquement dernier match (veille)
    seen_players = set()
    for player_game in data.get("data", {}).get("french_players", []):
        player_name = player_game.get("player_name")
        game_date = player_game.get("date", "")

        # Un seul match par joueur (le plus recent)
        if player_name in seen_players:
            continue

        # Filtrer par date (veille)
        if game_date and game_date >= cutoff_date:
            seen_players.add(player_name)
            items.append({
                "type": "player_stats",
                "sport": "basketball",
                "priority": 1,
                "league": "NBA",
                "player": player_name,
                "date": game_date,
                "matchup": player_game.get("matchup"),
                "result": player_game.get("result"),
                "points": player_game.get("points"),
                "rebounds": player_game.get("rebounds"),
                "assists": player_game.get("assists"),
                "steals": player_game.get("steals"),
                "blocks": player_game.get("blocks"),
            })

            # Detecter performances extraordinaires (francais)
            pts = player_game.get("points", 0) or 0
            reb = player_game.get("rebounds", 0) or 0
            ast = player_game.get("assists", 0) or 0
            thresholds = extraordinary_prefs.get("thresholds", {})

            is_extraordinary = (
                pts >= thresholds.get("points", 40) or
                reb >= thresholds.get("rebounds", 20) or
                ast >= thresholds.get("assists", 15) or
                (thresholds.get("triple_double") and pts >= 10 and reb >= 10 and ast >= 10) or
                (thresholds.get("double_double_40pts") and pts >= 40 and (reb >= 10 or ast >= 10))
            )

            if is_extraordinary:
                # Marquer comme performance extraordinaire
                items[-1]["extraordinary"] = True
                items[-1]["priority"] = 0  # Priorite maximale

    return items


def normalize_api_f1(data: dict, prefs: dict) -> list[dict]:
    """Normalise les donnees F1 API"""
    items = []

    # Resultats recents
    for result in data.get("data", {}).get("recent_results", []):
        items.append({
            "type": "race_result",
            "sport": "formule1",
            "priority": 2,
            "meeting": result.get("meeting_name"),
            "date": result.get("date"),
            "position": result.get("position"),
            "driver_number": result.get("driver_number"),
        })

    # Prochaines courses
    for race in data.get("data", {}).get("upcoming_races", [])[:3]:
        items.append({
            "type": "race_upcoming",
            "sport": "formule1",
            "priority": 2,
            "meeting": race.get("meeting_name"),
            "country": race.get("country"),
            "circuit": race.get("circuit"),
            "date": race.get("date_start"),
        })

    # Pilotes
    for driver in data.get("data", {}).get("drivers", []):
        items.append({
            "type": "driver_info",
            "sport": "formule1",
            "priority": 3,
            "name": driver.get("full_name"),
            "team": driver.get("team_name"),
            "number": driver.get("driver_number"),
            "country": driver.get("country_code"),
        })

    return items


def normalize_api_biathlon(data: dict, prefs: dict) -> list[dict]:
    """Normalise les donnees biathlon API"""
    items = []

    for result in data.get("data", [])[:20]:
        items.append({
            "type": "race_result",
            "sport": "biathlon",
            "priority": 1,  # Priorite haute car athletes francais
            "event": result.get("event"),
            "race": result.get("race"),
            "date": result.get("race_date"),
            "athlete": result.get("athlete"),
            "nation": result.get("nation"),
            "rank": result.get("rank"),
            "shooting": result.get("shooting"),
            "time": result.get("time"),
        })

    return items


def normalize_lnv_data(data: dict, prefs: dict) -> list[dict]:
    """Normalise les donnees LNV volleyball"""
    items = []
    favorite_teams = get_favorite_teams(prefs, "volleyball")
    data_type = data.get("type", "")
    league = data.get("league", "")

    if data_type == "calendrier":
        # Filtrer les matchs joues (score != 0-0 et != -)
        for match in data.get("matches", []):
            score = match.get("score", "")
            if score in ["0-0", "-", ""]:
                continue  # Match pas encore joue

            home = match.get("domicile", "")
            away = match.get("exterieur", "")

            # Verifier si equipe favorite
            is_favorite = any(
                fav.lower() in home.lower() or fav.lower() in away.lower()
                for fav in favorite_teams
            ) if home and away else False

            items.append({
                "type": "match_result",
                "sport": "volleyball",
                "priority": 1 if is_favorite else 2,
                "league": league,
                "date": match.get("date"),
                "journee": match.get("journee"),
                "home_team": home,
                "away_team": away,
                "score": score,
                "sets": match.get("sets", []),
            })

    elif data_type == "classement":
        for team in data.get("teams", []):
            team_name = team.get("nom", "")
            is_favorite = any(
                fav.lower() in team_name.lower()
                for fav in favorite_teams
            ) if team_name else False

            # Top 5 ou equipe favorite
            if team.get("rang", 99) <= 5 or is_favorite:
                items.append({
                    "type": "standing",
                    "sport": "volleyball",
                    "priority": 1 if is_favorite else 2,
                    "league": league,
                    "team": team_name,
                    "position": team.get("rang"),
                    "points": team.get("points"),
                    "played": team.get("matchs_joues"),
                    "won": team.get("matchs_gagnes"),
                    "lost": team.get("matchs_perdus"),
                    "sets_for": team.get("sets_pour"),
                    "sets_against": team.get("sets_contre"),
                })

    return items


def normalize_rss_articles(articles: list[dict], sport: str, prefs: dict) -> list[dict]:
    """Normalise les articles RSS"""
    items = []
    favorite_teams = get_favorite_teams(prefs, sport)

    for article in articles[:10]:  # Max 10 articles par source
        title = article.get("title", "")
        summary = article.get("summary", "")

        # Calculer la priorite
        priority = 3  # Par defaut
        for team in favorite_teams:
            if team.lower() in title.lower() or team.lower() in summary.lower():
                priority = 1
                break

        # Nettoyer le summary (enlever les balises HTML)
        clean_summary = summary
        if "<img" in clean_summary:
            # Extraire le texte apres la balise img
            import re
            clean_summary = re.sub(r'<[^>]+>', '', clean_summary).strip()

        items.append({
            "type": "news",
            "sport": sport,
            "priority": priority,
            "source": article.get("source"),
            "title": title,
            "summary": clean_summary[:300] if clean_summary else "",
            "link": article.get("link"),
            "published": article.get("published"),
        })

    return items


def aggregate_sport_data(sport: str, prefs: dict) -> list[dict]:
    """Agregue toutes les donnees pour un sport"""
    items = []
    sources = SPORT_SOURCES.get(sport, {"api": [], "rss": []})

    # Charger les donnees API
    for api_file in sources.get("api", []):
        api_data = load_api_data(api_file)
        if not api_data:
            continue

        # Normaliser selon le type
        if "football" in api_file and "nba" not in api_file:
            items.extend(normalize_api_football(api_data, prefs))
        elif "nba" in api_file:
            items.extend(normalize_api_nba(api_data, prefs))
        elif "f1" in api_file:
            items.extend(normalize_api_f1(api_data, prefs))
        elif "biathlon" in api_file:
            items.extend(normalize_api_biathlon(api_data, prefs))

    # Charger les donnees LNV (volleyball)
    for lnv_file in sources.get("lnv", []):
        lnv_path = RAW_DATA_DIR / lnv_file
        if lnv_path.exists():
            with open(lnv_path, "r", encoding="utf-8") as f:
                lnv_data = json.load(f)
                items.extend(normalize_lnv_data(lnv_data, prefs))

    # Charger les donnees RSS
    for rss_source in sources.get("rss", []):
        articles = load_rss_data(rss_source)
        items.extend(normalize_rss_articles(articles, sport, prefs))

    return items


def deduplicate_news(items: list[dict]) -> list[dict]:
    """Deduplique les articles similaires"""
    seen_titles = set()
    unique_items = []

    for item in items:
        if item.get("type") != "news":
            unique_items.append(item)
            continue

        title = item.get("title", "").lower()[:50]
        if title not in seen_titles:
            seen_titles.add(title)
            unique_items.append(item)

    return unique_items


def main():
    """Fonction principale d'agregation"""

    print("=" * 50)
    print("SPORTBRIEF - AGREGATION DES DONNEES")
    print("=" * 50)

    prefs = load_preferences()
    enabled_sports = get_enabled_sports(prefs)

    print(f"\n[INFO] Sports actives: {', '.join(enabled_sports)}")

    all_items = []

    # Agreger les donnees par sport
    for sport in enabled_sports:
        print(f"\n[INFO] Agregation {sport}...")
        sport_items = aggregate_sport_data(sport, prefs)
        all_items.extend(sport_items)
        print(f"  [OK] {len(sport_items)} elements")

    # Dedupliquer les news
    all_items = deduplicate_news(all_items)

    # Mode JO prioritaire : booster tous les items jeux_olympiques à priorité 0
    olympics_prefs = prefs.get("olympics", {})
    if olympics_prefs.get("enabled") and olympics_prefs.get("priority_mode"):
        for item in all_items:
            if item.get("sport") == "jeux_olympiques":
                item["priority"] = 0

    # Trier par priorite puis par type
    all_items.sort(key=lambda x: (x.get("priority", 5), x.get("type", "z")))

    # Construire le payload
    payload = {
        "generated_at": datetime.utcnow().isoformat(),
        "sports_included": enabled_sports,
        "total_items": len(all_items),
        "stats": {
            "news": len([i for i in all_items if i.get("type") == "news"]),
            "standings": len([i for i in all_items if i.get("type") == "standing"]),
            "match_results": len([i for i in all_items if i.get("type") == "match_result"]),
            "match_upcoming": len([i for i in all_items if i.get("type") == "match_upcoming"]),
            "player_stats": len([i for i in all_items if i.get("type") == "player_stats"]),
            "race_results": len([i for i in all_items if i.get("type") == "race_result"]),
        },
        "items": all_items,
    }

    # Sauvegarder
    output_file = OUTPUT_DIR / "aggregated_data.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 50}")
    print("RESUME:")
    print(f"  - Total elements: {payload['total_items']}")
    for stat_name, stat_value in payload["stats"].items():
        if stat_value > 0:
            print(f"  - {stat_name}: {stat_value}")

    print(f"\n[OK] Donnees agregees sauvegardees dans {output_file}")


if __name__ == "__main__":
    main()
