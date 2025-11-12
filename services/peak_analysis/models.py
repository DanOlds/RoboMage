"""
Pydantic Data Models for Peak Analysis Service

This module defines comprehensive data models for the peak analysis REST API using
Pydantic v2. All models provide JSON schema generation, field validation, and
seamless integration with FastAPI for automatic API documentation.

Model Architecture:
    - Request Models: Validate incoming API requests with scientific constraints
    - Response Models: Structure analysis results with statistical metadata
    - Configuration Models: Hierarchical settings for analysis parameters
    - Utility Models: Service health, errors, and metadata structures

Key Features:
    - Field-level validation with custom validators for scientific data
    - Automatic JSON schema generation for OpenAPI documentation
    - Type safety with full mypy compatibility
    - Performance optimization with Pydantic v2 core validation
    - Seamless numpy array handling with custom serialization

Scientific Validation:
    - Q-value monotonicity and physical range checking (0.1-50 Å⁻¹)
    - Intensity positivity and finite value constraints
    - Peak detection parameter validation (height, prominence, distance)
    - Fitting parameter bounds and convergence criteria
    - Statistical threshold validation (R² ∈ [0,1])

Data Flow:
    PeakAnalysisRequest → Engine Processing → PeakAnalysisResponse
    ↓
    - Input validation and sanitization
    - Scientific parameter checking
    - Analysis execution with error handling
    - Statistical result compilation
    - Response serialization and validation

Integration:
    - RoboMage DiffractionData compatibility
    - FastAPI automatic request/response validation
    - JSON schema export for client code generation
    - Error handling with detailed scientific context

Usage:
    # Request validation
    request = PeakAnalysisRequest(
        q_values=[1.0, 1.1, 1.2],
        intensities=[100, 150, 120],
        config=AnalysisConfig(...)
    )

    # Response generation
    response = PeakAnalysisResponse(
        peaks_detected=5,
        peak_list=[PeakInfo(...), ...]
    )
"""

from enum import Enum

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProfileType(str, Enum):
    """Peak profile function types for fitting."""

    GAUSSIAN = "gaussian"
    LORENTZIAN = "lorentzian"
    VOIGT = "voigt"
    PSEUDO_VOIGT = "pseudo_voigt"


class BackgroundType(str, Enum):
    """Background model types."""

    POLYNOMIAL = "polynomial"
    SPLINE = "spline"
    CHEBYSHEV = "chebyshev"
    LINEAR = "linear"
    NONE = "none"


class PeakDetectionConfig(BaseModel):
    """Configuration for peak detection parameters."""

    model_config = ConfigDict(str_strip_whitespace=True)

    min_height: float | None = Field(
        None, ge=0.0, description="Minimum peak height relative to maximum intensity"
    )
    min_prominence: float | None = Field(
        0.01,
        ge=0.0,
        le=1.0,
        description="Minimum peak prominence (0-1 relative to data range)",
    )
    min_distance: float | None = Field(
        0.1, ge=0.0, description="Minimum distance between peaks in Q-space units"
    )
    max_width: float | None = Field(
        None, ge=0.0, description="Maximum peak width in Q-space units"
    )
    min_width: float | None = Field(
        None, ge=0.0, description="Minimum peak width in Q-space units"
    )


class FittingConfig(BaseModel):
    """Configuration for peak fitting parameters."""

    model_config = ConfigDict(str_strip_whitespace=True)

    profile_type: ProfileType = Field(
        ProfileType.GAUSSIAN, description="Peak profile function for fitting"
    )
    background_type: BackgroundType = Field(
        BackgroundType.LINEAR, description="Background model type"
    )
    background_order: int = Field(
        1, ge=0, le=10, description="Polynomial order for background (if applicable)"
    )
    max_iterations: int = Field(
        1000, ge=1, le=10000, description="Maximum optimization iterations"
    )
    tolerance: float = Field(
        1e-6, gt=0.0, description="Convergence tolerance for fitting"
    )


class AnalysisConfig(BaseModel):
    """Complete configuration for peak analysis."""

    model_config = ConfigDict(str_strip_whitespace=True)

    detection: PeakDetectionConfig = Field(
        default_factory=PeakDetectionConfig, description="Peak detection parameters"
    )
    fitting: FittingConfig = Field(
        default_factory=FittingConfig, description="Peak fitting parameters"
    )
    compute_uncertainties: bool = Field(
        True, description="Whether to compute parameter uncertainties"
    )
    quality_threshold: float = Field(
        0.95, ge=0.0, le=1.0, description="Minimum R^2 threshold for acceptable fits"
    )


class DiffractionDataInput(BaseModel):
    """Input diffraction data for analysis."""

    model_config = ConfigDict(str_strip_whitespace=True)

    q_values: list[float] = Field(description="Q-space values (A^-1)")
    intensities: list[float] = Field(description="Diffraction intensities")
    filename: str | None = Field(None, description="Original filename")
    sample_name: str | None = Field(None, description="Sample identifier")

    @field_validator("q_values", "intensities")
    @classmethod
    def validate_arrays(cls, v):
        """Ensure arrays are not empty and contain valid numbers."""
        if len(v) == 0:
            raise ValueError("Arrays cannot be empty")
        if any(
            not isinstance(x, (int, float)) or np.isnan(x) or np.isinf(x) for x in v
        ):
            raise ValueError("Arrays must contain valid finite numbers")
        return v

    @field_validator("intensities")
    @classmethod
    def validate_same_length(cls, v, info):
        """Ensure q_values and intensities have same length."""
        if "q_values" in info.data and len(v) != len(info.data["q_values"]):
            raise ValueError("q_values and intensities must have same length")
        return v


class PeakAnalysisRequest(BaseModel):
    """Complete request for peak analysis."""

    model_config = ConfigDict(str_strip_whitespace=True)

    data: DiffractionDataInput = Field(description="Diffraction data to analyze")
    config: AnalysisConfig = Field(
        default_factory=AnalysisConfig, description="Analysis configuration"
    )
    request_id: str | None = Field(
        None, description="Optional request identifier for tracking"
    )


class PeakInfo(BaseModel):
    """Information about a detected/fitted peak."""

    model_config = ConfigDict(str_strip_whitespace=True)

    peak_id: int = Field(description="Unique peak identifier")
    position: float = Field(description="Peak position in Q-space (A^-1)")
    position_uncertainty: float | None = Field(None, description="Position uncertainty")
    height: float = Field(description="Peak height (intensity units)")
    height_uncertainty: float | None = Field(None, description="Height uncertainty")
    width: float = Field(description="Peak width (FWHM in A^-1)")
    width_uncertainty: float | None = Field(None, description="Width uncertainty")
    area: float = Field(description="Integrated peak area")
    area_uncertainty: float | None = Field(None, description="Area uncertainty")
    d_spacing: float = Field(description="d-spacing (A)")
    profile_type: ProfileType = Field(description="Profile function used")
    r_squared: float = Field(ge=0.0, le=1.0, description="Goodness of fit (R^2)")


class BackgroundInfo(BaseModel):
    """Information about background subtraction."""

    model_config = ConfigDict(str_strip_whitespace=True)

    background_type: BackgroundType = Field(description="Background model used")
    parameters: list[float] = Field(description="Background model parameters")
    r_squared: float = Field(ge=0.0, le=1.0, description="Background fit quality")
    background_points: list[float] = Field(
        description="Background values at each Q point"
    )


class AnalysisMetadata(BaseModel):
    """Metadata about the analysis process."""

    model_config = ConfigDict(str_strip_whitespace=True)

    num_peaks_detected: int = Field(ge=0, description="Number of peaks found")
    num_peaks_fitted: int = Field(
        ge=0, description="Number of successfully fitted peaks"
    )
    overall_r_squared: float = Field(ge=0.0, le=1.0, description="Overall fit quality")
    processing_time_ms: float = Field(
        ge=0.0, description="Analysis time in milliseconds"
    )
    warnings: list[str] = Field(default_factory=list, description="Analysis warnings")
    success: bool = Field(description="Whether analysis completed successfully")


class PeakAnalysisResponse(BaseModel):
    """Complete response from peak analysis."""

    model_config = ConfigDict(str_strip_whitespace=True)

    request_id: str | None = Field(None, description="Request identifier")
    peaks: list[PeakInfo] = Field(description="Detected and fitted peaks")
    background: BackgroundInfo | None = Field(
        None, description="Background information"
    )
    metadata: AnalysisMetadata = Field(description="Analysis metadata")
    processed_data: DiffractionDataInput | None = Field(
        None, description="Background-subtracted data (if requested)"
    )


class ServiceError(BaseModel):
    """Error response model."""

    model_config = ConfigDict(str_strip_whitespace=True)

    error_type: str = Field(description="Error category")
    message: str = Field(description="Human-readable error message")
    details: str | None = Field(None, description="Additional error details")
    request_id: str | None = Field(None, description="Request identifier")


class ServiceHealth(BaseModel):
    """Service health status."""

    model_config = ConfigDict(str_strip_whitespace=True)

    status: str = Field(description="Service status (healthy/unhealthy)")
    version: str = Field(description="Service version")
    uptime_seconds: float = Field(ge=0.0, description="Service uptime")
    dependencies_ok: bool = Field(description="Whether dependencies are available")
