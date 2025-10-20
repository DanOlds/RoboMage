"""Configuration management module for RoboMage (under development).

This module provides configuration schemas and validation for RoboMage's
planned refinement automation capabilities. The configuration system is
designed to support multiple powder diffraction refinement engines with
standardized parameter validation.

Development Status:
    ⚠️  This module is currently under development and contains placeholder
    schemas for future refinement automation features. The configuration
    structures are implemented but not yet integrated with refinement engines.

Planned Architecture:
    The configuration module will eventually provide:

    1. **Refinement Configuration**: Complete job specification including
       instrument parameters, phase information, and refinement constraints

    2. **Engine Integration**: Export configurations to GSAS-II, Topas,
       and other refinement software formats

    3. **Validation Framework**: Comprehensive parameter validation using
       Pydantic models with scientific domain knowledge

    4. **Template System**: Predefined configurations for common workflows
       and instrument setups

Current Components:
    - RefinementConfig: Main configuration container (placeholder)
    - InstrumentConfig: X-ray/neutron instrument parameters
    - PhaseConfig: Crystal phase refinement settings
    - BackgroundModel: Background function configuration

Future Usage (when implemented):
    >>> from robomage.config import RefinementConfig, InstrumentConfig
    >>> # Create instrument configuration
    >>> instrument = InstrumentConfig(beamline="XPD", wavelength=0.5)
    >>> # Define refinement job
    >>> config = RefinementConfig(
    ...     instrument=instrument,
    ...     phases=[PhaseConfig(name="LaB6", cif_path="lab6.cif")],
    ...     q_range=[1.0, 10.0],
    ... )
    >>> # Future: Export to refinement engine
    >>> # config.export_to_gsas2("refinement.gpx")
    >>> # config.export_to_topas("refinement.inp")

Integration Points:
    When implemented, this module will integrate with:
    - Data loading pipeline (robomage.data)
    - Visualization tools (robomage.visualization)
    - Command-line interface (robomage.__main__)
    - External refinement engines (GSAS-II, Topas, etc.)

Note:
    Current RoboMage functionality focuses on data loading, validation,
    and visualization. Refinement automation is planned for future releases.
    This module provides the architectural foundation for that functionality.

See Also:
    - refinement_schema.py: Detailed schema definitions
    - ../data/: Data structures and loading utilities
    - Future: Engine-specific export modules
"""

# Import refinement configuration schemas
# Note: These are currently placeholder schemas for future functionality
from .refinement_schema import (
    BackgroundModel,
    InstrumentConfig,
    PhaseConfig,
    RefinementConfig,
)

# Public API - planned interface for configuration management
__all__ = [
    # Main configuration containers (future functionality)
    "RefinementConfig",  # Complete refinement job specification
    # Component configuration classes
    "InstrumentConfig",  # X-ray/neutron instrument parameters
    "PhaseConfig",  # Crystal phase refinement settings
    "BackgroundModel",  # Background function configuration
]
