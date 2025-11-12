"""
Data models for powder diffraction analysis.

This module provides the core data structures for handling powder diffraction data
in RoboMage. The main classes are designed to provide a rich, type-safe interface
for working with Q-space diffraction patterns while maintaining scientific metadata
and ensuring data integrity.

Key Classes:
    DiffractionData: Main container for powder diffraction patterns with metadata
    DataStatistics: Computed quality metrics and statistical summaries

Example:
    Basic usage for loading and working with diffraction data:

    >>> from robomage.data import DiffractionData
    >>> import numpy as np
    >>> # Create diffraction data
    >>> q_vals = np.linspace(1.0, 10.0, 1000)
    >>> intensities = np.random.exponential(100, 1000)
    >>> data = DiffractionData(
    ...     q_values=q_vals,
    ...     intensities=intensities,
    ...     filename="sample.chi",
    ...     sample_name="LaB6_standard",
    ... )
    >>> # Access automatic statistics
    >>> stats = data.statistics
    >>> print(f"Data has {stats.num_points} points")
    >>> # Manipulate data while preserving metadata
    >>> trimmed = data.trim_q_range(q_min=2.0, q_max=8.0)
    >>> resampled = trimmed.interpolate(np.linspace(2.0, 8.0, 500))

Design Philosophy:
    - Immutable operations: All data transformations return new instances
    - Automatic validation: Data integrity is enforced at creation and modification
    - Rich metadata: Complete provenance tracking for scientific reproducibility
    - Type safety: Comprehensive type hints for IDE support and static analysis
    - Domain semantics: Methods and properties that match powder diffraction workflows
"""

from datetime import datetime, timezone
from typing import Any

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, computed_field


class DataStatistics(BaseModel):
    """
    Statistical summary and quality metrics for powder diffraction data.

    This class provides computed quality metrics that are essential for assessing
    the quality of powder diffraction measurements. All statistics are computed
    automatically when accessed through DiffractionData.statistics.

    Attributes:
        num_points (int): Total number of data points in the pattern
        q_range (tuple[float, float]): Q-space coverage (min, max) in Å⁻¹
        q_step_mean (float): Average spacing between Q points in Å⁻¹
        q_step_std (float): Standard deviation of Q point spacing in Å⁻¹
        intensity_range (tuple[float, float]): Intensity coverage (min, max)
        intensity_mean (float): Average intensity across all points
        intensity_std (float): Standard deviation of intensities

    Quality Indicators:
        - q_step_std/q_step_mean: Lower ratios indicate more uniform Q sampling
        - intensity_mean/intensity_std: Simple signal-to-noise estimate
        - num_points: Higher point density generally improves peak resolution

    Note:
        This class is typically not instantiated directly. Instead, access it
        through the computed `statistics` property of a DiffractionData instance.

    Example:
        >>> data = DiffractionData(q_values=q_vals, intensities=intensities)
        >>> stats = data.statistics
        >>> uniformity = (1 - stats.q_step_std / stats.q_step_mean) * 100
        >>> print(f"Q sampling uniformity: {uniformity:.1f}%")
    """

    num_points: int = Field(description="Number of data points")
    q_range: tuple[float, float] = Field(description="Q range (min, max) in Å⁻¹")
    q_step_mean: float = Field(description="Mean Q step size in Å⁻¹")
    q_step_std: float = Field(description="Standard deviation of Q step size")
    intensity_range: tuple[float, float] = Field(
        description="Intensity range (min, max)"
    )
    intensity_mean: float = Field(description="Mean intensity")
    intensity_std: float = Field(description="Standard deviation of intensity")


class DiffractionData(BaseModel):
    """
    Container for powder diffraction data with rich metadata and operations.

    This is the core data structure for RoboMage powder diffraction analysis.
    It combines raw measurement data (Q-space and intensities) with comprehensive
    metadata and provides domain-specific operations while ensuring data integrity.

    The class uses Pydantic v2 for validation and type safety, automatically
    enforcing data consistency and providing computed properties for quality
    assessment.

    Attributes:
        q_values (np.ndarray): Q-space values in Å⁻¹ (scattering vector magnitude)
        intensities (np.ndarray): Measured intensities (arbitrary units)
        filename (str | None): Source filename for provenance tracking
        sample_name (str | None): Human-readable sample identifier
        timestamp (datetime): Creation timestamp (UTC)
        wavelength (float | None): X-ray wavelength in Å (if known)
        temperature (float | None): Sample temperature in K (if measured)

    Computed Properties:
        statistics (DataStatistics): Automatic quality metrics and statistical summary

    Key Features:
        - Automatic data validation (length matching, non-empty arrays)
        - Automatic Q-space sorting for consistent data ordering
        - Immutable operations that preserve metadata
        - Type-safe interface with comprehensive error checking
        - Integration with pandas for data exploration
        - Domain-specific operations (trimming, interpolation)

    Data Validation:
        The class automatically validates that:
        - Q values and intensities have matching lengths
        - Arrays are not empty
        - Q values are sorted in ascending order (auto-sorts if needed)

    Example:
        Basic usage:

        >>> import numpy as np
        >>> from robomage.data import DiffractionData
        >>> # Create from arrays
        >>> q_vals = np.array([1.0, 2.0, 3.0, 4.0])
        >>> intensities = np.array([100, 200, 150, 300])
        >>> data = DiffractionData(
        ...     q_values=q_vals,
        ...     intensities=intensities,
        ...     filename="test.chi",
        ...     sample_name="LaB6_standard",
        ...     wavelength=1.54056,  # Cu Kα
        ... )

        Working with the data:

        >>> # Access automatic statistics
        >>> stats = data.statistics
        >>> print(f"Data quality: {stats.num_points} points")
        >>> print(f"Q range: {stats.q_range[0]:.2f} - {stats.q_range[1]:.2f} Å⁻¹")

        >>> # Data operations preserve metadata
        >>> trimmed = data.trim_q_range(q_min=1.5, q_max=3.5)
        >>> print(f"Original: {data.filename}")
        >>> print(f"Trimmed: {trimmed.filename}")  # Same filename preserved

        >>> # Convert to pandas for exploration
        >>> df = data.to_dataframe()
        >>> print(df.head())

        >>> # Interpolate to uniform grid
        >>> uniform_q = np.linspace(1.0, 4.0, 100)
        >>> interpolated = data.interpolate(uniform_q)

    Design Notes:
        This class follows the "rich domain model" pattern, encapsulating both
        data and behavior relevant to powder diffraction analysis. It prioritizes
        scientific correctness, data provenance, and ease of use over raw performance.

        All modification operations return new instances (immutable pattern),
        ensuring data integrity and making the code more predictable and testable.
    """

    # Core data
    q_values: np.ndarray = Field(description="Q values in Å⁻¹")
    intensities: np.ndarray = Field(description="Intensity values")

    # Metadata
    filename: str | None = Field(default=None, description="Source filename")
    sample_name: str | None = Field(default=None, description="Sample identifier")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Optional experimental parameters
    wavelength: float | None = Field(default=None, description="X-ray wavelength in Å")
    temperature: float | None = Field(
        default=None, description="Sample temperature in K"
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def model_post_init(self, __context: Any) -> None:
        """Validate data after initialization."""
        if len(self.q_values) != len(self.intensities):
            raise ValueError("Q values and intensities must have the same length")

        if len(self.q_values) == 0:
            raise ValueError("Data arrays cannot be empty")

        # Ensure Q values are sorted
        if not np.all(self.q_values[:-1] <= self.q_values[1:]):
            # Sort both arrays by Q values
            sort_indices = np.argsort(self.q_values)
            object.__setattr__(self, "q_values", self.q_values[sort_indices])
            object.__setattr__(self, "intensities", self.intensities[sort_indices])

    @computed_field
    def statistics(self) -> DataStatistics:
        """
        Compute comprehensive statistical summary of the diffraction data.

        This computed field automatically calculates quality metrics and statistical
        properties of the powder diffraction pattern. The computation is performed
        on-demand and cached for efficiency.

        Returns:
            DataStatistics: Object containing all computed quality metrics including:
                - Data coverage (num_points, q_range)
                - Q-space sampling quality (q_step_mean, q_step_std)
                - Signal characteristics (intensity stats)

        Quality Indicators:
            The returned statistics can be used to assess data quality:

            - **Sampling uniformity**: (1 - q_step_std/q_step_mean) * 100
              Higher percentages indicate more uniform Q-space sampling

            - **Signal-to-noise estimate**: intensity_mean/intensity_std
              Higher ratios suggest better signal quality

            - **Dynamic range**: intensity_max/intensity_min
              Indicates the range of measured intensities

        Example:
            >>> data = DiffractionData(q_values=q_vals, intensities=intensities)
            >>> stats = data.statistics
            >>> uniformity = (1 - stats.q_step_std / stats.q_step_mean) * 100
            >>> print(f"Q sampling uniformity: {uniformity:.1f}%")
            >>> snr = stats.intensity_mean / stats.intensity_std
            >>> print(f"Signal-to-noise estimate: {snr:.1f}")

        Note:
            This is a computed field, so it will be recalculated automatically
            if the underlying data changes, but results are cached for efficiency.
        """
        q_diff = np.diff(self.q_values)

        return DataStatistics(
            num_points=len(self.q_values),
            q_range=(float(self.q_values.min()), float(self.q_values.max())),
            q_step_mean=float(q_diff.mean()),
            q_step_std=float(q_diff.std()),
            intensity_range=(
                float(self.intensities.min()),
                float(self.intensities.max()),
            ),
            intensity_mean=float(self.intensities.mean()),
            intensity_std=float(self.intensities.std()),
        )

    def to_dataframe(self) -> pd.DataFrame:
        """Convert diffraction data to a pandas DataFrame for analysis.

        Returns:
            pd.DataFrame: DataFrame with columns 'Q' and 'intensity' containing
                all data points for convenient data analysis and manipulation.

        Example:
            >>> data = DiffractionData.from_arrays([1.0, 2.0], [100, 200])
            >>> df = data.to_dataframe()
            >>> print(df.columns.tolist())
            ['Q', 'intensity']
        """
        return pd.DataFrame({"Q": self.q_values, "intensity": self.intensities})

    @classmethod
    def from_dataframe(
        cls,
        df: pd.DataFrame,
        filename: str | None = None,
        sample_name: str | None = None,
        **kwargs: Any,
    ) -> "DiffractionData":
        """Create DiffractionData from pandas DataFrame.

        Args:
            df: DataFrame with 'Q' and 'intensity' columns containing
                diffraction data points.
            filename: Optional source filename for metadata.
            sample_name: Optional sample identifier for metadata.
            **kwargs: Additional metadata fields to store with the data.

        Returns:
            DiffractionData: New instance with data from the DataFrame.

        Raises:
            KeyError: If required columns 'Q' or 'intensity' are missing.

        Example:
            >>> import pandas as pd
            >>> df = pd.DataFrame({"Q": [1.0, 2.0], "intensity": [100, 200]})
            >>> data = DiffractionData.from_dataframe(df, filename="test.chi")
            >>> print(data.num_points)
            2
        """
        if "Q" not in df.columns or "intensity" not in df.columns:
            raise ValueError("DataFrame must contain 'Q' and 'intensity' columns")

        return cls(
            q_values=np.asarray(df["Q"].values),
            intensities=np.asarray(df["intensity"].values),
            filename=filename,
            sample_name=sample_name,
            **kwargs,
        )

    @classmethod
    def from_arrays(
        cls, q_values: np.ndarray, intensities: np.ndarray, **kwargs: Any
    ) -> "DiffractionData":
        """Create DiffractionData from numpy arrays.

        Args:
            q_values: Q values in Å⁻¹ (scattering vector magnitude).
            intensities: Corresponding intensity values (arbitrary units).
            **kwargs: Additional metadata fields to store with the data.

        Returns:
            DiffractionData: New instance with the provided arrays.

        Note:
            Data will be automatically sorted by Q values during creation
            for consistent ordering.

        Example:
            >>> import numpy as np
            >>> q = np.array([1.0, 2.0, 3.0])
            >>> intensity = np.array([100, 150, 80])
            >>> data = DiffractionData.from_arrays(q, intensity, sample_name="test")
            >>> print(data.num_points)
            3
        """
        return cls(q_values=q_values, intensities=intensities, **kwargs)

    def trim_q_range(
        self, q_min: float | None = None, q_max: float | None = None
    ) -> "DiffractionData":
        """Create a new DiffractionData instance trimmed to Q range.

        Args:
            q_min: Minimum Q value (inclusive). If None, no lower bound.
            q_max: Maximum Q value (inclusive). If None, no upper bound.

        Returns:
            DiffractionData: New instance with data points within the
                specified Q range. All metadata is preserved.

        Example:
            >>> data = DiffractionData.from_arrays(
            ...     [0.5, 1.0, 1.5, 2.0], [100, 200, 300, 400]
            ... )
            >>> trimmed = data.trim_q_range(q_min=1.0, q_max=1.5)
            >>> print(trimmed.num_points)
            2
            >>> print(trimmed.q_range)
            (1.0, 1.5)
        """
        mask = np.ones(len(self.q_values), dtype=bool)

        if q_min is not None:
            mask &= self.q_values >= q_min
        if q_max is not None:
            mask &= self.q_values <= q_max

        return self.__class__(
            q_values=self.q_values[mask],
            intensities=self.intensities[mask],
            filename=self.filename,
            sample_name=self.sample_name,
            timestamp=self.timestamp,
            wavelength=self.wavelength,
            temperature=self.temperature,
        )

    def interpolate(self, new_q_values: np.ndarray) -> "DiffractionData":
        """Interpolate data to new Q values using linear interpolation.

        Args:
            new_q_values: Target Q values for interpolation (in Å⁻¹).
                Must be within the range of existing Q values.

        Returns:
            DiffractionData: New instance with linearly interpolated
                intensities at the specified Q values. All metadata
                is preserved from the original data.

        Note:
            Uses numpy.interp for linear interpolation. Values outside
            the original Q range will be extrapolated using edge values.

        Example:
            >>> original = DiffractionData.from_arrays([1.0, 2.0, 3.0], [100, 200, 300])
            >>> new_q = np.array([1.5, 2.5])
            >>> interpolated = original.interpolate(new_q)
            >>> print(interpolated.intensities)  # [150, 250]
        """
        interpolated_intensities = np.interp(
            new_q_values, self.q_values, self.intensities
        )

        return self.__class__(
            q_values=new_q_values,
            intensities=interpolated_intensities,
            filename=self.filename,
            sample_name=self.sample_name,
            timestamp=self.timestamp,
            wavelength=self.wavelength,
            temperature=self.temperature,
        )
