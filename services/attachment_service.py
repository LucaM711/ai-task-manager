from typing import List, Tuple

from models import Attachment
from repositories.attachment_repository import AttachmentRepository
from repositories.task_repository import TaskRepository


class AttachmentService:
    def __init__(self, attachment_repo: AttachmentRepository = None, task_repo: TaskRepository = None):
        self.attachment_repo = attachment_repo or AttachmentRepository()
        self.task_repo = task_repo or TaskRepository()

    def _get_task_or_raise(self, task_id: str):
        task = self.task_repo.find_by_id(task_id)
        if not task:
            raise ValueError(f"Task with id {task_id} not found")
        return task

    def upload(self, task_id: str, file_bytes: bytes, filename: str, content_type: str) -> Attachment:
        """Carica un file su GridFS e lo associa al task. Rollback su fallimento dell'update."""
        task = self._get_task_or_raise(task_id)
        file_id = self.attachment_repo.save(file_bytes, filename, content_type)
        attachment = Attachment(file_id=file_id, filename=filename, content_type=content_type)
        task.attachments.append(attachment)
        try:
            self.task_repo.update(task)
        except Exception:
            self.attachment_repo.delete(file_id)
            raise
        return attachment

    def download(self, task_id: str, file_id: str) -> Tuple[bytes, Attachment]:
        """Ritorna (bytes, metadata) dell'allegato. Solleva ValueError se file_id non appartiene al task."""
        task = self._get_task_or_raise(task_id)
        matching = [a for a in task.attachments if a.file_id == file_id]
        if not matching:
            raise ValueError(f"Attachment {file_id} non appartiene al task {task_id}")
        file_bytes = self.attachment_repo.read(file_id)
        if file_bytes is None:
            raise ValueError(f"File {file_id} mancante in GridFS (riferimento orfano)")
        return file_bytes, matching[0]

    def delete_attachment(self, task_id: str, file_id: str) -> bool:
        """Cancella un singolo allegato dal task e da GridFS. False se file_id non era nel task."""
        task = self._get_task_or_raise(task_id)
        if not any(a.file_id == file_id for a in task.attachments):
            return False
        self.attachment_repo.delete(file_id)
        task.attachments = [a for a in task.attachments if a.file_id != file_id]
        self.task_repo.update(task)
        return True

    def delete_all_for_task(self, task_id: str) -> int:
        """Cascade: cancella i file GridFS di tutti gli allegati del task. Non aggiorna il task (è in delete)."""
        task = self._get_task_or_raise(task_id)
        deleted = 0
        for a in task.attachments:
            if self.attachment_repo.delete(a.file_id):
                deleted += 1
        return deleted

    def get_attachments(self, task_id: str) -> List[Attachment]:
        """Lista degli allegati associati al task."""
        return self._get_task_or_raise(task_id).attachments
