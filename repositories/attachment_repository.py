from typing import Optional
from bson import ObjectId
from bson.errors import InvalidId
from gridfs import GridFS
from gridfs.errors import NoFile
from config.database import MongoDBClient


class AttachmentRepository:
    def __init__(self, db_name: str = None):
        db = MongoDBClient().get_database(db_name)
        self.fs = GridFS(db)

    def save(self, file_data: bytes, filename: str, content_type: str) -> str:
        """Salva un file su GridFS. Restituisce il file_id come stringa."""
        file_id = self.fs.put(file_data, filename=filename, content_type=content_type)
        return str(file_id)

    def read(self, file_id: str) -> Optional[bytes]:
        """Legge i bytes di un file. Ritorna None se il file non esiste o l'ID non è valido."""
        try:
            return self.fs.get(ObjectId(file_id)).read()
        except (NoFile, InvalidId):
            return None

    def delete(self, file_id: str) -> bool:
        """Cancella un file. Ritorna True se esisteva, False altrimenti."""
        try:
            oid = ObjectId(file_id)
        except InvalidId:
            return False
        if not self.fs.exists(oid):
            return False
        self.fs.delete(oid)
        return True

    def get_metadata(self, file_id: str) -> Optional[dict]:
        """Ritorna i metadati del file (filename, content_type, length, upload_date) o None."""
        try:
            file = self.fs.get(ObjectId(file_id))
            return {
                "filename": file.filename,
                "content_type": file.content_type,
                "length": file.length,
                "upload_date": file.upload_date,
            }
        except (NoFile, InvalidId):
            return None
