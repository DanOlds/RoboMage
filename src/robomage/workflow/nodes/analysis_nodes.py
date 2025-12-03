"""
Analysis Nodes

Node handlers for scientific analysis operations.
"""

import logging
from typing import Any

from robomage.clients.gsasii_client import GSASIIClient
from robomage.clients.peak_analysis_client import PeakAnalysisClient
from robomage.workflow.nodes.registry import register_node

logger = logging.getLogger(__name__)


@register_node(
    type="peak_analysis",
    category="analysis",
    name="Peak Detection",
    description="Detect and fit crystallographic peaks",
    icon="fas fa-mountain",
    inputs=[{"name": "input", "type": "DiffractionData[]"}],
    outputs=[{"name": "output", "type": "PeakAnalysisResults[]"}],
    config_schema={
        "type": "object",
        "properties": {
            "profile_type": {
                "type": "string",
                "enum": ["gaussian", "lorentzian", "voigt"],
                "default": "gaussian",
            },
            "prominence": {"type": "number", "default": 0.1},
            "distance": {"type": "number", "default": 5},
            "service_url": {
                "type": "string",
                "default": "http://localhost:8001",
            },
        },
    },
)
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


@register_node(
    type="statistics",
    category="analysis",
    name="Statistics",
    description="Calculate statistical metrics",
    icon="fas fa-chart-bar",
    inputs=[{"name": "input", "type": "DiffractionData[]"}],
    outputs=[{"name": "output", "type": "Statistics[]"}],
    config_schema={
        "type": "object",
        "properties": {
            "metrics": {
                "type": "array",
                "items": {"type": "string"},
                "default": ["mean", "std", "range"],
            }
        },
    },
)
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


@register_node(
    type="gsasii_refinement",
    category="analysis",
    name="GSAS-II Refinement",
    description="Perform Rietveld refinement with GSAS-II",
    icon="fas fa-atom",
    inputs=[{"name": "input", "type": "DiffractionData[]"}],
    outputs=[{"name": "output", "type": "RefinementResults[]"}],
    config_schema={
        "type": "object",
        "properties": {
            "instrument_file": {
                "type": "string",
                "default": "PDF_1m.instprm",
                "description": "Instrument parameter file (asset name or path)",
            },
            "cif_file": {
                "type": "string",
                "default": "LaB6_SRM_660c.CIF",
                "description": "CIF file for phase (asset name or path)",
            },
            "phase_name": {
                "type": "string",
                "default": "LaB6",
                "description": "Phase name for refinement",
            },
            "refinement_cycles": {
                "type": "number",
                "default": 5,
                "description": "Number of refinement cycles",
            },
            "refine_background": {
                "type": "boolean",
                "default": True,
                "description": "Refine background parameters",
            },
            "refine_cell": {
                "type": "boolean",
                "default": True,
                "description": "Refine unit cell parameters",
            },
            "refine_size_strain": {
                "type": "boolean",
                "default": False,
                "description": "Refine crystallite size and strain",
            },
            "service_url": {
                "type": "string",
                "default": "http://localhost:8003",
                "description": "GSAS-II service URL",
            },
        },
        "required": ["instrument_file", "cif_file", "phase_name"],
    },
)
async def gsasii_refinement_handler(
    config: dict[str, Any], inputs: dict[str, Any], context: Any
) -> list:
    """
    Perform Rietveld refinement using GSAS-II.

    Config Parameters:
        - instrument_file: str (instrument parameter file)
        - cif_file: str (CIF file for phase structure)
        - phase_name: str (name of the phase)
        - refinement_cycles: int (number of refinement cycles, default: 5)
        - refine_background: bool (refine background, default: True)
        - refine_cell: bool (refine unit cell, default: True)
        - refine_size_strain: bool (refine size/strain, default: False)
        - service_url: str (GSAS-II service URL, default: http://localhost:8002)

    Inputs:
        - input: List of DiffractionData objects (must contain 2θ data)

    Outputs:
        List of dictionaries with refinement results

    Example:
        config = {
            "instrument_file": "PDF_1m.instprm",
            "cif_file": "LaB6_SRM_660c.CIF",
            "phase_name": "LaB6",
            "refinement_cycles": 5,
            "refine_background": True,
            "refine_cell": True,
            "service_url": "http://localhost:8002"
        }
    """
    service_url = config.get("service_url", "http://localhost:8002")

    # Extract recipe parameters
    instrument_file = config["instrument_file"]
    cif_file = config["cif_file"]
    phase_name = config["phase_name"]
    refinement_cycles = config.get("refinement_cycles", 5)
    refine_background = config.get("refine_background", True)
    refine_cell = config.get("refine_cell", True)
    refine_size_strain = config.get("refine_size_strain", False)

    logger.info(
        f"Running GSAS-II refinement with phase={phase_name}, "
        f"cycles={refinement_cycles}, cell={refine_cell}"
    )

    # Create client
    client = GSASIIClient(service_url, timeout=300.0)

    # Build refinement recipe
    recipe = {
        "instrument_file": instrument_file,
        "cif_file": cif_file,
        "phase_name": phase_name,
        "refinement_dict": {
            "Limits": [0.5, 16.0],  # 2θ range
            "Background": {
                "no. coeffs": 3,
                "type": "chebyschev-1",
                "refine": refine_background,
            },
            "Sample Parameters": ["Scale"],
            "Instrument Parameters": [],
            "Histograms": {},
            "Phases": {
                phase_name: {
                    "Cell": refine_cell,
                    "Size": refine_size_strain,
                    "Mustrain": {"type": "isotropic", "refine": refine_size_strain},
                }
            },
            "Cycles": refinement_cycles,
        },
    }

    files = inputs.get("input", [])
    if not files:
        raise ValueError("No input files provided for refinement")

    results = []
    errors = []
    for i, data in enumerate(files):
        try:
            logger.info(f"Refining file {i + 1}/{len(files)}: {data.filename}")
            response = client.refine(data, recipe)

            # Extract results from response
            # Response structure: {cell: {...}, fit_quality: {...}, fit_profile: {...}, plot_image: "..."}
            cell = response.get("cell", {})
            fit_quality = response.get("fit_quality", {})
            fit_profile = response.get("fit_profile", {})

            # Store result as dict
            result = {
                "filename": data.filename,
                "phase_name": phase_name,
                "cell_parameters": {
                    "a": cell.get("a", {}).get("value"),
                    "a_esd": cell.get("a", {}).get("esd"),
                    "b": cell.get("b", {}).get("value"),
                    "b_esd": cell.get("b", {}).get("esd"),
                    "c": cell.get("c", {}).get("value"),
                    "c_esd": cell.get("c", {}).get("esd"),
                    "alpha": cell.get("alpha", {}).get("value"),
                    "beta": cell.get("beta", {}).get("value"),
                    "gamma": cell.get("gamma", {}).get("value"),
                    "volume": cell.get("volume", {}).get("value"),
                },
                "fit_quality": {
                    "Rwp": fit_quality.get("Rwp"),
                    "chi2": fit_quality.get("chi2"),
                    "GoF": fit_quality.get("GoF"),
                },
                "convergence": response.get("convergence", "unknown"),
                "num_data_points": len(fit_profile.get("y_obs", [])),
            }
            results.append(result)
            logger.info(
                f"File {i + 1}: Rwp={fit_quality.get('Rwp', 'N/A'):.3f}%, "
                f"Cell a={cell.get('a', {}).get('value', 'N/A'):.6f} Å"
            )

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to refine file {i + 1}: {error_msg}")
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
                f"No files were refined successfully. "
                f"GSAS-II service may not be running.\n"
                f"Start the service with:\n"
                f"  cd /nsls2/users/dolds/dev/GSAS-II/pixi && "
                f"pixi run python /nsls2/users/dolds/dev/RoboMage/services/gsasii_refinement/main.py\n\n"
                f"Errors encountered:\n  - {error_details}"
            )
        else:
            raise ValueError(
                f"No files were refined successfully.\n"
                f"Errors encountered:\n  - {error_details}"
            )

    logger.info(f"Successfully refined {len(results)} files")
    return results
