"""
Sport Config Component pour SportBrief Streamlit App
Interface de configuration alignée sur user_preferences.json
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

# Ajouter le répertoire parent au path pour les imports
APP_DIR = Path(__file__).parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import streamlit as st

from services.config_manager import get_config_manager


# ========== LEAGUES DATABASE ==========
# Ligues disponibles par sport (à enrichir)
LEAGUES_DATABASE = {
    "football": [
        "Ligue 1", "Premier League", "La Liga", "Bundesliga", "Serie A",
        "Champions League", "Europa League", "Euro", "Coupe du Monde"
    ],
    "basketball": [
        "NBA", "Euroleague", "Pro A", "FIBA World Cup", "Olympic Games"
    ],
    "rugby": [
        "Top 14", "Champions Cup", "Six Nations", "Coupe du Monde",
        "Coupe du Monde Feminine", "Rugby Championship"
    ],
    "handball": [
        "Starligue", "Division 1 Women", "Champions League",
        "World Championship", "World Championship Women", "Olympic Games"
    ],
    "volleyball": [
        "Ligue A", "Ligue A Feminine", "Champions League",
        "World Championship", "World Championship Women", "Olympic Games"
    ],
    "tennis": [
        "Australian Open", "Roland Garros", "Wimbledon", "US Open",
        "Masters 1000", "WTA 1000", "ATP Finals", "Davis Cup"
    ],
    "formule1": [
        "Championnat du Monde F1", "Grands Prix"
    ],
    "mma": [
        "UFC", "Bellator", "PFL", "ONE Championship"
    ],
    "biathlon": [
        "Coupe du Monde IBU", "Championnats du Monde", "Jeux Olympiques"
    ],
    "pingpong": [
        "Championnats du Monde ITTF", "WTT", "Olympic Games"
    ]
}

# Options de filtre joueurs par sport
PLAYER_FILTER_OPTIONS = {
    "all": "Tous les joueurs/athlètes",
    "all_french": "Français uniquement",
    "french_top_ranked": "Top français classés",
    "custom": "Liste personnalisée"
}


def render_sport_toggle(
    sport: str,
    icon: str,
    enabled: bool
) -> bool:
    """Affiche un toggle ON/OFF pour un sport."""
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"### {icon} {sport.capitalize()}")
    with col2:
        new_value = st.toggle(
            label=f"Activer {sport}",
            value=enabled,
            key=f"sport_toggle_{sport}",
            label_visibility="collapsed"
        )
    return new_value


def render_leagues_selector(sport: str, current_leagues: List[str]) -> List[str]:
    """Affiche le sélecteur de ligues/compétitions."""
    available_leagues = LEAGUES_DATABASE.get(sport, [])

    if not available_leagues:
        return current_leagues

    selected = st.multiselect(
        label="🏆 Compétitions à suivre",
        options=available_leagues,
        default=[l for l in current_leagues if l in available_leagues],
        key=f"{sport}_leagues",
        placeholder="Sélectionner des compétitions..."
    )
    return selected


def render_teams_selector(sport: str, current_teams: List[dict]) -> List[dict]:
    """
    Affiche le sélecteur d'équipes avec 2 catégories: Clubs et Nations.
    Retourne une liste de dicts {name, aliases, type/reason}.
    """
    config_manager = get_config_manager()
    all_teams = config_manager.get_teams_for_sport(sport)

    if not all_teams:
        return current_teams

    # Séparer clubs et nations
    clubs = [t for t in all_teams if t.get("type") in ["club", "franchise", "team"]]
    nations = [t for t in all_teams if t.get("type") == "national"]

    # Extraire les noms actuellement sélectionnés
    current_names = {t.get("name") for t in current_teams if isinstance(t, dict)}

    selected_teams = []

    # Sélecteur Clubs
    if clubs:
        club_options = [t["name"] for t in clubs]
        club_defaults = [name for name in club_options if name in current_names]

        selected_clubs = st.multiselect(
            label="🏟️ Clubs / Équipes",
            options=club_options,
            default=club_defaults,
            key=f"{sport}_clubs",
            placeholder="Choisir des clubs..."
        )

        # Convertir en format user_preferences
        for name in selected_clubs:
            team_data = next((t for t in clubs if t["name"] == name), None)
            if team_data:
                selected_teams.append({
                    "name": team_data["name"],
                    "aliases": team_data.get("aliases", []),
                    "reason": "Club sélectionné"
                })

    # Sélecteur Nations
    if nations:
        nation_options = [t["name"] for t in nations]
        nation_defaults = [name for name in nation_options if name in current_names]

        selected_nations = st.multiselect(
            label="🏳️ Équipes nationales",
            options=nation_options,
            default=nation_defaults,
            key=f"{sport}_nations",
            placeholder="Choisir des nations..."
        )

        for name in selected_nations:
            team_data = next((t for t in nations if t["name"] == name), None)
            if team_data:
                selected_teams.append({
                    "name": team_data["name"],
                    "aliases": team_data.get("aliases", []),
                    "type": "national_team"
                })

    return selected_teams


def render_players_filter(sport: str, current_config: dict) -> dict:
    """
    Affiche le filtre joueurs/athlètes.
    Retourne un dict avec la config (players: "all_french" | list | etc.)
    """
    # Déterminer le champ selon le sport
    field_name = _get_player_field_name(sport)
    if not field_name:
        return {}

    current_value = current_config.get(field_name, "all_french")

    # Déterminer le type actuel
    if isinstance(current_value, list):
        current_type = "custom"
        custom_list = current_value
    elif current_value in PLAYER_FILTER_OPTIONS:
        current_type = current_value
        custom_list = []
    else:
        current_type = "all_french"
        custom_list = []

    st.markdown(f"**🏃 {_get_player_label(sport)}**")

    filter_type = st.radio(
        label="Filtre",
        options=list(PLAYER_FILTER_OPTIONS.keys()),
        index=list(PLAYER_FILTER_OPTIONS.keys()).index(current_type) if current_type in PLAYER_FILTER_OPTIONS else 1,
        format_func=lambda x: PLAYER_FILTER_OPTIONS[x],
        key=f"{sport}_player_filter",
        horizontal=True,
        label_visibility="collapsed"
    )

    result = {}

    if filter_type == "custom":
        # Afficher la liste personnalisée
        config_manager = get_config_manager()
        all_teams = config_manager.get_teams_for_sport(sport)
        athletes = [t for t in all_teams if t.get("type") in ["player", "driver", "fighter", "athlete"]]

        if athletes:
            athlete_options = [t["name"] for t in athletes]
            current_athletes = custom_list if isinstance(custom_list, list) else []

            selected = st.multiselect(
                label="Sélectionner les athlètes",
                options=athlete_options,
                default=[a for a in current_athletes if a in athlete_options],
                key=f"{sport}_custom_athletes",
                placeholder="Choisir des athlètes..."
            )
            result[field_name] = selected
        else:
            # Champ texte libre si pas de base
            athletes_text = st.text_input(
                label="Noms des athlètes (séparés par des virgules)",
                value=", ".join(custom_list) if custom_list else "",
                key=f"{sport}_athletes_text"
            )
            if athletes_text:
                result[field_name] = [a.strip() for a in athletes_text.split(",") if a.strip()]
            else:
                result[field_name] = []
    else:
        result[field_name] = filter_type

    return result


def _get_player_field_name(sport: str) -> Optional[str]:
    """Retourne le nom du champ joueur selon le sport."""
    mapping = {
        "basketball": "players",
        "tennis": "players",
        "pingpong": "players",
        "formule1": "drivers",
        "mma": "fighters",
        "biathlon": "athletes",
        "ski_alpin": "athletes"
    }
    return mapping.get(sport)


def _get_player_label(sport: str) -> str:
    """Retourne le label pour les joueurs selon le sport."""
    labels = {
        "basketball": "Joueurs",
        "tennis": "Joueurs",
        "pingpong": "Joueurs",
        "formule1": "Pilotes",
        "mma": "Combattants",
        "biathlon": "Athlètes",
        "ski_alpin": "Athlètes"
    }
    return labels.get(sport, "Athlètes")


def render_focus_selector(sport: str, current_focus: str) -> str:
    """Affiche un champ pour décrire le focus."""
    focus = st.text_input(
        label="🎯 Focus (description)",
        value=current_focus or "",
        key=f"{sport}_focus",
        placeholder="Ex: french_players_and_standings"
    )
    return focus


def render_standings_config(sport: str, current_config: dict) -> dict:
    """Affiche la config des classements (pour basketball notamment)."""
    if sport != "basketball":
        return {}

    st.markdown("**📊 Classements**")

    current_standings = current_config.get("standings", {})

    col1, col2 = st.columns(2)

    with col1:
        show_top = st.checkbox(
            "Afficher le top des équipes",
            value=current_standings.get("show_top_teams", True),
            key=f"{sport}_show_top"
        )

        top_count = st.number_input(
            "Nombre d'équipes",
            min_value=1,
            max_value=15,
            value=current_standings.get("top_count", 5),
            key=f"{sport}_top_count"
        )

    with col2:
        show_conferences = st.checkbox(
            "Afficher les 2 conférences",
            value=current_standings.get("show_both_conferences", True),
            key=f"{sport}_conferences"
        )

    return {
        "standings": {
            "show_top_teams": show_top,
            "top_count": top_count,
            "show_both_conferences": show_conferences
        }
    }


def render_extraordinary_performances(sport: str, current_config: dict) -> dict:
    """Affiche la config des performances exceptionnelles (basketball)."""
    if sport != "basketball":
        return {}

    st.markdown("**🌟 Performances exceptionnelles**")
    st.caption("Inclure les perfs de joueurs non-français dépassant ces seuils")

    current_perf = current_config.get("extraordinary_performances", {})
    thresholds = current_perf.get("thresholds", {})

    enabled = st.checkbox(
        "Activer",
        value=current_perf.get("enabled", True),
        key=f"{sport}_perf_enabled"
    )

    if enabled:
        col1, col2, col3 = st.columns(3)

        with col1:
            points = st.number_input(
                "Points min",
                min_value=20,
                max_value=60,
                value=thresholds.get("points", 40),
                key=f"{sport}_perf_points"
            )

        with col2:
            rebounds = st.number_input(
                "Rebonds min",
                min_value=10,
                max_value=30,
                value=thresholds.get("rebounds", 20),
                key=f"{sport}_perf_rebounds"
            )

        with col3:
            assists = st.number_input(
                "Passes min",
                min_value=10,
                max_value=25,
                value=thresholds.get("assists", 15),
                key=f"{sport}_perf_assists"
            )

        triple_double = st.checkbox(
            "Inclure triple-doubles",
            value=thresholds.get("triple_double", True),
            key=f"{sport}_triple_double"
        )

        return {
            "extraordinary_performances": {
                "enabled": True,
                "thresholds": {
                    "points": points,
                    "rebounds": rebounds,
                    "assists": assists,
                    "triple_double": triple_double
                }
            }
        }

    return {"extraordinary_performances": {"enabled": False}}


def render_olympics_section(current_olympics: dict) -> dict:
    """Affiche la section Jeux Olympiques."""
    st.markdown("### 🏅 Jeux Olympiques")

    enabled = st.checkbox(
        "Suivre les JO",
        value=current_olympics.get("enabled", True),
        key="olympics_enabled"
    )

    if not enabled:
        return {"enabled": False}

    priority_mode = st.toggle(
        "🏅 Mode JO prioritaire — les JO deviennent le sport principal du briefing",
        value=current_olympics.get("priority_mode", False),
        key="olympics_priority_mode"
    )
    if priority_mode:
        st.info("Les Jeux Olympiques seront traités en priorité absolue, avant tous les autres sports.")

    current_next = current_olympics.get("next_games", {})

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**❄️ JO d'hiver**")
        winter = current_next.get("winter", {})
        winter_name = st.text_input(
            "Nom",
            value=winter.get("name", "Milano-Cortina 2026"),
            key="olympics_winter_name"
        )
        winter_date = st.text_input(
            "Date",
            value=winter.get("date", "2026-02-06"),
            key="olympics_winter_date"
        )
        winter_location = st.text_input(
            "Lieu",
            value=winter.get("location", "Milan/Cortina, Italie"),
            key="olympics_winter_location"
        )

    with col2:
        st.markdown("**☀️ JO d'été**")
        summer = current_next.get("summer", {})
        summer_name = st.text_input(
            "Nom",
            value=summer.get("name", "Los Angeles 2028"),
            key="olympics_summer_name"
        )
        summer_date = st.text_input(
            "Date",
            value=summer.get("date", "2028-07-14"),
            key="olympics_summer_date"
        )
        summer_location = st.text_input(
            "Lieu",
            value=summer.get("location", "Los Angeles, USA"),
            key="olympics_summer_location"
        )

    # Focus JO
    focus_options = ["qualifications", "preparation", "athletes_francais", "calendrier", "medals"]
    current_focus = current_olympics.get("focus", ["qualifications", "athletes_francais"])

    selected_focus = st.multiselect(
        "Focus JO",
        options=focus_options,
        default=[f for f in current_focus if f in focus_options],
        key="olympics_focus"
    )

    return {
        "enabled": True,
        "priority_mode": priority_mode,
        "next_games": {
            "winter": {
                "name": winter_name,
                "date": winter_date,
                "location": winter_location
            },
            "summer": {
                "name": summer_name,
                "date": summer_date,
                "location": summer_location
            }
        },
        "focus": selected_focus
    }


def render_priority_selector(
    all_selected_items: List[dict],
    current_priorities: dict
) -> dict:
    """
    Affiche le sélecteur de priorités (1-3 items).
    all_selected_items: liste de {name, sport, type}
    current_priorities: dict actuel des priorités
    """
    st.markdown("### ⭐ Priorités du briefing (1-3)")
    st.caption("Ces éléments auront un focus prioritaire dans le briefing")

    if not all_selected_items:
        st.info("Sélectionnez d'abord des équipes ou athlètes")
        return current_priorities

    # Options disponibles
    options = [f"{item['name']} ({item['sport']})" for item in all_selected_items]

    # Trouver les priorités actuelles
    current_priority_names = list(current_priorities.get("teams_priorities", {}).keys())
    default_selection = [
        opt for opt in options
        if any(name in opt for name in current_priority_names)
    ][:3]

    selected = st.multiselect(
        label="Priorités",
        options=options,
        default=default_selection,
        max_selections=3,
        key="briefing_priorities",
        label_visibility="collapsed",
        placeholder="Choisir 1 à 3 priorités..."
    )

    # Construire le dict de priorités
    teams_priorities = {}
    for i, opt in enumerate(selected):
        # Extraire le nom
        name = opt.split(" (")[0]
        level = "maximum" if i == 0 else ("high" if i == 1 else "medium")
        teams_priorities[name] = {
            "level": level,
            "topics": ["resultats", "classement", "actualites"] if level != "medium" else ["resultats"],
            "description": f"Priorité {i+1}"
        }

    return {
        "global": current_priorities.get("global", {
            "content_order": ["resultats", "classements", "actualites"],
            "style": "resultats_first"
        }),
        "teams_priorities": teams_priorities,
        "default_team_priority": current_priorities.get("default_team_priority", {
            "level": "normal",
            "topics": ["resultats"]
        })
    }


def render_duration_selector(current_duration: dict) -> dict:
    """Affiche le sélecteur de durée du briefing."""
    current_mode = current_duration.get("mode", "medium") if isinstance(current_duration, dict) else current_duration

    duration_options = {
        "short": "⚡ Court (2-4 min)",
        "medium": "📻 Moyen (5-10 min)",
        "long": "📚 Long (10+ min)"
    }

    st.markdown("### ⏱️ Durée du briefing")

    durations = list(duration_options.keys())
    current_index = durations.index(current_mode) if current_mode in durations else 1

    selected = st.radio(
        label="Durée",
        options=durations,
        index=current_index,
        format_func=lambda x: duration_options[x],
        key="briefing_duration",
        label_visibility="collapsed",
        horizontal=True
    )

    return {
        "mode": selected,
        "options": {
            "short": {"duration_minutes": "2-4", "word_count": "300-600"},
            "medium": {"duration_minutes": "5-10", "word_count": "750-1500"},
            "long": {"duration_minutes": "10+", "word_count": "1500-3000"}
        }
    }


def render_sport_config_section(
    preferences: Dict,
    on_preferences_change: Optional[Callable] = None
) -> Dict:
    """
    Affiche la section complète de configuration.
    Compatible avec la structure de user_preferences.json.
    """
    config_manager = get_config_manager()
    teams_db = config_manager.load_teams_database()

    updated_prefs = preferences.copy()
    sports_prefs = updated_prefs.get("sports", {})

    # Collecter tous les items sélectionnés pour les priorités
    all_selected_items = []

    st.markdown("## ⚙️ Configuration des sports")

    # Pour chaque sport dans la base
    for sport in teams_db.keys():
        sport_data = teams_db[sport]
        icon = sport_data.get("icon", "🏆")
        sport_prefs = sports_prefs.get(sport, {"enabled": False})

        with st.container():
            # Toggle ON/OFF
            enabled = render_sport_toggle(
                sport=sport,
                icon=icon,
                enabled=sport_prefs.get("enabled", False)
            )
            sport_prefs["enabled"] = enabled

            # Configuration détaillée si activé
            if enabled:
                with st.expander("Configurer", expanded=False):
                    # 1. Ligues
                    current_leagues = sport_prefs.get("leagues", [])
                    sport_prefs["leagues"] = render_leagues_selector(sport, current_leagues)

                    # 2. Équipes (clubs + nations)
                    current_teams = sport_prefs.get("teams", [])
                    selected_teams = render_teams_selector(sport, current_teams)
                    sport_prefs["teams"] = selected_teams

                    # Ajouter aux items pour priorités
                    for team in selected_teams:
                        all_selected_items.append({
                            "name": team.get("name"),
                            "sport": sport,
                            "type": "team"
                        })

                    # 3. Filtre joueurs/athlètes (selon le sport)
                    player_config = render_players_filter(sport, sport_prefs)
                    sport_prefs.update(player_config)

                    # 4. Classements (basketball)
                    standings_config = render_standings_config(sport, sport_prefs)
                    sport_prefs.update(standings_config)

                    # 5. Performances exceptionnelles (basketball)
                    perf_config = render_extraordinary_performances(sport, sport_prefs)
                    sport_prefs.update(perf_config)

                    # 6. Focus
                    current_focus = sport_prefs.get("focus", "")
                    sport_prefs["focus"] = render_focus_selector(sport, current_focus)

            sports_prefs[sport] = sport_prefs
            st.divider()

    updated_prefs["sports"] = sports_prefs

    # Section Jeux Olympiques
    st.markdown("---")
    current_olympics = updated_prefs.get("olympics", {})
    updated_prefs["olympics"] = render_olympics_section(current_olympics)

    # Section Priorités globales
    st.markdown("---")
    current_priorities = updated_prefs.get("briefing_priorities", {})
    updated_prefs["briefing_priorities"] = render_priority_selector(
        all_selected_items,
        current_priorities
    )

    st.divider()

    # Durée du briefing
    current_duration = updated_prefs.get("briefing_duration", {"mode": "medium"})
    updated_prefs["briefing_duration"] = render_duration_selector(current_duration)

    return updated_prefs
