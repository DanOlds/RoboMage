"""
Unit tests for analysis result persistence.

Tests the AnalysisResult model and SessionManager API methods for
saving, retrieving, filtering, and deleting analysis results.
"""

import pytest
from datetime import datetime
import uuid

from robomage.persistence import SessionManager
from robomage.persistence.models import AnalysisResult
from robomage import load_test_data


@pytest.fixture
def session_manager():
    """Create SessionManager with in-memory database for testing."""
    return SessionManager(db_path=":memory:")


@pytest.fixture
def sample_session(session_manager):
    """Create a test session with unique name."""
    # Use UUID to ensure unique session names across all tests
    unique_name = f"Test Session {uuid.uuid4().hex[:8]}"
    session_id = session_manager.create_session(
        name=unique_name, description="For testing analysis persistence"
    )
    return session_id


@pytest.fixture
def sample_file(session_manager, sample_session):
    """Create a test file in the session."""
    data = load_test_data()
    file_obj = session_manager.add_file_to_session(
        session_id=sample_session,
        filename="test_sample.chi",
        wavelength=0.1665,
        data=data,
    )
    return file_obj


@pytest.fixture
def peak_detection_result():
    """Sample peak detection result data."""
    return {
        "peaks": [
            {
                "position": 2.856,
                "height": 1234.5,
                "width": 0.045,
                "area": 55.67,
                "d_spacing": 2.199,
                "r_squared": 0.985,
            },
            {
                "position": 3.142,
                "height": 987.3,
                "width": 0.052,
                "area": 48.21,
                "d_spacing": 2.001,
                "r_squared": 0.978,
            },
        ],
        "num_peaks_detected": 2,
        "num_peaks_fitted": 2,
        "overall_r_squared": 0.982,
    }


@pytest.fixture
def analysis_parameters():
    """Sample analysis parameters."""
    return {
        "profile_type": "gaussian",
        "min_prominence": 0.01,
        "min_distance": 0.1,
        "fit_background": True,
    }


@pytest.fixture
def quality_metrics():
    """Sample quality metrics."""
    return {
        "overall_r_squared": 0.982,
        "mean_fit_quality": 0.978,
        "failed_fits": 0,
    }


# ============================================================================
# save_analysis_result() tests
# ============================================================================


def test_save_analysis_result_basic(
    session_manager, sample_file, peak_detection_result
):
    """Test saving a basic peak detection result."""
    result_id = session_manager.save_analysis_result(
        file_id=sample_file.id,
        analysis_type="peak_detection",
        result_data=peak_detection_result,
    )

    assert result_id > 0
    assert isinstance(result_id, int)


def test_save_analysis_result_with_parameters(
    session_manager, sample_file, peak_detection_result, analysis_parameters
):
    """Test saving an analysis result with parameters."""
    result_id = session_manager.save_analysis_result(
        file_id=sample_file.id,
        analysis_type="peak_detection",
        result_data=peak_detection_result,
        parameters=analysis_parameters,
    )

    # Retrieve and verify parameters stored
    results = session_manager.get_analysis_results(sample_file.id)
    assert len(results) == 1
    assert results[0].parameters == analysis_parameters


def test_save_analysis_result_with_quality_metrics(
    session_manager, sample_file, peak_detection_result, quality_metrics
):
    """Test saving an analysis result with quality metrics."""
    result_id = session_manager.save_analysis_result(
        file_id=sample_file.id,
        analysis_type="peak_detection",
        result_data=peak_detection_result,
        quality_metrics=quality_metrics,
    )

    # Retrieve and verify quality metrics stored
    results = session_manager.get_analysis_results(sample_file.id)
    assert len(results) == 1
    assert results[0].quality_metrics == quality_metrics


def test_save_analysis_result_with_version(
    session_manager, sample_file, peak_detection_result
):
    """Test saving an analysis result with version string."""
    result_id = session_manager.save_analysis_result(
        file_id=sample_file.id,
        analysis_type="peak_detection",
        result_data=peak_detection_result,
        analysis_version="robomage-0.1.0",
    )

    # Retrieve and verify version stored
    results = session_manager.get_analysis_results(sample_file.id)
    assert len(results) == 1
    assert results[0].analysis_version == "robomage-0.1.0"


def test_save_analysis_result_complete(
    session_manager,
    sample_file,
    peak_detection_result,
    analysis_parameters,
    quality_metrics,
):
    """Test saving a complete analysis result with all fields."""
    result_id = session_manager.save_analysis_result(
        file_id=sample_file.id,
        analysis_type="peak_detection",
        result_data=peak_detection_result,
        parameters=analysis_parameters,
        quality_metrics=quality_metrics,
        analysis_version="robomage-0.1.0",
    )

    # Retrieve and verify all fields
    results = session_manager.get_analysis_results(sample_file.id)
    assert len(results) == 1

    result = results[0]
    assert result.file_id == sample_file.id
    assert result.analysis_type == "peak_detection"
    assert result.result_data == peak_detection_result
    assert result.parameters == analysis_parameters
    assert result.quality_metrics == quality_metrics
    assert result.analysis_version == "robomage-0.1.0"
    assert isinstance(result.created_at, datetime)


def test_save_analysis_result_invalid_file_id(
    session_manager, peak_detection_result
):
    """Test saving analysis result with invalid file_id raises error."""
    with pytest.raises(ValueError, match="File 99999 not found"):
        session_manager.save_analysis_result(
            file_id=99999,
            analysis_type="peak_detection",
            result_data=peak_detection_result,
        )


def test_save_multiple_analysis_results(
    session_manager, sample_file, peak_detection_result
):
    """Test saving multiple analysis results for same file."""
    # Save first analysis
    result_id_1 = session_manager.save_analysis_result(
        file_id=sample_file.id,
        analysis_type="peak_detection",
        result_data=peak_detection_result,
        parameters={"profile": "gaussian"},
    )

    # Save second analysis with different parameters
    result_id_2 = session_manager.save_analysis_result(
        file_id=sample_file.id,
        analysis_type="peak_detection",
        result_data=peak_detection_result,
        parameters={"profile": "lorentzian"},
    )

    # Both should be stored
    results = session_manager.get_analysis_results(sample_file.id)
    assert len(results) == 2
    assert result_id_1 != result_id_2


# ============================================================================
# get_analysis_results() tests
# ============================================================================


def test_get_analysis_results_empty(session_manager, sample_file):
    """Test getting analysis results when none exist."""
    results = session_manager.get_analysis_results(sample_file.id)
    assert results == []


def test_get_analysis_results_single(
    session_manager, sample_file, peak_detection_result
):
    """Test getting a single analysis result."""
    session_manager.save_analysis_result(
        file_id=sample_file.id,
        analysis_type="peak_detection",
        result_data=peak_detection_result,
    )

    results = session_manager.get_analysis_results(sample_file.id)
    assert len(results) == 1
    assert isinstance(results[0], AnalysisResult)


def test_get_analysis_results_ordered_by_time(
    session_manager, sample_file, peak_detection_result
):
    """Test that results are ordered by created_at descending (newest first)."""
    import time

    # Save first result
    session_manager.save_analysis_result(
        file_id=sample_file.id,
        analysis_type="peak_detection",
        result_data=peak_detection_result,
    )

    # Wait a tiny bit to ensure different timestamps
    time.sleep(0.01)

    # Save second result
    session_manager.save_analysis_result(
        file_id=sample_file.id,
        analysis_type="peak_detection",
        result_data=peak_detection_result,
    )

    results = session_manager.get_analysis_results(sample_file.id)
    assert len(results) == 2
    # Newest should be first
    assert results[0].created_at > results[1].created_at


def test_get_analysis_results_filter_by_type(session_manager, sample_file):
    """Test filtering results by analysis type."""
    # Save peak detection result
    session_manager.save_analysis_result(
        file_id=sample_file.id,
        analysis_type="peak_detection",
        result_data={"peaks": []},
    )

    # Save mock Rietveld result
    session_manager.save_analysis_result(
        file_id=sample_file.id,
        analysis_type="rietveld",
        result_data={"phases": []},
    )

    # Get all results
    all_results = session_manager.get_analysis_results(sample_file.id)
    assert len(all_results) == 2

    # Filter by peak_detection
    peak_results = session_manager.get_analysis_results(
        sample_file.id, analysis_type="peak_detection"
    )
    assert len(peak_results) == 1
    assert peak_results[0].analysis_type == "peak_detection"

    # Filter by rietveld
    rietveld_results = session_manager.get_analysis_results(
        sample_file.id, analysis_type="rietveld"
    )
    assert len(rietveld_results) == 1
    assert rietveld_results[0].analysis_type == "rietveld"


# ============================================================================
# get_latest_analysis() tests
# ============================================================================


def test_get_latest_analysis_none_exists(session_manager, sample_file):
    """Test getting latest analysis when none exists."""
    result = session_manager.get_latest_analysis(
        sample_file.id, analysis_type="peak_detection"
    )
    assert result is None


def test_get_latest_analysis_single(
    session_manager, sample_file, peak_detection_result
):
    """Test getting latest analysis with single result."""
    session_manager.save_analysis_result(
        file_id=sample_file.id,
        analysis_type="peak_detection",
        result_data=peak_detection_result,
    )

    result = session_manager.get_latest_analysis(
        sample_file.id, analysis_type="peak_detection"
    )
    assert result is not None
    assert isinstance(result, AnalysisResult)
    assert result.analysis_type == "peak_detection"


def test_get_latest_analysis_multiple(session_manager, sample_file):
    """Test getting latest analysis returns most recent."""
    import time

    # Save first result
    session_manager.save_analysis_result(
        file_id=sample_file.id,
        analysis_type="peak_detection",
        result_data={"peaks": [], "version": 1},
    )

    time.sleep(0.01)

    # Save second result (newer)
    session_manager.save_analysis_result(
        file_id=sample_file.id,
        analysis_type="peak_detection",
        result_data={"peaks": [], "version": 2},
    )

    result = session_manager.get_latest_analysis(
        sample_file.id, analysis_type="peak_detection"
    )
    assert result is not None
    # Should get version 2 (newer)
    assert result.result_data["version"] == 2


def test_get_latest_analysis_filters_by_type(session_manager, sample_file):
    """Test that get_latest_analysis filters by analysis type."""
    # Save peak detection result
    session_manager.save_analysis_result(
        file_id=sample_file.id,
        analysis_type="peak_detection",
        result_data={"type": "peaks"},
    )

    # Save Rietveld result
    session_manager.save_analysis_result(
        file_id=sample_file.id,
        analysis_type="rietveld",
        result_data={"type": "rietveld"},
    )

    # Get latest peak detection
    peak_result = session_manager.get_latest_analysis(
        sample_file.id, analysis_type="peak_detection"
    )
    assert peak_result is not None
    assert peak_result.result_data["type"] == "peaks"

    # Get latest Rietveld
    rietveld_result = session_manager.get_latest_analysis(
        sample_file.id, analysis_type="rietveld"
    )
    assert rietveld_result is not None
    assert rietveld_result.result_data["type"] == "rietveld"


# ============================================================================
# delete_analysis_result() tests
# ============================================================================


def test_delete_analysis_result_exists(
    session_manager, sample_file, peak_detection_result
):
    """Test deleting an existing analysis result."""
    # Save result
    result_id = session_manager.save_analysis_result(
        file_id=sample_file.id,
        analysis_type="peak_detection",
        result_data=peak_detection_result,
    )

    # Delete it
    deleted = session_manager.delete_analysis_result(result_id)
    assert deleted is True

    # Verify it's gone
    results = session_manager.get_analysis_results(sample_file.id)
    assert len(results) == 0


def test_delete_analysis_result_not_exists(session_manager):
    """Test deleting non-existent analysis result returns False."""
    deleted = session_manager.delete_analysis_result(99999)
    assert deleted is False


def test_delete_analysis_result_keeps_others(session_manager, sample_file):
    """Test deleting one result doesn't affect others."""
    # Save two results
    result_id_1 = session_manager.save_analysis_result(
        file_id=sample_file.id,
        analysis_type="peak_detection",
        result_data={"id": 1},
    )

    result_id_2 = session_manager.save_analysis_result(
        file_id=sample_file.id,
        analysis_type="peak_detection",
        result_data={"id": 2},
    )

    # Delete first
    session_manager.delete_analysis_result(result_id_1)

    # Second should still exist
    results = session_manager.get_analysis_results(sample_file.id)
    assert len(results) == 1
    assert results[0].result_data["id"] == 2


# ============================================================================
# Cascade delete tests
# ============================================================================


def test_cascade_delete_file_removes_analysis_results(
    session_manager, sample_session, peak_detection_result
):
    """Test that deleting a file's session cascades to delete analysis results."""
    # Create file
    data = load_test_data()
    file_obj = session_manager.add_file_to_session(
        session_id=sample_session,
        filename="test.chi",
        wavelength=0.1665,
        data=data,
    )

    # Save analysis result
    result_id = session_manager.save_analysis_result(
        file_id=file_obj.id,
        analysis_type="peak_detection",
        result_data=peak_detection_result,
    )

    # Verify result exists
    results = session_manager.get_analysis_results(file_obj.id)
    assert len(results) == 1

    # Delete session (will cascade to file and then to analysis result)
    session_manager.delete_session(sample_session)

    # Analysis result should be gone (cascade delete via session->file->analysis)
    deleted = session_manager.delete_analysis_result(result_id)
    assert deleted is False  # Already cascade-deleted


def test_cascade_delete_session_removes_analysis_results(
    session_manager, peak_detection_result
):
    """Test that deleting a session cascades to delete analysis results."""
    # Create session with unique name
    session_id = session_manager.create_session(f"Cascade Test {uuid.uuid4().hex[:8]}")

    # Add file
    data = load_test_data()
    file_obj = session_manager.add_file_to_session(
        session_id=session_id,
        filename="test.chi",
        wavelength=0.1665,
        data=data,
    )

    # Save analysis result
    result_id = session_manager.save_analysis_result(
        file_id=file_obj.id,
        analysis_type="peak_detection",
        result_data=peak_detection_result,
    )

    # Delete session (should cascade to file and then to analysis result)
    session_manager.delete_session(session_id)

    # Analysis result should be gone
    deleted = session_manager.delete_analysis_result(result_id)
    assert deleted is False  # Already cascade-deleted


# ============================================================================
# Extensibility tests (future analysis types)
# ============================================================================


def test_extensibility_multiple_analysis_types(session_manager, sample_file):
    """Test storing multiple analysis types demonstrates extensibility."""
    # Peak detection
    session_manager.save_analysis_result(
        file_id=sample_file.id,
        analysis_type="peak_detection",
        result_data={
            "peaks": [{"position": 2.856, "height": 1234.5}],
            "num_peaks_detected": 1,
        },
        parameters={"profile": "gaussian"},
    )

    # Mock Rietveld (future)
    session_manager.save_analysis_result(
        file_id=sample_file.id,
        analysis_type="rietveld",
        result_data={
            "phases": [{"name": "LaB6", "fraction": 0.95}],
            "rwp": 8.2,
            "gof": 1.34,
        },
        parameters={"refinement_cycles": 10},
    )

    # Mock phase ID (future)
    session_manager.save_analysis_result(
        file_id=sample_file.id,
        analysis_type="phase_identification",
        result_data={
            "matches": [{"phase_name": "Silicon", "score": 0.95}],
        },
        parameters={"database": "ICDD"},
    )

    # All three should be stored
    all_results = session_manager.get_analysis_results(sample_file.id)
    assert len(all_results) == 3

    # Each type should be retrievable
    peak_results = session_manager.get_analysis_results(
        sample_file.id, analysis_type="peak_detection"
    )
    assert len(peak_results) == 1

    rietveld_results = session_manager.get_analysis_results(
        sample_file.id, analysis_type="rietveld"
    )
    assert len(rietveld_results) == 1

    phase_results = session_manager.get_analysis_results(
        sample_file.id, analysis_type="phase_identification"
    )
    assert len(phase_results) == 1


def test_json_schema_flexibility(session_manager, sample_file):
    """Test that JSON storage adapts to different schemas."""
    # Complex nested structure for peak detection
    complex_peak_data = {
        "peaks": [
            {
                "position": 2.856,
                "fit": {
                    "type": "gaussian",
                    "center": 2.856,
                    "sigma": 0.022,
                    "amplitude": 1234.5,
                },
                "uncertainty": {"position": 0.001, "height": 5.2},
            }
        ],
        "metadata": {
            "background_subtracted": True,
            "normalization": "max",
            "processing_steps": ["smooth", "baseline", "detect"],
        },
    }

    session_manager.save_analysis_result(
        file_id=sample_file.id,
        analysis_type="peak_detection",
        result_data=complex_peak_data,
    )

    # Retrieve and verify structure preserved
    results = session_manager.get_analysis_results(sample_file.id)
    assert len(results) == 1
    assert results[0].result_data == complex_peak_data
    assert "fit" in results[0].result_data["peaks"][0]
    assert "metadata" in results[0].result_data
