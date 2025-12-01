"""
Background Subtraction Node - Medium Complexity Example

Demonstrates real-world data processing with DiffractionData objects,
including fitting backgrounds, validating Q-space alignment, and
preserving metadata through transformations.

This node shows:
- Working with NumPy arrays from DiffractionData
- Different background subtraction methods
- Q-range selection for fitting
- Creating new DiffractionData objects with modifications
- Quality metrics and validation

Author: RoboMage Team
Date: December 1, 2025
"""

import logging
from typing import Any, Literal

import numpy as np

from robomage.data.models import DiffractionData
from robomage.orchestrator import ExecutionContext

logger = logging.getLogger(__name__)


async def background_subtraction_handler(
    config: dict[str, Any],
    inputs: dict[str, Any],
    context: ExecutionContext,
) -> list[DiffractionData]:
    """
    Subtract background from diffraction patterns.

    Fits and removes background using linear, constant, or polynomial methods.
    The background is fitted in a specified Q-range (or full range if not specified),
    then subtracted from the entire pattern.

    Config Parameters:
        - method: str (background method: "linear", "constant", "polynomial")
        - q_fit_min: float (optional, minimum Q for fitting, default: use min Q)
        - q_fit_max: float (optional, maximum Q for fitting, default: use max Q)
        - polynomial_degree: int (for polynomial method, default: 2)
        - return_backgrounds: bool (store backgrounds in context, default: False)

    Inputs:
        - input: List[DiffractionData] (diffraction patterns)

    Outputs:
        List[DiffractionData] with backgrounds subtracted

    Example Configuration:
        {
            "method": "linear",
            "q_fit_min": 1.0,
            "q_fit_max": 2.0
        }

    Raises:
        ValueError: If method is invalid or Q-range is invalid
    """
    # Extract and validate configuration
    method = config.get("method", "linear")
    valid_methods = ["linear", "constant", "polynomial"]

    if method not in valid_methods:
        raise ValueError(
            f"Invalid method '{method}'. Must be one of: {', '.join(valid_methods)}"
        )

    # Q-range for background fitting (optional)
    q_fit_min = config.get("q_fit_min")
    q_fit_max = config.get("q_fit_max")

    # Polynomial degree (only used for polynomial method)
    poly_degree = int(config.get("polynomial_degree", 2))
    if poly_degree < 1:
        raise ValueError(f"polynomial_degree must be >= 1, got {poly_degree}")

    # Option to save extracted backgrounds
    return_backgrounds = config.get("return_backgrounds", False)

    logger.info(
        f"Background subtraction starting: method={method}, "
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

                if len(q_fit) < 2:
                    raise ValueError(
                        f"Not enough points in Q range [{fit_q_min}, {fit_q_max}] for fitting"
                    )
            else:
                # Use full range
                q_fit = q_values
                intensity_fit = intensities

            # Fit background based on method
            background = _fit_background(
                q_values, q_fit, intensity_fit, method, poly_degree
            )

            # Subtract background
            corrected_intensities = intensities - background

            # Optional: Clip negative values to zero
            # (Can be a config option if needed)
            corrected_intensities = np.maximum(corrected_intensities, 0.0)

            # Calculate quality metric (R² of fit in fitting region)
            fit_mask_full = (q_values >= q_fit.min()) & (q_values <= q_fit.max())
            r_squared = _calculate_r_squared(
                intensities[fit_mask_full], background[fit_mask_full]
            )

            logger.debug(
                f"File {file.filename}: Background fit R² = {r_squared:.4f}, "
                f"Max background = {background.max():.1f}"
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
                        "r_squared": float(r_squared),
                        "method": method,
                    }
                )

        except Exception as e:
            error_msg = f"File {i+1} ({file.filename if hasattr(file, 'filename') else 'unknown'}): {str(e)}"
            logger.error(f"Background subtraction failed: {error_msg}")
            errors.append(error_msg)

    # Check if any files were processed
    if not processed_files:
        error_details = "\n  - ".join(errors) if errors else "Unknown error"
        raise ValueError(
            f"No files processed successfully.\nErrors:\n  - {error_details}"
        )

    # Store backgrounds in context if requested
    if return_backgrounds and background_data:
        context.metadata["backgrounds"] = background_data
        logger.debug(f"Stored {len(background_data)} backgrounds in context")

    logger.info(
        f"Background subtraction complete: {len(processed_files)} files processed, "
        f"{len(errors)} failed"
    )

    return processed_files


def _fit_background(
    q_all: np.ndarray,
    q_fit: np.ndarray,
    intensity_fit: np.ndarray,
    method: Literal["linear", "constant", "polynomial"],
    poly_degree: int = 2,
) -> np.ndarray:
    """
    Fit background to intensity data.

    Args:
        q_all: Full Q-value array (where to evaluate background)
        q_fit: Q-values to use for fitting
        intensity_fit: Intensity values to fit
        method: Fitting method
        poly_degree: Polynomial degree (for polynomial method)

    Returns:
        Background intensity values at q_all positions
    """
    if method == "constant":
        # Constant background = median of fitting region
        bg_level = np.median(intensity_fit)
        background = np.full_like(q_all, bg_level, dtype=float)

    elif method == "linear":
        # Linear fit: y = mx + b
        coeffs = np.polyfit(q_fit, intensity_fit, deg=1)
        background = np.polyval(coeffs, q_all)

    elif method == "polynomial":
        # Polynomial fit of specified degree
        coeffs = np.polyfit(q_fit, intensity_fit, deg=poly_degree)
        background = np.polyval(coeffs, q_all)

    else:
        raise ValueError(f"Unknown method: {method}")

    return background


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


# ==============================================================================
# ALTERNATIVE: Return Analysis Results Instead of Modified Data
# ==============================================================================
#
# If you want to return background parameters for analysis rather than
# corrected data, use this pattern:
#


async def background_analysis_handler(
    config: dict[str, Any],
    inputs: dict[str, Any],
    context: ExecutionContext,
) -> list[dict[str, Any]]:
    """
    Analyze backgrounds without modifying data.

    Returns background parameters and quality metrics rather than
    background-subtracted data.

    Config Parameters:
        - method: str ("linear", "constant", "polynomial")
        - q_fit_min: float (optional)
        - q_fit_max: float (optional)

    Inputs:
        - input: List[DiffractionData]

    Outputs:
        List of dictionaries with background analysis:
        [
            {
                "filename": str,
                "method": str,
                "background_level": float,  # (for constant method)
                "slope": float,  # (for linear method)
                "intercept": float,  # (for linear method)
                "r_squared": float,
                "background_max": float,
                "background_min": float
            },
            ...
        ]
    """
    method = config.get("method", "linear")
    q_fit_min = config.get("q_fit_min")
    q_fit_max = config.get("q_fit_max")

    files = inputs.get("input", [])
    if not files:
        raise ValueError("No input files provided")

    results = []

    for file in files:
        q_values = file.q_values
        intensities = file.intensities

        # Determine fit range
        if q_fit_min is not None or q_fit_max is not None:
            fit_q_min = q_fit_min if q_fit_min is not None else q_values.min()
            fit_q_max = q_fit_max if q_fit_max is not None else q_values.max()
            fit_mask = (q_values >= fit_q_min) & (q_values <= fit_q_max)
            q_fit = q_values[fit_mask]
            intensity_fit = intensities[fit_mask]
        else:
            q_fit = q_values
            intensity_fit = intensities

        # Fit background
        background = _fit_background(q_values, q_fit, intensity_fit, method, 2)

        # Calculate metrics
        fit_mask_full = (q_values >= q_fit.min()) & (q_values <= q_fit.max())
        r_squared = _calculate_r_squared(
            intensities[fit_mask_full], background[fit_mask_full]
        )

        # Build result
        result: dict[str, Any] = {
            "filename": file.filename,
            "method": method,
            "r_squared": float(r_squared),
            "background_max": float(background.max()),
            "background_min": float(background.min()),
            "background_mean": float(background.mean()),
        }

        # Add method-specific parameters
        if method == "constant":
            result["background_level"] = float(np.median(intensity_fit))
        elif method == "linear":
            coeffs = np.polyfit(q_fit, intensity_fit, deg=1)
            result["slope"] = float(coeffs[0])
            result["intercept"] = float(coeffs[1])

        results.append(result)

    return results
