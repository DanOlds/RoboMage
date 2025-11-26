"""
Workflow Builder Callbacks

Handles workflow creation, execution, and management in the dashboard.
Integrates with the workflow service (port 8002).
"""

import json
import logging
from typing import Any

import requests
from dash import Input, Output, State, callback_context, html, no_update
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

logger = logging.getLogger(__name__)

WORKFLOW_SERVICE_URL = "http://localhost:8002"


def register_callbacks(app):
    """Register all workflow-related callbacks."""
    register_service_health_callback(app)
    register_node_palette_callback(app)
    register_workflow_management_callbacks(app)
    register_execution_callbacks(app)
    register_saved_workflows_callback(app)


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
                                        node["description"], className="text-muted d-block"
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
                return (
                    None,
                    dbc.Alert(
                        f"Execution failed: {exec_response.text}",
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
                                        html.Strong(f"{i+1}. {nr['node_id']}: "),
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
                                            html.Strong("Error: ", className="text-danger"),
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
    """Display list of saved workflows."""

    @app.callback(
        Output("saved-workflows-list", "children"),
        Input("workflow-service-check-interval", "n_intervals"),
    )
    def load_saved_workflows(n_intervals):
        """Fetch and display saved workflows."""
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
                                        html.Strong(wf["name"]),
                                        dbc.Badge(
                                            f"{len(wf['nodes'])} nodes",
                                            color="info",
                                            className="ms-2",
                                        ),
                                    ]
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
                        style={"cursor": "pointer"},
                        id={"type": "saved-workflow-item", "workflow_id": wf["id"]},
                    )
                    for wf in workflows
                ]

        except Exception as e:
            logger.debug(f"Failed to load saved workflows: {e}")
            return html.P("Unable to load workflows", className="text-muted")
