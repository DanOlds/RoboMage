"""Pydantic data models for GSAS-II refinement service

Request and response models for the REST API endpoints.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List


# ============================================================================
# Request Models
# ============================================================================


class DiffractionDataModel(BaseModel):
    """Diffraction pattern data for refinement"""

    q: List[float] = Field(..., description="Q values (Å⁻¹)", min_length=10)
    intensity: List[float] = Field(..., description="Intensity values", min_length=10)
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Optional metadata"
    )

    @field_validator("q", "intensity")
    @classmethod
    def validate_arrays(cls, v: List[float]) -> List[float]:
        """Validate that arrays are not empty and have reasonable values"""
        if len(v) < 10:
            raise ValueError("Arrays must contain at least 10 points")
        return v

    @field_validator("intensity")
    @classmethod
    def validate_intensity_positive(cls, v: List[float]) -> List[float]:
        """Check for negative intensities (warnings only)"""
        if any(i < 0 for i in v):
            # Note: GSAS-II can handle negative intensities (background subtracted)
            # but it's worth noting
            pass
        return v


class RefinementDict(BaseModel):
    """GSAS-II refinement dictionary (set/do structure)

    Follows GSAS-II's refinement dictionary format:
    {
      "set": {
        "Limits": {"low": 1, "high": 15},
        "Background": {"type": "chebyschev-1", "no. coeffs": 30, "refine": true},
        "Cell": true,
        "Sample Parameters": ["Scale"]
      }
    }
    """

    set: Dict[str, Any] = Field(
        ..., description="Refinement parameters (GSAS-II format)"
    )

    class Config:
        extra = "allow"  # Allow additional keys for GSAS-II flexibility


class Recipe(BaseModel):
    """Refinement recipe configuration

    Defines the complete refinement setup including structure, instrument,
    and refinement parameters.
    """

    instrument_file: str = Field(
        ...,
        description="Instrument parameter file (path, filename, or base64-encoded)",
    )
    cif_file: str = Field(
        ..., description="CIF structure file (path, filename, or base64-encoded)"
    )
    phase_name: str = Field(..., description="Phase name in CIF file")
    refinement_dict: RefinementDict = Field(..., description="GSAS-II refinement dict")
    recipe_description: Optional[str] = Field(
        None, description="Human-readable description"
    )


class RefinementOptions(BaseModel):
    """Optional refinement settings"""

    save_gpx: bool = Field(False, description="Save GSAS-II project file (.gpx)")
    generate_plot: bool = Field(True, description="Generate fit comparison plot")
    working_dir: Optional[str] = Field(None, description="Custom working directory")


class RefinementRequest(BaseModel):
    """Complete refinement request

    Everything needed to execute a GSAS-II Rietveld refinement.
    """

    diffraction_data: DiffractionDataModel = Field(..., description="Diffraction data")
    recipe: Recipe = Field(..., description="Refinement recipe")
    sample_name: str = Field(..., description="Sample identifier", min_length=1)
    cycles: int = Field(
        5,
        ge=0,
        le=20,
        description="Number of refinement cycles (0 = calculate only)",
    )
    options: RefinementOptions = Field(
        default_factory=RefinementOptions, description="Optional settings"
    )


# ============================================================================
# Response Models
# ============================================================================


class CellParameter(BaseModel):
    """Unit cell parameter with estimated standard deviation"""

    value: float = Field(..., description="Parameter value")
    esd: float = Field(..., description="Estimated standard deviation")


class CellParameters(BaseModel):
    """Refined unit cell parameters

    All lengths in Ångstroms, angles in degrees.
    """

    a: CellParameter = Field(..., description="a lattice parameter (Å)")
    b: CellParameter = Field(..., description="b lattice parameter (Å)")
    c: CellParameter = Field(..., description="c lattice parameter (Å)")
    alpha: CellParameter = Field(..., description="α angle (degrees)")
    beta: CellParameter = Field(..., description="β angle (degrees)")
    gamma: CellParameter = Field(..., description="γ angle (degrees)")
    volume: CellParameter = Field(..., description="Unit cell volume (ų)")


class FitQuality(BaseModel):
    """Refinement fit quality metrics"""

    Rwp: float = Field(..., description="Weighted R-factor (%)")
    chi2: Optional[float] = Field(None, description="Chi-squared value")
    GoF: Optional[float] = Field(None, description="Goodness of fit")


class FitProfile(BaseModel):
    """Complete fit profile data arrays

    All arrays are same length, corresponding point-by-point.
    """

    two_theta: List[float] = Field(..., description="2θ values (degrees)")
    q_values: List[float] = Field(..., description="Q values (Å⁻¹)")
    d_spacings: List[float] = Field(..., description="d-spacing values (Å)")
    y_obs: List[float] = Field(..., description="Observed intensities")
    y_calc: List[float] = Field(..., description="Calculated intensities")
    y_diff: List[float] = Field(..., description="Difference (obs - calc)")
    y_bkg: List[float] = Field(..., description="Background intensities")
    y_weights: List[float] = Field(..., description="Data point weights")


class RefinementResult(BaseModel):
    """Complete refinement result

    Structured output from GSAS-II refinement including refined parameters,
    fit quality, and full fit profile.
    """

    success: bool = Field(..., description="Whether refinement succeeded")
    parameters: Dict[str, Any] = Field(
        ..., description="All refined parameters (flexible)"
    )
    cell: CellParameters = Field(..., description="Refined unit cell parameters")
    fit_quality: FitQuality = Field(..., description="Fit quality metrics")
    fit_profile: FitProfile = Field(..., description="Complete fit profile data")
    plot_image: Optional[str] = Field(
        None, description="Base64-encoded PNG plot (if generate_plot=True)"
    )
    gpx_path: Optional[str] = Field(
        None, description="Path to .gpx file (if save_gpx=True)"
    )
    warnings: List[str] = Field(
        default_factory=list, description="Warnings from refinement"
    )
    execution_time_s: float = Field(..., description="Total execution time (seconds)")


# ============================================================================
# Utility Response Models
# ============================================================================


class HealthResponse(BaseModel):
    """Health check response"""

    status: str = Field(..., description="Service status (healthy/degraded)")
    gsasii_available: bool = Field(..., description="Is GSAS-II importable?")
    version: str = Field(..., description="Service version")


class RecipeTemplate(BaseModel):
    """Recipe template metadata"""

    name: str = Field(..., description="Recipe template name")
    description: str = Field(..., description="What this recipe does")
    template: Dict[str, Any] = Field(..., description="Recipe template structure")


class RecipeListResponse(BaseModel):
    """List of available recipe templates"""

    recipes: List[RecipeTemplate] = Field(..., description="Available recipe templates")


class RecipeValidationResponse(BaseModel):
    """Recipe validation result"""

    valid: bool = Field(..., description="Is the recipe valid?")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
