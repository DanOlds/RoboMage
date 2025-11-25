"""Tests for file storage system."""

import tempfile
from pathlib import Path

import numpy as np

from robomage import load_test_data
from robomage.persistence.file_store import FileStore


def test_file_store_initialization():
    """Test FileStore initialization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = FileStore(store_path=tmpdir)
        assert store.store_path == Path(tmpdir)
        assert store.store_path.exists()


def test_store_and_load_file():
    """Test storing and loading a diffraction file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = FileStore(store_path=tmpdir)

        # Get test data
        data = load_test_data()

        # Store file
        session_id = 1
        filename = "test.chi"
        stored_path = store.store_file(session_id, filename, data)

        # Verify session directory was created
        session_dir = Path(tmpdir) / "session_1"
        assert session_dir.exists()
        assert stored_path.exists()
        assert stored_path.name == filename

        # Load file back
        loaded_data = store.load_file(stored_path)

        # Verify data integrity
        assert len(loaded_data.q_values) == len(data.q_values)
        assert np.allclose(loaded_data.q_values, data.q_values)
        assert np.allclose(loaded_data.intensities, data.intensities)


def test_multiple_sessions():
    """Test storing files in multiple sessions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = FileStore(store_path=tmpdir)
        data = load_test_data()

        # Store in session 1
        path1 = store.store_file(1, "file1.chi", data)
        assert Path(tmpdir, "session_1", "file1.chi").exists()

        # Store in session 2
        path2 = store.store_file(2, "file2.chi", data)
        assert Path(tmpdir, "session_2", "file2.chi").exists()

        # Verify both can be loaded
        loaded1 = store.load_file(path1)
        loaded2 = store.load_file(path2)

        assert np.allclose(loaded1.q_values, data.q_values)
        assert np.allclose(loaded2.q_values, data.q_values)


def test_store_with_xy_extension():
    """Test storing file with .xy extension."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = FileStore(store_path=tmpdir)
        data = load_test_data()

        # Store with .xy extension
        stored_path = store.store_file(1, "test.xy", data)

        # Should be stored with .xy extension
        assert stored_path.suffix == ".xy"

        # Should load correctly
        loaded_data = store.load_file(stored_path)
        assert np.allclose(loaded_data.q_values, data.q_values)


def test_overwrite_file():
    """Test that duplicate filenames get unique names."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = FileStore(store_path=tmpdir)
        data = load_test_data()

        # Store file
        path1 = store.store_file(1, "test.chi", data)
        original_data = store.load_file(path1)

        # Create modified data
        modified_data = load_test_data()
        modified_data.intensities = modified_data.intensities * 2

        # Store again with same session/filename (should create unique name)
        path2 = store.store_file(1, "test.chi", modified_data)

        # Should be different paths (unique filename)
        assert path1 != path2
        assert path1.name == "test.chi"
        assert path2.name == "test_1.chi"

        # Both files should exist and have different data
        loaded_original = store.load_file(path1)
        loaded_modified = store.load_file(path2)

        assert np.allclose(loaded_original.intensities, original_data.intensities)
        assert np.allclose(loaded_modified.intensities, modified_data.intensities)
        assert not np.allclose(loaded_original.intensities, loaded_modified.intensities)
