from models import Project
from config.database import MongoDBClient
from typing import List
from datetime import datetime, timezone

class ProjectRepository:
    def __init__(self, db_name: str = None):
        client = MongoDBClient()
        self.collection = client.get_database(db_name)["projects"]
    
    def insert(self, project: Project) -> str:
        """Inserisce un nuovo progetto nel database e restituisce l'ID del progetto inserito."""
        project_dict = project.model_dump()
        self.collection.insert_one(project_dict)
        return str(project.id)
    
    def find_by_id(self, project_id: str) -> Project | None:
        """Trova un progetto per ID e restituisce un'istanza di Project."""
        project_data = self.collection.find_one({"id": project_id})
        if project_data:
            return Project.model_validate(project_data)
        return None
    
    def find_by_name(self, name: str) -> Project | None:
        """Trova un progetto per nome e restituisce un'istanza di Project. Se non è presente il progetto restituisce None."""
        project_data = self.collection.find_one({"name": name})
        if project_data:
            return Project.model_validate(project_data)
        return None
    
    def find_by_member(self, member_id: str) -> List[Project]:
        """Trova tutti i progetti a cui un membro specifico è associato. Se il membro non è presente o non è associato a nessun progetto, restituisce un elenco vuoto."""
        projects_data = self.collection.find({"members": member_id})
        return [Project.model_validate(project) for project in projects_data]
    
    def find_all(self) -> List[Project]:
        """Restituisce un elenco di tutti i progetti presenti nel database."""
        projects_data = self.collection.find()
        return [Project.model_validate(project) for project in projects_data]
    
    def update(self, project: Project) -> bool:
        """Aggiorna un progetto esistente nel database. restituisce True se l'aggiornamento è avvenuto con successo, altrimenti False."""
        result = self.collection.update_one(
            {"id": project.id},
            {"$set": project.model_dump()}
        )
        return result.modified_count > 0
    
    def delete(self, project_id: str) -> bool:
        """Elimina un progetto dal database. restituisce True se l'eliminazione è avvenuta con successo, altrimenti False."""
        result = self.collection.delete_one({"id": project_id})
        return result.deleted_count > 0
    