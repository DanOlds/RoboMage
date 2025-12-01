"""
Chebyshev Polynomial Background Subtraction Node

Fits and subtracts diffraction backgrounds using Chebyshev polynomials
of the first kind with a user-definable number of terms.

Chebyshev polynomials are particularly well-suited for background fitting
because they:
- Minimize oscillations (Runge's phenomenon)
- Provide stable numerical fitting
- Offer orthogonal basis functions over [-1, 1]
- Work well for smooth, slowly-varying backgrounds

Author: Custom Node Example
Date: December 1, 2025
"""

import logging
from typing import Any

import numpy as np

from robomage.data.models import DiffractionData
from robomage.orchestrator import ExecutionContext

logger = logging.getLogger(__name__)


async def chebyshev_background_handler(
    config: dict[str, Any],
    inputs: dict[str, Any],
    context: ExecutionContext,
) -> list[DiffractionData]:
    """
    Fit and subtract background using Chebyshev polynomial.

    Fits a Chebyshev polynomial of specified degree to the diffraction pattern
    (optionally in a specified Q-range) and subtracts the fitted background
    from the entire pattern.

    Config Parameters:
        - n_terms: int (number of Chebyshev polynomial terms, default: 5)
        - q_fit_min: float (optional, minimum Q for fitting, default: use min Q)
        - q_fit_max: float (optional, maximum Q for fitting, default: use max Q)
        - clip_negative: bool (set negative values to zero after subtraction, default: True)
        - return_backgrounds: bool (store fitted backgrounds in context, default: False)

    Inputs:
        - input: List[DiffractionData] (diffraction patterns to process)

    Outputs:
        List[DiffractionData] with Chebyshev backgrounds subtracted

    Example Configuration:
        {
            "n_terms": 7,
            "q_fit_min": 1.5,
            "q_fit_max": 8.0,
            "clip_negative": true
        }

    Raises:
        ValueError: If n_terms < 1 or Q-range is invalid
    """
    # Extract and validate configuration
    n_terms = int(config.get("n_terms", 5))
    if n_terms < 1:
        raise ValueError(f"n_terms must be >= 1, got {n_terms}")

    # Q-range for background fitting (optional)
    q_fit_min = config.get("q_fit_min")
    q_fit_max = config.get("q_fit_max")

    # Processing options
    clip_negative = config.get("clip_negative", True)
    return_backgrounds = config.get("return_backgrounds", False)

    logger.info(
        f"Chebyshev background subtraction starting: n_terms={n_terms}, "
        f"Q fit range=[{q_fit_min}, {q_fit_max}]"
    )

    # Get input files
    files = inputs.get("input", [])

    if not files:
        raise ValueError("No input files provided for background subtraction")

    if not isinstance(files, list):
        files = [files]  # Wrap single file in list

    # Process each file
    processed_files = []
    background_data = []  # For optional return
    errors = []

    for i, file in enumerate(files):
        try:
            logger.debug(f"Processing file {i+1}/{len(files)}: {file.filename}")

            # Validate input type
            if not isinstance(file, DiffractionData):
                raise ValueError(f"Expected DiffractionData, got {type(file).__name__}")

            # Extract data
            q_values = file.q_values
            intensities = file.intensities

            # Determine fitting range
            if q_fit_min is not None or q_fit_max is not None:
                # Use specified range
                fit_q_min = q_fit_min if q_fit_min is not None else q_values.min()
                fit_q_max = q_fit_max if q_fit_max is not None else q_values.max()

                # Validate range
                if fit_q_min >= fit_q_max:
                    raise ValueError(
                        f"Invalid Q range: q_fit_min ({fit_q_min}) >= q_fit_max ({fit_q_max})"
                    )

                # Find indices in range
                fit_mask = (q_values >= fit_q_min) & (q_values <= fit_q_max)
                q_fit = q_values[fit_mask]
                intensity_fit = intensities[fit_mask]

                if len(q_fit) < n_terms:
                    raise ValueError(
                        f"Not enough points ({len(q_fit)}) in Q range "
                        f"[{fit_q_min}, {fit_q_max}] for {n_terms} Chebyshev terms. "
                        f"Need at least {n_terms} points."
                    )
            else:
                # Use full range
                q_fit = q_values
                intensity_fit = intensities

                if len(q_fit) < n_terms:
                    raise ValueError(
                        f"Not enough data points ({len(q_fit)}) for {n_terms} "
                        f"Chebyshev terms. Need at least {n_terms} points."
                    )

            # Fit Chebyshev polynomial background
            background, coefficients = _fit_chebyshev_background(
                q_values, q_fit, intensity_fit, n_terms
            )

            # Subtract background
            corrected_intensities = intensities - background

            # Optionally clip negative values to zero
            if clip_negative:
                corrected_intensities = np.maximum(corrected_intensities, 0.0)

            # Calculate quality metric (R² of fit in fitting region)
            fit_mask_full = (q_values >= q_fit.min()) & (q_values <= q_fit.max())
            r_squared = _calculate_r_squared(
                intensities[fit_mask_full], background[fit_mask_full]
            )

            logger.debug(
                f"File {file.filename}: Chebyshev fit R² = {r_squared:.4f}, "
                f"n_terms = {n_terms}, Max background = {background.max():.1f}"
            )

            # Create new DiffractionData with corrected intensities
            # IMPORTANT: Preserve all metadata from original
            corrected_data = DiffractionData(
                q_values=file.q_values,  # Unchanged
                intensities=corrected_intensities,
                filename=file.filename,
                sample_name=file.sample_name,
            )

            processed_files.append(corrected_data)

            # Store background if requested
            if return_backgrounds:
                background_data.append(
                    {
                        "filename": file.filename,
                        "background": background.tolist(),  # Convert to list for JSON
                        "coefficients": coefficients.tolist(),
                        "r_squared": float(r_squared),
                        "n_terms": n_terms,
                        "method": "chebyshev",
                    }
                )

        except Exception as e:
            error_msg = f"File {i+1} ({file.filename if hasattr(file, 'filename') else 'unknown'}): {str(e)}"
            logger.error(f"Chebyshev background subtraction failed: {error_msg}")
            errors.append(error_msg)

    # Check if any files were processed
    if not processed_files:
        error_details = "\n  - ".join(errors) if errors else "Unknown error"
        raise ValueError(
            f"No files processed successfully.\nErrors:\n  - {error_details}"
        )

    # Store backgrounds in context if requested
    if return_backgrounds and background_data:
        context.metadata["chebyshev_backgrounds"] = background_data
        logger.debug(f"Stored {len(background_data)} Chebyshev backgrounds in context")

    logger.info(
        f"Chebyshev background subtraction complete: {len(processed_files)} files processed, "
        f"{len(errors)} failed"
    )

    return processed_files


def _fit_chebyshev_background(
    q_all: np.ndarray,
    q_fit: np.ndarray,
    intensity_fit: np.ndarray,
    n_terms: int,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Fit Chebyshev polynomial to intensity data.

    Chebyshev polynomials are defined on [-1, 1], so we normalize the Q-range
    to this interval, fit the polynomial, then evaluate on the full Q-range.

    Args:
        q_all: Full Q-value array (where to evaluate background)
        q_fit: Q-values to use for fitting
        intensity_fit: Intensity values to fit
        n_terms: Number of Chebyshev polynomial terms (degree = n_terms - 1)

    Returns:
        Tuple of (background, coefficients)
        - background: Background intensity values at q_all positions
        - coefficients: Chebyshev polynomial coefficients
    """
    # Normalize Q values to [-1, 1] for Chebyshev fitting
    q_min = q_fit.min()
    q_max = q_fit.max()

    # Map q_fit to [-1, 1]
    q_fit_normalized = 2.0 * (q_fit - q_min) / (q_max - q_min) - 1.0

    # Fit Chebyshev polynomial
    # np.polynomial.chebyshev.chebfit returns coefficients [c0, c1, c2, ...]
    # where the polynomial is c0*T0(x) + c1*T1(x) + c2*T2(x) + ...
    degree = n_terms - 1  # degree = n_terms - 1
    coefficients = np.polynomial.chebyshev.chebfit(
        q_fit_normalized, intensity_fit, deg=degree
    )

    # Evaluate background on full Q range
    q_all_normalized = 2.0 * (q_all - q_min) / (q_max - q_min) - 1.0
    background = np.polynomial.chebyshev.chebval(q_all_normalized, coefficients)

    return background, coefficients


def _calculate_r_squared(observed: np.ndarray, predicted: np.ndarray) -> float:
    """
    Calculate R² (coefficient of determination) for fit quality.

    R² = 1 - (SS_res / SS_tot)
    where:
        SS_res = sum of squared residuals
        SS_tot = total sum of squares

    Args:
        observed: Observed values
        predicted: Predicted (fitted) values

    Returns:
        R² value (1.0 = perfect fit, 0.0 = no better than mean)
    """
    # Residual sum of squares
    ss_res = np.sum((observed - predicted) ** 2)

    # Total sum of squares
    ss_tot = np.sum((observed - np.mean(observed)) ** 2)

    # R² calculation
    if ss_tot == 0:
        return 0.0

    r_squared = 1.0 - (ss_res / ss_tot)

    return float(r_squared)
