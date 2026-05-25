"""Helper di sidebar condiviso tra le pagine Streamlit.

File prefissato con underscore: Streamlit non lo registra come pagina ma
rimane importabile come modulo Python.
"""
from typing import Optional
import streamlit as st

from repositories.user_repository import UserRepository
from models import User


def render_current_user_selector() -> Optional[User]:
    """Mostra un selectbox in sidebar per scegliere l'utente corrente.

    Salva la scelta in st.session_state.current_user_id. Le pagine devono
    chiamare questo helper PRIMA di leggere lo state.

    Returns:
        L'oggetto User selezionato, o None se nessun utente è scelto/esiste.
    """
    users = UserRepository().find_all()

    with st.sidebar:
        st.subheader("👤 Utente corrente")

        if not users:
            st.caption("Nessun utente. Creane uno da '👥 Gestione Utenti'.")
            st.session_state.current_user_id = None
            return None

        # Indice di default: quello già salvato in session_state, altrimenti il primo
        current_id = st.session_state.get("current_user_id")
        user_ids = [u.id for u in users]
        default_index = user_ids.index(current_id) if current_id in user_ids else 0

        selected = st.selectbox(
            "Sono…",
            options=users,
            index=default_index,
            format_func=lambda u: f"{u.name} ({u.email})",
            key="_current_user_selectbox",
            label_visibility="collapsed",
        )
        st.session_state.current_user_id = selected.id
        return selected


def get_current_user_id(fallback: str = "user") -> str:
    """Ritorna l'id dell'utente corrente, o `fallback` se nessuno è scelto.

    Da usare al posto del placeholder `CHANGED_BY = "user"` nelle pagine.
    """
    return st.session_state.get("current_user_id") or fallback
