"""
Script di seed: crea utenti, progetto e task fittizi per testare l'AI assistant.

Uso (dalla root del progetto ai-task-manager):
    python scripts/seed_data.py

Lo script e' idempotente: rilanciandolo NON crea duplicati di utenti/progetti
(li riusa cercando per email/nome). I task vengono invece sempre ricreati
(prima cancellati tutti quelli del progetto seed, poi reinseriti).

Stampa a video gli ID di utenti / progetto / task cosi' li puoi copiare per
testare l'AI assistant (es. "elenca i task assegnati a <user_id>").
"""
import sys
from pathlib import Path

# Permette di lanciare lo script anche da dentro la cartella scripts/
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from datetime import datetime, timezone, timedelta

from models import TaskPriority, TaskStatus, UserRoles
from services.user_service import UserService
from services.project_service import ProjectService
from services.task_service import TaskService
from repositories.task_repository import TaskRepository


SEED_PROJECT_NAME = "Progetto Demo"


def get_or_create_user(user_service: UserService, email: str, name: str, role: UserRoles = UserRoles.USER):
    try:
        user = user_service.get_user_by_email(email)
        print(f"  [=] Utente gia' esistente: {name} ({email}) -> {user.id}")
        return user
    except ValueError:
        user = user_service.create_user(email=email, name=name, role=role)
        print(f"  [+] Utente creato: {name} ({email}) -> {user.id}")
        return user


def get_or_create_project(project_service: ProjectService, name: str, description: str):
    for p in project_service.get_all_projects():
        if p.name == name:
            print(f"  [=] Progetto gia' esistente: {name} -> {p.id}")
            return p
    project = project_service.create_project(name=name, description=description)
    print(f"  [+] Progetto creato: {name} -> {project.id}")
    return project


def main():
    user_service = UserService()
    project_service = ProjectService()
    task_service = TaskService()
    task_repo = TaskRepository()

    print("\n=== UTENTI ===")
    luca = get_or_create_user(user_service, "luca@example.com", "Luca Mambelli", UserRoles.ADMIN)
    anna = get_or_create_user(user_service, "anna@example.com", "Anna Rossi")
    marco = get_or_create_user(user_service, "marco@example.com", "Marco Bianchi")

    print("\n=== PROGETTO ===")
    project = get_or_create_project(
        project_service,
        SEED_PROJECT_NAME,
        "Progetto di test per l'AI assistant",
    )

    # Pulizia task del progetto seed per evitare duplicati ad ogni run
    deleted = task_repo.delete_by_project(project.id)
    if deleted:
        print(f"\n  [-] Eliminati {deleted} task precedenti del progetto seed")

    print("\n=== TASK ===")
    now = datetime.now(timezone.utc)

    task_specs = [
        # (title, description, priority, assigned_to, due_offset_days, status)
        ("Consegnare report mensile",       "Report KPI di maggio",                 TaskPriority.HIGH,   luca.id,  1,  TaskStatus.TODO),
        ("Aggiornare CV",                   "Aggiungere ultimo progetto",           TaskPriority.LOW,    luca.id,  3,  TaskStatus.TODO),
        ("Chiamare cliente Acme",           "Discutere rinnovo contratto",          TaskPriority.HIGH,   luca.id,  5,  TaskStatus.IN_PROGRESS),
        ("Preparare slide demo",            "Demo settimanale per il team",         TaskPriority.MEDIUM, anna.id,  2,  TaskStatus.TODO),
        ("Code review PR #42",              "Modulo autenticazione",                TaskPriority.MEDIUM, anna.id,  7,  TaskStatus.IN_PROGRESS),
        ("Setup ambiente staging",          "Server di test",                       TaskPriority.HIGH,   marco.id, 4,  TaskStatus.TODO),
        ("Pianificare ferie estate",        "Discutere con il team",                TaskPriority.LOW,    marco.id, 20, TaskStatus.TODO),
        ("Task scaduto da rivedere",        "Era in scadenza ieri",                 TaskPriority.HIGH,   luca.id,  -1, TaskStatus.TODO),
        ("Task completato",                 "Gia' fatto, escluso dalle scadenze",   TaskPriority.MEDIUM, luca.id,  2,  TaskStatus.COMPLETED),
        ("Task senza scadenza",             "Nessuna due_date",                     TaskPriority.LOW,    anna.id,  None, TaskStatus.TODO),
    ]

    created_tasks = []
    for title, desc, prio, assignee, offset, status in task_specs:
        due = now + timedelta(days=offset) if offset is not None else None
        task = task_service.create_task(
            title=title,
            project_id=project.id,
            description=desc,
            priority=prio,
            assigned_to=assignee,
            due_date=due,
        )
        # create_task non accetta status: aggiorniamo se diverso dal default TODO
        if status != TaskStatus.TODO:
            task.status = status
            task_repo.update(task)
        created_tasks.append((task, status))
        due_str = due.strftime("%Y-%m-%d") if due else "nessuna"
        print(f"  [+] {title[:35]:<35} | prio={prio.value:<6} | scad={due_str} | -> {task.id}")

    print("\n=== RIEPILOGO ID (per il test AI) ===")
    print(f"  Luca  (admin) : {luca.id}")
    print(f"  Anna          : {anna.id}")
    print(f"  Marco         : {marco.id}")
    print(f"  Progetto      : {project.id}")
    print(f"\nEsempi di prompt per testare l'AI:")
    print(f"  - 'Quali task scadono nei prossimi 7 giorni?'")
    print(f"  - 'Mostra i task urgenti'")
    print(f"  - 'Quali task sono assegnati all'utente {luca.id}?'")
    print(f"  - 'Marca il task {created_tasks[0][0].id} come completato'")
    print()


if __name__ == "__main__":
    main()
