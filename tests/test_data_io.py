"""Tests for data input/output functionality."""

from pathlib import Path

import pandas as pd
import pytest

from robomage.data_io import get_data_info, load_chi_file, load_test_data


def test_load_test_data():
    """Test loading the standard test dataset."""
    df = load_test_data()

    # Check that we got a DataFrame
    assert isinstance(df, pd.DataFrame)

    # Check expected columns
    assert list(df.columns) == ["Q", "intensity"]

    # Check that we have data
    assert len(df) > 0

    # Check that Q values are sorted (typical for diffraction data)
    assert df["Q"].is_monotonic_increasing

    # Check that intensities are positive (typical for diffraction)
    assert (df["intensity"] >= 0).all()


def test_get_data_info():
    """Test the data info function."""
    df = load_test_data()
    info = get_data_info(df)

    # Check that all expected keys are present
    expected_keys = {
        "num_points",
        "q_range",
        "q_step_mean",
        "q_step_std",
        "intensity_range",
        "intensity_mean",
        "intensity_std",
    }
    assert set(info.keys()) == expected_keys

    # Check some basic sanity
    assert info["num_points"] > 0
    assert info["q_range"][0] < info["q_range"][1]
    assert info["intensity_range"][0] <= info["intensity_range"][1]


def test_load_chi_file_directly():
    """Test loading the chi file directly."""
    # Get project root and test file path
    current_file = Path(__file__)
    project_root = current_file.parents[1]  # Go up from tests/ to root
    test_file = project_root / "examples" / "pdf_SRM_660b_q.chi"

    df = load_chi_file(test_file)

    # Basic checks
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["Q", "intensity"]
    assert len(df) > 0


def test_load_nonexistent_file():
    """Test that loading a nonexistent file raises appropriate error."""
    with pytest.raises(FileNotFoundError):
        load_chi_file("nonexistent_file.chi")


def test_load_wrong_extension():
    """Test that loading a file with wrong extension raises error."""
    with pytest.raises(ValueError, match="Expected .chi file"):
        load_chi_file("somefile.txt")
