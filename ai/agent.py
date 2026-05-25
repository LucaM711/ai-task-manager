"""
Costruzione dell'AI Agent: ChatOllama (qwen3.5:2b locale) + tool + memoria persistente.

La memoria conversazionale è gestita dal checkpointer `MongoDBSaver` di
langgraph-checkpoint-mongodb, che persiste i checkpoint nelle collezioni
`checkpoints` e `checkpoint_writes` del database configurato. Sopravvive al
riavvio di Streamlit. Ogni thread_id mantiene una conversazione separata.
"""
from datetime import date
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent, ToolNode
from langgraph.checkpoint.mongodb import MongoDBSaver

from config.settings import settings
from config.database import MongoDBClient
from ai.prompts import SYSTEM_PROMPT
from ai.tools import (
    get_all_projects,
    get_all_users,
    get_urgent_tasks,
    get_tasks_by_user,
    get_tasks_by_deadline,
    get_tasks_by_priority,
    get_task_by_title,
    get_tasks_by_status,
    get_task_history,
    get_task_attachments,
    update_task_status,
    update_task_priority,
    update_task_description,
    create_task,
    delete_task,
    delete_tasks,
)

TOOLS = [
    get_all_projects,
    get_all_users,
    get_urgent_tasks,
    get_tasks_by_user,
    get_tasks_by_deadline,
    get_tasks_by_priority,
    get_task_by_title,
    get_tasks_by_status,
    get_task_history,
    get_task_attachments,
    update_task_status,
    update_task_priority,
    update_task_description,
    create_task,
    delete_task,
    delete_tasks,
]

_agent = None  # singleton, costruito al primo accesso


def _build_agent():
    """Costruisce LLM + system prompt + tool + agent + checkpointer.

    Chiamato una sola volta (vedi get_agent).
    """
    llm = ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        temperature=settings.llm_temperature,
        num_ctx=4096,  # finestra esplicita: serve per system prompt + 10 tool schemas + history
        num_predict=2048,  # default Ollama=128 tronca elenchi lunghi a metà
        reasoning=False,  # disattiva il thinking mode di Qwen 3 (no <think>...</think>)
        timeout=120,  # 2 minuti: evita blocchi infiniti se Ollama è offline o lento
    )

    system_text = SYSTEM_PROMPT.format(current_date=date.today().isoformat())

    # Checkpointer persistente: i thread_id sopravvivono al riavvio Streamlit.
    # Riusiamo il MongoClient di MongoDBClient — stesso DB del resto del progetto.
    checkpointer = MongoDBSaver(
        client=MongoDBClient().client,
        db_name=settings.mongodb_db_name,
    )

    # handle_tool_errors=True: cattura QUALSIASI eccezione del tool (es. ValueError
    # da get_task) e la passa al modello come ToolMessage di errore, invece di
    # propagarla e crashare lo stream. Il modello può così correggere e riprovare.
    tool_node = ToolNode(TOOLS, handle_tool_errors=True)

    return create_react_agent(
        model=llm,
        tools=tool_node,
        prompt=system_text,
        checkpointer=checkpointer,
    )


def get_agent():
    """Ritorna l'agent (singleton) pronto all'uso.

    Uso:
        agent = get_agent()
        result = agent.invoke(
            {"messages": [{"role": "user", "content": "ciao"}]},
            config={"configurable": {"thread_id": "demo"}},
        )
        # result["messages"][-1].content contiene la risposta dell'agent
    """
    global _agent
    if _agent is None:
        _agent = _build_agent()
    return _agent
