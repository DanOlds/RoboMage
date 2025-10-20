"""RoboMage: Automated powder diffraction analysis framework.

RoboMage is a Python library for loading, analyzing, and visualizing powder
diffraction data with a focus on automation, reproducibility, and ease of use.
It provides both programmatic APIs and command-line tools for common powder
diffraction workflows.

Key Features:
    - Robust data loading with validation and error handling
    - Modern Pydantic-based data models with automatic validation
    - Statistical analysis and quality assessment tools
    - Publication-quality visualization capabilities
    - Command-line interface for batch processing
    - Extensible architecture for custom analysis pipelines

Package Structure:
    - data: Core data structures and loading utilities
    - config: Configuration schemas and validation
    - visualization: Plotting and analysis tools (planned)
    - CLI: Command-line interface via python -m robomage

Quick Start:
    >>> import robomage
    >>> # Load and analyze diffraction data
    >>> data = robomage.load_diffraction_file("sample.chi")
    >>> print(f"Loaded {len(data.q_values)} data points")
    >>> # Get statistical summary
    >>> stats = data.statistics
    >>> print(f"Quality score: {stats.quality_score:.2f}")
    >>> # Load test data for development
    >>> test_data = robomage.load_test_data()
    >>> print(f"Test data Q range: {test_data.statistics.q_range}")

Public API:
    The following functions and classes are available for import:

    Data Loading:
        - load_diffraction_file(): Load data with automatic format detection
        - load_chi_file(): Load .chi files specifically
        - load_test_data(): Load built-in SRM 660b test dataset

    Data Structures:
        - DiffractionData: Main data container with validation
        - DataStatistics: Computed statistical properties

    Legacy API (for compatibility):
        - load_chi_file_df(): Load as pandas DataFrame
        - get_data_info(): Extract DataFrame statistics
        - load_test_data_df(): Load test data as DataFrame

Installation:
    RoboMage is designed to work with the Pixi package manager:

    $ pixi install
    $ pixi run python -c "import robomage; print(robomage.__version__)"

Command-line Usage:
    $ pixi run python -m robomage test --info --plot
    $ pixi run python -m robomage sample.chi --save-plot result.png
    $ pixi run python -m robomage --files *.chi --output plots/

Dependencies:
    Core: numpy, pandas, pydantic
    Optional: matplotlib (for visualization)
    Development: pytest, ruff, mypy

See Also:
    - Documentation: README.md
    - Examples: examples/ directory
    - Tests: tests/ directory
    - Configuration: pyproject.toml, pixi.toml

Version: 0.1.0 (development)
License: See LICENSE file
"""

# Version information
__version__ = "0.1.0-dev"
__author__ = "RoboMage Development Team"
__license__ = "See LICENSE file"

# Core imports - Modern API (recommended for new code)
from .data.loaders import (
    load_chi_file,
    load_diffraction_file,
    load_test_data,
)
from .data.models import (
    DataStatistics,
    DiffractionData,
)

# Legacy imports - DataFrame-based API (for backward compatibility)
from .data_io import (
    get_data_info,
)
from .data_io import (
    load_chi_file as load_chi_file_df,
)
from .data_io import (
    load_test_data as load_test_data_df,
)

# Define public API - controls what gets imported with "from robomage import *"
__all__ = [
    # Version and metadata
    "__version__",
    "__author__",
    "__license__",
    # Modern API - recommended for new code
    "load_diffraction_file",
    "load_chi_file",
    "load_test_data",
    "DiffractionData",
    "DataStatistics",
    # Legacy API - for backward compatibility
    "load_chi_file_df",
    "load_test_data_df",
    "get_data_info",
]
