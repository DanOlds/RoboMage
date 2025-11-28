"""
Analysis Nodes

Node handlers for scientific analysis operations.
"""

import logging
from typing import Any

from robomage.clients.peak_analysis_client import PeakAnalysisClient

logger = logging.getLogger(__name__)


async def peak_analysis_handler(
    config: dict[str, Any], inputs: dict[str, Any], context: Any
) -> list:
    """
    Perform peak analysis on diffraction data.

    Config Parameters:
        - profile_type: str (peak profile: "gaussian", "lorentzian", "voigt")
        - prominence: float (peak prominence threshold, default: 0.1)
        - distance: float (minimum distance between peaks, default: 5)
        - service_url: str (peak analysis service URL, default: http://localhost:8001)

    Inputs:
        - input: List of DiffractionData objects

    Outputs:
        List of dictionaries with peak analysis results

    Example:
        config = {
            "profile_type": "gaussian",
            "prominence": 0.1,
            "distance": 5
        }
    """
    service_url = config.get("service_url", "http://localhost:8001")
    profile_type = config.get("profile_type", "gaussian")
    prominence = config.get("prominence", 0.1)
    distance = config.get("distance", 5)

    logger.info(
        f"Running peak analysis with profile={profile_type}, "
        f"prominence={prominence}, distance={distance}"
    )

    # Create client
    client = PeakAnalysisClient(service_url)

    # Build analysis config matching the service's AnalysisConfig model
    analysis_config = {
        "detection": {
            "min_prominence": prominence,
            "min_distance": distance,
        },
        "fitting": {
            "profile_type": profile_type,
        },
    }

    files = inputs.get("input", [])
    if not files:
        raise ValueError("No input files provided for analysis")

    results = []
    errors = []
    for i, data in enumerate(files):
        try:
            logger.info(f"Analyzing file {i + 1}/{len(files)}: {data.filename}")
            response = client.analyze_peaks(data, analysis_config)

            # Extract results from response
            # Response structure: {peaks: [...], metadata: {...}, background: {...}}
            peaks = response.get("peaks", [])
            metadata = response.get("metadata", {})

            # Store result as dict
            result = {
                "filename": data.filename,
                "peaks_detected": metadata.get("num_peaks_detected", len(peaks)),
                "peaks_fitted": metadata.get("num_peaks_fitted", len(peaks)),
                "overall_r_squared": metadata.get("overall_r_squared", 0.0),
                "peak_list": [
                    {
                        "position": peak.get("position"),
                        "d_spacing": peak.get("d_spacing"),
                        "height": peak.get("height"),
                        "width": peak.get("width"),
                        "area": peak.get("area"),
                        "r_squared": peak.get("r_squared", 0.0),
                    }
                    for peak in peaks
                ],
            }
            results.append(result)
            logger.info(
                f"File {i + 1}: Found {metadata.get('num_peaks_detected', len(peaks))} peaks, "
                f"fitted {metadata.get('num_peaks_fitted', len(peaks))}"
            )

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to analyze file {i + 1}: {error_msg}")
            errors.append(
                f"File {i + 1} ({data.filename if hasattr(data, 'filename') else 'unknown'}): {error_msg}"
            )

    if not results:
        # Provide detailed error message
        error_details = "\n  - ".join(errors) if errors else "Unknown error"

        # Check if it's likely a service connection issue
        if errors and any(
            "Connection" in err or "refused" in err.lower() or "timeout" in err.lower()
            for err in errors
        ):
            raise ValueError(
                f"No files were analyzed successfully. "
                f"Peak analysis service may not be running.\n"
                f"Start the service with:\n"
                f"  pixi run python services/peak_analysis/main.py --port 8001\n\n"
                f"Errors encountered:\n  - {error_details}"
            )
        else:
            raise ValueError(
                f"No files were analyzed successfully.\n"
                f"Errors encountered:\n  - {error_details}"
            )

    logger.info(f"Successfully analyzed {len(results)} files")
    return results


async def statistics_handler(
    config: dict[str, Any], inputs: dict[str, Any], context: Any
) -> list:
    """
    Calculate statistical metrics on diffraction data.

    Config Parameters:
        - metrics: list[str] (metrics to calculate: ["mean", "std", "range", "peaks"])

    Inputs:
        - input: List of DiffractionData objects

    Outputs:
        List of dictionaries with statistical summaries

    Example:
        config = {"metrics": ["mean", "std", "range"]}
    """
    import numpy as np

    metrics = config.get("metrics", ["mean", "std", "range"])
    logger.info(f"Calculating statistics: {metrics}")

    files = inputs.get("input", [])
    if not files:
        raise ValueError("No input files provided for statistics")

    stats_results = []
    for i, data in enumerate(files):
        try:
            stats = {"filename": data.filename}

            if "mean" in metrics:
                stats["intensity_mean"] = float(np.mean(data.intensity_values))

            if "std" in metrics:
                stats["intensity_std"] = float(np.std(data.intensity_values))

            if "range" in metrics:
                stats["intensity_min"] = float(np.min(data.intensity_values))
                stats["intensity_max"] = float(np.max(data.intensity_values))
                stats["q_min"] = float(np.min(data.q_values))
                stats["q_max"] = float(np.max(data.q_values))

            if "peaks" in metrics:
                # Use data statistics if available
                if hasattr(data, "statistics"):
                    stats["num_points"] = data.statistics.num_points
                    stats["q_step_mean"] = data.statistics.q_step_mean
                else:
                    stats["num_points"] = len(data.q_values)

            stats_results.append(stats)
            logger.debug(f"File {i + 1}: Computed {len(stats)} statistics")

        except Exception as e:
            logger.warning(f"Failed to compute statistics for file {i + 1}: {e}")

    logger.info(f"Computed statistics for {len(stats_results)} files")
    return stats_results
