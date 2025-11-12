"""Legacy data input/output utilities for RoboMage.

This module provides pandas DataFrame-based data loading utilities for backward
compatibility with older code and for use cases where direct DataFrame access
is preferred over the more structured DiffractionData objects.

Design Notes:
    - This module returns pandas DataFrames directly
    - For new code, consider using `robomage.data.loaders` which returns
      validated DiffractionData objects with richer functionality
    - Functions here focus on basic I/O operations without validation
    - Useful for integration with existing pandas-based workflows

Relationship to Other Modules:
    - `data.loaders`: Modern API returning DiffractionData objects
    - `data.models`: Data structures and validation
    - This module: Legacy DataFrame-based API

Supported Formats:
    - .chi files: Two-column text files with Q (Å⁻¹) and intensity data
    - .xy files: Two-column text files with Q (Å⁻¹) and intensity data

Functions:
    - load_diffraction_file_df(): Load .chi/.xy files into DataFrames
    - load_chi_file(): Backward-compatible wrapper for chi files
    - get_data_info(): Extract statistical summaries from DataFrames
    - load_test_data(): Load SRM 660b test dataset as DataFrame

Migration Path:
    To migrate from this module to the modern API:

    # Old approach (this module)
    >>> from robomage.data_io import load_chi_file
    >>> df = load_chi_file("sample.chi")

    # New approach (recommended)
    >>> from robomage.data.loaders import load_chi_file
    >>> data = load_chi_file("sample.chi")
    >>> df = data.to_dataframe()  # Convert to DataFrame if needed

Warning:
    This module may be deprecated in future versions. New projects should
    use `robomage.data.loaders` for enhanced functionality and validation.
"""

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def load_diffraction_file_df(filepath: str | Path) -> pd.DataFrame:
    """Load a diffraction data file (.chi or .xy) into a DataFrame.

    This is the legacy DataFrame-based loader for diffraction files. For new code,
    consider using `robomage.data.loaders.load_diffraction_file()` which returns
    a validated DiffractionData object with additional functionality.

    Supported formats:
    - .chi files: Two-column text files (Q, intensity)
    - .xy files: Two-column text files (Q, intensity)

    Both formats contain Q values (scattering vector magnitude in Å⁻¹) and
    corresponding intensity values. Comment lines starting with '#' are
    automatically skipped.

    Args:
        filepath: Path to the diffraction file to load. Can be a string or Path object.

    Returns:
        pd.DataFrame: DataFrame with columns ['Q', 'intensity'] containing
            the loaded diffraction data. No validation or sorting is applied.

    Raises:
        FileNotFoundError: If the specified file doesn't exist.
        ValueError: If the file extension is not '.chi' or '.xy', the file doesn't
            contain exactly 2 columns, or parsing fails for any reason.

    Note:
        - Comment lines (starting with '#') are automatically ignored
        - Data is expected in two columns: Q values, then intensities
        - No data validation or automatic sorting is performed
        - Supports both .chi and .xy formats
        - For validated data objects, use `robomage.data.loaders` instead

    Example:
        >>> from robomage.data_io import load_diffraction_file_df
        >>> df = load_diffraction_file_df("sample.chi")  # or "sample.xy"
        >>> print(df.columns.tolist())
        ['Q', 'intensity']
        >>> print(f"Loaded {len(df)} data points")

    See Also:
        robomage.data.loaders.load_diffraction_file: Modern API with validation
    """
    filepath = Path(filepath)

    if filepath.suffix.lower() not in [".chi", ".xy"]:
        raise ValueError(f"Expected .chi or .xy file, got: {filepath.suffix}")

    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    try:
        # Read the file, skipping comment lines that start with #
        data = np.loadtxt(filepath, comments="#")

        if data.shape[1] != 2:
            raise ValueError(f"Expected 2 columns, got {data.shape[1]}")

        # Create DataFrame with meaningful column names
        df = pd.DataFrame(data, columns=["Q", "intensity"])

        return df

    except Exception as e:
        raise ValueError(f"Failed to parse {filepath}: {e}") from e


def load_chi_file(filepath: str | Path) -> pd.DataFrame:
    """Load a .chi file containing Q and intensity data into a DataFrame.

    Backward compatibility wrapper for load_diffraction_file_df().

    Args:
        filepath: Path to the .chi file to load.

    Returns:
        pd.DataFrame: DataFrame with columns ['Q', 'intensity'].

    Note:
        This function now supports both .chi and .xy files for convenience.
        For new code, consider using robomage.data.loaders instead.
    """
    return load_diffraction_file_df(filepath)


def get_data_info(df: pd.DataFrame) -> dict[str, Any]:
    """Get comprehensive summary statistics for diffraction data.

    Extracts key statistical information from a DataFrame containing
    diffraction data, including data coverage, Q-space sampling, and
    intensity statistics. Useful for data quality assessment and
    experimental parameter evaluation.

    Args:
        df: DataFrame containing diffraction data with columns 'Q' and
            'intensity'. Q values should be in Å⁻¹ and intensities in
            arbitrary units.

    Returns:
        dict[str, Any]: Dictionary containing statistical summaries:
            - num_points (int): Total number of data points
            - q_range (tuple): Min and max Q values (Å⁻¹)
            - q_step_mean (float): Average Q spacing (Å⁻¹)
            - q_step_std (float): Standard deviation of Q spacing
            - intensity_range (tuple): Min and max intensity values
            - intensity_mean (float): Mean intensity value
            - intensity_std (float): Standard deviation of intensities

    Note:
        - Q spacing statistics help assess data quality and uniformity
        - Large q_step_std indicates non-uniform sampling
        - For validated data objects with richer statistics, use
          DiffractionData.statistics property instead

    Example:
        >>> from robomage.data_io import load_chi_file, get_data_info
        >>> df = load_chi_file("sample.chi")
        >>> info = get_data_info(df)
        >>> print(f"Data points: {info['num_points']}")
        >>> print(f"Q range: {info['q_range'][0]:.2f} - {info['q_range'][1]:.2f} Å⁻¹")
        >>> print(f"Average Q step: {info['q_step_mean']:.4f} Å⁻¹")

    See Also:
        DiffractionData.statistics: Modern API with computed statistics
    """
    return {
        "num_points": len(df),
        "q_range": (df["Q"].min(), df["Q"].max()),
        "q_step_mean": float(df["Q"].diff().mean()),  # type: ignore[misc]
        "q_step_std": float(df["Q"].diff().std()),  # type: ignore[misc]
        "intensity_range": (df["intensity"].min(), df["intensity"].max()),
        "intensity_mean": float(df["intensity"].mean()),
        "intensity_std": float(df["intensity"].std()),
    }


def load_test_data() -> pd.DataFrame:
    """Load the standard test dataset (SRM 660b LaB₆) as a DataFrame.

    Loads the SRM 660b (LaB₆) powder diffraction standard from NIST as a
    pandas DataFrame for backward compatibility with legacy code. This is
    the same dataset available through the modern API but returned as a
    raw DataFrame without validation or metadata.

    Returns:
        pd.DataFrame: DataFrame with columns ['Q', 'intensity'] containing
            the SRM 660b diffraction pattern. Q values are in Å⁻¹ and
            intensities are in arbitrary units.

    Raises:
        FileNotFoundError: If the test data file cannot be found in the
            expected location (examples/pdf_SRM_660b_q.chi).

    Note:
        - For new code, consider using `robomage.data.loaders.load_test_data()`
          which returns a validated DiffractionData object
        - This function provides direct DataFrame access for pandas workflows
        - No metadata or validation is included with the returned data
        - Path resolution is relative to the package structure

    Example:
        >>> from robomage.data_io import load_test_data, get_data_info
        >>> df = load_test_data()
        >>> info = get_data_info(df)
        >>> print(f"Test data: {info['num_points']} points")
        >>> print(f"Q range: {info['q_range']}")

        >>> # Convert to DiffractionData if needed
        >>> from robomage.data.models import DiffractionData
        >>> data = DiffractionData.from_dataframe(df, filename="SRM_660b")

    Reference:
        NIST SRM 660b: LaB₆ powder for X-ray diffraction calibration
        https://www.nist.gov/srm

    See Also:
        robomage.data.loaders.load_test_data: Modern API with validation
    """
    # Get the project root directory
    current_file = Path(__file__)
    project_root = current_file.parents[2]  # Go up from src/robomage/data_io.py to root

    test_file = project_root / "examples" / "pdf_SRM_660b_q.chi"

    if not test_file.exists():
        raise FileNotFoundError(f"Test data file not found: {test_file}")

    return load_chi_file(test_file)
