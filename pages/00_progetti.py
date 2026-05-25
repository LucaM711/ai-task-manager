import streamlit as st

st.set_page_config(page_title="Progetti", layout="wide")

from config.database import ensure_mongo_available
ensure_mongo_available()

from services.project_service import ProjectService
from services.task_service import TaskService
from models import Project
from pages._sidebar import render_current_user_selector

project_service = ProjectService()
task_service = TaskService()

render_current_user_selector()

st.title("📁 Gestione Progetti")


@st.dialog("Conferma eliminazione")
def confirm_delete_project(project: Project, n_tasks: int) -> None:
    """Modale di conferma per la cancellazione di un progetto (cascade sui task)."""
    st.write(f"Sei sicuro di voler eliminare il progetto **{project.name}**?")
    if n_tasks > 0:
        st.warning(
            f"⚠️ Verranno eliminati anche **{n_tasks} task** collegati. "
            "Operazione irreversibile."
        )
    else:
        st.caption("Il progetto non ha task collegati. Operazione irreversibile.")

    col_yes, col_no = st.columns(2)
    with col_yes:
        if st.button("🗑️ Sì, elimina", type="primary", use_container_width=True):
            try:
                project_service.delete_project(project.id)
                st.toast("Progetto eliminato!", icon="🗑️")
                st.rerun()
            except Exception as e:
                st.error(f"Errore durante l'eliminazione: {e}")
    with col_no:
        if st.button("Annulla", use_container_width=True):
            st.rerun()


# --- CREA NUOVO PROGETTO ---
with st.expander("➕ Crea nuovo progetto"):
    with st.form("create_project_form", clear_on_submit=True):
        new_name = st.text_input("Nome del progetto")
        new_desc = st.text_area("Descrizione (opzionale)")
        submit = st.form_submit_button("Crea progetto")

        if submit:
            if not new_name.strip():
                st.error("Il nome del progetto è obbligatorio.")
            else:
                project_service.create_project(
                    name=new_name.strip(),
                    description=new_desc.strip() or None
                )
                st.toast("Progetto creato!", icon="✅")
                st.rerun()

st.divider()

# --- LISTA PROGETTI ESISTENTI ---
st.subheader("Progetti esistenti")

projects = project_service.get_all_projects()

if not projects:
    st.info("Nessun progetto. Creane uno qui sopra.")
else:
    for project in projects:
        tasks_by_status = task_service.get_tasks_by_project(project.id)
        n_tasks = sum(len(tasks) for tasks in tasks_by_status.values())

        with st.expander(f"📂 {project.name}  —  {n_tasks} task"):

            # --- Form modifica ---
            with st.form(f"edit_form_{project.id}"):
                edit_name = st.text_input(
                    "Nome",
                    value=project.name,
                    key=f"name_{project.id}"
                )
                edit_desc = st.text_area(
                    "Descrizione",
                    value=project.description or "",
                    key=f"desc_{project.id}"
                )
                save = st.form_submit_button("💾 Salva modifiche")

                if save:
                    if not edit_name.strip():
                        st.error("Il nome non può essere vuoto.")
                    else:
                        project_service.update_project(
                            project.id,
                            name=edit_name.strip(),
                            description=edit_desc.strip() or None
                        )
                        st.toast("Modifiche salvate!", icon="💾")
                        st.rerun()

            st.divider()

            # --- Bottone elimina → apre dialog di conferma ---
            if st.button(
                "🗑️ Elimina progetto",
                key=f"delete_{project.id}",
                type="primary"
            ):
                confirm_delete_project(project, n_tasks)
