"""
Integration tests for session save/load workflows.

Tests the complete flow from dashboard state → database → restore.
Ensures wavelength, file data, and UI state are correctly preserved.
"""

import tempfile
from pathlib import Path

import numpy as np
import pytest

from robomage.data.models import DiffractionData
from robomage.persistence import SessionManager
from robomage.persistence.file_store import FileStore


@pytest.fixture
def temp_storage():
    """Create temporary storage for database and files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        yield {
            "db_path": tmpdir_path / "test.db",
            "file_store_path": tmpdir_path / "files",
        }


@pytest.fixture
def session_manager(temp_storage):
    """Create a SessionManager with temporary database and file store."""
    # Create file store with temp directory
    file_store = FileStore(store_path=temp_storage["file_store_path"])

    # Create session manager with temp database
    mgr = SessionManager(db_path=temp_storage["db_path"])

    # Replace file store with our temp one
    mgr.file_store = file_store

    return mgr


@pytest.fixture
def sample_diffraction_data():
    """Create sample diffraction data for testing."""
    q_values = np.linspace(0.5, 25.0, 1000)
    intensities = np.exp(-((q_values - 10.0) ** 2) / 2.0) * 1000 + np.random.normal(
        0, 10, 1000
    )

    return DiffractionData(
        filename="test_sample.chi",
        q_values=q_values,
        intensities=intensities,
        wavelength=1.5406,  # Cu Kα
    )


class TestSessionSaveLoad:
    """Test complete save/load workflows."""

    def test_save_and_load_single_file_session(
        self, session_manager, sample_diffraction_data
    ):
        """Test saving and loading a session with one file."""
        # Save session
        session_id = session_manager.create_session(
            name="Integration Test - Single File Session",
            description="Integration test session",
        )

        session_manager.add_file_to_session(
            session_id=session_id,
            filename=sample_diffraction_data.filename,
            wavelength=sample_diffraction_data.wavelength,
            data=sample_diffraction_data,
        )

        # Load session
        session = session_manager.get_session(session_id)
        assert session.name == "Integration Test - Single File Session"
        assert session.description == "Integration test session"
        assert len(session.files) == 1

        # Load file data
        files = session_manager.get_session_files(session_id)
        assert len(files) == 1

        file_record = files[0]
        assert file_record.filename == "test_sample.chi"
        assert file_record.wavelength == 1.5406
        assert file_record.num_points == 1000

        # Load actual data
        loaded_data = session_manager.file_store.load_file(file_record.stored_path)
        assert loaded_data is not None
        assert loaded_data.filename == "test_sample.chi"
        assert len(loaded_data.q_values) == 1000
        assert len(loaded_data.intensities) == 1000

        # Verify data integrity
        np.testing.assert_allclose(
            loaded_data.q_values, sample_diffraction_data.q_values, rtol=1e-10
        )
        np.testing.assert_allclose(
            loaded_data.intensities, sample_diffraction_data.intensities, rtol=1e-10
        )

    def test_save_and_load_multiple_files(self, session_manager):
        """Test saving and loading a session with multiple files."""
        # Create session
        session_id = session_manager.create_session(
            name="Multi-file Session", description="Session with 3 files"
        )

        # Add multiple files with same wavelength
        wavelength = 1.5406  # Cu Kα
        for i in range(3):
            q_values = np.linspace(0.5, 25.0, 500 + i * 100)
            intensities = np.random.normal(1000, 100, len(q_values))

            data = DiffractionData(
                filename=f"file_{i}.chi",
                q_values=q_values,
                intensities=intensities,
                wavelength=wavelength,
            )

            session_manager.add_file_to_session(
                session_id=session_id,
                filename=data.filename,
                wavelength=wavelength,
                data=data,
            )

        # Load session
        session = session_manager.get_session(session_id)
        assert len(session.files) == 3

        # Verify all files have same wavelength
        files = session_manager.get_session_files(session_id)
        wavelengths = {f.wavelength for f in files}
        assert len(wavelengths) == 1
        assert list(wavelengths)[0] == 1.5406

    def test_wavelength_preservation(self, session_manager):
        """Test that different wavelengths are correctly preserved."""
        test_wavelengths = {
            "synchrotron.chi": 0.1665,
            "cu_kalpha.chi": 1.5406,
            "mo_kalpha.chi": 0.7107,
            "cr_kalpha.chi": 2.2897,
            "custom.chi": 1.2345,  # Custom wavelength
        }

        for filename, wavelength in test_wavelengths.items():
            # Create session for each wavelength
            session_id = session_manager.create_session(
                name=f"Session {wavelength}", description=f"Testing {wavelength} Å"
            )

            # Create data
            q_values = np.linspace(0.5, 25.0, 500)
            intensities = np.random.normal(1000, 100, 500)

            data = DiffractionData(
                filename=filename,
                q_values=q_values,
                intensities=intensities,
                wavelength=wavelength,
            )

            # Save
            session_manager.add_file_to_session(
                session_id=session_id,
                filename=filename,
                wavelength=wavelength,
                data=data,
            )

            # Load and verify
            files = session_manager.get_session_files(session_id)
            assert len(files) == 1
            assert files[0].wavelength == wavelength
            assert files[0].filename == filename

    def test_default_wavelength_preservation(self, session_manager):
        """
        Test that the default wavelength (0.1665 Å) is correctly saved and loaded.

        This is a regression test for the bug where default wavelength
        wasn't being saved/loaded correctly.
        """
        session_id = session_manager.create_session(
            name="Default Wavelength Test", description="Testing 0.1665 Å (synchrotron)"
        )

        # Create data with default wavelength
        q_values = np.linspace(0.5, 25.0, 1000)
        intensities = np.random.normal(1000, 100, 1000)

        data = DiffractionData(
            filename="synchrotron_default.chi",
            q_values=q_values,
            intensities=intensities,
            wavelength=0.1665,  # Default synchrotron wavelength
        )

        # Save
        session_manager.add_file_to_session(
            session_id=session_id,
            filename=data.filename,
            wavelength=0.1665,
            data=data,
        )

        # Load and verify wavelength is exactly 0.1665
        files = session_manager.get_session_files(session_id)
        assert len(files) == 1
        assert files[0].wavelength == 0.1665

        # Also verify it matches within tolerance for UI matching
        assert abs(files[0].wavelength - 0.1665) < 0.0001

    def test_simulate_dashboard_save_workflow(self, session_manager):
        """
        Simulate the actual dashboard save workflow.

        Tests the conversion from dashboard state → DiffractionData → storage.
        """
        # Simulate dashboard state (from file-data-store)
        file_data = {
            "sample1.chi": {
                "filename": "sample1.chi",
                "q": [0.5, 1.0, 1.5, 2.0, 2.5],
                "intensity": [100.0, 200.0, 150.0, 120.0, 90.0],
                "metadata": {},
                "num_points": 5,
                "q_range": [0.5, 2.5],
                "intensity_range": [90.0, 200.0],
            },
            "sample2.chi": {
                "filename": "sample2.chi",
                "q": [0.6, 1.1, 1.6, 2.1],
                "intensity": [110.0, 190.0, 140.0, 100.0],
                "metadata": {},
                "num_points": 4,
                "q_range": [0.6, 2.1],
                "intensity_range": [100.0, 190.0],
            },
        }

        # Simulate wavelength-store
        wavelength_data = {
            "current_wavelength": 1.5406,  # Cu Kα
            "source_type": "standard",
        }

        # Extract global wavelength (as in save callback)
        global_wavelength = wavelength_data["current_wavelength"]

        # Create session
        session_id = session_manager.create_session(
            name="Dashboard Test Session", description="Simulated from dashboard"
        )

        # Add each file (as in save callback)
        for filename, file_info in file_data.items():
            q_array = np.array(file_info["q"])
            intensity_array = np.array(file_info["intensity"])

            diffraction = DiffractionData(
                filename=filename,
                q_values=q_array,
                intensities=intensity_array,
                wavelength=global_wavelength,
            )

            session_manager.add_file_to_session(
                session_id=session_id,
                filename=filename,
                wavelength=global_wavelength,
                data=diffraction,
            )

        # Verify session was created
        session = session_manager.get_session(session_id)
        assert session.name == "Dashboard Test Session"
        assert len(session.files) == 2

        # Verify files have correct wavelength
        files = session_manager.get_session_files(session_id)
        assert all(f.wavelength == 1.5406 for f in files)

    def test_simulate_dashboard_load_workflow(self, session_manager):
        """
        Simulate the actual dashboard load workflow.

        Tests the conversion from storage → DiffractionData → dashboard state.
        """
        # First, save a session
        session_id = session_manager.create_session(
            name="Load Test Session", description="For testing load workflow"
        )

        original_data = {
            "test_file.chi": {
                "q": np.array([1.0, 2.0, 3.0, 4.0, 5.0]),
                "intensity": np.array([100.0, 200.0, 300.0, 250.0, 150.0]),
                "wavelength": 0.7107,  # Mo Kα
            }
        }

        for filename, data in original_data.items():
            diffraction = DiffractionData(
                filename=filename,
                q_values=data["q"],
                intensities=data["intensity"],
                wavelength=data["wavelength"],
            )

            session_manager.add_file_to_session(
                session_id=session_id,
                filename=filename,
                wavelength=data["wavelength"],
                data=diffraction,
            )

        # Now simulate load workflow (as in load callback)
        session_files = session_manager.get_session_files(session_id)

        # Reconstruct file data (as in load callback)
        file_data = {}
        loaded_wavelength = 0.1665  # Default

        for session_file in session_files:
            # Load from FileStore
            diffraction = session_manager.file_store.load_file(session_file.stored_path)

            # Get wavelength from DB (first file)
            if not file_data:
                loaded_wavelength = session_file.wavelength

            # Convert to dashboard format
            filename = diffraction.filename or "unknown.chi"
            file_data[filename] = {
                "filename": filename,
                "q": diffraction.q_values.tolist(),
                "intensity": diffraction.intensities.tolist(),
                "metadata": {},
                "num_points": len(diffraction.q_values),
                "q_range": [
                    float(diffraction.q_values.min()),
                    float(diffraction.q_values.max()),
                ],
                "intensity_range": [
                    float(diffraction.intensities.min()),
                    float(diffraction.intensities.max()),
                ],
            }

        # Restore wavelength data (as in load callback)
        wavelength_data = {
            "current_wavelength": loaded_wavelength,
            "source_type": "standard",
        }

        # Verify loaded state matches original
        assert len(file_data) == 1
        assert "test_file.chi" in file_data

        loaded_file = file_data["test_file.chi"]
        assert loaded_file["num_points"] == 5
        assert loaded_file["q"] == [1.0, 2.0, 3.0, 4.0, 5.0]
        assert loaded_file["intensity"] == [100.0, 200.0, 300.0, 250.0, 150.0]

        # Verify wavelength was loaded from DB (not from file!)
        assert wavelength_data["current_wavelength"] == 0.7107
        assert wavelength_data["source_type"] == "standard"

    def test_session_delete_cleanup(self, session_manager):
        """Test that deleting a session removes all associated data."""
        # Create session with files
        session_id = session_manager.create_session(
            name="Delete Test", description="Will be deleted"
        )

        q_values = np.linspace(0.5, 25.0, 500)
        intensities = np.random.normal(1000, 100, 500)

        data = DiffractionData(
            filename="to_delete.chi",
            q_values=q_values,
            intensities=intensities,
            wavelength=1.5406,
        )

        session_manager.add_file_to_session(
            session_id=session_id,
            filename=data.filename,
            wavelength=1.5406,
            data=data,
        )

        # Verify session exists
        session = session_manager.get_session(session_id)
        assert session is not None

        files = session_manager.get_session_files(session_id)
        assert len(files) == 1

        # Get stored path before deletion
        stored_path = Path(files[0].stored_path)
        assert stored_path.exists()

        # Delete session
        session_manager.delete_session(session_id)

        # Verify session is gone (returns None, not exception)
        deleted_session = session_manager.get_session(session_id)
        assert deleted_session is None

        # Verify files are gone from filesystem
        assert not stored_path.exists()
        assert not stored_path.parent.exists()  # Session directory also removed

    def test_multiple_sessions_different_wavelengths(self, session_manager):
        """Test saving multiple sessions with different wavelengths."""
        sessions = {
            "Synchrotron Session": 0.1665,
            "Cu Kα Session": 1.5406,
            "Mo Kα Session": 0.7107,
        }

        session_ids = []

        # Create sessions
        for name, wavelength in sessions.items():
            session_id = session_manager.create_session(
                name=name, description=f"Testing {wavelength} Å"
            )
            session_ids.append(session_id)

            # Add file to session
            q_values = np.linspace(0.5, 25.0, 500)
            intensities = np.random.normal(1000, 100, 500)

            data = DiffractionData(
                filename=f"{name.replace(' ', '_').lower()}.chi",
                q_values=q_values,
                intensities=intensities,
                wavelength=wavelength,
            )

            session_manager.add_file_to_session(
                session_id=session_id,
                filename=data.filename,
                wavelength=wavelength,
                data=data,
            )

        # List all sessions
        all_sessions = session_manager.list_sessions()
        assert len(all_sessions) >= 3

        # Verify each session has correct wavelength
        for session_id, (name, expected_wavelength) in zip(
            session_ids, sessions.items(), strict=False
        ):
            session = session_manager.get_session(session_id)
            assert session.name == name

            files = session_manager.get_session_files(session_id)
            assert len(files) == 1
            assert files[0].wavelength == expected_wavelength


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_session(self, session_manager):
        """Test creating a session with no files."""
        session_id = session_manager.create_session(
            name="Empty Session", description="No files added"
        )

        session = session_manager.get_session(session_id)
        assert session.name == "Empty Session"
        assert len(session.files) == 0

        files = session_manager.get_session_files(session_id)
        assert len(files) == 0

    def test_duplicate_filenames_in_session(self, session_manager):
        """Test adding files with duplicate names to same session."""
        session_id = session_manager.create_session(name="Duplicate Names Test")

        # Add three files with same name
        for i in range(3):
            q_values = np.linspace(0.5, 25.0, 500)
            intensities = np.random.normal(1000 + i * 100, 100, 500)

            data = DiffractionData(
                filename="duplicate.chi",
                q_values=q_values,
                intensities=intensities,
                wavelength=1.5406,
            )

            session_manager.add_file_to_session(
                session_id=session_id,
                filename="duplicate.chi",
                wavelength=1.5406,
                data=data,
            )

        # All three files should be saved with unique stored paths
        files = session_manager.get_session_files(session_id)
        assert len(files) == 3

        # Verify stored paths are unique
        stored_paths = {f.stored_path for f in files}
        assert len(stored_paths) == 3

    def test_very_large_dataset(self, session_manager):
        """Test saving and loading a large dataset."""
        session_id = session_manager.create_session(name="Large Dataset Test")

        # Create large dataset (10,000 points)
        q_values = np.linspace(0.5, 100.0, 10000)
        intensities = np.random.normal(1000, 100, 10000)

        data = DiffractionData(
            filename="large_dataset.chi",
            q_values=q_values,
            intensities=intensities,
            wavelength=1.5406,
        )

        # Save
        session_manager.add_file_to_session(
            session_id=session_id,
            filename=data.filename,
            wavelength=1.5406,
            data=data,
        )

        # Load
        files = session_manager.get_session_files(session_id)
        assert files[0].num_points == 10000

        loaded_data = session_manager.file_store.load_file(files[0].stored_path)
        assert len(loaded_data.q_values) == 10000
        assert len(loaded_data.intensities) == 10000

        # Verify data integrity
        np.testing.assert_allclose(loaded_data.q_values, q_values, rtol=1e-10)
        np.testing.assert_allclose(loaded_data.intensities, intensities, rtol=1e-10)
