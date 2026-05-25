import uuid
import streamlit as st

st.set_page_config(page_title="Assistente AI", layout="wide")

from config.database import ensure_mongo_available
ensure_mongo_available()

from services.ai_service import AIService
from pages._sidebar import render_current_user_selector

current_user = render_current_user_selector()

st.title("🤖 Assistente AI")

st.caption(
    "Chiedi all'assistente di mostrarti task urgenti, scadenze, storico, "
    "oppure di creare un task o cambiarne stato/priorità. "
    "Risponde in italiano e ricorda la conversazione."
)


# --- Singleton dell'AIService (carica una sola volta Ollama + tool + memory) ---
@st.cache_resource(show_spinner="Inizializzo l'assistente...")
def get_ai_service() -> AIService:
    return AIService()


ai_service = get_ai_service()


# --- Stato sessione: thread_id (memoria AI persistente) + messaggi (rendering UI) ---
# thread_id legato all'utente: ogni utente mantiene una conversazione persistente
# separata in MongoDB. Cambiando utente cambia automaticamente il thread.
default_thread_id = f"user-{current_user.id}" if current_user else "guest"
if "thread_id" not in st.session_state or st.session_state.get("_thread_user_id") != (current_user.id if current_user else None):
    st.session_state.thread_id = default_thread_id
    st.session_state._thread_user_id = current_user.id if current_user else None
    st.session_state.messages = []  # UI pulita per il nuovo utente (l'agent ricorda lato MongoDB)

if "messages" not in st.session_state:
    st.session_state.messages = []


# --- Sidebar: reset conversazione ---
with st.sidebar:
    st.subheader("Conversazione")
    st.caption(f"Thread: `{st.session_state.thread_id}`")
    st.caption("Memoria persistente su MongoDB ✓")
    if st.button("🧹 Nuova conversazione", use_container_width=True):
        # Reset UI + nuovo thread_id (i checkpoint del vecchio thread restano in MongoDB)
        st.session_state.messages = []
        suffix = uuid.uuid4().hex[:8]
        st.session_state.thread_id = (
            f"user-{current_user.id}-{suffix}" if current_user else f"guest-{suffix}"
        )
        st.toast("Conversazione resettata", icon="🧹")
        st.rerun()


# --- Render dei messaggi esistenti ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# --- Input utente ---
user_input = st.chat_input("Scrivi qui...")
if user_input:
    # Mostra subito il messaggio utente
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Spinner finché non arriva il primo token, poi streaming token-by-token.
    # Lo spinner copre l'attesa quando il modello sta ragionando o chiamando tool.
    with st.chat_message("assistant"):
        try:
            stream = ai_service.ask_stream(
                user_input,
                session_id=st.session_state.thread_id,
                current_user=(
                    {"id": current_user.id, "name": current_user.name}
                    if current_user
                    else None
                ),
            )
            with st.spinner("Sto pensando..."):
                first_chunk = next(stream, "")

            def chunks():
                if first_chunk:
                    yield first_chunk
                yield from stream

            response = st.write_stream(chunks())
        except Exception as e:
            import logging
            logging.error("AI stream error", exc_info=True)
            response = f"⚠️ Errore: {e}"
            st.error(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
