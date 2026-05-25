from typing import Iterator, Optional

from ai.agent import get_agent


def _build_messages(message: str, current_user: Optional[dict]) -> list[dict]:
    """Costruisce la lista di messaggi da passare all'agent.

    Se è disponibile un utente corrente, prepende un messaggio system di
    contesto in modo che l'AI possa risolvere "i miei task" senza fare lookup.
    """
    messages: list[dict] = []
    if current_user:
        messages.append({
            "role": "system",
            "content": (
                f"CONTESTO UTENTE: l'utente corrente è "
                f"{current_user['name']} (id: {current_user['id']})."
            ),
        })
    messages.append({"role": "user", "content": message})
    return messages


class AIService:
    def __init__(self):
        self.agent = get_agent()

    def ask(
        self,
        message: str,
        session_id: str = "default",
        current_user: Optional[dict] = None,
    ) -> str:
        """Invia un messaggio all'agent e ritorna la risposta completa.

        Args:
            message: il testo dell'utente.
            session_id: identificatore della conversazione (usato come thread_id
                        di langgraph per separare le memorie).
            current_user: dict opzionale con `name` e `id` dell'utente loggato.
                          Se passato, l'agent sa chi è "io"/"me"/"miei".

        Returns:
            La risposta testuale dell'agent.
        """
        result = self.agent.invoke(
            {"messages": _build_messages(message, current_user)},
            config={"configurable": {"thread_id": session_id}},
        )
        return result["messages"][-1].content

    def ask_stream(
        self,
        message: str,
        session_id: str = "default",
        current_user: Optional[dict] = None,
    ) -> Iterator[str]:
        """Versione streaming: yielda i chunk testuali della risposta finale.

        Filtra i chunk emessi dai tool (nodo "tools") e quelli vuoti, in modo
        che il chiamante riceva solo i token dell'AIMessage finale.
        Compatibile con st.write_stream.
        """
        stream = self.agent.stream(
            {"messages": _build_messages(message, current_user)},
            config={"configurable": {"thread_id": session_id}},
            stream_mode="messages",
        )
        for chunk, metadata in stream:
            if metadata.get("langgraph_node") == "tools":
                continue
            text = getattr(chunk, "content", "")
            if text:
                yield text
