"""Data handling module for RoboMage powder diffraction analysis.

This module provides the core data structures and loading utilities for working
with powder diffraction data. It combines robust file I/O with validated data
models to ensure reliable data handling throughout the analysis pipeline.

Architecture:
    The data module follows a layered architecture:

    1. **File Loaders** (loaders.py): Handle various file formats with validation
    2. **Data Models** (models.py): Pydantic-based validated data containers
    3. **Public API** (this file): Clean interface for common operations

Key Components:
    - DiffractionData: Main data container with automatic validation
    - DataStatistics: Computed statistical properties and quality metrics
    - load_diffraction_file(): Smart file loader with format auto-detection
    - load_chi_file(): Specialized loader for .chi format files

Design Philosophy:
    - **Validation First**: All data is validated upon loading using Pydantic
    - **Immutability**: Data objects are immutable to prevent accidental modification
    - **Rich Metadata**: Preserve experimental conditions and file provenance
    - **Statistical Analysis**: Built-in quality assessment and data characterization
    - **Type Safety**: Full type hints for better IDE support and error detection

Quick Start:
    >>> from robomage.data import DiffractionData, load_diffraction_file
    >>> # Load data with automatic format detection
    >>> data = load_diffraction_file("sample.chi")
    >>> print(f"Loaded {len(data.q_values)} data points")
    >>> # Access statistical properties
    >>> stats = data.statistics
    >>> print(f"Quality score: {stats.quality_score:.2f}")
    >>> print(f"Q range: {stats.q_range}")
    >>> # Create data from arrays
    >>> import numpy as np
    >>> q = np.linspace(1, 10, 100)
    >>> intensity = 1000 * np.exp(-((q - 5) ** 2) / 2)
    >>> custom_data = DiffractionData.from_arrays(q, intensity, sample_name="synthetic")

Data Flow:
    Raw Files → File Loaders → DiffractionData → Analysis/Visualization

    1. File loaders parse and validate input files
    2. DiffractionData provides a standardized container
    3. Statistics are computed automatically and cached
    4. Data can be exported for analysis or visualization

Supported File Formats:
    - .chi files: Two-column Q/intensity text files
    - Future: .xy, .dat, .xye, and other common formats

Error Handling:
    - FileNotFoundError: For missing input files
    - ValueError: For invalid file formats or data structure
    - ValidationError: For data that fails Pydantic validation

Integration:
    The data module integrates seamlessly with:
    - Command-line interface (robomage.__main__)
    - Legacy DataFrame API (robomage.data_io)
    - Future visualization tools (robomage.visualization)
    - Configuration system (robomage.config)

See Also:
    - models.py: Detailed documentation of data structures
    - loaders.py: File format specifications and loading examples
    - ../data_io.py: Legacy pandas-based interface
"""

# Import core data structures from models
# Import file loading utilities from loaders
# Also import the test data loader for convenience
from .loaders import load_chi_file, load_diffraction_file, load_test_data
from .models import DataStatistics, DiffractionData

# Public API - these are the recommended imports for users
__all__ = [
    # Core data structures (most important)
    "DiffractionData",  # Main data container with validation
    "DataStatistics",  # Statistical properties and quality metrics
    # File loading functions (primary interface)
    "load_diffraction_file",  # Smart loader with format auto-detection
    "load_chi_file",  # Specialized .chi file loader
    "load_test_data",  # Built-in SRM 660b test dataset
]
