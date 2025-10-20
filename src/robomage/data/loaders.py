"""Data loading utilities for powder diffraction files.

This module provides functions for loading powder diffraction data from various
file formats into standardized DiffractionData objects. The loaders handle
file format detection, data validation, and metadata extraction.

Supported Formats:
    - .chi files: Two-column text files with Q (Å⁻¹) and intensity data
    - More formats planned for future releases

Key Features:
    - Automatic file format detection
    - Comprehensive error handling and validation
    - Metadata extraction from filenames and headers
    - Standard test data loading for development and testing

Usage:
    >>> from robomage.data.loaders import load_diffraction_file
    >>> data = load_diffraction_file("sample.chi")
    >>> print(f"Loaded {data.num_points} data points")

    >>> # Load test data for development
    >>> from robomage.data.loaders import load_test_data
    >>> test_data = load_test_data()
    >>> print(f"Test data Q range: {test_data.q_range}")

Error Handling:
    All loaders provide detailed error messages for common issues:
    - File not found
    - Unsupported formats
    - Invalid data structure
    - Parsing errors

See Also:
    - DiffractionData: The main data container class
    - models.py: Core data structures and validation
"""

from pathlib import Path

import numpy as np

from .models import DiffractionData


def load_chi_file(filepath: str | Path) -> DiffractionData:
    """Load a .chi file containing Q and intensity data.

    Chi files are a common format for powder diffraction data, consisting of
    two-column text files with Q values (scattering vector magnitude in Å⁻¹)
    and corresponding intensity values. Comment lines starting with '#' are
    automatically skipped.

    Args:
        filepath: Path to the .chi file to load. Can be a string or Path object.

    Returns:
        DiffractionData: A validated DiffractionData instance containing the
            loaded data with automatic Q-value sorting and metadata from the
            filename.

    Raises:
        FileNotFoundError: If the specified file doesn't exist.
        ValueError: If the file extension is not '.chi', the file doesn't
            contain exactly 2 columns, or parsing fails for any reason.

    Note:
        - Comment lines (starting with '#') are automatically ignored
        - Data is expected in two columns: Q values, then intensities
        - Q values should be in Å⁻¹ units
        - Intensity values are in arbitrary units

    Example:
        >>> from robomage.data.loaders import load_chi_file
        >>> data = load_chi_file("sample.chi")
        >>> print(f"Loaded {data.num_points} points")
        >>> print(f"Q range: {data.q_range}")
        >>> print(f"Filename: {data.filename}")

        >>> # File format example:
        >>> # # Comments are ignored
        >>> # 1.0  100.5
        >>> # 1.1  150.2
        >>> # 1.2  120.8
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
    """Load a diffraction data file with automatic format detection.

    This is the main entry point for loading diffraction data files. The
    function automatically detects the file format based on the file extension
    and delegates to the appropriate specialized loader.

    Currently Supported Formats:
        - .chi: Two-column text files (Q, intensity)

    Planned Future Support:
        - .xy: Generic two-column data files
        - .dat: Various instrument-specific formats
        - .xye: Three-column files with error values

    Args:
        filepath: Path to the diffraction data file. Can be a string or
            Path object.

    Returns:
        DiffractionData: A validated DiffractionData instance containing the
            loaded data with appropriate metadata.

    Raises:
        ValueError: If the file format is not supported or if the file
            cannot be parsed.
        FileNotFoundError: If the specified file doesn't exist.

    Example:
        >>> from robomage.data.loaders import load_diffraction_file
        >>> # Works with any supported format
        >>> data = load_diffraction_file("my_sample.chi")
        >>> print(f"Loaded {data.filename} with {data.num_points} points")

        >>> # Error handling
        >>> try:
        ...     data = load_diffraction_file("unsupported.xyz")
        ... except ValueError as e:
        ...     print(f"Format error: {e}")
    """
    filepath = Path(filepath)

    if filepath.suffix.lower() == ".chi":
        return load_chi_file(filepath)
    else:
        raise ValueError(
            f"Unsupported file format: {filepath.suffix}. Supported formats: .chi"
        )


def load_test_data() -> DiffractionData:
    """Load the standard test dataset (SRM 660b LaB₆).

    Loads the SRM 660b (LaB₆) powder diffraction standard from NIST, which
    is included with RoboMage for testing, development, and demonstration
    purposes. This is a well-characterized reference material commonly used
    for instrument calibration and method validation.

    Returns:
        DiffractionData: The SRM 660b diffraction pattern with metadata
            including the filename and sample identification.

    Raises:
        FileNotFoundError: If the test data file cannot be found in the
            expected location (examples/pdf_SRM_660b_q.chi).

    Note:
        - The data is in Q-space (Å⁻¹) vs intensity
        - This is a real experimental dataset from NIST
        - Useful for testing algorithms and demonstrating functionality
        - The file is automatically located relative to the package structure

    Example:
        >>> from robomage.data.loaders import load_test_data
        >>> test_data = load_test_data()
        >>> print(f"Test data: {test_data.filename}")
        >>> print(f"Data points: {test_data.num_points}")
        >>> print(f"Q range: {test_data.q_range}")

        >>> # Use for development and testing
        >>> stats = test_data.statistics()
        >>> print(f"Peak intensity: {stats.max_intensity}")
        >>> print(f"Quality score: {stats.quality_score:.2f}")

    Reference:
        NIST SRM 660b: LaB₆ powder for X-ray diffraction calibration
        https://www.nist.gov/srm
    """
    # Get the project root directory
    current_file = Path(__file__)
    project_root = current_file.parents[3]  # Go up from src/robomage/data/loaders.py

    test_file = project_root / "examples" / "pdf_SRM_660b_q.chi"

    if not test_file.exists():
        raise FileNotFoundError(f"Test data file not found: {test_file}")

    return load_chi_file(test_file)
