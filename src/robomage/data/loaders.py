"""Data loading utilities for powder diffraction files."""

from pathlib import Path

import numpy as np

from .models import DiffractionData


def load_chi_file(filepath: str | Path) -> DiffractionData:
    """
    Load a .chi file containing Q and intensity data.

    Args:
        filepath: Path to the .chi file

    Returns:
        DiffractionData instance

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file format is invalid
    """
    filepath = Path(filepath)

    if not filepath.suffix.lower() == ".chi":
        raise ValueError(f"Expected .chi file, got: {filepath.suffix}")

    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    try:
        # Read the file, skipping comment lines that start with #
        data = np.loadtxt(filepath, comments="#")

        if data.shape[1] != 2:
            raise ValueError(f"Expected 2 columns, got {data.shape[1]}")

        # Extract filename for metadata
        filename = filepath.name

        # Create DiffractionData with metadata
        return DiffractionData(
            q_values=data[:, 0],
            intensities=data[:, 1],
            filename=filename,
        )

    except Exception as e:
        raise ValueError(f"Failed to parse {filepath}: {e}") from e


def load_diffraction_file(filepath: str | Path) -> DiffractionData:
    """
    Load a diffraction data file, automatically detecting the format.

    Currently supports:
    - .chi files (Q vs intensity)

    Args:
        filepath: Path to the diffraction data file

    Returns:
        DiffractionData instance

    Raises:
        ValueError: If the file format is not supported
    """
    filepath = Path(filepath)
    
    if filepath.suffix.lower() == ".chi":
        return load_chi_file(filepath)
    else:
        raise ValueError(
            f"Unsupported file format: {filepath.suffix}. "
            "Supported formats: .chi"
        )


def load_test_data() -> DiffractionData:
    """
    Load the standard test dataset (SRM 660b).

    Returns:
        DiffractionData with the test diffraction pattern
    """
    # Get the project root directory
    current_file = Path(__file__)
    project_root = current_file.parents[3]  # Go up from src/robomage/data/loaders.py
    
    test_file = project_root / "examples" / "pdf_SRM_660b_q.chi"

    if not test_file.exists():
        raise FileNotFoundError(f"Test data file not found: {test_file}")

    return load_chi_file(test_file)