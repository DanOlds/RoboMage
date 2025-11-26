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

    # Build analysis config
    analysis_config = {
        "peak_detection": {"prominence": prominence, "distance": distance},
        "fitting": {"profile_type": profile_type},
    }

    files = inputs.get("input", [])
    if not files:
        raise ValueError("No input files provided for analysis")

    results = []
    for i, data in enumerate(files):
        try:
            logger.info(f"Analyzing file {i+1}/{len(files)}: {data.filename}")
            response = client.analyze_diffraction_data(data, analysis_config)

            # Store result as dict
            result = {
                "filename": data.filename,
                "peaks_detected": response.peaks_detected,
                "peaks_fitted": response.peaks_fitted,
                "overall_r_squared": response.overall_r_squared,
                "peak_list": [
                    {
                        "position": peak.position,
                        "d_spacing": peak.d_spacing,
                        "height": peak.height,
                        "width": peak.width,
                        "r_squared": peak.r_squared,
                    }
                    for peak in response.peak_list
                ],
            }
            results.append(result)
            logger.info(
                f"File {i+1}: Found {response.peaks_detected} peaks, "
                f"fitted {response.peaks_fitted}"
            )

        except Exception as e:
            logger.error(f"Failed to analyze file {i+1}: {e}")
            # Continue with other files

    if not results:
        raise ValueError("No files were analyzed successfully")

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
            logger.debug(f"File {i+1}: Computed {len(stats)} statistics")

        except Exception as e:
            logger.warning(f"Failed to compute statistics for file {i+1}: {e}")

    logger.info(f"Computed statistics for {len(stats_results)} files")
    return stats_results
