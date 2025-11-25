"""Tests for persistence layer database models."""

import pytest
from sqlalchemy.exc import IntegrityError

from robomage.persistence.database import DatabaseManager
from robomage.persistence.models import File, Session


def test_session_creation():
    """Test creating a session in the database."""
    db_mgr = DatabaseManager(":memory:")  # In-memory for testing
    db = db_mgr.get_session()

    session = Session(name="Test Session", description="Test description")
    db.add(session)
    db.commit()

    assert session.id is not None
    assert session.name == "Test Session"
    assert session.description == "Test description"
    db.close()


def test_session_unique_name():
    """Test that session names must be unique."""
    db_mgr = DatabaseManager(":memory:")
    db = db_mgr.get_session()

    session1 = Session(name="Unique Name")
    db.add(session1)
    db.commit()

    # Trying to create another session with the same name should fail
    session2 = Session(name="Unique Name")
    db.add(session2)

    with pytest.raises(IntegrityError):
        db.commit()

    db.close()


def test_session_with_files():
    """Test session with file relationship."""
    db_mgr = DatabaseManager(":memory:")
    db = db_mgr.get_session()

    session = Session(name="Test Session")
    file1 = File(filename="test1.chi", wavelength=0.1665, stored_path="/tmp/test1.chi")
    file2 = File(filename="test2.chi", wavelength=0.1665, stored_path="/tmp/test2.chi")

    session.files.append(file1)
    session.files.append(file2)

    db.add(session)
    db.commit()

    assert len(session.files) == 2
    assert file1.session_id == session.id
    assert file2.session_id == session.id
    db.close()


def test_cascade_delete():
    """Test that deleting session deletes files."""
    db_mgr = DatabaseManager(":memory:")
    db = db_mgr.get_session()

    session = Session(name="Test Session")
    file1 = File(filename="test.chi", wavelength=0.1665, stored_path="/tmp/test.chi")
    session.files.append(file1)

    db.add(session)
    db.commit()

    session_id = session.id
    file_id = file1.id

    # Delete session
    db.delete(session)
    db.commit()

    # Files should be deleted too (cascade)
    files = db.query(File).filter_by(id=file_id).all()
    assert len(files) == 0

    # Session should be gone
    sessions = db.query(Session).filter_by(id=session_id).all()
    assert len(sessions) == 0

    db.close()


def test_file_metadata():
    """Test file metadata storage."""
    db_mgr = DatabaseManager(":memory:")
    db = db_mgr.get_session()

    session = Session(name="Test Session")
    file = File(
        filename="sample.chi",
        stored_path="/tmp/sample.chi",
        wavelength=1.54056,  # Cu Kα
        num_points=1000,
        q_min=1.0,
        q_max=10.0,
    )
    session.files.append(file)

    db.add(session)
    db.commit()

    # Verify metadata
    assert file.wavelength == 1.54056
    assert file.num_points == 1000
    assert file.q_min == 1.0
    assert file.q_max == 10.0

    db.close()
