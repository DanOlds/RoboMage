"""Data models for powder diffraction analysis."""

from datetime import datetime, timezone

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, computed_field


class DataStatistics(BaseModel):
    """Statistical summary of diffraction data."""

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
    Container for powder diffraction data with metadata.

    This class represents a powder diffraction pattern with Q (scattering vector)
    and intensity data, along with associated metadata and computed statistics.
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

    def model_post_init(self, __context) -> None:
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
    @property
    def statistics(self) -> DataStatistics:
        """Compute statistical summary of the data."""
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
        """
        Convert to pandas DataFrame.

        Returns:
            DataFrame with Q and intensity columns
        """
        return pd.DataFrame({"Q": self.q_values, "intensity": self.intensities})

    @classmethod
    def from_dataframe(
        cls,
        df: pd.DataFrame,
        filename: str | None = None,
        sample_name: str | None = None,
        **kwargs,
    ) -> "DiffractionData":
        """
        Create DiffractionData from pandas DataFrame.

        Args:
            df: DataFrame with Q and intensity columns
            filename: Source filename
            sample_name: Sample identifier
            **kwargs: Additional metadata

        Returns:
            DiffractionData instance
        """
        if "Q" not in df.columns or "intensity" not in df.columns:
            raise ValueError("DataFrame must contain 'Q' and 'intensity' columns")

        return cls(
            q_values=df["Q"].values,
            intensities=df["intensity"].values,
            filename=filename,
            sample_name=sample_name,
            **kwargs,
        )

    @classmethod
    def from_arrays(
        cls, q_values: np.ndarray, intensities: np.ndarray, **kwargs
    ) -> "DiffractionData":
        """
        Create DiffractionData from numpy arrays.

        Args:
            q_values: Q values in Å⁻¹
            intensities: Intensity values
            **kwargs: Additional metadata

        Returns:
            DiffractionData instance
        """
        return cls(q_values=q_values, intensities=intensities, **kwargs)

    def trim_q_range(
        self, q_min: float | None = None, q_max: float | None = None
    ) -> "DiffractionData":
        """
        Create a new DiffractionData instance trimmed to a specific Q range.

        Args:
            q_min: Minimum Q value (inclusive)
            q_max: Maximum Q value (inclusive)

        Returns:
            New DiffractionData instance with trimmed data
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
        """
        Interpolate data to new Q values.

        Args:
            new_q_values: Target Q values for interpolation

        Returns:
            New DiffractionData instance with interpolated data
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
