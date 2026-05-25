import streamlit as st

st.set_page_config(page_title="Dashboard", layout="wide")

from config.database import ensure_mongo_available
ensure_mongo_available()

import pandas as pd
import plotly.express as px
from datetime import datetime, timezone, timedelta
from services.task_service import TaskService
from services.project_service import ProjectService
from models import TaskStatus, TaskPriority, PRIORITY_LABELS
from pages._sidebar import render_current_user_selector

task_service = TaskService()
project_service = ProjectService()

render_current_user_selector()

st.title("📊 Dashboard")

# --- Selezione progetto ---
projects = project_service.get_all_projects()

if not projects:
    st.warning("Nessun progetto trovato.")
    st.stop()

project_names = [p.name for p in projects]
selected_name = st.selectbox("Seleziona progetto", project_names)
selected_project = next((p for p in projects if p.name == selected_name), None)
if not selected_project:
    st.error("Progetto non trovato. Aggiorna la pagina.")
    st.stop()

# --- Caricamento task ---
tasks_by_status = task_service.get_tasks_by_project(selected_project.id)
all_tasks = [task for tasks in tasks_by_status.values() for task in tasks]

if not all_tasks:
    st.info("Nessun task trovato per questo progetto.")
    st.stop()

st.divider()

# --- Metriche principali ---
col1, col2, col3 = st.columns(3)

with col1:
    completion_rate = len(tasks_by_status.get(TaskStatus.COMPLETED, [])) / len(all_tasks) * 100
    st.metric("Completamento", f"{completion_rate:.1f}%")

with col2:
    now = datetime.now(timezone.utc)
    limit = now + timedelta(days=3)
    expiring_tasks = [
        t for t in all_tasks
        if t.due_date is not None
        and t.status != TaskStatus.COMPLETED
        and t.due_date <= limit
    ]
    st.metric("In scadenza (3gg)", len(expiring_tasks))

with col3:
    st.metric("Task totali", len(all_tasks))
st.divider()

# --- Grafici ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Distribuzione per priorità")
    df = pd.DataFrame({
        "Priorità": [PRIORITY_LABELS[p] for p in TaskPriority],
        "Conteggio": [sum(1 for t in all_tasks if t.priority == p) for p in TaskPriority]
    })
    fig = px.pie(df, names="Priorità", values="Conteggio")
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("Task in scadenza nei prossimi 7 giorni")
    upcoming = sorted(
        [t for t in all_tasks 
        if t.due_date is not None 
        and t.status != TaskStatus.COMPLETED 
        and t.due_date <= now + timedelta(days=7)],
        key=lambda t: t.due_date
    )
    if not upcoming:
        st.info("Nessun task in scadenza")
    else:
        df = pd.DataFrame([
            {
                "Titolo": t.title,
                "Scadenza": t.due_date.strftime("%Y-%m-%d"),
                "Priorità": PRIORITY_LABELS[t.priority]
            }
            for t in upcoming
        ])
        st.dataframe(df, use_container_width=True)

    