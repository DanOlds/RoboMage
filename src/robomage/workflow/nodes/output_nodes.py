"""
Output Nodes

Node handlers for exporting results and generating outputs.
"""

import csv
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


async def export_csv_handler(
    config: dict[str, Any], inputs: dict[str, Any], context: Any
) -> dict:
    """
    Export analysis results to CSV files.
    
    Config Parameters:
        - output_path: str (output file path or directory)
        - format: str (csv format: "peaks", "statistics", "data")
    
    Inputs:
        - input: List of results (from peak analysis or statistics)
    
    Outputs:
        Dictionary with export information
    
    Example:
        config = {
            "output_path": "results/peaks.csv",
            "format": "peaks"
        }
    """
    output_path = config.get("output_path", "workflow_output.csv")
    format_type = config.get("format", "peaks")

    logger.info(f"Exporting to CSV: {output_path} (format: {format_type})")

    results = inputs.get("input", [])
    if not results:
        raise ValueError("No input data provided for CSV export")

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    if format_type == "peaks":
        # Export peak analysis results
        with open(output_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "filename",
                    "peak_id",
                    "position_q",
                    "d_spacing",
                    "height",
                    "width",
                    "r_squared",
                ]
            )

            for result in results:
                filename = result.get("filename", "unknown")
                for i, peak in enumerate(result.get("peak_list", [])):
                    writer.writerow(
                        [
                            filename,
                            i,
                            peak.get("position", 0),
                            peak.get("d_spacing", 0),
                            peak.get("height", 0),
                            peak.get("width", 0),
                            peak.get("r_squared", 0),
                        ]
                    )

    elif format_type == "statistics":
        # Export statistical results
        if results:
            with open(output_file, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=results[0].keys())
                writer.writeheader()
                writer.writerows(results)

    else:
        raise ValueError(f"Unknown export format: {format_type}")

    logger.info(f"Exported {len(results)} results to {output_file}")

    return {
        "output_file": str(output_file),
        "records_exported": len(results),
        "format": format_type,
    }


async def export_json_handler(
    config: dict[str, Any], inputs: dict[str, Any], context: Any
) -> dict:
    """
    Export results to JSON file.
    
    Config Parameters:
        - output_path: str (output file path)
        - pretty: bool (pretty print JSON, default: True)
    
    Inputs:
        - input: Any serializable data
    
    Outputs:
        Dictionary with export information
    """
    output_path = config.get("output_path", "workflow_output.json")
    pretty = config.get("pretty", True)

    logger.info(f"Exporting to JSON: {output_path}")

    data = inputs.get("input")
    if data is None:
        raise ValueError("No input data provided for JSON export")

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w") as f:
        if pretty:
            json.dump(data, f, indent=2, default=str)
        else:
            json.dump(data, f, default=str)

    logger.info(f"Exported data to {output_file}")

    return {"output_file": str(output_file), "format": "json"}


async def save_results_handler(
    config: dict[str, Any], inputs: dict[str, Any], context: Any
) -> dict:
    """
    Save workflow results to context for later retrieval.
    
    Config Parameters:
        - key: str (key name for storing results)
    
    Inputs:
        - input: Any data to save
    
    Outputs:
        Confirmation dictionary
    """
    key = config.get("key", "results")

    logger.info(f"Saving results to context with key: {key}")

    data = inputs.get("input")
    if data is None:
        raise ValueError("No input data provided to save")

    # Store in context metadata
    context.metadata[key] = data

    return {"saved": True, "key": key, "data_type": type(data).__name__}
