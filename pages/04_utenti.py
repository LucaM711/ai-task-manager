import streamlit as st

st.set_page_config(page_title="Utenti", layout="wide")

from config.database import ensure_mongo_available
ensure_mongo_available()

from services.user_service import UserService
from models import User, UserRoles
from pages._sidebar import render_current_user_selector

user_service = UserService()

render_current_user_selector()

st.title("👥 Gestione Utenti")


@st.dialog("Conferma eliminazione")
def confirm_delete_user(user: User) -> None:
    """Modale di conferma per la cancellazione di un utente."""
    st.write(f"Sei sicuro di voler eliminare **{user.name}** ({user.email})?")
    st.caption("I task assegnati a questo utente verranno automaticamente de-assegnati.")
    col_yes, col_no = st.columns(2)
    with col_yes:
        if st.button("🗑️ Sì, elimina", type="primary", use_container_width=True):
            user_service.delete_user(user.id)
            # se l'utente eliminato era quello corrente, resetta
            if st.session_state.get("current_user_id") == user.id:
                st.session_state.current_user_id = None
            st.toast("Utente eliminato!", icon="🗑️")
            st.rerun()
    with col_no:
        if st.button("Annulla", use_container_width=True):
            st.rerun()


# --- CREA NUOVO UTENTE ---
with st.expander("➕ Crea nuovo utente"):
    with st.form("create_user_form", clear_on_submit=True):
        new_name = st.text_input("Nome")
        new_email = st.text_input("Email")
        new_role = st.selectbox(
            "Ruolo",
            options=list(UserRoles),
            format_func=lambda r: r.value,
        )
        submit = st.form_submit_button("Crea utente")

        if submit:
            if not new_name.strip() or not new_email.strip():
                st.error("Nome ed email sono obbligatori.")
            else:
                email_taken = False
                try:
                    user_service.get_user_by_email(new_email.strip())
                    email_taken = True
                except ValueError:
                    pass
                if email_taken:
                    st.error(f"Email '{new_email.strip()}' già usata.")
                else:
                    user_service.create_user(
                        name=new_name.strip(),
                        email=new_email.strip(),
                        role=new_role,
                    )
                    st.toast("Utente creato!", icon="✅")
                    st.rerun()

st.divider()

# --- LISTA UTENTI ESISTENTI ---
st.subheader("Utenti esistenti")

users = user_service.get_all_users()

if not users:
    st.info("Nessun utente. Creane uno qui sopra.")
else:
    for user in users:
        with st.expander(f"👤 {user.name}  —  {user.email}  ({user.role.value})"):

            # --- Form modifica (solo nome, l'email è la chiave logica) ---
            with st.form(f"edit_form_{user.id}"):
                edit_name = st.text_input(
                    "Nome",
                    value=user.name,
                    key=f"name_{user.id}",
                )
                st.caption(f"Email: `{user.email}` (non modificabile)")
                st.caption(f"Ruolo: `{user.role.value}` (non modificabile)")
                save = st.form_submit_button("💾 Salva modifiche")

                if save:
                    if not edit_name.strip():
                        st.error("Il nome non può essere vuoto.")
                    else:
                        user_service.update_user(user.id, name=edit_name.strip())
                        st.toast("Modifiche salvate!", icon="💾")
                        st.rerun()

            st.divider()

            if st.button(
                "🗑️ Elimina utente",
                key=f"delete_{user.id}",
                type="primary",
            ):
                confirm_delete_user(user)
