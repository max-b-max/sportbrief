"""
SportBrief Dashboard - Application Streamlit principale
Interface pour configurer, exécuter et écouter les briefings sportifs
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour les imports
APP_DIR = Path(__file__).parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import streamlit as st
from datetime import datetime

from services.config_manager import get_config_manager
from services.pipeline_runner import get_pipeline_runner
from components.audio_player import render_audio_section
from components.sport_config import render_sport_config_section


# Configuration de la page
st.set_page_config(
    page_title="SportBrief",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)


def init_session_state():
    """Initialise les variables de session Streamlit"""
    if "pipeline_status" not in st.session_state:
        st.session_state.pipeline_status = "idle"  # idle, running, success, error
    if "last_update" not in st.session_state:
        st.session_state.last_update = None
    if "config_dirty" not in st.session_state:
        st.session_state.config_dirty = False
    if "last_error" not in st.session_state:
        st.session_state.last_error = None


def format_datetime(dt: datetime) -> str:
    """Formate une datetime pour l'affichage"""
    if dt is None:
        return "Jamais"
    return dt.strftime("%d/%m/%Y à %H:%M")


def main():
    """Point d'entrée principal de l'application"""
    init_session_state()

    config_manager = get_config_manager()
    pipeline_runner = get_pipeline_runner()

    # Charger les préférences
    preferences = config_manager.load_preferences()

    # === SIDEBAR ===
    with st.sidebar:
        st.title("⚙️ Configuration")

        # Section configuration des sports
        updated_prefs = render_sport_config_section(preferences)

        # Détecter les changements
        if updated_prefs != preferences:
            st.session_state.config_dirty = True

        st.divider()

        # Bouton Sauvegarder
        col1, col2 = st.columns(2)
        with col1:
            save_disabled = not st.session_state.config_dirty
            if st.button(
                "💾 Sauvegarder",
                disabled=save_disabled,
                use_container_width=True,
                type="primary" if st.session_state.config_dirty else "secondary"
            ):
                if config_manager.save_preferences(updated_prefs):
                    st.session_state.config_dirty = False
                    st.success("Configuration sauvegardée!")
                    st.rerun()
                else:
                    st.error("Erreur lors de la sauvegarde")

        with col2:
            if st.button("↩️ Annuler", disabled=save_disabled, use_container_width=True):
                st.session_state.config_dirty = False
                st.rerun()

        # Indicateur de modifications non sauvegardées
        if st.session_state.config_dirty:
            st.warning("⚠️ Modifications non sauvegardées")

    # === ZONE PRINCIPALE ===
    st.title("🏆 SportBrief")
    st.caption("Votre briefing sportif personnalisé")

    # Indicateur de dernière mise à jour
    last_update = pipeline_runner.get_last_update_time()
    if last_update:
        st.info(f"📅 Dernier briefing: {format_datetime(last_update)}")
    else:
        st.info("📅 Aucun briefing généré")

    # Bouton Rafraîchir le pipeline
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        refresh_disabled = st.session_state.pipeline_status == "running"

        if st.button(
            "🔄 Générer un nouveau briefing",
            disabled=refresh_disabled,
            use_container_width=True,
            type="primary"
        ):
            st.session_state.pipeline_status = "running"
            st.session_state.last_error = None

            with st.spinner("Génération du briefing en cours... Cela peut prendre quelques minutes."):
                result = pipeline_runner.run_pipeline(with_audio=True)

            if result.success:
                st.session_state.pipeline_status = "success"
                st.session_state.last_update = datetime.now()
                st.success(f"✅ Briefing généré en {result.duration:.1f}s")
                st.rerun()
            else:
                st.session_state.pipeline_status = "error"
                st.session_state.last_error = result.error
                st.error(f"❌ Erreur: {result.error}")

    # Afficher l'erreur précédente si elle existe
    if st.session_state.last_error and st.session_state.pipeline_status == "error":
        with st.expander("🔍 Détails de l'erreur", expanded=False):
            st.code(st.session_state.last_error)

    st.divider()

    # Section Audio et Texte du briefing
    if pipeline_runner.has_briefing():
        audio_path = pipeline_runner.get_audio_path()
        briefing_text = pipeline_runner.get_briefing_text()

        render_audio_section(
            audio_path=audio_path,
            briefing_text=briefing_text,
            show_text=True
        )
    else:
        st.info("🎙️ Aucun briefing disponible. Cliquez sur 'Générer un nouveau briefing' pour commencer.")

    # Footer
    st.divider()
    st.caption("SportBrief - Propulsé par Gemini et Edge TTS")


if __name__ == "__main__":
    main()
