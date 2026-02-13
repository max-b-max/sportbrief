"""
Audio Player Component pour SportBrief Streamlit App
Composant Streamlit pour lire les fichiers audio MP3
"""

import base64
from pathlib import Path
from typing import Optional

import streamlit as st


def render_audio_player(audio_path: Optional[Path]) -> None:
    """
    Affiche un lecteur audio HTML5 pour le fichier MP3 donné.

    Args:
        audio_path: Chemin vers le fichier audio MP3
    """
    if audio_path is None or not audio_path.exists():
        st.info("🔇 Aucun fichier audio disponible")
        return

    try:
        # Lire le fichier audio et l'encoder en base64
        with open(audio_path, "rb") as audio_file:
            audio_bytes = audio_file.read()

        audio_base64 = base64.b64encode(audio_bytes).decode()

        # Créer le lecteur HTML5 avec contrôles
        audio_html = f"""
        <audio controls style="width: 100%;">
            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
            Votre navigateur ne supporte pas l'élément audio.
        </audio>
        """

        st.markdown(audio_html, unsafe_allow_html=True)

        # Afficher les infos du fichier
        file_size_mb = len(audio_bytes) / (1024 * 1024)
        st.caption(f"📁 {audio_path.name} ({file_size_mb:.2f} MB)")

    except Exception as e:
        st.error(f"Erreur lors du chargement de l'audio: {e}")


def render_audio_section(
    audio_path: Optional[Path],
    briefing_text: Optional[str],
    show_text: bool = True
) -> None:
    """
    Affiche la section complète du briefing avec audio et texte.

    Args:
        audio_path: Chemin vers le fichier audio
        briefing_text: Texte du briefing
        show_text: Si True, affiche aussi le texte du briefing
    """
    st.subheader("🎧 Briefing du jour")

    # Lecteur audio
    render_audio_player(audio_path)

    # Texte du briefing (optionnel)
    if show_text and briefing_text:
        with st.expander("📄 Voir le texte du briefing", expanded=False):
            st.markdown(briefing_text)
    elif show_text and not briefing_text:
        st.info("Aucun texte de briefing disponible")
