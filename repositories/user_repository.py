from models import User, UserRoles
from config.database import MongoDBClient
from typing import List

class UserRepository:
    def __init__(self, db_name: str = None):
        client = MongoDBClient()
        self.collection = client.get_database(db_name)["users"]
    
    def insert(self, user: User) -> str:
        """inserisce un nuovo utente nel database e restituisce l'ID dell'utente inserito."""
        user_dict = user.model_dump()
        self.collection.insert_one(user_dict)
        return str(user.id)
    
    def find_by_id(self, user_id: str) -> User | None:
        """Trova un utente per ID e restituisce un'istanza di User."""
        user_data = self.collection.find_one({"id": user_id})
        if user_data:
            return User.model_validate(user_data)
        return None

    def find_by_email(self, email: str) -> User | None:
        """trova un utente per email e restituisce un'istanza di User. Se l'utente non è presente restituisce None."""
        user_data = self.collection.find_one({"email": email})
        if user_data:
            return User.model_validate(user_data)
        return None
    
    def find_by_role(self, role: UserRoles) -> List[User]:
        """Trova tutti gli utenti con un ruolo specifico. Se non sono presenti utenti con quel ruolo restituisce un elenco vuoto."""
        users_data = self.collection.find({"role": role.value})
        return [User.model_validate(user) for user in users_data]

    def find_all(self) -> List[User]:
        """Trova tutti gli utenti presenti nel database. Se non sono presenti utenti restituisce un elenco vuoto"""
        users_data = self.collection.find()
        return [User.model_validate(user) for user in users_data]

    def update(self, user: User) -> bool:
        """Aggiorna un utente esistente nel database. Restituisce True se l'aggiornamento è avvenuto con successo, altrimenti False."""
        result = self.collection.update_one(
            {"id": user.id},
            {"$set": user.model_dump()}
        )
        return result.modified_count > 0

    def delete(self, user_id: str) -> bool:
        """Elimina un utente dal database. Restituisce True se l'eliminazione è avvenuta con successo, altrimenti False."""
        result = self.collection.delete_one({"id": user_id})
        return result.deleted_count > 0