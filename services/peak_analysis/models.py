"""
Data models for the peak analysis service.

This module defines Pydantic models for request/response structures used in the
peak analysis REST API. Models follow RoboMage patterns for validation and
JSON schema generation.
"""

from enum import Enum

import numpy as np
from pydantic import BaseModel, Field, ConfigDict, validator


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
        None, 
        ge=0.0,
        description="Minimum peak height relative to maximum intensity"
    )
    min_prominence: float | None = Field(
        0.01,
        ge=0.0, 
        le=1.0,
        description="Minimum peak prominence (0-1 relative to data range)"
    )
    min_distance: float | None = Field(
        0.1,
        ge=0.0,
        description="Minimum distance between peaks in Q-space units"
    )
    max_width: float | None = Field(
        None,
        ge=0.0,
        description="Maximum peak width in Q-space units"
    )
    min_width: float | None = Field(
        None,
        ge=0.0,
        description="Minimum peak width in Q-space units"
    )


class FittingConfig(BaseModel):
    """Configuration for peak fitting parameters."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    profile_type: ProfileType = Field(
        ProfileType.GAUSSIAN,
        description="Peak profile function for fitting"
    )
    background_type: BackgroundType = Field(
        BackgroundType.LINEAR,
        description="Background model type"
    )
    background_order: int = Field(
        1,
        ge=0,
        le=10,
        description="Polynomial order for background (if applicable)"
    )
    max_iterations: int = Field(
        1000,
        ge=1,
        le=10000,
        description="Maximum optimization iterations"
    )
    tolerance: float = Field(
        1e-6,
        gt=0.0,
        description="Convergence tolerance for fitting"
    )


class AnalysisConfig(BaseModel):
    """Complete configuration for peak analysis."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    detection: PeakDetectionConfig = Field(
        default_factory=PeakDetectionConfig,
        description="Peak detection parameters"
    )
    fitting: FittingConfig = Field(
        default_factory=FittingConfig,
        description="Peak fitting parameters"
    )
    compute_uncertainties: bool = Field(
        True,
        description="Whether to compute parameter uncertainties"
    )
    quality_threshold: float = Field(
        0.95,
        ge=0.0,
        le=1.0,
        description="Minimum R² threshold for acceptable fits"
    )


class DiffractionDataInput(BaseModel):
    """Input diffraction data for analysis."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    q_values: list[float] = Field(
        description="Q-space values (Å⁻¹)"
    )
    intensities: list[float] = Field(
        description="Diffraction intensities"
    )
    filename: str | None = Field(
        None,
        description="Original filename"
    )
    sample_name: str | None = Field(
        None,
        description="Sample identifier"
    )
    
    @validator('q_values', 'intensities')
    def validate_arrays(cls, v):
        """Ensure arrays are not empty and contain valid numbers."""
        if len(v) == 0:
            raise ValueError("Arrays cannot be empty")
        if any(
            not isinstance(x, (int, float)) or np.isnan(x) or np.isinf(x) 
            for x in v
        ):
            raise ValueError("Arrays must contain valid finite numbers")
        return v
    
    @validator('intensities')
    def validate_same_length(cls, v, values):
        """Ensure q_values and intensities have same length."""
        if 'q_values' in values and len(v) != len(values['q_values']):
            raise ValueError("q_values and intensities must have same length")
        return v


class PeakAnalysisRequest(BaseModel):
    """Complete request for peak analysis."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    data: DiffractionDataInput = Field(
        description="Diffraction data to analyze"
    )
    config: AnalysisConfig = Field(
        default_factory=AnalysisConfig,
        description="Analysis configuration"
    )
    request_id: str | None = Field(
        None,
        description="Optional request identifier for tracking"
    )


class PeakInfo(BaseModel):
    """Information about a detected/fitted peak."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    peak_id: int = Field(description="Unique peak identifier")
    position: float = Field(description="Peak position in Q-space (Å⁻¹)")
    position_uncertainty: float | None = Field(None, description="Position uncertainty")
    height: float = Field(description="Peak height (intensity units)")
    height_uncertainty: float | None = Field(None, description="Height uncertainty")
    width: float = Field(description="Peak width (FWHM in Å⁻¹)")
    width_uncertainty: float | None = Field(None, description="Width uncertainty")
    area: float = Field(description="Integrated peak area")
    area_uncertainty: float | None = Field(None, description="Area uncertainty")
    d_spacing: float = Field(description="d-spacing (Å)")
    profile_type: ProfileType = Field(description="Profile function used")
    r_squared: float = Field(
        ge=0.0, 
        le=1.0, 
        description="Goodness of fit (R²)"
    )


class BackgroundInfo(BaseModel):
    """Information about background subtraction."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    background_type: BackgroundType = Field(description="Background model used")
    parameters: list[float] = Field(description="Background model parameters")
    r_squared: float = Field(
        ge=0.0, 
        le=1.0, 
        description="Background fit quality"
    )
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
    overall_r_squared: float = Field(
        ge=0.0, 
        le=1.0, 
        description="Overall fit quality"
    )
    processing_time_ms: float = Field(
        ge=0.0, description="Analysis time in milliseconds"
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Analysis warnings"
    )
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
        None, 
        description="Background-subtracted data (if requested)"
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