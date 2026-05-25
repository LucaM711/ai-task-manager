import pytest
from bson import ObjectId
from repositories.attachment_repository import AttachmentRepository
from config.database import MongoDBClient


@pytest.fixture
def attachment_repo():
    repo = AttachmentRepository(db_name="ai_task_manager_test")
    yield repo
    # teardown: pulisci entrambe le collezioni GridFS via MongoDBClient diretto
    db = MongoDBClient().get_database("ai_task_manager_test")
    db["fs.files"].drop()
    db["fs.chunks"].drop()


def test_save_returns_string_id(attachment_repo):
    file_id = attachment_repo.save(b"hello", "test.txt", "text/plain")
    assert isinstance(file_id, str)
    # deve essere un ObjectId valido
    assert ObjectId(file_id)


def test_read_returns_bytes(attachment_repo):
    file_id = attachment_repo.save(b"contenuto del file", "x.bin", "application/octet-stream")
    data = attachment_repo.read(file_id)
    assert data == b"contenuto del file"


def test_read_missing_returns_none(attachment_repo):
    assert attachment_repo.read(str(ObjectId())) is None


def test_delete_existing_returns_true(attachment_repo):
    file_id = attachment_repo.save(b"x", "a.txt", "text/plain")
    assert attachment_repo.delete(file_id) is True
    # secondo delete sullo stesso id deve dare False
    assert attachment_repo.delete(file_id) is False


def test_delete_missing_returns_false(attachment_repo):
    assert attachment_repo.delete(str(ObjectId())) is False


def test_get_metadata(attachment_repo):
    file_id = attachment_repo.save(b"hello world", "report.pdf", "application/pdf")
    meta = attachment_repo.get_metadata(file_id)
    assert meta is not None
    assert meta["filename"] == "report.pdf"
    assert meta["content_type"] == "application/pdf"
    assert meta["length"] == 11
    assert "upload_date" in meta


def test_get_metadata_missing_returns_none(attachment_repo):
    assert attachment_repo.get_metadata(str(ObjectId())) is None
