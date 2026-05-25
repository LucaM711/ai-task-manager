import re
from models import Task, TaskStatus, TaskPriority
from config.database import MongoDBClient
from typing import List
from datetime import datetime, timezone, timedelta

class TaskRepository:
    def __init__(self, db_name: str = None):
        client = MongoDBClient()
        self.collection = client.get_database(db_name)["tasks"]
    
    def insert(self, task: Task) -> str:
        """Inserische una nuova attività nel database e restituisce l'ID dell'attività inserita."""
        task_dict = task.model_dump()
        self.collection.insert_one(task_dict)
        return str(task.id)
    
    def find_by_id(self, task_id: str) -> Task | None:
        """Trova un'attività per ID e restituisce un'istanza di Task."""
        task_data = self.collection.find_one({"id": task_id})
        if task_data:
            return Task.model_validate(task_data)
        return None
    
    def find_by_project(self, project_id: str) -> List[Task]:
        """Trova tutte le attività associate ad un progetto specifico. Se non è presente il progetto restituisce un elenco vuoto."""
        tasks_data = self.collection.find({"project_id": project_id})
        return [Task.model_validate(task) for task in tasks_data]
    
    def find_by_user(self, user_id: str) -> List[Task]:
        """Trova tutte le attività assegnate ad un utente specifico. Se l'utente non è presente o non possiede attività, restituisce un elenco vuoto."""
        tasks_data = self.collection.find({"assigned_to": user_id})
        return [Task.model_validate(task) for task in tasks_data]
    
    def find_by_status(self, status: TaskStatus) -> List[Task]:
        """Trova le attività con lo stato specificato. Restituisce un elenco vuoto se non ce ne sono."""
        tasks_data = self.collection.find({"status": status.value})
        return [Task.model_validate(task) for task in tasks_data]

    def find_by_priority(self, priority: TaskPriority) -> List[Task]:
        """Trova le attività assegnate ad una priorità specifica. Se non sono presenti attività con quella priorità restituisce un elenco vuoto."""
        tasks_data = self.collection.find({"priority": priority.value})
        return [Task.model_validate(task) for task in tasks_data]

    def find_by_title(self, title: str) -> List[Task]:
        """Trova le attività con titolo che contiene la stringa (match parziale, case-insensitive)."""
        tasks_data = self.collection.find({"title": {"$regex": re.escape(title), "$options": "i"}})
        return [Task.model_validate(task) for task in tasks_data]
    
    def find_urgent_tasks(self, priority: TaskPriority = TaskPriority.HIGH) -> List[Task]:
        """Trova le attività ad alta priorità con scadenza nei prossimi 3 giorni. Se non sono presenti attività urgenti restituisce un elenco vuoto."""
        now = datetime.now(timezone.utc)
        three_days_later = now + timedelta(days=3)
        tasks_data = self.collection.find({
            "priority": priority.value,
            "due_date": {"$gte": now, "$lte": three_days_later},
            "status": {"$ne": TaskStatus.COMPLETED.value}
        })
        return [Task.model_validate(task) for task in tasks_data]
        
    def update(self, task: Task) -> bool:
        """Aggiorna un'attività esistente nel database. restituisce True se l'aggiornamento è avvenuto con successo, altrimenti False."""
        task.updated_at = datetime.now(timezone.utc)
        result = self.collection.update_one(
            {"id": task.id},
            {"$set": task.model_dump()}
        )
        return result.modified_count > 0

    def delete(self, task_id: str) -> bool:
        """Elimina un'attività dal database. restituisce True se l'eliminazione è avvenuta con successo, altrimenti False."""
        result = self.collection.delete_one({"id": task_id})
        return result.deleted_count > 0
    
    def delete_by_project(self, project_id: str) -> int:
        """Elimina tutte le attività associate ad un progetto specifico. restituisce il numero di attività eliminate."""
        result = self.collection.delete_many({"project_id": project_id})
        return result.deleted_count

    def delete_many_by_ids(self, task_ids: List[str]) -> int:
        """Elimina più task in un'unica query. Restituisce il numero di task effettivamente eliminati."""
        if not task_ids:
            return 0
        result = self.collection.delete_many({"id": {"$in": task_ids}})
        return result.deleted_count
    
    def unassign_by_user(self, user_id: str) -> int:
        """Rimuove l'assegnazione da tutti i task di un utente. Restituisce il numero di task aggiornati."""
        result = self.collection.update_many(
            {"assigned_to": user_id},
            {"$set": {"assigned_to": None}}
        )
        return result.modified_count

    def find_by_deadline(self, days: int) -> List[Task]:
        """Trova le attività con scadenza tra adesso e N giorni nel futuro (esclusi i task completati)."""
        now = datetime.now(timezone.utc)
        limit = now + timedelta(days=days)
        tasks_data = self.collection.find({
            "due_date": {"$gte": now, "$lte": limit},
            "status": {"$ne": TaskStatus.COMPLETED.value}
        })
        return [Task.model_validate(t) for t in tasks_data]