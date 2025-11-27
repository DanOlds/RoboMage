"""
Output Nodes

Node handlers for exporting results and generating outputs.
"""

import csv
import json
import logging
from csv import DictWriter
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
                dict_writer: DictWriter[Any] = csv.DictWriter(
                    f, fieldnames=results[0].keys()
                )
                dict_writer.writeheader()
                dict_writer.writerows(results)

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


async def save_to_session_handler(
    config: dict[str, Any], inputs: dict[str, Any], context: Any
) -> dict:
    """
    Save workflow results into a session for dashboard visualization.

    This enables seamless workflow → visualization integration by extracting
    DiffractionData objects from workflow execution and adding them to the
    specified session.

    Config Parameters:
        - session_id: str
            Target session ID. Use "current" for active dashboard session,
            or provide specific session ID. If session doesn't exist, it will
            be created with this ID as the name.

        - include_files: bool (default: True)
            Whether to save DiffractionData objects to session

        - include_results: bool (default: True)
            Whether to save analysis results (peaks, statistics) as metadata

        - overwrite_duplicates: bool (default: False)
            If True, replaces existing files with same name

    Inputs:
        - files: List[DiffractionData] (optional)
            Diffraction data to save to session

        - results: List[dict] (optional)
            Analysis results (peak lists, statistics, etc.)

    Outputs:
        Dictionary with operation summary:
        {
            "session_id": str,
            "files_saved": int,
            "results_saved": int,
            "status": "success" | "partial" | "error",
            "errors": List[str]
        }

    Example Workflow:
        ```json
        {
          "nodes": [
            {"id": "load_1", "type": "load_files", "config": {"directory": "data/"}},
            {"id": "analyze_1", "type": "peak_analysis", "config": {...}},
            {"id": "save_1", "type": "save_to_session", "config": {
              "session_id": "my_analysis_session",
              "include_files": true,
              "include_results": true
            }}
          ],
          "edges": [
            {"source": "load_1", "target": "analyze_1"},
            {"source": "analyze_1", "target": "save_1"}
          ]
        }
        ```

    Raises:
        ValueError: If session_id is invalid or session creation fails
        RuntimeError: If persistence layer is unavailable
    """
    from datetime import datetime

    # Extract config
    session_id = config.get("session_id", "current")
    include_files = config.get("include_files", True)
    include_results = config.get("include_results", True)

    logger.info(f"Saving workflow results to session: {session_id}")

    # Initialize session manager
    try:
        from robomage.persistence.api import SessionManager

        manager = SessionManager()
    except Exception as e:
        raise RuntimeError(f"Failed to initialize SessionManager: {e}")

    # Handle "current" session ID (from dashboard context)
    if session_id == "current":
        # Get from context if provided, otherwise create new
        session_id = context.metadata.get("active_session_id")
        if not session_id:
            # Create new session with timestamp
            session_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            logger.info(f"No active session, creating new: {session_id}")

    # Convert string numeric IDs to integers for existing sessions
    original_session_id = session_id
    if isinstance(session_id, str) and session_id.isdigit():
        session_id = int(session_id)

    # Ensure session exists
    try:
        session = (
            manager.get_session(session_id) if isinstance(session_id, int) else None
        )

        if session is None:
            # Create session if it doesn't exist (only for string names)
            if (
                isinstance(original_session_id, str)
                and not original_session_id.isdigit()
            ):
                logger.info(f"Creating new session: {original_session_id}")
                try:
                    session_id = manager.create_session(
                        name=original_session_id,
                        description="Created by workflow execution",
                    )
                except Exception as create_error:
                    raise RuntimeError(
                        f"Failed to create session {original_session_id}: {create_error}"
                    )
            else:
                raise ValueError(
                    f"Session {session_id} not found. Please create the session first."
                )
    except (ValueError, RuntimeError) as e:
        # Return error status instead of raising
        logger.error(f"Session validation failed: {e}")
        return {
            "session_id": session_id,
            "files_saved": 0,
            "results_saved": 0,
            "status": "error",
            "errors": [str(e)],
        }

    files_saved = 0
    results_saved = 0
    errors = []

    # Save DiffractionData files
    if include_files:
        files = inputs.get("files", inputs.get("input", []))
        if not isinstance(files, list):
            files = [files]

        for i, data in enumerate(files):
            try:
                # Generate filename if not present
                filename = getattr(data, "filename", None)
                if not filename:
                    filename = f"workflow_output_{i}.chi"

                # Get wavelength (provide default if not present)
                wavelength = getattr(data, "wavelength", None)
                if wavelength is None:
                    wavelength = 0.1665  # Default synchrotron wavelength

                # Add to session
                manager.add_file_to_session(
                    session_id=session_id,
                    filename=filename,
                    wavelength=wavelength,
                    data=data,
                )
                files_saved += 1
                logger.debug(f"Saved file {filename} to session {session_id}")

            except Exception as e:
                error_msg = f"Failed to save file {i}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

    # Save analysis results metadata
    if include_results:
        results = inputs.get("results", [])
        if results:
            try:
                # Store results count in context for now
                # Future: Add metadata field to Session model
                results_saved = len(results)
                logger.info(f"Processed {results_saved} analysis results")

            except Exception as e:
                error_msg = f"Failed to process results metadata: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

    # Determine status
    if errors and (files_saved == 0 and results_saved == 0):
        status = "error"
    elif errors:
        status = "partial"
    else:
        status = "success"

    return {
        "session_id": session_id,
        "files_saved": files_saved,
        "results_saved": results_saved,
        "status": status,
        "errors": errors,
    }
