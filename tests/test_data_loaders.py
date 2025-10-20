"""Tests for the data loaders module."""

from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from robomage.data.loaders import load_chi_file, load_diffraction_file
from robomage.data.models import DiffractionData


def test_load_chi_file_validation():
    """Test that load_chi_file validates file extensions and existence."""
    # Test wrong extension
    with pytest.raises(ValueError, match="Expected .chi file"):
        load_chi_file("test.txt")

    # Test non-existent file
    with pytest.raises(FileNotFoundError, match="File not found"):
        load_chi_file("nonexistent.chi")


@patch("numpy.loadtxt")
@patch("pathlib.Path.exists")
def test_load_chi_file_success(mock_exists, mock_loadtxt):
    """Test successful loading of a .chi file."""
    # Mock file existence and data
    mock_exists.return_value = True
    mock_data = np.array([[1.0, 100.0], [2.0, 200.0], [3.0, 150.0]])
    mock_loadtxt.return_value = mock_data

    # Load the file
    result = load_chi_file("test.chi")

    # Verify result
    assert isinstance(result, DiffractionData)
    assert result.filename == "test.chi"
    np.testing.assert_array_equal(result.q_values, [1.0, 2.0, 3.0])
    np.testing.assert_array_equal(result.intensities, [100.0, 200.0, 150.0])

    # Verify numpy.loadtxt was called correctly
    mock_loadtxt.assert_called_once()
    args, kwargs = mock_loadtxt.call_args
    assert kwargs.get("comments") == "#"


@patch("numpy.loadtxt")
@patch("pathlib.Path.exists")
def test_load_chi_file_wrong_columns(mock_exists, mock_loadtxt):
    """Test error handling for wrong number of columns."""
    mock_exists.return_value = True
    mock_loadtxt.return_value = np.array([[1.0, 2.0, 3.0]])  # 3 columns

    with pytest.raises(ValueError, match="Expected 2 columns, got 3"):
        load_chi_file("test.chi")


@patch("numpy.loadtxt")
@patch("pathlib.Path.exists")
def test_load_chi_file_parse_error(mock_exists, mock_loadtxt):
    """Test error handling for file parsing failures."""
    mock_exists.return_value = True
    mock_loadtxt.side_effect = Exception("Parse error")

    with pytest.raises(ValueError, match="Failed to parse.*Parse error"):
        load_chi_file("test.chi")


def test_load_diffraction_file_chi():
    """Test that load_diffraction_file delegates to load_chi_file."""
    with patch("robomage.data.loaders.load_chi_file") as mock_load_chi:
        mock_result = DiffractionData(
            q_values=np.array([1.0]), intensities=np.array([100.0])
        )
        mock_load_chi.return_value = mock_result

        result = load_diffraction_file("test.chi")

        assert result == mock_result
        mock_load_chi.assert_called_once_with(Path("test.chi"))


def test_load_diffraction_file_unsupported():
    """Test error for unsupported file formats."""
    with pytest.raises(ValueError, match="Unsupported file format.*\\.txt"):
        load_diffraction_file("test.txt")
