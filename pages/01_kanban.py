import streamlit as st

st.set_page_config(page_title="Kanban", layout="wide")

from config.database import ensure_mongo_available
ensure_mongo_available()

from datetime import datetime, time, timezone
from services.task_service import TaskService
from services.project_service import ProjectService
from services.attachment_service import AttachmentService
from services.user_service import UserService
from models import (
    Task,
    TaskStatus,
    TaskPriority,
    STATUS_LABELS,
    PRIORITY_LABELS,
)
from pages._sidebar import render_current_user_selector, get_current_user_id

task_service = TaskService()
project_service = ProjectService()
attachment_service = AttachmentService()
user_service = UserService()

render_current_user_selector()
CHANGED_BY = get_current_user_id()

st.title("📋 Kanban Board")


@st.dialog("Conferma eliminazione")
def confirm_delete_task(task: Task) -> None:
    """Modale di conferma per la cancellazione di un task."""
    st.write(f"Sei sicuro di voler eliminare il task **{task.title}**?")
    if task.attachments:
        st.warning(
            f"⚠️ Verranno eliminati anche **{len(task.attachments)} allegati**."
        )
    st.caption("Operazione irreversibile.")
    col_yes, col_no = st.columns(2)
    with col_yes:
        if st.button("🗑️ Sì, elimina", type="primary", use_container_width=True):
            try:
                task_service.delete_task(task.id)
                st.toast("Task eliminato!", icon="🗑️")
                st.rerun()
            except Exception as e:
                st.error(f"Errore durante l'eliminazione: {e}")
    with col_no:
        if st.button("Annulla", use_container_width=True):
            st.rerun()


# --- Selezione progetto ---
projects = project_service.get_all_projects()

if not projects:
    st.warning("Nessun progetto trovato. Creane uno dalla pagina '📁 Gestione Progetti'.")
    st.stop()

project_names = [p.name for p in projects]
selected_name = st.selectbox("Seleziona progetto", project_names)
selected_project = next((p for p in projects if p.name == selected_name), None)
if not selected_project:
    st.error("Progetto non trovato. Aggiorna la pagina.")
    st.stop()

# --- Lookup utenti (per assegnazione + display) ---
users = user_service.get_all_users()
user_name_by_id = {u.id: u.name for u in users}


# --- Form crea nuovo task ---
with st.expander("➕ Nuovo task"):
    with st.form("create_task_form", clear_on_submit=True):
        new_title = st.text_input("Titolo")
        new_desc = st.text_area("Descrizione (opzionale)")

        col_p, col_s, col_d = st.columns(3)
        with col_p:
            new_priority_label = st.selectbox(
                "Priorità",
                options=list(TaskPriority),
                index=1,  # default MEDIUM
                format_func=lambda p: PRIORITY_LABELS[p],
            )
        with col_s:
            new_status_choice = st.selectbox(
                "Stato iniziale",
                options=list(TaskStatus),
                index=0,  # default TODO
                format_func=lambda s: STATUS_LABELS[s],
            )
        with col_d:
            has_due_date = st.checkbox("Imposta scadenza")
            new_due_date = st.date_input("Scadenza", disabled=not has_due_date)

        # Assegnazione: None = non assegnato. Default = utente corrente se esiste.
        assign_options = [None] + [u.id for u in users]
        current_uid = st.session_state.get("current_user_id")
        default_assign_idx = (
            assign_options.index(current_uid) if current_uid in assign_options else 0
        )
        new_assigned_to = st.selectbox(
            "Assegna a",
            options=assign_options,
            index=default_assign_idx,
            format_func=lambda uid: user_name_by_id.get(uid, "— Nessuno —"),
        )

        submit = st.form_submit_button("Crea task")

        if submit:
            if not new_title.strip():
                st.error("Il titolo è obbligatorio.")
            else:
                due_dt = None
                if has_due_date and new_due_date is not None:
                    due_dt = datetime.combine(
                        new_due_date, time(23, 59), tzinfo=timezone.utc
                    )

                created = task_service.create_task(
                    title=new_title.strip(),
                    project_id=selected_project.id,
                    description=new_desc.strip() or None,
                    priority=new_priority_label,
                    due_date=due_dt,
                    assigned_to=new_assigned_to,
                )

                # Se lo status iniziale è diverso dal default TODO, aggiornalo
                if new_status_choice != TaskStatus.TODO:
                    task_service.update_task_status(
                        created.id,
                        new_status_choice,
                        changed_by=CHANGED_BY,
                    )

                st.toast("Task creato!", icon="✅")
                st.rerun()


# --- Caricamento task raggruppati per status ---
tasks_by_status = task_service.get_tasks_by_project(selected_project.id)


def render_task_card(task: Task) -> None:
    """Disegna una singola card di task con pulsanti di transizione e delete."""
    st.markdown(f"**{task.title}**")
    if task.description:
        st.markdown(f"*{task.description}*")
    st.markdown(f"**Priorità:** {PRIORITY_LABELS[task.priority]}")
    st.markdown(
        f"**Scadenza:** {task.due_date.strftime('%Y-%m-%d') if task.due_date else 'N/A'}"
    )
    if task.assigned_to:
        assigned_label = user_name_by_id.get(task.assigned_to, "⚠️ utente eliminato")
        st.markdown(f"**Assegnato a:** {assigned_label}")

    # Pulsanti di transizione: una colonna per ogni stato diverso dal corrente
    other_statuses = [s for s in TaskStatus if s != task.status]
    cols = st.columns(len(other_statuses))
    for col, target_status in zip(cols, other_statuses):
        with col:
            if st.button(
                f"→ {STATUS_LABELS[target_status]}",
                key=f"move_{task.id}_{target_status.value}",
                use_container_width=True,
            ):
                task_service.update_task_status(
                    task.id, target_status, changed_by=CHANGED_BY
                )
                st.toast(f"Spostato in '{STATUS_LABELS[target_status]}'", icon="🔀")
                st.rerun()

    # Sezione allegati
    with st.expander(f"📎 Allegati ({len(task.attachments)})"):
        uploaded = st.file_uploader(
            "Aggiungi allegato",
            key=f"upload_{task.id}",
            accept_multiple_files=False,
            label_visibility="collapsed",
        )
        # Sentinella: processiamo l'upload una sola volta. Senza questo check,
        # ogni rerun di Streamlit rivede `uploaded != None` e ricarica il file.
        processed_key = f"_processed_upload_{task.id}"
        if uploaded is not None and st.session_state.get(processed_key) != uploaded.file_id:
            attachment_service.upload(
                task_id=task.id,
                file_bytes=uploaded.getvalue(),
                filename=uploaded.name,
                content_type=uploaded.type or "application/octet-stream",
            )
            st.session_state[processed_key] = uploaded.file_id
            st.toast(f"'{uploaded.name}' caricato!", icon="📎")
            st.rerun()

        for att in task.attachments:
            col_name, col_dl, col_del = st.columns([5, 1, 1])
            with col_name:
                st.markdown(f"📄 {att.filename}")
                st.caption(att.content_type)
            with col_dl:
                file_bytes, _meta = attachment_service.download(task.id, att.file_id)
                st.download_button(
                    label="⬇️",
                    data=file_bytes,
                    file_name=att.filename,
                    mime=att.content_type,
                    key=f"dl_{task.id}_{att.file_id}",
                )
            with col_del:
                if st.button("🗑️", key=f"del_att_{task.id}_{att.file_id}"):
                    attachment_service.delete_attachment(task.id, att.file_id)
                    st.toast(f"'{att.filename}' eliminato!", icon="🗑️")
                    st.rerun()

    # Bottone elimina → apre dialog di conferma
    if st.button(
        "🗑️ Elimina",
        key=f"del_{task.id}",
        type="primary",
        use_container_width=True,
    ):
        confirm_delete_task(task)

    st.divider()


# --- Layout a 3 colonne ---
col_todo, col_in_progress, col_done = st.columns(3)

with col_todo:
    st.subheader(f"📌 {STATUS_LABELS[TaskStatus.TODO]}")
    todo_tasks = tasks_by_status.get(TaskStatus.TODO, [])
    if not todo_tasks:
        st.caption("_Nessun task_")
    for task in todo_tasks:
        render_task_card(task)

with col_in_progress:
    st.subheader(f"⚙️ {STATUS_LABELS[TaskStatus.IN_PROGRESS]}")
    ip_tasks = tasks_by_status.get(TaskStatus.IN_PROGRESS, [])
    if not ip_tasks:
        st.caption("_Nessun task_")
    for task in ip_tasks:
        render_task_card(task)

with col_done:
    st.subheader(f"✅ {STATUS_LABELS[TaskStatus.COMPLETED]}")
    done_tasks = tasks_by_status.get(TaskStatus.COMPLETED, [])
    if not done_tasks:
        st.caption("_Nessun task_")
    for task in done_tasks:
        render_task_card(task)
