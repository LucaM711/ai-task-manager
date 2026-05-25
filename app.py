"""
AI Task Manager — Entry Point

Run with: streamlit run app.py
"""
import streamlit as st

st.set_page_config(page_title="AI Task Manager", layout="wide")

from config.database import ensure_mongo_available
ensure_mongo_available()

from services.project_service import ProjectService
from services.task_service import TaskService
from models import TaskStatus
from pages._sidebar import render_current_user_selector

render_current_user_selector()

st.title("AI Task Manager Dashboard")
st.markdown("Benvenuto nel tuo task manager! Qui puoi vedere una panoramica dei tuoi progetti e delle attività in corso.")

st.divider()

project_service = ProjectService()
task_service = TaskService()

projects = project_service.get_all_projects()
total_projects = len(projects)

all_tasks = []
completed = 0
for p in projects:
    tasks_by_status = task_service.get_tasks_by_project(p.id)
    for status, tasks in tasks_by_status.items():
        all_tasks.extend(tasks)
        if status == TaskStatus.COMPLETED:
            completed += len(tasks)

total_tasks = len(all_tasks)
completion = (completed / total_tasks * 100) if total_tasks > 0 else 0

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Progetti totali", total_projects)
with col2:
    st.metric("Task totali", total_tasks)
with col3:
    st.metric("Completamento", f"{completion:.1f}%")
