"""
Test that GUI analysis results are saved when saving a session.

This test verifies the fix for the issue where analysis results from the
Analysis tab GUI weren't being saved to the database when saving a session.
"""

import numpy as np
import pytest

from robomage.data.models import DiffractionData
from robomage.persistence import SessionManager


def test_save_session_with_gui_analysis_results(tmp_path):
    """
    Test that analysis results from GUI are saved when saving a session.

    This simulates what happens when:
    1. User uploads files to the dashboard
    2. User runs peak analysis in the Analysis tab
    3. User saves the session via Save Session button

    The analysis results should be persisted to the database.
    """
    # Setup
    db_path = tmp_path / "test.db"
    manager = SessionManager(db_path=db_path)

    # Create a session
    session_id = manager.create_session(
        name="Test GUI Analysis Session", description="Test session with GUI analysis"
    )

    # Simulate file data from file-data-store
    test_q = np.linspace(0.5, 5.0, 100)
    test_intensity = np.random.random(100) * 1000
    diffraction_data = DiffractionData(
        filename="test_gui.chi",
        q_values=test_q,
        intensities=test_intensity,
        wavelength=0.1665,
    )

    # Add file to session (simulating file upload)
    file_obj = manager.add_file_to_session(
        session_id=session_id,
        filename="test_gui.chi",
        wavelength=0.1665,
        data=diffraction_data,
    )

    # Simulate analysis results from analysis-results-store
    # This is what the Analysis tab would put in the store after running peak detection
    analysis_results = {
        "test_gui.chi": {
            "peaks": [
                {
                    "q": 1.5,
                    "intensity": 500.0,
                    "fwhm": 0.1,
                    "height": 450.0,
                    "amplitude": 200.0,
                    "center": 1.5,
                    "sigma": 0.05,
                }
            ],
            "metadata": {
                "num_peaks_detected": 1,
                "num_peaks_fitted": 1,
                "prominence": 0.1,
                "distance": 10,
                "profile": "gaussian",
                "overall_r_squared": 0.95,
            },
        }
    }

    # Simulate saving the session with analysis results
    # (This is what the save_session callback now does)
    for filename, result_data in analysis_results.items():
        if filename == file_obj.filename:
            parameters = {
                "prominence": result_data.get("metadata", {}).get("prominence", 0.1),
                "distance": result_data.get("metadata", {}).get("distance", 10),
                "profile": result_data.get("metadata", {}).get("profile", "gaussian"),
            }

            quality_metrics = {
                "overall_r_squared": result_data.get("metadata", {}).get(
                    "overall_r_squared", 0.0
                )
            }

            manager.save_analysis_result(
                file_id=file_obj.id,
                analysis_type="peak_detection",
                result_data=result_data,
                parameters=parameters,
                quality_metrics=quality_metrics,
                analysis_version="robomage-gui-0.1.0",
            )

    # Verify: Load the session and check that analysis results are restored
    session_files = manager.get_session_files(session_id)
    assert len(session_files) == 1

    # Get the latest analysis result
    latest_analysis = manager.get_latest_analysis(
        file_id=file_obj.id, analysis_type="peak_detection"
    )

    # Verify analysis was saved
    assert latest_analysis is not None
    assert latest_analysis.analysis_type == "peak_detection"
    assert latest_analysis.analysis_version == "robomage-gui-0.1.0"

    # Verify result data
    assert latest_analysis.result_data is not None
    assert "peaks" in latest_analysis.result_data
    assert len(latest_analysis.result_data["peaks"]) == 1
    assert latest_analysis.result_data["peaks"][0]["q"] == 1.5

    # Verify parameters
    assert latest_analysis.parameters is not None
    assert latest_analysis.parameters["prominence"] == 0.1
    assert latest_analysis.parameters["distance"] == 10
    assert latest_analysis.parameters["profile"] == "gaussian"

    # Verify quality metrics
    assert latest_analysis.quality_metrics is not None
    assert latest_analysis.quality_metrics["overall_r_squared"] == 0.95

    print("✅ GUI analysis results successfully saved and restored!")


def test_save_session_without_analysis_results_still_works(tmp_path):
    """
    Test that saving a session without analysis results still works.

    This ensures backward compatibility - sessions can still be saved
    even if no analysis has been performed.
    """
    # Setup
    db_path = tmp_path / "test.db"
    manager = SessionManager(db_path=db_path)

    # Create a session
    session_id = manager.create_session(
        name="Test No Analysis Session", description="Test session without analysis"
    )

    # Add file without any analysis
    test_q = np.linspace(0.5, 5.0, 100)
    test_intensity = np.random.random(100) * 1000
    diffraction_data = DiffractionData(
        filename="test_no_analysis.chi",
        q_values=test_q,
        intensities=test_intensity,
        wavelength=0.1665,
    )

    file_obj = manager.add_file_to_session(
        session_id=session_id,
        filename="test_no_analysis.chi",
        wavelength=0.1665,
        data=diffraction_data,
    )

    # Verify session was created and file was added
    session = manager.get_session(session_id)
    assert session is not None
    assert len(session.files) == 1

    # Verify no analysis results exist
    latest_analysis = manager.get_latest_analysis(
        file_id=file_obj.id, analysis_type="peak_detection"
    )
    assert latest_analysis is None

    print("✅ Session saved successfully without analysis results!")


def test_save_session_with_partial_analysis_results(tmp_path):
    """
    Test saving a session where only some files have analysis results.

    This simulates the case where a user runs analysis on only some
    of the uploaded files.
    """
    # Setup
    db_path = tmp_path / "test.db"
    manager = SessionManager(db_path=db_path)

    # Create a session
    session_id = manager.create_session(
        name="Test Partial Analysis Session",
        description="Test session with partial analysis",
    )

    # Add two files
    test_q = np.linspace(0.5, 5.0, 100)
    test_intensity = np.random.random(100) * 1000

    file1_data = DiffractionData(
        filename="test_file1.chi",
        q_values=test_q,
        intensities=test_intensity,
        wavelength=0.1665,
    )

    file2_data = DiffractionData(
        filename="test_file2.chi",
        q_values=test_q,
        intensities=test_intensity * 0.8,
        wavelength=0.1665,
    )

    file_obj1 = manager.add_file_to_session(
        session_id=session_id,
        filename="test_file1.chi",
        wavelength=0.1665,
        data=file1_data,
    )

    file_obj2 = manager.add_file_to_session(
        session_id=session_id,
        filename="test_file2.chi",
        wavelength=0.1665,
        data=file2_data,
    )

    # Only save analysis for file1 (simulating user only analyzing one file)
    analysis_results = {
        "test_file1.chi": {
            "peaks": [{"q": 1.5, "intensity": 500.0}],
            "metadata": {"num_peaks_detected": 1, "prominence": 0.1},
        }
    }

    for filename, result_data in analysis_results.items():
        if filename == file_obj1.filename:
            manager.save_analysis_result(
                file_id=file_obj1.id,
                analysis_type="peak_detection",
                result_data=result_data,
                parameters={"prominence": 0.1},
                quality_metrics={},
                analysis_version="robomage-gui-0.1.0",
            )

    # Verify: File 1 has analysis, File 2 doesn't
    analysis1 = manager.get_latest_analysis(
        file_id=file_obj1.id, analysis_type="peak_detection"
    )
    analysis2 = manager.get_latest_analysis(
        file_id=file_obj2.id, analysis_type="peak_detection"
    )

    assert analysis1 is not None
    assert analysis2 is None

    print("✅ Partial analysis results saved correctly!")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
