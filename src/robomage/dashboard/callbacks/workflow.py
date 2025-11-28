"""
Workflow Builder Callbacks

Handles workflow creation, execution, and management in the dashboard.
Integrates with the workflow service (port 8002).
"""

import json
import logging

import dash_bootstrap_components as dbc
import requests
from dash import ALL, Input, Output, State, callback_context, html, no_update
from dash.exceptions import PreventUpdate

logger = logging.getLogger(__name__)

WORKFLOW_SERVICE_URL = "http://localhost:8002"


def register_callbacks(app):
    """Register all workflow-related callbacks."""
    register_service_health_callback(app)
    register_node_palette_callback(app)
    register_workflow_management_callbacks(app)
    register_execution_callbacks(app)
    register_saved_workflows_callback(app)
    register_session_integration_callback(app)


def register_service_health_callback(app):
    """Check workflow service health and update status indicator."""

    @app.callback(
        Output("workflow-service-status", "children"),
        Input("workflow-service-check-interval", "n_intervals"),
    )
    def check_service_health(n_intervals):
        """Check if workflow service is running."""
        try:
            response = requests.get(f"{WORKFLOW_SERVICE_URL}/health", timeout=2)
            if response.status_code == 200:
                data = response.json()
                return dbc.Alert(
                    [
                        html.I(className="fas fa-check-circle me-2"),
                        f"Workflow service connected ({data['workflows_count']} workflows, "
                        f"{data['node_types_registered']} node types)",
                    ],
                    color="success",
                    className="mb-0 py-2",
                )
        except Exception as e:
            logger.debug(f"Workflow service not available: {e}")

        return dbc.Alert(
            [
                html.I(className="fas fa-exclamation-triangle me-2"),
                "Workflow service not available. Start with: ",
                html.Code(
                    "pixi run python services/workflow_engine/main.py --port 8002",
                    className="ms-1",
                ),
            ],
            color="warning",
            className="mb-0 py-2",
        )


def register_node_palette_callback(app):
    """Load and display available node types from service."""

    @app.callback(
        Output("workflow-node-palette", "children"),
        Input("workflow-service-check-interval", "n_intervals"),
    )
    def load_node_palette(n_intervals):
        """Fetch node types from workflow service and create palette."""
        try:
            response = requests.get(f"{WORKFLOW_SERVICE_URL}/node-types", timeout=2)
            if response.status_code == 200:
                node_types = response.json()
                return create_node_palette_ui(node_types)
        except Exception as e:
            logger.debug(f"Failed to load node types: {e}")

        return html.P("Node types unavailable", className="text-muted")

    @app.callback(
        Output("workflow-templates", "children"),
        Input("workflow-service-check-interval", "n_intervals"),
    )
    def load_workflow_templates(n_intervals):
        """Create quick start workflow templates."""
        templates = [
            {
                "name": "Peak Analysis",
                "icon": "fa-mountain",
                "description": "Load files → Detect peaks → Export CSV",
            },
            {
                "name": "Batch Processing",
                "icon": "fa-list",
                "description": "Load files → Filter → Normalize → Export",
            },
            {
                "name": "Statistics Report",
                "icon": "fa-chart-bar",
                "description": "Load files → Calculate stats → Export JSON",
            },
        ]

        return [
            dbc.Card(
                dbc.CardBody(
                    [
                        html.Div(
                            [
                                html.I(className=f"fas {t['icon']} me-2"),
                                html.Strong(t["name"]),
                            ]
                        ),
                        html.Small(t["description"], className="text-muted"),
                    ],
                    className="py-2",
                ),
                className="mb-2 cursor-pointer",
                style={"cursor": "pointer"},
                id={"type": "workflow-template", "index": i},
            )
            for i, t in enumerate(templates)
        ]


def create_node_palette_ui(node_types: list[dict]) -> list:
    """Create UI for node palette organized by category."""
    # Group nodes by category
    categories = {}
    for node in node_types:
        category = node.get("category", "other")
        if category not in categories:
            categories[category] = []
        categories[category].append(node)

    # Category display names and order
    category_info = {
        "data": {"name": "Data Input", "icon": "fa-database"},
        "transform": {"name": "Transform", "icon": "fa-exchange-alt"},
        "analysis": {"name": "Analysis", "icon": "fa-microscope"},
        "output": {"name": "Output", "icon": "fa-file-export"},
    }

    palette = []
    for cat_key in ["data", "transform", "analysis", "output"]:
        if cat_key not in categories:
            continue

        info = category_info.get(cat_key, {"name": cat_key, "icon": "fa-cube"})
        nodes = categories[cat_key]

        palette.append(
            html.Div(
                [
                    html.H6(
                        [
                            html.I(className=f"fas {info['icon']} me-2"),
                            info["name"],
                        ],
                        className="text-primary mt-3 mb-2",
                    ),
                    *[
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div(
                                        [
                                            html.I(
                                                className=f"{node.get('icon', 'fas fa-cube')} me-2"
                                            ),
                                            html.Strong(node["name"]),
                                        ]
                                    ),
                                    html.Small(
                                        node["description"],
                                        className="text-muted d-block",
                                    ),
                                ],
                                className="py-2",
                            ),
                            className="mb-2 node-palette-item",
                            style={"cursor": "pointer"},
                            id={"type": "node-palette-item", "node_type": node["type"]},
                        )
                        for node in nodes
                    ],
                ]
            )
        )

    return palette


def register_workflow_management_callbacks(app):
    """Callbacks for saving, loading, and creating workflows."""

    @app.callback(
        Output("current-workflow-data", "data"),
        Output("workflow-json-editor", "value"),
        Output("workflow-name-input", "value"),
        Output("workflow-description-input", "value"),
        Input("save-workflow-btn", "n_clicks"),
        Input("new-workflow-btn", "n_clicks"),
        State("workflow-json-editor", "value"),
        State("workflow-name-input", "value"),
        State("workflow-description-input", "value"),
        prevent_initial_call=True,
    )
    def manage_workflow(
        save_clicks, new_clicks, json_value, name_value, description_value
    ):
        """Handle workflow save and new operations."""
        ctx = callback_context
        if not ctx.triggered:
            raise PreventUpdate

        button_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if button_id == "save-workflow-btn":
            # Save workflow to service
            try:
                workflow_data = json.loads(json_value)
                workflow_data["name"] = name_value or "Untitled Workflow"
                workflow_data["description"] = description_value or ""

                response = requests.post(
                    f"{WORKFLOW_SERVICE_URL}/workflows",
                    json=workflow_data,
                    timeout=5,
                )

                if response.status_code == 200:
                    saved_workflow = response.json()
                    logger.info(f"Saved workflow: {saved_workflow['id']}")
                    return (
                        saved_workflow,
                        json_value,
                        name_value,
                        description_value,
                    )
            except Exception as e:
                logger.error(f"Failed to save workflow: {e}")
                return no_update, no_update, no_update, no_update

        elif button_id == "new-workflow-btn":
            # Reset to default workflow
            from robomage.dashboard.layouts.workflow_layout import (
                get_default_workflow_json,
            )

            default_json = get_default_workflow_json()
            return None, default_json, "New Workflow", ""

        raise PreventUpdate


def register_execution_callbacks(app):
    """Callbacks for workflow execution."""

    @app.callback(
        Output("workflow-execution-result", "data"),
        Output("workflow-execution-log", "children"),
        Input("execute-workflow-btn", "n_clicks"),
        State("workflow-json-editor", "value"),
        State("workflow-name-input", "value"),
        State("current-workflow-data", "data"),
        prevent_initial_call=True,
    )
    def execute_workflow(n_clicks, json_value, workflow_name, current_workflow):
        """Execute the current workflow."""
        if not n_clicks:
            raise PreventUpdate

        try:
            # Parse workflow JSON
            workflow_data = json.loads(json_value)
            workflow_data["name"] = workflow_name or "Untitled Workflow"

            # First save the workflow if not already saved
            workflow_id = None
            if current_workflow and "id" in current_workflow:
                workflow_id = current_workflow["id"]
            else:
                # Create new workflow
                response = requests.post(
                    f"{WORKFLOW_SERVICE_URL}/workflows",
                    json=workflow_data,
                    timeout=5,
                )
                if response.status_code == 200:
                    workflow_id = response.json()["id"]

            if not workflow_id:
                return (
                    None,
                    dbc.Alert(
                        "Failed to save workflow before execution",
                        color="danger",
                    ),
                )

            # Execute workflow
            logger.info(f"Executing workflow: {workflow_id}")
            exec_response = requests.post(
                f"{WORKFLOW_SERVICE_URL}/workflows/{workflow_id}/execute",
                timeout=60,  # Allow longer timeout for execution
            )

            if exec_response.status_code == 200:
                result = exec_response.json()
                return result, create_execution_log_ui(result)
            else:
                # Try to get detailed error from response
                try:
                    error_detail = exec_response.json().get(
                        "detail", exec_response.text
                    )
                except:
                    error_detail = exec_response.text

                logger.error(f"Workflow execution failed: {error_detail}")
                return (
                    None,
                    dbc.Alert(
                        [
                            html.Strong("Execution failed: "),
                            html.Br(),
                            html.Code(error_detail),
                        ],
                        color="danger",
                    ),
                )

        except json.JSONDecodeError as e:
            return (
                None,
                dbc.Alert(
                    [
                        html.Strong("Invalid JSON: "),
                        str(e),
                    ],
                    color="danger",
                ),
            )
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}", exc_info=True)
            return (
                None,
                dbc.Alert(
                    [
                        html.Strong("Execution error: "),
                        str(e),
                    ],
                    color="danger",
                ),
            )


def create_execution_log_ui(result: dict) -> html.Div:
    """Create UI for execution results."""
    status = result.get("status", "unknown")
    status_color = "success" if status == "completed" else "danger"

    node_results = result.get("node_results", [])

    return html.Div(
        [
            dbc.Alert(
                [
                    html.Strong(f"Status: {status.upper()}"),
                    html.Br(),
                    f"Execution ID: {result.get('execution_id', 'N/A')}",
                    html.Br(),
                    f"Duration: {result.get('total_duration_ms', 0):.1f} ms",
                ],
                color=status_color,
                className="mb-3",
            ),
            html.H6("Node Results:", className="mt-3"),
            html.Div(
                [
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.Div(
                                    [
                                        html.Strong(f"{i + 1}. {nr['node_id']}: "),
                                        dbc.Badge(
                                            nr["status"],
                                            color="success"
                                            if nr["status"] == "completed"
                                            else "danger",
                                            className="ms-2",
                                        ),
                                    ]
                                ),
                                html.Small(
                                    f"Duration: {nr.get('duration_ms', 0):.1f} ms",
                                    className="text-muted d-block",
                                ),
                                (
                                    html.Div(
                                        [
                                            html.Strong(
                                                "Error: ", className="text-danger"
                                            ),
                                            html.Code(nr["error"]),
                                        ],
                                        className="mt-2",
                                    )
                                    if nr.get("error")
                                    else None
                                ),
                            ],
                            className="py-2",
                        ),
                        className="mb-2",
                    )
                    for i, nr in enumerate(node_results)
                ]
            ),
            (
                html.Div(
                    [
                        html.H6("Error Details:", className="mt-3 text-danger"),
                        html.Pre(result.get("error", ""), className="bg-light p-2"),
                    ]
                )
                if result.get("error")
                else None
            ),
        ]
    )


def register_saved_workflows_callback(app):
    """Display list of saved workflows with load and delete actions."""

    @app.callback(
        Output("saved-workflows-list", "children"),
        Input("workflow-service-check-interval", "n_intervals"),
        Input({"type": "delete-workflow", "workflow_id": ALL}, "n_clicks"),
        prevent_initial_call=False,
    )
    def load_saved_workflows(n_intervals, delete_clicks):
        """Fetch and display saved workflows."""
        ctx = callback_context

        # Check if delete was triggered
        if ctx.triggered and ctx.triggered[0]["prop_id"] != ".":
            triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
            if "delete-workflow" in triggered_id:
                import json

                button_id = json.loads(triggered_id)
                workflow_id = button_id["workflow_id"]

                # Delete the workflow
                try:
                    response = requests.delete(
                        f"{WORKFLOW_SERVICE_URL}/workflows/{workflow_id}", timeout=2
                    )
                    if response.status_code == 200:
                        logger.info(f"Deleted workflow: {workflow_id}")
                except Exception as e:
                    logger.error(f"Failed to delete workflow: {e}")

        # Load and display workflows
        try:
            response = requests.get(f"{WORKFLOW_SERVICE_URL}/workflows", timeout=2)
            if response.status_code == 200:
                workflows = response.json()

                if not workflows:
                    return html.P("No saved workflows yet", className="text-muted")

                return [
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.Strong(wf["name"]),
                                                dbc.Badge(
                                                    f"{len(wf['nodes'])} nodes",
                                                    color="info",
                                                    className="ms-2",
                                                ),
                                            ],
                                            style={"flex": "1"},
                                        ),
                                        dbc.ButtonGroup(
                                            [
                                                dbc.Button(
                                                    html.I(className="fas fa-upload"),
                                                    id={
                                                        "type": "load-workflow",
                                                        "workflow_id": wf["id"],
                                                    },
                                                    color="primary",
                                                    size="sm",
                                                    title="Load workflow",
                                                ),
                                                dbc.Button(
                                                    html.I(className="fas fa-trash"),
                                                    id={
                                                        "type": "delete-workflow",
                                                        "workflow_id": wf["id"],
                                                    },
                                                    color="danger",
                                                    size="sm",
                                                    title="Delete workflow",
                                                ),
                                            ],
                                            size="sm",
                                        ),
                                    ],
                                    className="d-flex justify-content-between align-items-center",
                                ),
                                (
                                    html.Small(
                                        wf["description"],
                                        className="text-muted d-block mt-1",
                                    )
                                    if wf.get("description")
                                    else None
                                ),
                                html.Small(
                                    f"ID: {wf['id'][:8]}...",
                                    className="text-muted d-block",
                                ),
                            ],
                            className="py-2",
                        ),
                        className="mb-2",
                    )
                    for wf in workflows
                ]

        except Exception as e:
            logger.debug(f"Failed to load saved workflows: {e}")
            return html.P("Unable to load workflows", className="text-muted")

    @app.callback(
        Output("workflow-json-input", "value", allow_duplicate=True),
        Output("workflow-load-feedback", "children", allow_duplicate=True),
        Input({"type": "load-workflow", "workflow_id": ALL}, "n_clicks"),
        State({"type": "load-workflow", "workflow_id": ALL}, "id"),
        prevent_initial_call=True,
    )
    def load_workflow_into_editor(n_clicks_list, button_ids):
        """Load a saved workflow into the JSON editor."""
        ctx = callback_context
        if not ctx.triggered:
            return no_update, no_update

        # Find which button was clicked
        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if triggered_id == "":
            return no_update, no_update

        import json

        button_id = json.loads(triggered_id)
        workflow_id = button_id["workflow_id"]

        try:
            # Fetch the workflow
            response = requests.get(
                f"{WORKFLOW_SERVICE_URL}/workflows/{workflow_id}", timeout=2
            )

            if response.status_code == 200:
                workflow = response.json()
                workflow_json = json.dumps(workflow, indent=2)

                feedback = dbc.Alert(
                    [
                        html.I(className="fas fa-check-circle me-2"),
                        f"Loaded workflow: {workflow['name']}",
                    ],
                    color="success",
                    dismissable=True,
                    duration=3000,
                )

                return workflow_json, feedback
            else:
                return no_update, dbc.Alert(
                    f"Failed to load workflow: {response.status_code}",
                    color="danger",
                    dismissable=True,
                )

        except Exception as e:
            logger.error(f"Error loading workflow: {e}")
            return no_update, dbc.Alert(
                f"Error: {str(e)}",
                color="danger",
                dismissable=True,
            )


def register_session_integration_callback(app):
    """Save workflow execution results to active session."""

    @app.callback(
        Output("save-to-session-alert", "children"),
        Output("save-to-session-alert", "is_open"),
        Output("file-data-store", "data", allow_duplicate=True),
        Output("wavelength-store", "data", allow_duplicate=True),
        Output("analysis-results-store", "data", allow_duplicate=True),
        Input("save-results-to-session-btn", "n_clicks"),
        State("workflow-execution-result", "data"),
        State("current-session-id", "data"),
        prevent_initial_call=True,
    )
    def save_workflow_results_to_session(
        n_clicks, execution_results, current_session_id
    ):
        """
        Extract workflow execution results and save to active session.

        This allows users to run a workflow and immediately visualize
        results in the Visualization tab without manual export/import.

        Also extracts peak analysis results if available.

        Returns:
            Tuple of (alert, is_open, file_data, wavelength_data, analysis_results)
        """
        import dash

        if not execution_results:
            return (
                dbc.Alert(
                    "No execution results to save",
                    color="warning",
                    className="mb-0 py-2",
                ),
                True,
                dash.no_update,
                dash.no_update,
                dash.no_update,
            )

        if not current_session_id:
            return (
                dbc.Alert(
                    "No active session. Please load or create a session first.",
                    color="warning",
                    className="mb-0 py-2",
                ),
                True,
                dash.no_update,
                dash.no_update,
                dash.no_update,
            )

        session_id = current_session_id

        # Debug logging
        logger.info(f"Save to session called - session_id: {session_id}")
        logger.info(
            f"Execution results structure: {list(execution_results.keys()) if execution_results else 'None'}"
        )

        try:
            from robomage.data.models import DiffractionData
            from robomage.persistence.api import SessionManager

            manager = SessionManager()

            files_saved = 0
            errors = []
            analysis_results = {}  # Store peak analysis results by filename

            # Extract node results directly from execution results
            # The API returns WorkflowExecutionResult which has node_results at top level
            node_results = execution_results.get("node_results", [])

            logger.info(f"Found {len(node_results)} node results")
            logger.info(f"Execution status: {execution_results.get('status')}")
            print(f"\n🔍 WORKFLOW SAVE: Processing {len(node_results)} node results")

            # Look for DiffractionData in node outputs
            for node_result in node_results:
                node_id = node_result.get("node_id")
                node_type = node_result.get("node_type")  # Get node type
                output = node_result.get("output")
                status = node_result.get("status")

                print(
                    f"🔍 Node: id={node_id}, type={node_type}, status={status}, output_type={type(output).__name__}"
                )
                logger.info(
                    f"Node {node_id} ({node_type}): status={status}, output type={type(output).__name__}"
                )

                # Log more detail about output structure
                if isinstance(output, list) and len(output) > 0:
                    logger.info(f"  First item type: {type(output[0]).__name__}")
                    if isinstance(output[0], dict):
                        logger.info(f"  First item keys: {list(output[0].keys())}")
                elif isinstance(output, dict):
                    logger.info(f"  Output dict keys: {list(output.keys())}")

                # Skip failed nodes
                if status != "completed":
                    logger.info(f"  Skipping {node_id} - status is {status}")
                    continue

                # Extract peak analysis results from peak_analysis nodes
                if node_type in ("peak_detection", "peak_analysis"):
                    print(
                        f"🔍 Found peak analysis node: {node_id}, output type: {type(output)}"
                    )
                    logger.info(f"Found peak analysis node: {node_id}")
                    logger.info(f"  Output type: {type(output)}")

                    # peak_analysis_handler returns a list of result dicts
                    if isinstance(output, list):
                        logger.info(f"  Processing {len(output)} analysis results")
                        for result in output:
                            if isinstance(result, dict) and "filename" in result:
                                filename = result["filename"]

                                # Convert workflow format to analysis-results-store format
                                # Workflow format: {"filename": ..., "peaks_detected": ..., "peak_list": [...]}
                                # Analysis tab expects full PeakAnalysisClient response format
                                # Need to include "peaks", "metadata", etc.

                                # Reconstruct the expected format
                                peaks = []
                                for peak in result.get("peak_list", []):
                                    peaks.append(
                                        {
                                            "position": peak.get("position"),
                                            "height": peak.get("height"),
                                            "width": peak.get("width"),
                                            "area": peak.get("area"),
                                            "d_spacing": peak.get("d_spacing"),
                                            "r_squared": peak.get("r_squared", 0.0),
                                        }
                                    )

                                analysis_results[filename] = {
                                    "filename": filename,
                                    "peaks": peaks,
                                    "metadata": {
                                        "num_peaks_detected": result.get(
                                            "peaks_detected", len(peaks)
                                        ),
                                        "num_peaks_fitted": result.get(
                                            "peaks_fitted", len(peaks)
                                        ),
                                        "overall_r_squared": result.get(
                                            "overall_r_squared", 0.0
                                        ),
                                    },
                                }
                                logger.info(
                                    f"  ✅ Added analysis for {filename} ({len(peaks)} peaks)"
                                )
                                print(
                                    f"  ✅ Added analysis for {filename} ({len(peaks)} peaks)"
                                )

                    # Also handle dict format (if output is already keyed by filename)
                    elif isinstance(output, dict):
                        if "peaks" in output or "filename" in output:
                            # Single file result
                            filename = output.get("filename", "unknown.chi")
                            analysis_results[filename] = output
                            logger.info(
                                f"  ✅ Added analysis for {filename} (dict format)"
                            )
                        else:
                            # Multiple files (dict of results)
                            for key, value in output.items():
                                if isinstance(value, dict) and (
                                    "peaks" in value or "peak_list" in value
                                ):
                                    analysis_results[key] = value
                                    logger.info(f"  ✅ Added analysis for {key}")

                # Handle different output types
                if isinstance(output, list):
                    logger.info(
                        f"Node {node_id} has list output with {len(output)} items"
                    )
                    for i, item in enumerate(output):
                        item_type = type(item).__name__
                        has_q = isinstance(item, dict) and "q_values" in item
                        logger.info(
                            f"  Item {i}: type={item_type}, has q_values={has_q}"
                        )
                        if isinstance(item, dict):
                            logger.info(f"    Keys: {list(item.keys())[:10]}")

                        # Check if this looks like DiffractionData dict
                        if isinstance(item, dict) and "q_values" in item:
                            try:
                                # Convert lists to numpy arrays (JSON serialization converts arrays to lists)
                                import numpy as np

                                item_copy = item.copy()
                                if isinstance(item_copy.get("q_values"), list):
                                    item_copy["q_values"] = np.array(
                                        item_copy["q_values"]
                                    )
                                if isinstance(item_copy.get("intensities"), list):
                                    item_copy["intensities"] = np.array(
                                        item_copy["intensities"]
                                    )

                                # Reconstruct DiffractionData from dict
                                data = DiffractionData(**item_copy)

                                filename = item.get(
                                    "filename", f"{node_id}_output_{i}.chi"
                                )
                                # Use default wavelength if None or missing
                                wavelength = item.get("wavelength") or 0.1665

                                file_obj = manager.add_file_to_session(
                                    session_id=session_id,
                                    filename=filename,
                                    wavelength=wavelength,
                                    data=data,
                                )
                                files_saved += 1
                                logger.info(
                                    f"  ✅ Saved {filename} to session {session_id}"
                                )

                                # Sprint 7: Save analysis results to database if we have them for this file
                                if filename in analysis_results:
                                    try:
                                        result_data = analysis_results[filename]
                                        # Extract parameters from workflow execution if available
                                        # (in future could pass from workflow node)
                                        parameters = {
                                            "source": "workflow",
                                            "node_id": node_id,
                                        }
                                        # Extract quality metrics from result
                                        quality_metrics = {
                                            "overall_r_squared": result_data.get(
                                                "metadata", {}
                                            ).get("overall_r_squared", 0.0)
                                        }

                                        manager.save_analysis_result(
                                            file_id=file_obj.id,
                                            analysis_type="peak_detection",
                                            result_data=result_data,
                                            parameters=parameters,
                                            quality_metrics=quality_metrics,
                                            analysis_version="robomage-workflow-0.1.0",
                                        )
                                        logger.info(
                                            f"  ✅ Saved peak analysis results for {filename} to database"
                                        )
                                        print(
                                            f"  ✅ Saved peak analysis results for {filename} to database"
                                        )
                                    except Exception as db_error:
                                        logger.warning(
                                            f"  ⚠️ Could not save analysis results for {filename}: {db_error}"
                                        )

                            except Exception as e:
                                error_msg = (
                                    f"Failed to save {node_id} output {i}: {str(e)}"
                                )
                                logger.error(error_msg, exc_info=True)
                                errors.append(error_msg)

            # Sprint 7: Save analysis results for existing files in session (not just new files from output)
            # This handles workflows that run peak analysis on already-loaded files
            if analysis_results:
                try:
                    session_files = manager.get_session_files(session_id)
                    logger.info(
                        f"🔍 Checking {len(analysis_results)} analysis results against {len(session_files)} session files"
                    )

                    for session_file in session_files:
                        try:
                            diffraction = manager.file_store.load_file(
                                session_file.stored_path
                            )
                            if diffraction is None:
                                continue

                            filename = diffraction.filename or "unknown.chi"

                            # If we have analysis results for this file, save them
                            if filename in analysis_results:
                                # Check if we already saved this (from file creation above)
                                existing_analysis = manager.get_latest_analysis(
                                    file_id=session_file.id,
                                    analysis_type="peak_detection",
                                )

                                # Only save if no analysis exists or if it's different
                                # (Simple check: if existing analysis has different peak count, it's different)
                                should_save = True
                                if existing_analysis:
                                    existing_peak_count = len(
                                        existing_analysis.result_data.get("peaks", [])
                                    )
                                    new_peak_count = len(
                                        analysis_results[filename].get("peaks", [])
                                    )
                                    if existing_peak_count == new_peak_count:
                                        should_save = False
                                        logger.info(
                                            f"  ℹ️ Analysis for {filename} already in database (skipping)"
                                        )

                                if should_save:
                                    result_data = analysis_results[filename]
                                    parameters = {
                                        "source": "workflow",
                                        "workflow_type": "existing_files",
                                    }
                                    quality_metrics = {
                                        "overall_r_squared": result_data.get(
                                            "metadata", {}
                                        ).get("overall_r_squared", 0.0)
                                    }

                                    manager.save_analysis_result(
                                        file_id=session_file.id,
                                        analysis_type="peak_detection",
                                        result_data=result_data,
                                        parameters=parameters,
                                        quality_metrics=quality_metrics,
                                        analysis_version="robomage-workflow-0.1.0",
                                    )
                                    logger.info(
                                        f"  ✅ Saved peak analysis for existing file {filename} to database"
                                    )
                                    print(
                                        f"  ✅ Saved peak analysis for existing file {filename} to database"
                                    )
                        except Exception as file_error:
                            logger.warning(
                                f"  ⚠️ Could not process analysis for {session_file.filename}: {file_error}"
                            )
                            continue

                except Exception as analysis_save_error:
                    logger.warning(
                        f"Could not save analysis results for existing files: {analysis_save_error}"
                    )

            # Build alert message
            if files_saved > 0:
                # Reload session data to refresh UI
                try:
                    session = manager.get_session(session_id)
                    session_files = manager.get_session_files(session_id)

                    # Reconstruct file data (same as load_session callback)
                    file_data = {}
                    loaded_wavelength = 0.1665

                    for session_file in session_files:
                        diffraction = manager.file_store.load_file(
                            session_file.stored_path
                        )
                        if diffraction is None:
                            continue

                        if not file_data:  # First file
                            loaded_wavelength = session_file.wavelength or 0.1665

                        filename = diffraction.filename or "unknown.chi"
                        file_info = {
                            "filename": filename,
                            "q": diffraction.q_values.tolist(),
                            "intensity": diffraction.intensities.tolist(),
                            "metadata": {},
                            "num_points": len(diffraction.q_values),
                            "q_range": [
                                float(diffraction.q_values.min()),
                                float(diffraction.q_values.max()),
                            ],
                            "intensity_range": [
                                float(diffraction.intensities.min()),
                                float(diffraction.intensities.max()),
                            ],
                        }
                        file_data[filename] = file_info

                    wavelength_data = {
                        "current_wavelength": loaded_wavelength,
                        "source_type": "standard",
                    }

                except Exception as reload_error:
                    logger.warning(f"Could not reload session data: {reload_error}")
                    file_data = dash.no_update
                    wavelength_data = dash.no_update

                message = (
                    f"✅ Successfully saved {files_saved} file(s) to session. "
                    f"Data refreshed in Visualization tab."
                )
                if analysis_results:
                    message += (
                        f" Found {len(analysis_results)} peak analysis result(s)."
                    )
                if errors:
                    message += f" Note: {len(errors)} item(s) could not be saved."
                color = "success"
            else:
                logger.warning(
                    f"No diffraction data found. Node results: {len(node_results)}, Errors: {len(errors)}"
                )
                message = "⚠️ No diffraction data found in workflow results to save."
                if errors:
                    message += f" Errors: {'; '.join(errors[:3])}"
                color = "warning"
                file_data = dash.no_update
                wavelength_data = dash.no_update
                # Still return analysis results even if no files
                # (workflow might have only peak detection on existing data)

            print(
                f"🔍 WORKFLOW SAVE COMPLETE: {files_saved} files, {len(analysis_results)} analysis results"
            )
            return (
                dbc.Alert(message, color=color, className="mb-0 py-2"),
                True,
                file_data,
                wavelength_data,
                analysis_results if analysis_results else dash.no_update,
            )

        except Exception as e:
            logger.error(f"Error saving workflow results to session: {e}")
            return (
                dbc.Alert(
                    f"❌ Error: {str(e)}",
                    color="danger",
                    className="mb-0 py-2",
                ),
                True,
                dash.no_update,
                dash.no_update,
                dash.no_update,
            )
