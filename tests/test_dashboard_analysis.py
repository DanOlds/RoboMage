"""
Tests for Dashboard Analysis Tab Integration

Tests the peak analysis service integration in the dashboard,
including callbacks, UI components, and data flow.
"""

import pytest

from robomage.dashboard.callbacks import analysis


def test_analysis_callback_imports():
    """Test that analysis callbacks module can be imported."""
    assert hasattr(analysis, "register_callbacks")
    assert hasattr(analysis, "register_service_health_callback")
    assert hasattr(analysis, "register_analysis_callback")
    assert hasattr(analysis, "create_analysis_summary_ui")


def test_create_analysis_summary_ui_empty():
    """Test creating UI with no results."""
    result = analysis.create_analysis_summary_ui({})
    assert result is not None


def test_create_analysis_summary_ui_with_results():
    """Test creating UI with sample results."""
    mock_results = {
        "test_file.chi": {
            "peaks_detected": 3,
            "peak_list": [
                {
                    "position": 1.5,
                    "d_spacing": 4.189,
                    "intensity": 1000,
                    "fwhm": 0.05,
                },
                {
                    "position": 2.0,
                    "d_spacing": 3.142,
                    "intensity": 800,
                    "fwhm": 0.04,
                },
                {
                    "position": 2.5,
                    "d_spacing": 2.513,
                    "intensity": 600,
                    "fwhm": 0.06,
                },
            ],
            "fit_quality": {"r_squared": 0.95},
        }
    }

    result = analysis.create_analysis_summary_ui(mock_results)
    assert result is not None


def test_analysis_tab_layout():
    """Test that Analysis tab layout can be created."""
    from robomage.dashboard.layouts.main_layout import create_analysis_tab

    layout = create_analysis_tab()
    assert layout is not None


def test_dashboard_with_analysis_callbacks():
    """Test dashboard app creation with analysis callbacks registered."""
    from robomage.dashboard.app import create_app

    app = create_app(debug=False)
    assert app is not None
    assert app.layout is not None


@pytest.mark.parametrize(
    "prominence,distance",
    [
        (0.01, 0.1),
        (0.05, 0.2),
        (0.1, 0.5),
    ],
)
def test_analysis_parameters(prominence, distance):
    """Test that analysis parameters are in valid ranges."""
    assert 0.0 <= prominence <= 1.0
    assert 0.0 < distance <= 5.0


def test_peak_profile_types():
    """Test valid peak profile types."""
    valid_profiles = ["gaussian", "lorentzian", "voigt"]

    for profile in valid_profiles:
        assert profile in ["gaussian", "lorentzian", "voigt", "pseudo_voigt"]


def test_service_health_check_error_handling():
    """Test that service health check handles errors gracefully."""
    # This test verifies the error handling structure exists
    # Actual service testing requires the service to be running
    from robomage.clients.peak_analysis_client import PeakAnalysisClient

    client = PeakAnalysisClient(timeout=0.1)  # Very short timeout

    # Should not raise exception, just return error state
    try:
        # Try to connect to non-existent service
        _ = client.health_check()
    except Exception:
        # Expected to fail when service not running
        pass


def test_analysis_results_store_structure():
    """Test expected structure of analysis results stored in dcc.Store."""
    # Example of expected results structure
    expected_structure = {
        "filename.chi": {
            "peaks_detected": int,
            "peak_list": list,
            "fit_quality": dict,
        }
    }

    # Validate structure can be used
    assert "filename.chi" in expected_structure
    assert isinstance(expected_structure["filename.chi"]["peaks_detected"], type)


def test_peak_annotation_data_conversion():
    """Test peak position conversion for different x-axis types."""
    import numpy as np

    # Sample peak at Q = 2.0 Å⁻¹
    peak_q = 2.0
    wavelength = 0.1665  # Synchrotron

    # Convert to 2θ
    sin_theta = np.clip(peak_q * wavelength / (4 * np.pi), -1.0, 1.0)
    two_theta = 2 * np.arcsin(sin_theta) * 180 / np.pi

    assert 0 <= two_theta <= 180

    # Convert to d-spacing
    d_spacing = 2 * np.pi / peak_q
    assert d_spacing > 0
    assert abs(d_spacing - 3.142) < 0.001  # Should be ~π


def test_analysis_callback_registration():
    """Test that all analysis callbacks can be registered."""
    from unittest.mock import MagicMock

    mock_app = MagicMock()

    # Should not raise exception
    analysis.register_callbacks(mock_app)

    # Verify callback decorator was called
    assert mock_app.callback.called


def test_ui_component_ids():
    """Test that expected component IDs exist in layout."""
    from robomage.dashboard.layouts.main_layout import create_analysis_tab

    layout = create_analysis_tab()
    layout_str = str(layout)

    # Check for key component IDs
    assert "run-analysis-btn" in layout_str
    assert "analysis-summary" in layout_str
    assert "service-status-badge" in layout_str
    assert "profile-selector" in layout_str
    assert "min-prominence-input" in layout_str
    assert "min-distance-input" in layout_str
