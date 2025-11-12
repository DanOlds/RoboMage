"""Test XY file loading functionality."""

from pathlib import Path

import pytest

from robomage.data import load_diffraction_file, load_xy_file


def test_load_xy_file_direct():
    """Test direct loading of XY files."""
    # Use one of the example .xy files in the project root
    project_root = Path(__file__).parent.parent
    xy_file = project_root / "detector_5_roi_175-181_18-218_frames_17847-17978.xy"

    if not xy_file.exists():
        pytest.skip(f"Test XY file not found: {xy_file}")

    # Load using the direct loader
    data = load_xy_file(xy_file)

    # Verify the data structure
    assert data.filename == xy_file.name
    assert data.statistics.num_points > 0
    assert len(data.q_values) == len(data.intensities)
    assert data.statistics.q_range[0] < data.statistics.q_range[1]


def test_load_xy_file_via_auto_detection():
    """Test XY file loading via automatic format detection."""
    project_root = Path(__file__).parent.parent
    xy_file = project_root / "detector_5_roi_190-196_19-219_frames_17847-17978.xy"

    if not xy_file.exists():
        pytest.skip(f"Test XY file not found: {xy_file}")

    # Load using the auto-detection loader
    data = load_diffraction_file(xy_file)

    # Verify the data structure
    assert data.filename == xy_file.name
    assert data.statistics.num_points > 0
    assert len(data.q_values) == len(data.intensities)

    # Verify data quality
    assert data.statistics.intensity_mean > 0
    assert data.statistics.intensity_range[0] >= 0


def test_xy_file_comparison():
    """Test that both example XY files can be loaded and compared."""
    project_root = Path(__file__).parent.parent
    xy_file1 = project_root / "detector_5_roi_175-181_18-218_frames_17847-17978.xy"
    xy_file2 = project_root / "detector_5_roi_190-196_19-219_frames_17847-17978.xy"

    if not (xy_file1.exists() and xy_file2.exists()):
        pytest.skip("Test XY files not found")

    data1 = load_diffraction_file(xy_file1)
    data2 = load_diffraction_file(xy_file2)

    # Both should have the same Q range and number of points (same detector setup)
    assert data1.statistics.num_points == data2.statistics.num_points
    assert data1.statistics.q_range == data2.statistics.q_range

    # But different intensity characteristics (different ROIs)
    assert data1.statistics.intensity_mean != data2.statistics.intensity_mean


def test_xy_file_error_handling():
    """Test error handling for invalid XY files."""
    # Test file not found
    with pytest.raises(FileNotFoundError):
        load_xy_file("nonexistent.xy")

    # Test unsupported format through auto-detection
    with pytest.raises(ValueError, match="Unsupported file format"):
        load_diffraction_file("test.unsupported")
