"""
Integration tests for workflow analysis result persistence.

Tests the complete flow:
1. Run workflow with peak analysis
2. Save results to session (including analysis results to database)
3. Reload session
4. Verify analysis results restored from database
"""

import uuid

import pytest

from robomage import load_test_data
from robomage.persistence import SessionManager


@pytest.fixture
def session_manager():
    """Create SessionManager with in-memory database."""
    return SessionManager(db_path=":memory:")


def test_workflow_analysis_persistence_roundtrip(session_manager):
    """
    Test complete workflow: save analysis → reload → verify persistence.

    Simulates the dashboard workflow:
    1. User runs peak analysis workflow
    2. Saves results to session (files + analysis)
    3. Page reloads
    4. Analysis results are restored from database
    """
    # Create session
    session_name = f"Test Workflow {uuid.uuid4().hex[:8]}"
    session_id = session_manager.create_session(session_name, "Integration test")

    # Simulate workflow execution - add file to session
    data = load_test_data()
    file_obj = session_manager.add_file_to_session(
        session_id=session_id,
        filename="test_sample.chi",
        wavelength=0.1665,
        data=data,
    )

    # Simulate peak analysis results
    analysis_result_data = {
        "filename": "test_sample.chi",
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
        "metadata": {
            "num_peaks_detected": 2,
            "num_peaks_fitted": 2,
            "overall_r_squared": 0.982,
        },
    }

    # Save analysis results to database (what workflow callback does in Sprint 7)
    result_id = session_manager.save_analysis_result(
        file_id=file_obj.id,
        analysis_type="peak_detection",
        result_data=analysis_result_data,
        parameters={"source": "workflow", "profile": "gaussian"},
        quality_metrics={"overall_r_squared": 0.982},
        analysis_version="robomage-workflow-0.1.0",
    )

    assert result_id > 0

    # === SIMULATE PAGE RELOAD ===
    # In real dashboard, stores are cleared and session is reloaded

    # Load analysis results from database (what _load_session_files does)
    latest_analysis = session_manager.get_latest_analysis(
        file_id=file_obj.id, analysis_type="peak_detection"
    )

    # Verify analysis results were persisted
    assert latest_analysis is not None
    assert latest_analysis.analysis_type == "peak_detection"
    assert latest_analysis.result_data == analysis_result_data
    assert latest_analysis.parameters["source"] == "workflow"
    assert latest_analysis.quality_metrics["overall_r_squared"] == 0.982
    assert latest_analysis.analysis_version == "robomage-workflow-0.1.0"

    # Verify the restored data matches original
    assert len(latest_analysis.result_data["peaks"]) == 2
    assert latest_analysis.result_data["peaks"][0]["position"] == 2.856
    assert latest_analysis.result_data["metadata"]["num_peaks_detected"] == 2


def test_multiple_files_analysis_persistence(session_manager):
    """Test persisting analysis results for multiple files in same session."""
    # Create session
    session_id = session_manager.create_session(
        f"Multi-file Test {uuid.uuid4().hex[:8]}"
    )

    # Add two files
    data = load_test_data()
    file1 = session_manager.add_file_to_session(session_id, "sample1.chi", 0.1665, data)
    file2 = session_manager.add_file_to_session(session_id, "sample2.chi", 0.1665, data)

    # Save analysis for file 1
    session_manager.save_analysis_result(
        file_id=file1.id,
        analysis_type="peak_detection",
        result_data={
            "peaks": [{"position": 1.5}],
            "metadata": {"num_peaks_detected": 1},
        },
    )

    # Save analysis for file 2
    session_manager.save_analysis_result(
        file_id=file2.id,
        analysis_type="peak_detection",
        result_data={
            "peaks": [{"position": 2.5}],
            "metadata": {"num_peaks_detected": 1},
        },
    )

    # Reload - verify both analyses persisted
    analysis1 = session_manager.get_latest_analysis(file1.id, "peak_detection")
    analysis2 = session_manager.get_latest_analysis(file2.id, "peak_detection")

    assert analysis1 is not None
    assert analysis2 is not None
    assert analysis1.result_data["peaks"][0]["position"] == 1.5
    assert analysis2.result_data["peaks"][0]["position"] == 2.5


def test_analysis_persistence_with_session_delete(session_manager):
    """Test that deleting session cascades to delete analysis results."""
    # Create session with file and analysis
    session_id = session_manager.create_session(f"Cascade Test {uuid.uuid4().hex[:8]}")

    data = load_test_data()
    file_obj = session_manager.add_file_to_session(session_id, "test.chi", 0.1665, data)

    result_id = session_manager.save_analysis_result(
        file_id=file_obj.id,
        analysis_type="peak_detection",
        result_data={"peaks": []},
    )

    # Verify analysis exists
    analysis = session_manager.get_latest_analysis(file_obj.id, "peak_detection")
    assert analysis is not None

    # Delete session (should cascade)
    session_manager.delete_session(session_id)

    # Verify analysis was cascade-deleted
    deleted = session_manager.delete_analysis_result(result_id)
    assert deleted is False  # Already gone via cascade


def test_analysis_persistence_version_tracking(session_manager):
    """Test that analysis version and parameters are preserved."""
    session_id = session_manager.create_session(f"Version Test {uuid.uuid4().hex[:8]}")

    data = load_test_data()
    file_obj = session_manager.add_file_to_session(session_id, "test.chi", 0.1665, data)

    # Save with specific version and parameters
    session_manager.save_analysis_result(
        file_id=file_obj.id,
        analysis_type="peak_detection",
        result_data={"peaks": []},
        parameters={
            "profile": "voigt",
            "min_prominence": 0.02,
            "background_order": 2,
        },
        analysis_version="robomage-0.2.0",
    )

    # Reload and verify metadata preserved
    analysis = session_manager.get_latest_analysis(file_obj.id, "peak_detection")

    assert analysis.analysis_version == "robomage-0.2.0"
    assert analysis.parameters["profile"] == "voigt"
    assert analysis.parameters["min_prominence"] == 0.02
    assert analysis.parameters["background_order"] == 2


def test_extensibility_future_analysis_types(session_manager):
    """Test storing different analysis types (peak + mock Rietveld)."""
    session_id = session_manager.create_session(
        f"Extensibility Test {uuid.uuid4().hex[:8]}"
    )

    data = load_test_data()
    file_obj = session_manager.add_file_to_session(session_id, "test.chi", 0.1665, data)

    # Save peak detection
    session_manager.save_analysis_result(
        file_id=file_obj.id,
        analysis_type="peak_detection",
        result_data={"peaks": [{"position": 2.5}]},
    )

    # Save mock Rietveld (future feature)
    session_manager.save_analysis_result(
        file_id=file_obj.id,
        analysis_type="rietveld",
        result_data={
            "phases": [{"name": "LaB6", "fraction": 0.95}],
            "rwp": 8.2,
            "gof": 1.34,
        },
    )

    # Both should be retrievable
    peak_analysis = session_manager.get_latest_analysis(file_obj.id, "peak_detection")
    rietveld_analysis = session_manager.get_latest_analysis(file_obj.id, "rietveld")

    assert peak_analysis is not None
    assert rietveld_analysis is not None
    assert peak_analysis.analysis_type == "peak_detection"
    assert rietveld_analysis.analysis_type == "rietveld"
    assert rietveld_analysis.result_data["rwp"] == 8.2
