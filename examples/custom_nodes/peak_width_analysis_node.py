"""
Peak Width Analysis Node - Advanced Example

Demonstrates advanced scientific analysis using scipy, including:
- Integration with external scientific libraries
- Processing results from other analysis nodes
- Calculating Full Width Half Maximum (FWHM)
- Statistical analysis and classification
- Error handling for edge cases
- Optional dependencies with helpful error messages

This node operates on peak analysis results and calculates peak widths
using Gaussian, Lorentzian, or Voigt profile fitting.

Author: RoboMage Team
Date: December 1, 2025
"""

import logging
from typing import Any, Literal

import numpy as np

from robomage.data.models import DiffractionData
from robomage.orchestrator import ExecutionContext

# Optional dependency - check at runtime
try:
    from scipy import optimize
    from scipy.special import voigt_profile

    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

logger = logging.getLogger(__name__)


async def peak_width_analysis_handler(
    config: dict[str, Any],
    inputs: dict[str, Any],
    context: ExecutionContext,
) -> list[dict[str, Any]]:
    """
    Analyze peak widths (FWHM) from detected peaks.

    Takes peak positions from peak analysis results, fits specified profiles
    to each peak, and calculates Full Width Half Maximum (FWHM). Provides
    statistical summaries and quality classifications.

    Config Parameters:
        - fit_profile: str (profile type: "gaussian", "lorentzian", "voigt", default: "gaussian")
        - window_size: float (Q-range around peak for fitting, default: 0.5 Å⁻¹)
        - min_height: float (minimum peak height to analyze, default: 0.0)
        - classify_widths: bool (classify peaks as narrow/medium/broad, default: True)
        - narrow_threshold: float (FWHM threshold for narrow peaks, default: 0.1)
        - broad_threshold: float (FWHM threshold for broad peaks, default: 0.3)

    Inputs:
        - files: List[DiffractionData] (original diffraction data)
        - peak_results: List[dict] (results from peak_analysis node)
            Expected structure: [{"filename": str, "peak_list": [{"position": float, ...}]}]

    Outputs:
        List of dictionaries with FWHM analysis:
        [
            {
                "filename": str,
                "num_peaks_analyzed": int,
                "peaks": [
                    {
                        "position": float,
                        "fwhm": float,
                        "amplitude": float,
                        "fit_quality": float,  # R² value
                        "classification": str  # "narrow" | "medium" | "broad"
                    },
                    ...
                ],
                "statistics": {
                    "mean_fwhm": float,
                    "std_fwhm": float,
                    "min_fwhm": float,
                    "max_fwhm": float,
                    "median_fwhm": float
                },
                "classification_counts": {
                    "narrow": int,
                    "medium": int,
                    "broad": int
                }
            },
            ...
        ]

    Example Configuration:
        {
            "fit_profile": "gaussian",
            "window_size": 0.5,
            "min_height": 100.0,
            "classify_widths": true,
            "narrow_threshold": 0.1,
            "broad_threshold": 0.3
        }

    Raises:
        ImportError: If scipy is not installed
        ValueError: If inputs are invalid or missing
    """
    # Check for scipy dependency
    if not SCIPY_AVAILABLE:
        raise ImportError(
            "Peak width analysis requires scipy.\n"
            "Install with:\n"
            "  pixi add scipy\n"
            "or add 'scipy>=1.11.0' to pyproject.toml dependencies"
        )

    # Extract and validate configuration
    fit_profile = config.get("fit_profile", "gaussian")
    valid_profiles = ["gaussian", "lorentzian", "voigt"]

    if fit_profile not in valid_profiles:
        raise ValueError(
            f"Invalid fit_profile '{fit_profile}'. "
            f"Must be one of: {', '.join(valid_profiles)}"
        )

    window_size = float(config.get("window_size", 0.5))
    min_height = float(config.get("min_height", 0.0))
    classify_widths = config.get("classify_widths", True)
    narrow_threshold = float(config.get("narrow_threshold", 0.1))
    broad_threshold = float(config.get("broad_threshold", 0.3))

    if window_size <= 0:
        raise ValueError(f"window_size must be positive, got {window_size}")

    if narrow_threshold >= broad_threshold:
        raise ValueError(
            f"narrow_threshold ({narrow_threshold}) must be < "
            f"broad_threshold ({broad_threshold})"
        )

    logger.info(
        f"Peak width analysis starting: profile={fit_profile}, "
        f"window={window_size}, min_height={min_height}"
    )

    # Get inputs - both original data and peak analysis results
    files = inputs.get("files", inputs.get("input", []))
    peak_results = inputs.get("peak_results", inputs.get("results", []))

    if not files:
        raise ValueError("No diffraction files provided")

    if not peak_results:
        raise ValueError(
            "No peak analysis results provided. "
            "Connect this node to peak_analysis output."
        )

    # Match files with peak results by filename
    file_dict = {f.filename: f for f in files}

    results = []
    errors = []

    for i, peak_result in enumerate(peak_results):
        try:
            filename = peak_result.get("filename")
            if not filename:
                raise ValueError("Peak result missing 'filename' field")

            # Get corresponding diffraction data
            if filename not in file_dict:
                raise ValueError(
                    f"No diffraction data found for filename: {filename}"
                )

            file_data = file_dict[filename]
            peak_list = peak_result.get("peak_list", [])

            if not peak_list:
                logger.warning(f"No peaks found for {filename}, skipping")
                continue

            logger.debug(
                f"Analyzing {len(peak_list)} peaks for {filename}"
            )

            # Analyze each peak
            peak_widths = []
            classifications = {"narrow": 0, "medium": 0, "broad": 0}

            for peak in peak_list:
                try:
                    position = peak.get("position")
                    height = peak.get("height", 0)

                    # Skip peaks below minimum height
                    if height < min_height:
                        continue

                    # Extract data around peak
                    q_window, intensity_window = _extract_peak_window(
                        file_data.q_values,
                        file_data.intensities,
                        position,
                        window_size,
                    )

                    if len(q_window) < 5:  # Need minimum points for fitting
                        logger.warning(
                            f"Not enough points around peak at Q={position:.2f}"
                        )
                        continue

                    # Fit profile and calculate FWHM
                    fwhm, amplitude, r_squared = _fit_peak_profile(
                        q_window, intensity_window, position, fit_profile
                    )

                    # Classify width
                    if classify_widths:
                        if fwhm < narrow_threshold:
                            classification = "narrow"
                            classifications["narrow"] += 1
                        elif fwhm > broad_threshold:
                            classification = "broad"
                            classifications["broad"] += 1
                        else:
                            classification = "medium"
                            classifications["medium"] += 1
                    else:
                        classification = "unclassified"

                    peak_widths.append(
                        {
                            "position": float(position),
                            "fwhm": float(fwhm),
                            "amplitude": float(amplitude),
                            "fit_quality": float(r_squared),
                            "classification": classification,
                        }
                    )

                except Exception as e:
                    logger.warning(
                        f"Failed to analyze peak at Q={peak.get('position', '?')}: {e}"
                    )
                    continue

            if not peak_widths:
                logger.warning(f"No peaks successfully analyzed for {filename}")
                continue

            # Calculate statistics
            fwhm_values = np.array([p["fwhm"] for p in peak_widths])

            statistics = {
                "mean_fwhm": float(np.mean(fwhm_values)),
                "std_fwhm": float(np.std(fwhm_values)),
                "min_fwhm": float(np.min(fwhm_values)),
                "max_fwhm": float(np.max(fwhm_values)),
                "median_fwhm": float(np.median(fwhm_values)),
            }

            result = {
                "filename": filename,
                "num_peaks_analyzed": len(peak_widths),
                "profile_type": fit_profile,
                "peaks": peak_widths,
                "statistics": statistics,
            }

            if classify_widths:
                result["classification_counts"] = classifications

            results.append(result)

            logger.info(
                f"{filename}: Analyzed {len(peak_widths)} peaks, "
                f"mean FWHM = {statistics['mean_fwhm']:.4f}"
            )

        except Exception as e:
            error_msg = f"File {i+1} ({peak_result.get('filename', 'unknown')}): {str(e)}"
            logger.error(f"Peak width analysis failed: {error_msg}")
            errors.append(error_msg)

    if not results:
        error_details = "\n  - ".join(errors) if errors else "Unknown error"
        raise ValueError(
            f"No files analyzed successfully.\nErrors:\n  - {error_details}"
        )

    logger.info(
        f"Peak width analysis complete: {len(results)} files analyzed, "
        f"{len(errors)} failed"
    )

    return results


def _extract_peak_window(
    q_values: np.ndarray, intensities: np.ndarray, position: float, window_size: float
) -> tuple[np.ndarray, np.ndarray]:
    """
    Extract data around a peak position.

    Args:
        q_values: Full Q-value array
        intensities: Full intensity array
        position: Peak position (Q value)
        window_size: Half-width of window in Q units

    Returns:
        Tuple of (q_window, intensity_window) around peak
    """
    q_min = position - window_size / 2
    q_max = position + window_size / 2

    mask = (q_values >= q_min) & (q_values <= q_max)

    return q_values[mask], intensities[mask]


def _fit_peak_profile(
    q_values: np.ndarray,
    intensities: np.ndarray,
    initial_position: float,
    profile_type: Literal["gaussian", "lorentzian", "voigt"],
) -> tuple[float, float, float]:
    """
    Fit profile to peak and calculate FWHM.

    Args:
        q_values: Q-values around peak
        intensities: Intensity values around peak
        initial_position: Initial guess for peak position
        profile_type: Type of profile to fit

    Returns:
        Tuple of (fwhm, amplitude, r_squared)
    """
    # Initial parameter guesses
    amplitude_guess = np.max(intensities)
    position_guess = initial_position
    width_guess = 0.1  # Initial width guess

    if profile_type == "gaussian":
        # Gaussian: I(Q) = A * exp(-((Q - Q0)^2 / (2 * sigma^2)))
        def gaussian(q, amplitude, position, sigma):
            return amplitude * np.exp(-((q - position) ** 2) / (2 * sigma**2))

        try:
            popt, _ = optimize.curve_fit(
                gaussian,
                q_values,
                intensities,
                p0=[amplitude_guess, position_guess, width_guess],
                maxfev=5000,
            )
            amplitude, position, sigma = popt

            # FWHM for Gaussian = 2 * sqrt(2 * ln(2)) * sigma ≈ 2.355 * sigma
            fwhm = 2.355 * abs(sigma)

            # Calculate fit quality
            fitted = gaussian(q_values, *popt)
            r_squared = _calculate_r_squared(intensities, fitted)

        except Exception as e:
            logger.warning(f"Gaussian fit failed: {e}, using approximate FWHM")
            fwhm = width_guess * 2.355
            amplitude = amplitude_guess
            r_squared = 0.0

    elif profile_type == "lorentzian":
        # Lorentzian: I(Q) = A / (1 + ((Q - Q0) / gamma)^2)
        def lorentzian(q, amplitude, position, gamma):
            return amplitude / (1 + ((q - position) / gamma) ** 2)

        try:
            popt, _ = optimize.curve_fit(
                lorentzian,
                q_values,
                intensities,
                p0=[amplitude_guess, position_guess, width_guess],
                maxfev=5000,
            )
            amplitude, position, gamma = popt

            # FWHM for Lorentzian = 2 * gamma
            fwhm = 2 * abs(gamma)

            fitted = lorentzian(q_values, *popt)
            r_squared = _calculate_r_squared(intensities, fitted)

        except Exception as e:
            logger.warning(f"Lorentzian fit failed: {e}, using approximate FWHM")
            fwhm = 2 * width_guess
            amplitude = amplitude_guess
            r_squared = 0.0

    elif profile_type == "voigt":
        # Voigt profile (convolution of Gaussian and Lorentzian)
        # More complex - use scipy's voigt_profile
        def voigt(q, amplitude, position, sigma, gamma):
            return amplitude * voigt_profile(q - position, sigma, gamma)

        try:
            popt, _ = optimize.curve_fit(
                voigt,
                q_values,
                intensities,
                p0=[amplitude_guess, position_guess, width_guess, width_guess],
                maxfev=5000,
            )
            amplitude, position, sigma, gamma = popt

            # Approximate FWHM for Voigt (no analytical form)
            # Use Gaussian FWHM as approximation
            fwhm = 2.355 * abs(sigma)

            fitted = voigt(q_values, *popt)
            r_squared = _calculate_r_squared(intensities, fitted)

        except Exception as e:
            logger.warning(f"Voigt fit failed: {e}, using approximate FWHM")
            fwhm = 2.355 * width_guess
            amplitude = amplitude_guess
            r_squared = 0.0

    else:
        raise ValueError(f"Unknown profile type: {profile_type}")

    return fwhm, amplitude, r_squared


def _calculate_r_squared(observed: np.ndarray, predicted: np.ndarray) -> float:
    """
    Calculate R² (coefficient of determination).

    Args:
        observed: Observed values
        predicted: Predicted (fitted) values

    Returns:
        R² value (1.0 = perfect fit, 0.0 = no better than mean)
    """
    ss_res = np.sum((observed - predicted) ** 2)
    ss_tot = np.sum((observed - np.mean(observed)) ** 2)

    if ss_tot == 0:
        return 0.0

    r_squared = 1.0 - (ss_res / ss_tot)
    return float(r_squared)
