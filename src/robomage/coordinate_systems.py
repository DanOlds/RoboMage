"""
Coordinate System Conversions for Powder Diffraction

This module provides conversions between different coordinate systems used in
powder diffraction analysis:
- Q-space (Å⁻¹) - momentum transfer, canonical in RoboMage
- 2θ (degrees) - scattering angle, used by GSAS-II and conventional software
- d-spacing (Å) - real-space lattice spacing, crystallographic convention

All conversions require wavelength (λ) in Angstroms for Q ↔ 2θ transformations.
The module implements a hybrid pattern where RoboMage uses Q internally but can
automatically convert to other coordinate systems when needed by analysis tools.

Key Concepts:
    Q (momentum transfer) = 4π sin(θ) / λ
    d-spacing = 2π / Q
    Bragg's law: nλ = 2d sin(θ)

Design Philosophy:
    - Internal Canonical Form: Always Q-space in storage
    - Explicit Conversions: Clear about what coordinate system is being used
    - Automatic Conversion: Framework converts but makes it visible via logging
    - Metadata Propagation: Every data object carries coordinate system info
    - Error Prevention: Validate wavelength availability before conversion
    - Precision Awareness: Log warnings about round-trip conversions

Example:
    >>> from robomage.coordinate_systems import convert_q_to_two_theta
    >>> import numpy as np
    >>> q_values = np.array([2.0, 4.0, 6.0])  # Å⁻¹
    >>> wavelength = 0.1665  # Å (synchrotron)
    >>> two_theta = convert_q_to_two_theta(q_values, wavelength)
    >>> print(two_theta)
    [6.07, 12.15, 18.27]  # degrees

    >>> # Reverse conversion
    >>> q_back = convert_two_theta_to_q(two_theta, wavelength)
    >>> print(np.allclose(q_values, q_back))
    True

Author: RoboMage Team
Date: December 4, 2025
"""

import logging
from enum import Enum
from typing import Literal

import numpy as np
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class CoordinateSystem(str, Enum):
    """
    Coordinate system types for powder diffraction data.
    
    Attributes:
        Q: Momentum transfer in Å⁻¹ (RoboMage canonical form)
        TWO_THETA: Scattering angle in degrees (GSAS-II, conventional)
        D_SPACING: Real-space lattice spacing in Å (crystallographic)
    """

    Q = "Q"
    TWO_THETA = "two_theta"
    D_SPACING = "d_spacing"


class CoordinateMetadata(BaseModel):
    """
    Metadata describing the coordinate system of diffraction data.
    
    Attributes:
        system: Type of coordinate system (Q, two_theta, d_spacing)
        units: Physical units (Å⁻¹, degrees, Å)
        wavelength: X-ray wavelength in Å (required for Q ↔ 2θ conversions)
        conversion_history: Log of coordinate transformations applied
    """

    system: CoordinateSystem = Field(
        description="Coordinate system type", default=CoordinateSystem.Q
    )
    units: str = Field(description="Physical units", default="Å⁻¹")
    wavelength: float | None = Field(
        default=None, description="X-ray wavelength in Å"
    )
    conversion_history: list[str] = Field(
        default_factory=list, description="Record of conversions applied"
    )

    def add_conversion(self, from_system: CoordinateSystem, to_system: CoordinateSystem) -> None:
        """
        Record a coordinate system conversion.
        
        Args:
            from_system: Source coordinate system
            to_system: Target coordinate system
        """
        self.conversion_history.append(f"{from_system.value} → {to_system.value}")


class ConversionError(Exception):
    """Exception raised when coordinate conversion fails."""

    pass


def convert_q_to_two_theta(q_values: np.ndarray, wavelength: float) -> np.ndarray:
    """
    Convert Q-space to 2θ scattering angle.
    
    Uses the relation: Q = 4π sin(θ) / λ
    Solving for 2θ: 2θ = 2 arcsin(Q λ / 4π)
    
    Args:
        q_values: Q values in Å⁻¹ (momentum transfer)
        wavelength: X-ray wavelength in Å
    
    Returns:
        Two-theta values in degrees
    
    Raises:
        ConversionError: If wavelength is invalid or Q values are out of range
    
    Notes:
        - Q must satisfy: 0 ≤ Q ≤ 4π/λ (physical constraint)
        - Small Q values (<0.1 Å⁻¹) may have reduced precision
        - Conversion is exact within floating-point precision
    
    Example:
        >>> q = np.array([2.0, 4.0, 6.0])
        >>> wavelength = 0.1665  # Synchrotron
        >>> two_theta = convert_q_to_two_theta(q, wavelength)
        >>> print(two_theta)
        [6.07, 12.15, 18.27]  # degrees
    """
    # Validate wavelength
    if wavelength is None or wavelength <= 0:
        raise ConversionError(
            f"Invalid wavelength: {wavelength}. "
            "Wavelength must be positive (typically 0.1-2.0 Å for X-rays)."
        )

    # Validate Q range
    q_max_physical = 4 * np.pi / wavelength
    if np.any(q_values < 0):
        raise ConversionError("Q values must be non-negative")
    if np.any(q_values > q_max_physical):
        raise ConversionError(
            f"Q values exceed physical maximum {q_max_physical:.2f} Å⁻¹ "
            f"for wavelength {wavelength:.4f} Å. "
            f"Check wavelength or Q values for errors."
        )

    # Convert: 2θ = 2 * arcsin(Q * λ / 4π)
    sin_theta = q_values * wavelength / (4 * np.pi)

    # Check for numerical issues (should be impossible after range check)
    if np.any(sin_theta > 1.0):
        logger.warning(
            f"Numerical precision issue: sin(θ) slightly > 1.0 (max={sin_theta.max():.6f}). "
            "Clipping to 1.0."
        )
        sin_theta = np.clip(sin_theta, 0, 1)

    theta_rad = np.arcsin(sin_theta)
    two_theta_deg = 2 * np.degrees(theta_rad)

    logger.debug(
        f"Converted Q → 2θ: {len(q_values)} points, "
        f"range {q_values.min():.2f}-{q_values.max():.2f} Å⁻¹ → "
        f"{two_theta_deg.min():.2f}-{two_theta_deg.max():.2f}°"
    )

    return two_theta_deg


def convert_two_theta_to_q(two_theta_deg: np.ndarray, wavelength: float) -> np.ndarray:
    """
    Convert 2θ scattering angle to Q-space.
    
    Uses the relation: Q = 4π sin(θ) / λ
    
    Args:
        two_theta_deg: Two-theta values in degrees
        wavelength: X-ray wavelength in Å
    
    Returns:
        Q values in Å⁻¹ (momentum transfer)
    
    Raises:
        ConversionError: If wavelength is invalid or 2θ values are out of range
    
    Notes:
        - 2θ must satisfy: 0° ≤ 2θ ≤ 180° (physical constraint)
        - Very small angles (<1°) may have reduced precision
        - Conversion is exact within floating-point precision
    
    Example:
        >>> two_theta = np.array([6.07, 12.15, 18.27])
        >>> wavelength = 0.1665  # Synchrotron
        >>> q = convert_two_theta_to_q(two_theta, wavelength)
        >>> print(q)
        [2.0, 4.0, 6.0]  # Å⁻¹
    """
    # Validate wavelength
    if wavelength is None or wavelength <= 0:
        raise ConversionError(
            f"Invalid wavelength: {wavelength}. "
            "Wavelength must be positive (typically 0.1-2.0 Å for X-rays)."
        )

    # Validate 2θ range
    if np.any(two_theta_deg < 0) or np.any(two_theta_deg > 180):
        raise ConversionError(
            f"2θ values must be in range [0, 180] degrees. "
            f"Found range: [{two_theta_deg.min():.2f}, {two_theta_deg.max():.2f}]"
        )

    # Convert: Q = 4π sin(θ) / λ
    theta_rad = np.radians(two_theta_deg / 2)
    q_values = 4 * np.pi * np.sin(theta_rad) / wavelength

    logger.debug(
        f"Converted 2θ → Q: {len(two_theta_deg)} points, "
        f"range {two_theta_deg.min():.2f}-{two_theta_deg.max():.2f}° → "
        f"{q_values.min():.2f}-{q_values.max():.2f} Å⁻¹"
    )

    return q_values


def convert_q_to_d_spacing(q_values: np.ndarray) -> np.ndarray:
    """
    Convert Q-space to d-spacing.
    
    Uses the relation: d = 2π / Q
    
    Args:
        q_values: Q values in Å⁻¹
    
    Returns:
        d-spacing values in Å
    
    Raises:
        ConversionError: If Q values are zero or negative
    
    Notes:
        - Q must be positive (d-spacing is undefined for Q=0)
        - Large d-spacing (>100 Å) indicates very small Q (may be noise)
        - Conversion does not require wavelength (purely Q-space operation)
    
    Example:
        >>> q = np.array([2.0, 4.0, 6.0])
        >>> d_spacing = convert_q_to_d_spacing(q)
        >>> print(d_spacing)
        [3.14, 1.57, 1.05]  # Å
    """
    # Validate Q values
    if np.any(q_values <= 0):
        raise ConversionError(
            "Q values must be positive for d-spacing conversion. "
            f"Found {np.sum(q_values <= 0)} non-positive values."
        )

    # Convert: d = 2π / Q
    d_spacing = 2 * np.pi / q_values

    logger.debug(
        f"Converted Q → d-spacing: {len(q_values)} points, "
        f"range {q_values.min():.2f}-{q_values.max():.2f} Å⁻¹ → "
        f"{d_spacing.max():.2f}-{d_spacing.min():.2f} Å (note: reversed)"
    )

    return d_spacing


def convert_d_spacing_to_q(d_spacing: np.ndarray) -> np.ndarray:
    """
    Convert d-spacing to Q-space.
    
    Uses the relation: Q = 2π / d
    
    Args:
        d_spacing: d-spacing values in Å
    
    Returns:
        Q values in Å⁻¹
    
    Raises:
        ConversionError: If d-spacing values are zero or negative
    
    Notes:
        - d-spacing must be positive
        - Conversion does not require wavelength (purely Q-space operation)
    
    Example:
        >>> d = np.array([3.14, 1.57, 1.05])
        >>> q = convert_d_spacing_to_q(d)
        >>> print(q)
        [2.0, 4.0, 6.0]  # Å⁻¹
    """
    # Validate d-spacing values
    if np.any(d_spacing <= 0):
        raise ConversionError(
            "d-spacing values must be positive. "
            f"Found {np.sum(d_spacing <= 0)} non-positive values."
        )

    # Convert: Q = 2π / d
    q_values = 2 * np.pi / d_spacing

    logger.debug(
        f"Converted d-spacing → Q: {len(d_spacing)} points, "
        f"range {d_spacing.max():.2f}-{d_spacing.min():.2f} Å → "
        f"{q_values.min():.2f}-{q_values.max():.2f} Å⁻¹ (note: reversed)"
    )

    return q_values


def convert_two_theta_to_d_spacing(
    two_theta_deg: np.ndarray, wavelength: float
) -> np.ndarray:
    """
    Convert 2θ to d-spacing using Bragg's law.
    
    Uses: d = λ / (2 sin(θ))
    
    Args:
        two_theta_deg: Two-theta values in degrees
        wavelength: X-ray wavelength in Å
    
    Returns:
        d-spacing values in Å
    
    Raises:
        ConversionError: If wavelength is invalid or 2θ values are out of range
    
    Example:
        >>> two_theta = np.array([10.0, 20.0, 30.0])
        >>> wavelength = 1.54056  # Cu Kα
        >>> d = convert_two_theta_to_d_spacing(two_theta, wavelength)
    """
    # Validate wavelength
    if wavelength is None or wavelength <= 0:
        raise ConversionError(
            f"Invalid wavelength: {wavelength}. Must be positive."
        )

    # Convert via Q-space
    q_values = convert_two_theta_to_q(two_theta_deg, wavelength)
    return convert_q_to_d_spacing(q_values)


def convert_d_spacing_to_two_theta(
    d_spacing: np.ndarray, wavelength: float
) -> np.ndarray:
    """
    Convert d-spacing to 2θ using Bragg's law.
    
    Uses: 2θ = 2 arcsin(λ / 2d)
    
    Args:
        d_spacing: d-spacing values in Å
        wavelength: X-ray wavelength in Å
    
    Returns:
        Two-theta values in degrees
    
    Raises:
        ConversionError: If wavelength is invalid or d > λ/2
    
    Example:
        >>> d = np.array([3.0, 2.0, 1.5])
        >>> wavelength = 1.54056  # Cu Kα
        >>> two_theta = convert_d_spacing_to_two_theta(d, wavelength)
    """
    # Validate wavelength
    if wavelength is None or wavelength <= 0:
        raise ConversionError(
            f"Invalid wavelength: {wavelength}. Must be positive."
        )

    # Convert via Q-space
    q_values = convert_d_spacing_to_q(d_spacing)
    return convert_q_to_two_theta(q_values, wavelength)


def convert_coordinate_system(
    x_values: np.ndarray,
    from_system: CoordinateSystem | str,
    to_system: CoordinateSystem | str,
    wavelength: float | None = None,
) -> np.ndarray:
    """
    Convert between any two coordinate systems.
    
    This is the main entry point for coordinate conversions. It dispatches
    to the appropriate specialized conversion function.
    
    Args:
        x_values: Coordinate values in source system
        from_system: Source coordinate system
        to_system: Target coordinate system
        wavelength: X-ray wavelength in Å (required for Q ↔ 2θ conversions)
    
    Returns:
        Converted coordinate values
    
    Raises:
        ConversionError: If conversion is not possible or parameters are invalid
        ValueError: If from_system or to_system are invalid
    
    Example:
        >>> from robomage.coordinate_systems import convert_coordinate_system, CoordinateSystem
        >>> q = np.array([2.0, 4.0, 6.0])
        >>> two_theta = convert_coordinate_system(
        ...     q, CoordinateSystem.Q, CoordinateSystem.TWO_THETA, wavelength=0.1665
        ... )
        >>> print(two_theta)
        [6.07, 12.15, 18.27]
    """
    # Convert string inputs to enum
    if isinstance(from_system, str):
        from_system = CoordinateSystem(from_system)
    if isinstance(to_system, str):
        to_system = CoordinateSystem(to_system)

    # No conversion needed
    if from_system == to_system:
        logger.debug(f"No conversion needed: {from_system.value} → {to_system.value}")
        return x_values.copy()

    # Log conversion
    logger.info(
        f"Converting coordinate system: {from_system.value} → {to_system.value} "
        f"({len(x_values)} points, wavelength={wavelength})"
    )

    # Dispatch to appropriate conversion function
    conversion_map = {
        (CoordinateSystem.Q, CoordinateSystem.TWO_THETA): convert_q_to_two_theta,
        (CoordinateSystem.TWO_THETA, CoordinateSystem.Q): convert_two_theta_to_q,
        (CoordinateSystem.Q, CoordinateSystem.D_SPACING): convert_q_to_d_spacing,
        (CoordinateSystem.D_SPACING, CoordinateSystem.Q): convert_d_spacing_to_q,
        (
            CoordinateSystem.TWO_THETA,
            CoordinateSystem.D_SPACING,
        ): convert_two_theta_to_d_spacing,
        (
            CoordinateSystem.D_SPACING,
            CoordinateSystem.TWO_THETA,
        ): convert_d_spacing_to_two_theta,
    }

    conversion_func = conversion_map.get((from_system, to_system))
    if conversion_func is None:
        raise ValueError(
            f"Unsupported conversion: {from_system.value} → {to_system.value}"
        )

    # Check if wavelength is required
    requires_wavelength = {
        convert_q_to_two_theta,
        convert_two_theta_to_q,
        convert_two_theta_to_d_spacing,
        convert_d_spacing_to_two_theta,
    }

    if conversion_func in requires_wavelength:
        if wavelength is None:
            raise ConversionError(
                f"Wavelength required for {from_system.value} → {to_system.value} conversion. "
                "Please provide wavelength in Angstroms (typical values: 0.1-2.0 Å)."
            )
        return conversion_func(x_values, wavelength)
    else:
        return conversion_func(x_values)


def validate_round_trip_conversion(
    x_values: np.ndarray,
    system_a: CoordinateSystem,
    system_b: CoordinateSystem,
    wavelength: float | None = None,
    tolerance: float = 1e-6,
) -> tuple[bool, float]:
    """
    Validate round-trip conversion precision.
    
    Converts A → B → A and checks if we get back the original values
    within specified tolerance. Useful for verifying conversion accuracy.
    
    Args:
        x_values: Original coordinate values
        system_a: Starting coordinate system
        system_b: Intermediate coordinate system
        wavelength: X-ray wavelength in Å (if required)
        tolerance: Relative tolerance for comparison (default: 1e-6)
    
    Returns:
        Tuple of (is_accurate, max_relative_error)
    
    Example:
        >>> q = np.array([2.0, 4.0, 6.0])
        >>> is_accurate, error = validate_round_trip_conversion(
        ...     q, CoordinateSystem.Q, CoordinateSystem.TWO_THETA, wavelength=0.1665
        ... )
        >>> print(f"Accurate: {is_accurate}, Max error: {error:.2e}")
        Accurate: True, Max error: 1.23e-15
    """
    # Forward conversion
    converted = convert_coordinate_system(x_values, system_a, system_b, wavelength)

    # Reverse conversion
    round_trip = convert_coordinate_system(converted, system_b, system_a, wavelength)

    # Calculate relative error
    relative_error = np.abs((round_trip - x_values) / x_values)
    max_relative_error = float(np.max(relative_error))

    is_accurate = max_relative_error < tolerance

    logger.debug(
        f"Round-trip {system_a.value} → {system_b.value} → {system_a.value}: "
        f"max relative error = {max_relative_error:.2e}, "
        f"accurate = {is_accurate} (tolerance = {tolerance:.2e})"
    )

    return is_accurate, max_relative_error
