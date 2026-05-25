import pytest
from unittest.mock import MagicMock
import uuid
from services.attachment_service import AttachmentService
from models import Attachment


@pytest.fixture
def mock_attachment_repo():
    return MagicMock()


@pytest.fixture
def mock_task_repo():
    return MagicMock()


@pytest.fixture
def service(mock_attachment_repo, mock_task_repo):
    return AttachmentService(attachment_repo=mock_attachment_repo, task_repo=mock_task_repo)


def _make_task_mock(attachments=None):
    """Helper: crea un task mock con la lista attachments fornita."""
    task = MagicMock()
    task.attachments = attachments if attachments is not None else []
    return task


def test_upload_happy_path(service, mock_attachment_repo, mock_task_repo):
    task = _make_task_mock()
    mock_task_repo.find_by_id.return_value = task
    mock_attachment_repo.save.return_value = "fake-file-id"

    att = service.upload(str(uuid.uuid4()), b"data", "doc.pdf", "application/pdf")

    mock_attachment_repo.save.assert_called_once_with(b"data", "doc.pdf", "application/pdf")
    mock_task_repo.update.assert_called_once_with(task)
    assert isinstance(att, Attachment)
    assert att.file_id == "fake-file-id"
    assert att.filename == "doc.pdf"
    assert len(task.attachments) == 1


def test_upload_task_not_found(service, mock_task_repo):
    mock_task_repo.find_by_id.return_value = None
    with pytest.raises(ValueError):
        service.upload(str(uuid.uuid4()), b"data", "f.txt", "text/plain")


def test_upload_rollback_on_update_failure(service, mock_attachment_repo, mock_task_repo):
    """Se task_repo.update fallisce, i bytes salvati su GridFS devono essere cancellati."""
    task = _make_task_mock()
    mock_task_repo.find_by_id.return_value = task
    mock_attachment_repo.save.return_value = "rollback-id"
    mock_task_repo.update.side_effect = RuntimeError("DB down")

    with pytest.raises(RuntimeError):
        service.upload(str(uuid.uuid4()), b"x", "x.txt", "text/plain")
    mock_attachment_repo.delete.assert_called_once_with("rollback-id")


def test_download_happy_path(service, mock_attachment_repo, mock_task_repo):
    att = Attachment(file_id="fid-1", filename="x.txt", content_type="text/plain")
    task = _make_task_mock(attachments=[att])
    mock_task_repo.find_by_id.return_value = task
    mock_attachment_repo.read.return_value = b"file bytes"

    data, meta = service.download(str(uuid.uuid4()), "fid-1")
    assert data == b"file bytes"
    assert meta.filename == "x.txt"


def test_download_file_not_in_task_raises(service, mock_task_repo):
    task = _make_task_mock(attachments=[])
    mock_task_repo.find_by_id.return_value = task
    with pytest.raises(ValueError, match="non appartiene"):
        service.download(str(uuid.uuid4()), "fid-orphan")


def test_download_orphan_bytes_raises(service, mock_attachment_repo, mock_task_repo):
    att = Attachment(file_id="fid-orphan", filename="x.txt", content_type="text/plain")
    task = _make_task_mock(attachments=[att])
    mock_task_repo.find_by_id.return_value = task
    mock_attachment_repo.read.return_value = None
    with pytest.raises(ValueError, match="mancante in GridFS"):
        service.download(str(uuid.uuid4()), "fid-orphan")


def test_delete_attachment_happy_path(service, mock_attachment_repo, mock_task_repo):
    att = Attachment(file_id="fid-1", filename="x.txt", content_type="text/plain")
    task = _make_task_mock(attachments=[att])
    mock_task_repo.find_by_id.return_value = task

    ok = service.delete_attachment(str(uuid.uuid4()), "fid-1")
    assert ok is True
    mock_attachment_repo.delete.assert_called_once_with("fid-1")
    assert task.attachments == []
    mock_task_repo.update.assert_called_once_with(task)


def test_delete_attachment_not_in_task(service, mock_attachment_repo, mock_task_repo):
    task = _make_task_mock(attachments=[])
    mock_task_repo.find_by_id.return_value = task
    ok = service.delete_attachment(str(uuid.uuid4()), "fid-missing")
    assert ok is False
    mock_attachment_repo.delete.assert_not_called()
    mock_task_repo.update.assert_not_called()


def test_delete_all_for_task(service, mock_attachment_repo, mock_task_repo):
    atts = [
        Attachment(file_id=f"fid-{i}", filename=f"f{i}.txt", content_type="text/plain")
        for i in range(3)
    ]
    task = _make_task_mock(attachments=atts)
    mock_task_repo.find_by_id.return_value = task
    mock_attachment_repo.delete.return_value = True

    deleted = service.delete_all_for_task(str(uuid.uuid4()))
    assert deleted == 3
    assert mock_attachment_repo.delete.call_count == 3
    # NON aggiorna il task (è in fase di delete)
    mock_task_repo.update.assert_not_called()


def test_delete_all_for_task_no_attachments(service, mock_attachment_repo, mock_task_repo):
    task = _make_task_mock(attachments=[])
    mock_task_repo.find_by_id.return_value = task
    deleted = service.delete_all_for_task(str(uuid.uuid4()))
    assert deleted == 0
    mock_attachment_repo.delete.assert_not_called()


def test_get_attachments(service, mock_task_repo):
    atts = [Attachment(file_id="fid-1", filename="x", content_type="text/plain")]
    task = _make_task_mock(attachments=atts)
    mock_task_repo.find_by_id.return_value = task
    result = service.get_attachments(str(uuid.uuid4()))
    assert result == atts
