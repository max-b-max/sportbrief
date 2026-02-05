"""
Collector NBA utilisant nba_api (scrape NBA.com)
Package Python gratuit - pas de clé API nécessaire

Données disponibles:
- Classements Est/Ouest
- Matchs du jour / récents
- Stats des joueurs français
"""

import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# nba_api imports
from nba_api.stats.endpoints import (
    scoreboardv2,
    leaguestandings,
    playergamelog,
    commonplayerinfo,
)
from nba_api.stats.static import teams, players

# Configuration
OUTPUT_DIR = Path("data/raw/api/nba")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Délai entre requêtes pour éviter le rate limiting de NBA.com
REQUEST_DELAY = 1  # seconde

# Saison actuelle (format NBA: "2025-26")
CURRENT_SEASON = "2025-26"

# Joueurs français à suivre (IDs NBA)
# Ces IDs peuvent être trouvés via players.find_players_by_full_name()
FRENCH_PLAYERS = [
    {"name": "Victor Wembanyama", "id": 1641705},
    {"name": "Rudy Gobert", "id": 203497},
    {"name": "Nicolas Batum", "id": 201587},
    {"name": "Bilal Coulibaly", "id": 1641706},
    {"name": "Alexandre Sarr", "id": 1642259},
    {"name": "Zaccharie Risacher", "id": 1642258},
    {"name": "Guerschon Yabusele", "id": 1627824},
    {"name": "Ousmane Dieng", "id": 1631099},
    {"name": "Tidjane Salaun", "id": 1642267},
]


def load_preferences() -> dict:
    """Charge les préférences utilisateur depuis le fichier JSON"""
    prefs_file = Path("user_preferences.json")
    if prefs_file.exists():
        with open(prefs_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def get_french_players_config() -> list[dict]:
    """Récupère la liste des joueurs français depuis la config ou utilise la liste par défaut"""
    prefs = load_preferences()
    basketball_prefs = prefs.get("sports", {}).get("basketball", {})

    # Si "all_french" est configuré, utiliser la liste par défaut
    if basketball_prefs.get("players") == "all_french":
        return FRENCH_PLAYERS

    return FRENCH_PLAYERS


def collect_standings() -> dict:
    """
    Collecte les classements NBA Est et Ouest

    Returns:
        Dictionnaire avec les classements des deux conférences
    """
    data = {"east": [], "west": []}

    try:
        print("  [INFO] Recuperation des classements...")
        standings = leaguestandings.LeagueStandings(season=CURRENT_SEASON)
        df = standings.get_data_frames()[0]

        for _, row in df.iterrows():
            team_data = {
                "sport": "basketball",
                "league": "NBA",
                "source": "nba_api",
                "type": "standing",
                "season": CURRENT_SEASON,
                "conference": row["Conference"],
                "rank": int(row["PlayoffRank"]),
                "team_id": int(row["TeamID"]),
                "team": row["TeamName"],
                "team_city": row["TeamCity"],
                "wins": int(row["WINS"]),
                "losses": int(row["LOSSES"]),
                "win_pct": float(row["WinPCT"]),
                "home_record": row["HOME"],
                "road_record": row["ROAD"],
                "last_10": row["L10"],
                "streak": row["CurrentStreak"],
            }

            if row["Conference"] == "East":
                data["east"].append(team_data)
            else:
                data["west"].append(team_data)

        print(f"  [OK] Est: {len(data['east'])} equipes, Ouest: {len(data['west'])} equipes")

    except Exception as e:
        print(f"  [ERROR] Classements: {e}")

    return data


def collect_recent_games(days: int = 3) -> list[dict]:
    """
    Collecte les matchs des derniers jours

    Args:
        days: Nombre de jours à remonter

    Returns:
        Liste des matchs récents
    """
    data = []

    try:
        print(f"  [INFO] Recuperation des matchs ({days} derniers jours)...")

        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")

            time.sleep(REQUEST_DELAY)

            try:
                scoreboard = scoreboardv2.ScoreboardV2(game_date=date_str)
                games_header = scoreboard.game_header.get_data_frame()
                line_score = scoreboard.line_score.get_data_frame()

                for _, game in games_header.iterrows():
                    game_id = game["GAME_ID"]

                    # Trouver les scores dans line_score
                    home_data = line_score[line_score["GAME_ID"] == game_id]

                    if len(home_data) >= 2:
                        # Premier = visiteur, second = domicile
                        visitor = home_data.iloc[0]
                        home = home_data.iloc[1]

                        game_data = {
                            "sport": "basketball",
                            "league": "NBA",
                            "source": "nba_api",
                            "type": "game_result",
                            "season": CURRENT_SEASON,
                            "game_id": game_id,
                            "date": date_str,
                            "status": game.get("GAME_STATUS_TEXT", ""),
                            "home_team_id": int(home["TEAM_ID"]),
                            "home_team": home["TEAM_ABBREVIATION"],
                            "home_score": int(home["PTS"]) if home["PTS"] else None,
                            "visitor_team_id": int(visitor["TEAM_ID"]),
                            "visitor_team": visitor["TEAM_ABBREVIATION"],
                            "visitor_score": int(visitor["PTS"]) if visitor["PTS"] else None,
                        }
                        data.append(game_data)

            except Exception as e:
                print(f"    [WARNING] Erreur pour {date_str}: {e}")
                continue

        print(f"  [OK] {len(data)} matchs collectes")

    except Exception as e:
        print(f"  [ERROR] Matchs recents: {e}")

    return data


def collect_french_players_stats() -> list[dict]:
    """
    Collecte les stats récentes des joueurs français

    Returns:
        Liste des stats des joueurs français
    """
    data = []
    french_players = get_french_players_config()

    print(f"  [INFO] Recuperation stats joueurs francais ({len(french_players)} joueurs)...")

    for player in french_players:
        player_id = player.get("id")
        player_name = player.get("name")

        if not player_id:
            print(f"    [SKIP] {player_name}: pas d'ID")
            continue

        time.sleep(REQUEST_DELAY)

        try:
            # Derniers matchs du joueur
            gamelog = playergamelog.PlayerGameLog(
                player_id=player_id,
                season=CURRENT_SEASON
            )
            df = gamelog.get_data_frames()[0]

            if df.empty:
                print(f"    [SKIP] {player_name}: pas de matchs cette saison")
                continue

            # Prendre les 5 derniers matchs
            recent_games = df.head(5)

            for _, game in recent_games.iterrows():
                game_data = {
                    "sport": "basketball",
                    "league": "NBA",
                    "source": "nba_api",
                    "type": "player_game",
                    "season": CURRENT_SEASON,
                    "player_id": player_id,
                    "player_name": player_name,
                    "game_id": game["Game_ID"],
                    "date": game["GAME_DATE"],
                    "matchup": game["MATCHUP"],
                    "result": game["WL"],
                    "minutes": game["MIN"],
                    "points": int(game["PTS"]),
                    "rebounds": int(game["REB"]),
                    "assists": int(game["AST"]),
                    "steals": int(game["STL"]),
                    "blocks": int(game["BLK"]),
                    "fg_pct": float(game["FG_PCT"]) if game["FG_PCT"] else None,
                    "fg3_pct": float(game["FG3_PCT"]) if game["FG3_PCT"] else None,
                    "plus_minus": int(game["PLUS_MINUS"]) if game["PLUS_MINUS"] else None,
                }
                data.append(game_data)

            # Résumé pour ce joueur
            avg_pts = recent_games["PTS"].mean()
            print(f"    [OK] {player_name}: {len(recent_games)} matchs, {avg_pts:.1f} pts/match")

        except Exception as e:
            print(f"    [ERROR] {player_name}: {e}")
            continue

    print(f"  [OK] {len(data)} lignes de stats joueurs")
    return data


def main():
    """Fonction principale de collecte NBA"""

    print("=" * 50)
    print("NBA COLLECTOR (nba_api)")
    print("=" * 50)
    print(f"Saison: {CURRENT_SEASON}")

    all_data = {
        "standings": {"east": [], "west": []},
        "recent_games": [],
        "french_players": [],
    }

    # 1. Classements
    print("\n[1/3] CLASSEMENTS")
    all_data["standings"] = collect_standings()

    # 2. Matchs récents
    print("\n[2/3] MATCHS RECENTS")
    all_data["recent_games"] = collect_recent_games(days=3)

    # 3. Stats joueurs français
    print("\n[3/3] JOUEURS FRANCAIS")
    all_data["french_players"] = collect_french_players_stats()

    # Résumé
    total_standings = len(all_data["standings"]["east"]) + len(all_data["standings"]["west"])
    total_games = len(all_data["recent_games"])
    total_player_games = len(all_data["french_players"])

    print(f"\n{'=' * 50}")
    print("RESUME:")
    print(f"  - Classements: {total_standings} equipes")
    print(f"  - Matchs recents: {total_games}")
    print(f"  - Stats joueurs FR: {total_player_games} lignes")

    # Sauvegarder
    payload = {
        "source": "nba_api",
        "sport": "basketball",
        "league": "NBA",
        "season": CURRENT_SEASON,
        "fetched_at": datetime.utcnow().isoformat(),
        "stats": {
            "total_standings": total_standings,
            "total_games": total_games,
            "total_player_games": total_player_games,
        },
        "data": all_data,
    }

    output_file = OUTPUT_DIR / "nba_data.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Donnees sauvegardees dans {output_file}")


if __name__ == "__main__":
    main()
