"""Tests for SessionManager API."""

import tempfile
from pathlib import Path

import numpy as np
import pytest

from robomage import load_test_data
from robomage.persistence import SessionManager
from robomage.persistence.database import DatabaseManager
from robomage.persistence.file_store import FileStore


@pytest.fixture
def session_mgr():
    """Create SessionManager with temporary database for each test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create unique paths for this test
        db_path = Path(tmpdir) / "test.db"
        file_store_path = Path(tmpdir) / "files"
        file_store_path.mkdir()

        # Create fresh instances (not singletons)
        db_mgr = DatabaseManager(db_path=db_path)
        file_store = FileStore(store_path=file_store_path)

        # Create SessionManager and inject dependencies
        mgr = SessionManager(db_path=db_path)
        mgr.db_manager = db_mgr
        mgr.file_store = file_store

        yield mgr


def test_create_session(session_mgr):
    """Test creating a new session."""
    session_id = session_mgr.create_session("Test Session", "Test description")

    assert session_id is not None
    assert isinstance(session_id, int)

    # Verify session exists
    session = session_mgr.get_session(session_id)
    assert session is not None
    assert session.name == "Test Session"
    assert session.description == "Test description"


def test_create_duplicate_session(session_mgr):
    """Test that duplicate session names are rejected."""
    session_mgr.create_session("Unique Name")

    with pytest.raises(ValueError, match="already exists"):
        session_mgr.create_session("Unique Name")


def test_list_sessions(session_mgr):
    """Test listing all sessions."""
    # Create multiple sessions
    id1 = session_mgr.create_session("Session 1")
    id2 = session_mgr.create_session("Session 2")
    id3 = session_mgr.create_session("Session 3")

    sessions = session_mgr.list_sessions()

    assert len(sessions) == 3
    # Most recently accessed should be first
    assert sessions[0].id == id3
    assert sessions[1].id == id2
    assert sessions[2].id == id1


def test_add_file_to_session(session_mgr):
    """Test adding a file to a session."""
    session_id = session_mgr.create_session("Test Session")
    data = load_test_data()

    file_obj = session_mgr.add_file_to_session(
        session_id, "sample.chi", wavelength=0.1665, data=data
    )

    assert file_obj is not None
    assert file_obj.filename == "sample.chi"
    assert file_obj.wavelength == 0.1665
    assert file_obj.session_id == session_id
    assert file_obj.num_points == len(data.q_values)
    assert file_obj.q_min == pytest.approx(data.q_values.min())
    assert file_obj.q_max == pytest.approx(data.q_values.max())


def test_add_file_to_nonexistent_session(session_mgr):
    """Test adding file to non-existent session fails."""
    data = load_test_data()

    with pytest.raises(ValueError, match="not found"):
        session_mgr.add_file_to_session(999, "sample.chi", 0.1665, data)


def test_get_session_files(session_mgr):
    """Test getting all files for a session."""
    session_id = session_mgr.create_session("Test Session")
    data = load_test_data()

    # Add multiple files
    file1 = session_mgr.add_file_to_session(session_id, "file1.chi", 0.1665, data)
    file2 = session_mgr.add_file_to_session(session_id, "file2.chi", 1.54056, data)
    file3 = session_mgr.add_file_to_session(session_id, "file3.xy", 0.1665, data)

    files = session_mgr.get_session_files(session_id)

    assert len(files) == 3
    assert {f.id for f in files} == {file1.id, file2.id, file3.id}
    assert {f.filename for f in files} == {"file1.chi", "file2.chi", "file3.xy"}


def test_load_file_data(session_mgr):
    """Test loading diffraction data from stored file."""
    session_id = session_mgr.create_session("Test Session")
    original_data = load_test_data()

    # Store file
    file_obj = session_mgr.add_file_to_session(
        session_id, "sample.chi", 0.1665, original_data
    )

    # Load file
    loaded_data = session_mgr.load_file_data(file_obj.id)

    # Verify data integrity
    assert len(loaded_data.q_values) == len(original_data.q_values)
    assert np.allclose(loaded_data.q_values, original_data.q_values)
    assert np.allclose(loaded_data.intensities, original_data.intensities)


def test_load_nonexistent_file(session_mgr):
    """Test loading non-existent file fails."""
    with pytest.raises(ValueError, match="not found"):
        session_mgr.load_file_data(999)


def test_delete_session(session_mgr):
    """Test deleting a session and its files."""
    session_id = session_mgr.create_session("Test Session")
    data = load_test_data()

    # Add files to session
    file1 = session_mgr.add_file_to_session(session_id, "file1.chi", 0.1665, data)
    file2 = session_mgr.add_file_to_session(session_id, "file2.chi", 0.1665, data)

    # Verify files exist
    files = session_mgr.get_session_files(session_id)
    assert len(files) == 2

    # Delete session
    session_mgr.delete_session(session_id)

    # Verify session is gone
    session = session_mgr.get_session(session_id)
    assert session is None

    # Verify files are gone from database
    files = session_mgr.get_session_files(session_id)
    assert len(files) == 0

    # Verify physical files are gone
    file1_path = Path(file1.stored_path)
    file2_path = Path(file2.stored_path)
    assert not file1_path.exists()
    assert not file2_path.exists()


def test_delete_nonexistent_session(session_mgr):
    """Test deleting non-existent session fails."""
    with pytest.raises(ValueError, match="not found"):
        session_mgr.delete_session(999)


def test_get_file(session_mgr):
    """Test getting file metadata."""
    session_id = session_mgr.create_session("Test Session")
    data = load_test_data()

    file_obj = session_mgr.add_file_to_session(session_id, "sample.chi", 0.1665, data)

    # Get file metadata
    retrieved = session_mgr.get_file(file_obj.id)

    assert retrieved is not None
    assert retrieved.id == file_obj.id
    assert retrieved.filename == "sample.chi"
    assert retrieved.wavelength == 0.1665


def test_end_to_end_workflow(session_mgr):
    """Test complete workflow: create session, add files, load session, delete."""
    # Create session
    session_id = session_mgr.create_session(
        "Analysis Session", "Complete workflow test"
    )

    # Add multiple files with different wavelengths
    data1 = load_test_data()
    data2 = load_test_data()
    data3 = load_test_data()

    session_mgr.add_file_to_session(session_id, "cu_ka.chi", 1.54056, data1)
    session_mgr.add_file_to_session(session_id, "synchrotron.chi", 0.1665, data2)
    session_mgr.add_file_to_session(session_id, "data.xy", 0.1665, data3)

    # Verify session has all files
    files = session_mgr.get_session_files(session_id)
    assert len(files) == 3

    # Load each file and verify data
    for file_obj in files:
        loaded_data = session_mgr.load_file_data(file_obj.id)
        assert len(loaded_data.q_values) == len(data1.q_values)
        assert np.allclose(loaded_data.q_values, data1.q_values)

    # Verify wavelengths are preserved
    wavelengths = {f.filename: f.wavelength for f in files}
    assert wavelengths["cu_ka.chi"] == 1.54056
    assert wavelengths["synchrotron.chi"] == 0.1665
    assert wavelengths["data.xy"] == 0.1665

    # List sessions
    sessions = session_mgr.list_sessions()
    assert len(sessions) == 1
    assert sessions[0].id == session_id

    # Delete session
    session_mgr.delete_session(session_id)

    # Verify everything is cleaned up
    assert session_mgr.get_session(session_id) is None
    assert len(session_mgr.list_sessions()) == 0


def test_multiple_sessions_isolation(session_mgr):
    """Test that files in different sessions are isolated."""
    data = load_test_data()

    # Create two sessions
    session1_id = session_mgr.create_session("Session 1")
    session2_id = session_mgr.create_session("Session 2")

    # Add files to each session
    file1 = session_mgr.add_file_to_session(session1_id, "data.chi", 0.1665, data)
    file2 = session_mgr.add_file_to_session(session2_id, "data.chi", 1.54056, data)

    # Verify files are in correct sessions
    session1_files = session_mgr.get_session_files(session1_id)
    session2_files = session_mgr.get_session_files(session2_id)

    assert len(session1_files) == 1
    assert len(session2_files) == 1
    assert session1_files[0].id == file1.id
    assert session2_files[0].id == file2.id

    # Verify wavelengths are different
    assert session1_files[0].wavelength == 0.1665
    assert session2_files[0].wavelength == 1.54056

    # Delete session 1
    session_mgr.delete_session(session1_id)

    # Verify session 2 is unaffected
    session2_files_after = session_mgr.get_session_files(session2_id)
    assert len(session2_files_after) == 1
    loaded_data = session_mgr.load_file_data(session2_files_after[0].id)
    assert np.allclose(loaded_data.q_values, data.q_values)
