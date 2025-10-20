"""Tests for the data models module."""

from datetime import datetime

import numpy as np
import pytest

from robomage.data.models import DataStatistics, DiffractionData


def test_diffraction_data_creation():
    """Test basic DiffractionData creation."""
    q_values = np.array([1.0, 2.0, 3.0])
    intensities = np.array([100.0, 200.0, 150.0])

    data = DiffractionData(q_values=q_values, intensities=intensities)

    assert len(data.q_values) == 3
    assert len(data.intensities) == 3
    assert data.filename is None
    assert data.sample_name is None
    assert isinstance(data.timestamp, datetime)


def test_diffraction_data_with_metadata():
    """Test DiffractionData creation with metadata."""
    q_values = np.array([1.0, 2.0, 3.0])
    intensities = np.array([100.0, 200.0, 150.0])

    data = DiffractionData(
        q_values=q_values,
        intensities=intensities,
        filename="test.chi",
        sample_name="test_sample",
        wavelength=1.54,
        temperature=300.0,
    )

    assert data.filename == "test.chi"
    assert data.sample_name == "test_sample"
    assert data.wavelength == 1.54
    assert data.temperature == 300.0


def test_diffraction_data_validation():
    """Test that DiffractionData validates input correctly."""
    # Test mismatched array lengths
    with pytest.raises(ValueError, match="same length"):
        DiffractionData(
            q_values=np.array([1.0, 2.0]), intensities=np.array([100.0, 200.0, 150.0])
        )

    # Test empty arrays
    with pytest.raises(ValueError, match="cannot be empty"):
        DiffractionData(q_values=np.array([]), intensities=np.array([]))


def test_diffraction_data_sorting():
    """Test that Q values are automatically sorted."""
    q_values = np.array([3.0, 1.0, 2.0])
    intensities = np.array([150.0, 100.0, 200.0])

    data = DiffractionData(q_values=q_values, intensities=intensities)

    # Check that data is sorted by Q
    expected_q = np.array([1.0, 2.0, 3.0])
    expected_i = np.array([100.0, 200.0, 150.0])

    np.testing.assert_array_equal(data.q_values, expected_q)
    np.testing.assert_array_equal(data.intensities, expected_i)


def test_statistics_computation():
    """Test statistical summary computation."""
    q_values = np.array([1.0, 2.0, 3.0, 4.0])
    intensities = np.array([100.0, 200.0, 150.0, 300.0])

    data = DiffractionData(q_values=q_values, intensities=intensities)
    stats = data.statistics

    assert isinstance(stats, DataStatistics)
    assert stats.num_points == 4
    assert stats.q_range == (1.0, 4.0)
    assert stats.q_step_mean == 1.0  # Uniform spacing
    assert stats.q_step_std == 0.0  # Uniform spacing
    assert stats.intensity_range == (100.0, 300.0)
    assert stats.intensity_mean == 187.5


def test_dataframe_conversion():
    """Test conversion to and from pandas DataFrame."""
    q_values = np.array([1.0, 2.0, 3.0])
    intensities = np.array([100.0, 200.0, 150.0])

    # Create DiffractionData
    data = DiffractionData(q_values=q_values, intensities=intensities)

    # Convert to DataFrame
    df = data.to_dataframe()
    assert list(df.columns) == ["Q", "intensity"]
    assert len(df) == 3

    # Convert back from DataFrame
    data2 = DiffractionData.from_dataframe(df, filename="test.chi")

    np.testing.assert_array_equal(data2.q_values, q_values)
    np.testing.assert_array_equal(data2.intensities, intensities)
    assert data2.filename == "test.chi"


def test_trim_q_range():
    """Test Q range trimming functionality."""
    q_values = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    intensities = np.array([100.0, 200.0, 150.0, 300.0, 250.0])

    data = DiffractionData(q_values=q_values, intensities=intensities)

    # Trim to Q range 2-4
    trimmed = data.trim_q_range(q_min=2.0, q_max=4.0)

    expected_q = np.array([2.0, 3.0, 4.0])
    expected_i = np.array([200.0, 150.0, 300.0])

    np.testing.assert_array_equal(trimmed.q_values, expected_q)
    np.testing.assert_array_equal(trimmed.intensities, expected_i)


def test_interpolation():
    """Test data interpolation functionality."""
    q_values = np.array([1.0, 2.0, 3.0])
    intensities = np.array([100.0, 200.0, 300.0])

    data = DiffractionData(q_values=q_values, intensities=intensities)

    # Interpolate to new Q grid
    new_q = np.array([1.5, 2.5])
    interpolated = data.interpolate(new_q)

    expected_i = np.array([150.0, 250.0])  # Linear interpolation

    np.testing.assert_array_equal(interpolated.q_values, new_q)
    np.testing.assert_array_equal(interpolated.intensities, expected_i)
