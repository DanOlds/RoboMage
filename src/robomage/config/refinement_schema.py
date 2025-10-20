"""Configuration schemas for powder diffraction refinement (under development).

This module defines Pydantic models for configuring powder diffraction
refinement workflows. The schemas provide validation and type safety for
refinement parameters, instrument settings, and analysis constraints.

Development Status:
    ⚠️  This module is currently a placeholder and under active development.
    The schemas defined here represent the planned configuration structure
    but may not yet be fully integrated with refinement engines.

Planned Features:
    - Integration with GSAS-II, Topas, and other refinement engines
    - Automated parameter optimization workflows
    - Validation of refinement convergence criteria
    - Export to engine-specific configuration formats

Current Schema Components:
    - InstrumentConfig: X-ray/neutron instrument parameters
    - PhaseConfig: Crystal structure refinement settings
    - BackgroundModel: Background function configuration
    - RefinementConfig: Complete refinement job specification

Usage (when implemented):
    >>> from robomage.config.refinement_schema import RefinementConfig
    >>> config = RefinementConfig(
    ...     instrument=InstrumentConfig(beamline="XPD", wavelength=0.5),
    ...     phases=[PhaseConfig(name="LaB6", cif_path="lab6.cif")],
    ...     q_range=[1.0, 10.0],
    ... )
    >>> # Future: config.export_to_gsas2()

Note:
    This is architectural groundwork for future refinement automation.
    Current RoboMage functionality focuses on data loading and visualization.
    Refinement integration planned for future releases.
"""

from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator


class InstrumentConfig(BaseModel):
    """X-ray/neutron instrument configuration parameters.

    Defines instrumental parameters needed for accurate powder diffraction
    refinement. These settings affect peak shapes, background modeling,
    and data correction procedures.

    Note:
        Currently a placeholder schema. Integration with refinement engines
        is planned for future releases.
    """

    beamline: str = Field(..., description="e.g., 'XPD', 'PDF'")
    wavelength: float = Field(..., gt=0, description="Å")
    zero_shift: float = Field(0.0, description="degrees")


class PhaseConfig(BaseModel):
    """Crystal phase refinement configuration.

    Specifies which crystalline phases to include in the refinement and
    which parameters to refine for each phase (lattice parameters,
    atomic positions, thermal parameters, etc.).

    Note:
        Currently a placeholder schema. CIF file integration and parameter
        selection logic will be implemented in future releases.
    """

    name: str
    cif_path: str
    refine_cell: bool = True
    refine_profile: bool = False


class BackgroundModel(BaseModel):
    """Background function configuration for refinement.

    Defines the mathematical model used to fit the background contribution
    to the diffraction pattern. Proper background modeling is crucial for
    accurate structure refinement.

    Note:
        Currently supports basic Chebyshev polynomial configuration.
        Additional background models planned for future releases.
    """

    model: str = Field(default="chebyshev")
    order: int = Field(default=6, ge=1, le=12)


class RefinementConfig(BaseModel):
    """Complete configuration for powder diffraction refinement workflow.

    Combines all refinement parameters into a single validated configuration
    object. This serves as the main interface for configuring automated
    refinement jobs.

    Planned Integration:
        - Export to GSAS-II project files
        - Topas input file generation
        - Automated refinement execution
        - Result validation and reporting

    Note:
        Currently a placeholder schema for future refinement automation.
        The validation logic is implemented but refinement engine integration
        is planned for future releases.
    """

    schema_version: str = "1.0"
    instrument: InstrumentConfig
    phases: list[PhaseConfig]
    background: BackgroundModel = Field(default_factory=lambda: BackgroundModel())
    q_range: list[float] = Field(..., min_length=2, max_length=2)  # <- updated
    constraints: list[str] | None = None
    engine: str = Field("gsas2")
    max_iterations: int = Field(50, ge=1, le=500)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )  # <- updated

    @field_validator("q_range")
    @classmethod
    def _validate_qrange(cls, v: list[float]):
        if v[1] <= v[0]:
            raise ValueError("q_range must be [Qmin, Qmax] with Qmax > Qmin")
        return v
