"""
Data Input and Transformation Nodes

Node handlers for loading and transforming diffraction data.
"""

import glob
import logging
from pathlib import Path
from typing import Any

import robomage

logger = logging.getLogger(__name__)


async def load_files_handler(
    config: dict[str, Any], inputs: dict[str, Any], context: Any
) -> list:
    """
    Load diffraction files from directory.

    Config Parameters:
        - directory: str (path to directory, default: ".")
        - pattern: str (glob pattern, default: "*.chi")
        - wavelength: float (optional, override file wavelength in Angstroms)

    Outputs:
        List of DiffractionData objects

    Example:
        config = {
            "directory": "/data/experiment_1",
            "pattern": "*.chi",
            "wavelength": 0.1665
        }
    """
    directory = config.get("directory", ".")
    pattern = config.get("pattern", "*.chi")
    wavelength = config.get("wavelength")

    logger.info(f"Loading files from {directory} with pattern {pattern}")

    # Find matching files
    search_path = Path(directory) / pattern
    file_paths = sorted(glob.glob(str(search_path)))

    if not file_paths:
        raise ValueError(f"No files found matching: {search_path}")

    logger.info(f"Found {len(file_paths)} files to load")

    # Load files
    loaded_files = []
    for file_path in file_paths:
        try:
            data = robomage.load_diffraction_file(file_path)
            if wavelength:
                # Override wavelength if specified
                # Note: DiffractionData doesn't have wavelength attribute yet,
                # but this is where we'd set it
                pass
            loaded_files.append(data)
            logger.debug(f"Loaded: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to load {file_path}: {e}")
            # Continue with other files

    if not loaded_files:
        raise ValueError("No files could be loaded successfully")

    logger.info(f"Successfully loaded {len(loaded_files)} files")
    return loaded_files


async def filter_q_range_handler(
    config: dict[str, Any], inputs: dict[str, Any], context: Any
) -> list:
    """
    Filter diffraction data by Q-range.

    Config Parameters:
        - q_min: float (minimum Q value, default: 0)
        - q_max: float (maximum Q value, default: infinity)

    Inputs:
        - input: List of DiffractionData objects

    Outputs:
        Filtered list of DiffractionData objects

    Example:
        config = {
            "q_min": 2.0,
            "q_max": 8.0
        }
    """
    q_min = config.get("q_min", 0.0)
    q_max = config.get("q_max", float("inf"))

    logger.info(f"Filtering Q-range: [{q_min}, {q_max}]")

    files = inputs.get("input", [])
    if not files:
        raise ValueError("No input files provided to filter")

    filtered = []
    for i, data in enumerate(files):
        try:
            trimmed = data.trim_q_range(q_min, q_max)
            filtered.append(trimmed)
            logger.debug(
                f"File {i + 1}: Trimmed from {len(data.q_values)} to {len(trimmed.q_values)} points"
            )
        except Exception as e:
            logger.warning(f"Failed to filter file {i + 1}: {e}")
            # Continue with other files

    logger.info(f"Filtered {len(filtered)} files")
    return filtered


async def normalize_handler(
    config: dict[str, Any], inputs: dict[str, Any], context: Any
) -> list:
    """
    Normalize intensity values.

    Config Parameters:
        - method: str (normalization method: "max", "area", "zscore")

    Inputs:
        - input: List of DiffractionData objects

    Outputs:
        Normalized list of DiffractionData objects

    Example:
        config = {"method": "max"}
    """
    import numpy as np

    method = config.get("method", "max")
    logger.info(f"Normalizing intensities using method: {method}")

    files = inputs.get("input", [])

    if not files:
        raise ValueError("No input files provided to normalize")

    normalized = []
    for i, data in enumerate(files):
        try:
            intensities = data.intensities.copy()

            if method == "max":
                # Normalize to maximum value
                max_val = np.max(intensities)
                if max_val > 0:
                    intensities = intensities / max_val
            elif method == "area":
                # Normalize by total area (sum)
                area = np.sum(intensities)
                if area > 0:
                    intensities = intensities / area
            elif method == "zscore":
                # Z-score normalization
                mean = np.mean(intensities)
                std = np.std(intensities)
                if std > 0:
                    intensities = (intensities - mean) / std
            else:
                raise ValueError(f"Unknown normalization method: {method}")

            # Create new DiffractionData with normalized intensities
            from robomage.data.models import DiffractionData

            normalized_data = DiffractionData(
                q_values=data.q_values,
                intensities=intensities,
                filename=data.filename,
                sample_name=data.sample_name,
            )
            normalized.append(normalized_data)
            logger.debug(f"File {i + 1}: Normalized using {method}")

        except Exception as e:
            logger.warning(f"Failed to normalize file {i + 1}: {e}")

    logger.info(f"Normalized {len(normalized)} files")
    return normalized
