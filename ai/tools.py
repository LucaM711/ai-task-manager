from datetime import datetime, timezone
from typing import List
from langchain_core.tools import tool
from services.task_service import TaskService
from services.project_service import ProjectService
from services.attachment_service import AttachmentService
from repositories.user_repository import UserRepository
from models import TaskStatus, TaskPriority

task_service = TaskService()
project_service = ProjectService()
attachment_service = AttachmentService()
user_repo = UserRepository()

AI_CHANGED_BY = "ai_assistant"


@tool
def get_all_projects() -> str:
    """Elenca tutti i progetti (id, nome). Chiamalo prima di create_task se non hai il project_id."""
    projects = project_service.get_all_projects()
    if not projects:
        return "Nessun progetto esistente."
    return "\n".join(f"- [{p.id}] {p.name}" for p in projects)


@tool
def get_all_users() -> str:
    """Elenca tutti gli utenti (id, nome, email). Chiamalo prima di get_tasks_by_user se hai solo il nome."""
    users = user_repo.find_all()
    if not users:
        return "Nessun utente esistente."
    return "\n".join(f"- [{u.id}] {u.name} ({u.email})" for u in users)


@tool
def get_urgent_tasks() -> str:
    """SOLO task ad alta priorità con scadenza ENTRO 3 GIORNI. È un sottoinsieme stretto.
    Per "tutti i task ad alta priorità" usa get_tasks_by_priority('high')."""
    tasks = task_service.get_urgent_tasks()
    if not tasks:
        return "Nessun task urgente."
    return "\n".join(
        f"- [{t.id}] {t.title} — scadenza {t.due_date.strftime('%Y-%m-%d')} — priorità {t.priority.value}"
        for t in tasks
    )


@tool
def get_tasks_by_user(user_id: str) -> str:
    """Task assegnati a un utente. user_id è un UUID, non un nome."""
    tasks = task_service.get_tasks_by_user(user_id)
    if not tasks:
        return f"Nessun task assegnato a {user_id}."
    return "\n".join(
        f"- [{t.id}] {t.title} — stato {t.status.value} — priorità {t.priority.value}"
        for t in tasks
    )


@tool
def get_tasks_by_deadline(days: int) -> str:
    """Task in scadenza entro N giorni (esclusi i completati)."""
    tasks = task_service.get_tasks_by_deadline(days)
    if not tasks:
        return f"Nessun task in scadenza entro {days} giorni."
    return "\n".join(
        f"- [{t.id}] {t.title} — scadenza {t.due_date.strftime('%Y-%m-%d')} — priorità {t.priority.value}"
        for t in tasks
    )


@tool
def get_tasks_by_priority(priority: str) -> str:
    """TUTTI i task con priorità data ("low", "medium", "high"), senza filtro scadenza."""
    try:
        priority_enum = TaskPriority(priority)
    except ValueError:
        return f"Priorità '{priority}' non valida. Usa: low, medium, high."
    tasks = task_service.get_tasks_by_priority(priority_enum)
    if not tasks:
        return f"Nessun task con priorità {priority_enum.value}."
    return "\n".join(
        f"- [{t.id}] {t.title} — stato {t.status.value} — "
        f"scadenza {t.due_date.strftime('%Y-%m-%d') if t.due_date else 'N/A'}"
        for t in tasks
    )


@tool
def get_task_by_title(title: str) -> str:
    """Cerca task per titolo (match parziale, case-insensitive). Usalo SEMPRE quando l'utente
    si riferisce a un task per nome — restituisce id, titolo, stato. Se trova più match,
    elencali tutti e chiedi all'utente quale."""
    tasks = task_service.get_tasks_by_title(title)
    if not tasks:
        return f"Nessun task con titolo che contiene '{title}'."
    if len(tasks) == 1:
        t = tasks[0]
        return (
            f"Trovato 1 task: [{t.id}] {t.title} — stato {t.status.value} — "
            f"priorità {t.priority.value}"
        )
    lines = [f"Trovati {len(tasks)} task con '{title}' nel titolo:"]
    lines.extend(
        f"- [{t.id}] {t.title} — stato {t.status.value} — priorità {t.priority.value}"
        for t in tasks
    )
    return "\n".join(lines)


@tool
def get_task_history(task_id: str) -> str:
    """Storico modifiche di un task. task_id è un UUID."""
    task = task_service.get_task(task_id)
    if not task.history:
        return f"Il task '{task.title}' non ha modifiche registrate."
    return "\n".join(
        f"- {h.changed_at.strftime('%Y-%m-%d %H:%M')} | {h.changed_by}: {h.field} {h.old_value} → {h.new_value}"
        for h in task.history
    )


@tool
def get_task_attachments(task_id: str) -> str:
    """Elenca gli allegati di un task (nome, tipo, data). task_id è un UUID."""
    task = task_service.get_task(task_id)
    attachments = attachment_service.get_attachments(task_id)
    if not attachments:
        return f"Il task '{task.title}' non ha allegati."
    lines = [f"Il task '{task.title}' ha {len(attachments)} allegati:"]
    lines.extend(
        f"- {a.filename} ({a.content_type}, caricato il {a.uploaded_at.strftime('%Y-%m-%d')})"
        for a in attachments
    )
    return "\n".join(lines)


@tool
def update_task_status(task_id: str, new_status: str) -> str:
    """Cambia stato task. new_status: "todo" | "in_progress" | "completed". task_id è un UUID."""
    try:
        status_enum = TaskStatus(new_status)
    except ValueError:
        return f"Stato '{new_status}' non valido. Usa: todo, in_progress, completed."
    task = task_service.get_task(task_id)
    task_service.update_task_status(task_id, status_enum, changed_by=AI_CHANGED_BY)
    return f"Task '{task.title}' → stato {status_enum.value}."


@tool
def update_task_priority(task_id: str, new_priority: str) -> str:
    """Cambia priorità task. new_priority: "low" | "medium" | "high". task_id è un UUID."""
    try:
        priority_enum = TaskPriority(new_priority)
    except ValueError:
        return f"Priorità '{new_priority}' non valida. Usa: low, medium, high."
    task = task_service.get_task(task_id)
    task_service.update_task_priority(task_id, priority_enum, changed_by=AI_CHANGED_BY)
    return f"Task '{task.title}' → priorità {priority_enum.value}."


@tool
def update_task_description(task_id: str, new_description: str) -> str:
    """Aggiorna/imposta la descrizione di un task ESISTENTE. NON crea un nuovo task.
    task_id è un UUID (mai un titolo). Per sostituire una descrizione esistente, passa il nuovo testo completo."""
    task = task_service.get_task(task_id)
    task_service.update_task_description(task_id, new_description, changed_by=AI_CHANGED_BY)
    return f"Task '{task.title}' → descrizione aggiornata."


@tool
def get_tasks_by_status(status: str) -> str:
    """TUTTI i task con lo stato dato ("todo", "in_progress", "completed")."""
    try:
        status_enum = TaskStatus(status)
    except ValueError:
        return f"Stato '{status}' non valido. Usa: todo, in_progress, completed."
    tasks = task_service.get_tasks_by_status(status_enum)
    if not tasks:
        return f"Nessun task con stato {status_enum.value}."
    return "\n".join(
        f"- [{t.id}] {t.title} — priorità {t.priority.value} — "
        f"scadenza {t.due_date.strftime('%Y-%m-%d') if t.due_date else 'N/A'}"
        for t in tasks
    )


@tool
def delete_task(task_id: str) -> str:
    """Elimina DEFINITIVAMENTE un SINGOLO task. task_id è un UUID (mai un titolo).
    Per eliminare PIÙ task usa delete_tasks (più veloce)."""
    task = task_service.get_task(task_id)
    title = task.title
    task_service.delete_task(task_id)
    return f"Task '{title}' eliminato."


@tool
def delete_tasks(task_ids: List[str]) -> str:
    """Elimina più task in UNA sola chiamata. task_ids è una lista di UUID.
    Usalo per "elimina tutti i task X": prima recupera gli id (es. get_tasks_by_status),
    poi passa la lista qui — NON chiamare delete_task in loop."""
    if not task_ids:
        return "Nessun id fornito."
    deleted = task_service.delete_tasks(task_ids)
    return f"{deleted} task eliminati."


@tool
def create_task(
    title: str,
    project_id: str,
    description: str = None,
    priority: str = "medium",
    due_date: str = None,
) -> str:
    """Crea un task. project_id è un UUID (usa get_all_projects se hai solo il nome). due_date: 'YYYY-MM-DD' o None."""
    try:
        priority_enum = TaskPriority(priority)
    except ValueError:
        return f"Priorità '{priority}' non valida. Usa: low, medium, high."

    if due_date:
        try:
            due_date_dt = datetime.strptime(due_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            return "Data non valida. Usa formato 'YYYY-MM-DD'."
    else:
        due_date_dt = None

    task = task_service.create_task(
        title=title,
        project_id=project_id,
        description=description,
        priority=priority_enum,
        due_date=due_date_dt,
    )
    return f"Task '{task.title}' creato con id {task.id}."
