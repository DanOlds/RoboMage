"""
Workflow Builder Callbacks

Handles workflow creation, execution, and management in the dashboard.
Integrates with the workflow service using the service registry.
"""

import json
import logging

import dash_bootstrap_components as dbc
import requests
from dash import ALL, Input, Output, State, callback_context, html, no_update
from dash.exceptions import PreventUpdate

from robomage.dashboard.components.service_monitor import check_service_health
from robomage.service_registry import ServiceRegistry

logger = logging.getLogger(__name__)


def get_workflow_service_url() -> str:
    """Get workflow service URL from registry.
    
    Returns:
        Workflow service base URL or default if registry fails
    """
    try:
        registry = ServiceRegistry()
        registry.load_registry()
        service = registry.get_service("workflow_engine")
        return service.get_base_url()
    except Exception as e:
        logger.warning(f"Failed to get workflow service from registry: {e}")
        return "http://localhost:8002"  # Fallback


WORKFLOW_SERVICE_URL = get_workflow_service_url()


def register_callbacks(app):
    """Register all workflow-related callbacks."""
    register_service_health_callback(app)
    register_node_palette_callback(app)
    register_workflow_management_callbacks(app)
    register_execution_callbacks(app)
    register_saved_workflows_callback(app)
    register_session_integration_callback(app)
    # Sprint 8: Visual workflow builder callbacks
    register_visual_workflow_callbacks(app)


def register_service_health_callback(app):
    """Check workflow service health using service registry."""

    @app.callback(
        Output("workflow-service-status", "children"),
        Input("workflow-service-check-interval", "n_intervals"),
    )
    def check_workflow_service_health(n_intervals):
        """Check if workflow service is running using service registry."""
        try:
            # Load service metadata from registry
            registry = ServiceRegistry()
            registry.load_registry()
            service = registry.get_service("workflow_engine")

            # Check service health
            health_result = check_service_health(service, timeout=2.0)

            if health_result["is_connected"]:
                data = health_result["status_data"]
                return dbc.Alert(
                    [
                        html.I(className="fas fa-check-circle me-2"),
                        f"Workflow service connected ({data.get('workflows_count', 0)} workflows, "
                        f"{data.get('node_types_registered', 0)} node types)",
                    ],
                    color="success",
                    className="mb-0 py-2",
                )
        except Exception as e:
            logger.debug(f"Workflow service not available: {e}")

        # Get startup command from registry
        try:
            registry = ServiceRegistry()
            registry.load_registry()
            service = registry.get_service("workflow_engine")
            startup_cmd = service.format_startup_command()
        except Exception:
            startup_cmd = "pixi run python services/workflow_engine/main.py --port 8002"

        return dbc.Alert(
            [
                html.I(className="fas fa-exclamation-triangle me-2"),
                "Workflow service not available. Start with: ",
                html.Code(
                    startup_cmd,
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
                        dbc.Button(
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
                                    className="text-muted d-block mt-1",
                                ),
                            ],
                            id={"type": "node-palette-item", "node_type": node["type"]},
                            color="light",
                            className="mb-2 text-start w-100",
                            style={
                                "whiteSpace": "normal",
                                "height": "auto",
                                "padding": "0.75rem",
                            },
                        )
                        for node in nodes
                    ],
                ]
            )
        )

    return palette


def register_workflow_management_callbacks(app):
    """Callbacks for saving, loading, and creating workflows."""

    # Toggle Load Workflow Modal
    @app.callback(
        Output("load-workflow-modal", "is_open"),
        [
            Input("load-workflow-btn", "n_clicks"),
            Input("load-workflow-modal-cancel", "n_clicks"),
        ],
        [State("load-workflow-modal", "is_open")],
        prevent_initial_call=True,
    )
    def toggle_load_workflow_modal(load_clicks, cancel_clicks, is_open):
        """Toggle load workflow modal."""
        ctx = callback_context
        if not ctx.triggered:
            raise PreventUpdate

        button_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if button_id == "load-workflow-btn":
            # Open modal
            return True
        elif button_id == "load-workflow-modal-cancel":
            # Close modal
            return False

        raise PreventUpdate

    # Populate Load Workflow Modal with saved workflows
    @app.callback(
        Output("load-workflow-list-container", "children"),
        [Input("load-workflow-modal", "is_open")],
        prevent_initial_call=False,
    )
    def populate_load_workflow_list(is_open):
        """Fetch and display saved workflows in load modal."""
        if not is_open:
            raise PreventUpdate

        try:
            response = requests.get(f"{WORKFLOW_SERVICE_URL}/workflows", timeout=2)
            if response.status_code == 200:
                workflows = response.json()

                if not workflows:
                    return dbc.Alert(
                        "No saved workflows found. Create and save a workflow first.",
                        color="info",
                    )

                # Create clickable cards for each workflow
                workflow_cards = []
                for wf in workflows:
                    card = dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    html.H6(
                                                        wf["name"], className="mb-1"
                                                    ),
                                                    html.Small(
                                                        wf.get("description", ""),
                                                        className="text-muted",
                                                    ),
                                                ],
                                                width=9,
                                            ),
                                            dbc.Col(
                                                [
                                                    dbc.Badge(
                                                        f"{len(wf['nodes'])} nodes",
                                                        color="info",
                                                    )
                                                ],
                                                width=3,
                                                className="text-end",
                                            ),
                                        ]
                                    ),
                                    dbc.Button(
                                        [
                                            html.I(className="fas fa-upload me-2"),
                                            "Load This Workflow",
                                        ],
                                        id={
                                            "type": "load-workflow-from-modal",
                                            "workflow_id": wf["id"],
                                        },
                                        color="primary",
                                        size="sm",
                                        className="mt-2 w-100",
                                    ),
                                ]
                            )
                        ],
                        className="mb-2",
                    )
                    workflow_cards.append(card)

                return workflow_cards

        except requests.exceptions.RequestException:
            return dbc.Alert(
                "Could not connect to workflow service. Please ensure it is running.",
                color="danger",
            )

    # Load workflow from modal into canvas
    @app.callback(
        Output("current-workflow-data", "data", allow_duplicate=True),
        Output("workflow-name-input", "value", allow_duplicate=True),
        Output("workflow-description-input", "value", allow_duplicate=True),
        Output("load-workflow-modal", "is_open", allow_duplicate=True),
        Output("load-workflow-modal-feedback", "children"),
        Input({"type": "load-workflow-from-modal", "workflow_id": ALL}, "n_clicks"),
        State({"type": "load-workflow-from-modal", "workflow_id": ALL}, "id"),
        prevent_initial_call=True,
    )
    def load_workflow_from_modal(n_clicks_list, button_ids):
        """Load selected workflow from modal into canvas."""
        ctx = callback_context
        if not ctx.triggered:
            raise PreventUpdate

        # Check if any button was actually clicked (not just rendered)
        if not any(n_clicks_list) or all(clicks is None for clicks in n_clicks_list):
            raise PreventUpdate

        # Find which button was clicked
        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if triggered_id == "":
            raise PreventUpdate

        import json as json_lib

        button_id = json_lib.loads(triggered_id)
        workflow_id = button_id["workflow_id"]

        try:
            response = requests.get(
                f"{WORKFLOW_SERVICE_URL}/workflows/{workflow_id}", timeout=2
            )

            if response.status_code == 200:
                workflow = response.json()
                return (
                    workflow,
                    workflow.get("name", "Loaded Workflow"),
                    workflow.get("description", ""),
                    False,  # Close modal
                    dbc.Alert(
                        f"Loaded workflow: {workflow['name']}",
                        color="success",
                        duration=3000,
                    ),
                )
            else:
                return (
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    dbc.Alert(
                        f"Failed to load workflow: {response.status_code}",
                        color="danger",
                    ),
                )

        except Exception as e:
            logger.error(f"Error loading workflow: {e}")
            return (
                no_update,
                no_update,
                no_update,
                no_update,
                dbc.Alert(f"Error: {str(e)}", color="danger"),
            )

    # Toggle Save Workflow Modal
    @app.callback(
        Output("save-workflow-modal", "is_open"),
        [
            Input("save-workflow-btn", "n_clicks"),
            Input("save-workflow-modal-cancel", "n_clicks"),
            Input("save-workflow-modal-confirm", "n_clicks"),
        ],
        [State("save-workflow-modal", "is_open")],
        prevent_initial_call=True,
    )
    def toggle_save_workflow_modal(save_clicks, cancel_clicks, confirm_clicks, is_open):
        """Toggle save workflow modal."""
        ctx = callback_context
        if not ctx.triggered:
            raise PreventUpdate

        button_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if button_id == "save-workflow-btn":
            # Open modal
            return True
        elif button_id in ["save-workflow-modal-cancel", "save-workflow-modal-confirm"]:
            # Close modal
            return False

        raise PreventUpdate

    # Populate save modal with current workflow metadata
    @app.callback(
        Output("save-workflow-name-input", "value"),
        Output("save-workflow-description-input", "value"),
        Input("save-workflow-modal", "is_open"),
        State("workflow-name-input", "value"),
        State("workflow-description-input", "value"),
        prevent_initial_call=False,
    )
    def populate_save_modal(is_open, current_name, current_description):
        """Pre-fill save modal with current workflow metadata."""
        if not is_open:
            raise PreventUpdate
        return current_name or "My Workflow", current_description or ""

    # Save workflow from modal
    @app.callback(
        Output("current-workflow-data", "data", allow_duplicate=True),
        Output("save-workflow-modal-feedback", "children"),
        Input("save-workflow-modal-confirm", "n_clicks"),
        State("save-workflow-name-input", "value"),
        State("save-workflow-description-input", "value"),
        State("current-workflow-data", "data"),
        prevent_initial_call=True,
    )
    def save_workflow_from_modal(
        n_clicks, name_value, description_value, workflow_data
    ):
        """Save workflow from modal to service."""
        if not n_clicks:
            raise PreventUpdate

        if not name_value or name_value.strip() == "":
            return no_update, dbc.Alert(
                "Workflow name is required!", color="danger", duration=3000
            )

        if not workflow_data or not workflow_data.get("nodes"):
            return no_update, dbc.Alert(
                "Cannot save empty workflow!", color="danger", duration=3000
            )

        try:
            # Update workflow metadata
            workflow_to_save = workflow_data.copy()
            workflow_to_save["name"] = name_value.strip()
            workflow_to_save["description"] = description_value or ""

            response = requests.post(
                f"{WORKFLOW_SERVICE_URL}/workflows",
                json=workflow_to_save,
                timeout=5,
            )

            if response.status_code == 200:
                saved_workflow = response.json()
                logger.info(f"Saved workflow: {saved_workflow['id']}")
                return saved_workflow, dbc.Alert(
                    [
                        html.I(className="fas fa-check-circle me-2"),
                        f"Workflow '{name_value}' saved successfully!",
                    ],
                    color="success",
                    duration=3000,
                )
            else:
                return no_update, dbc.Alert(
                    f"Failed to save workflow: {response.status_code}",
                    color="danger",
                    duration=3000,
                )

        except Exception as e:
            logger.error(f"Failed to save workflow: {e}")
            return no_update, dbc.Alert(
                f"Error: {str(e)}", color="danger", duration=3000
            )

    # Handle New Workflow button
    @app.callback(
        Output("current-workflow-data", "data", allow_duplicate=True),
        Output("workflow-name-input", "value", allow_duplicate=True),
        Output("workflow-description-input", "value", allow_duplicate=True),
        Input("new-workflow-btn", "n_clicks"),
        prevent_initial_call=True,
    )
    def new_workflow(n_clicks):
        """Reset to default workflow."""
        if not n_clicks:
            raise PreventUpdate

        from robomage.dashboard.layouts.workflow_layout import get_default_workflow

        default_workflow = get_default_workflow()
        return default_workflow, "New Workflow", ""


def register_execution_callbacks(app):
    """Callbacks for workflow execution."""

    @app.callback(
        Output("workflow-execution-result", "data"),
        Output("workflow-execution-log", "children"),
        Input("execute-workflow-btn", "n_clicks"),
        State("current-workflow-data", "data"),
        State("workflow-name-input", "value"),
        prevent_initial_call=True,
    )
    def execute_workflow(n_clicks, current_workflow, workflow_name):
        """Execute the current workflow."""
        if not n_clicks:
            raise PreventUpdate

        if not current_workflow or not current_workflow.get("nodes"):
            return (
                None,
                dbc.Alert(
                    "Cannot execute empty workflow. Add nodes to the canvas first.",
                    color="warning",
                ),
            )

        try:
            # Use workflow data directly from store
            workflow_data = current_workflow.copy()
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

            # Execute workflow with inspection enabled
            logger.info(f"Executing workflow: {workflow_id}")
            exec_response = requests.post(
                f"{WORKFLOW_SERVICE_URL}/workflows/{workflow_id}/execute",
                params={"enable_inspection": True},  # Enable inspection for debugging
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
                except Exception:
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


def register_visual_workflow_callbacks(app):
    """
    Register callbacks for Sprint 8 visual workflow builder.

    Handles:
    - Storing node type metadata from service
    - Adding nodes to canvas via palette clicks
    - Node selection and properties panel
    - Configuration updates
    - Canvas interactions (delete, validation)
    - Workflow state synchronization
    """

    @app.callback(
        Output("node-types-data", "data"),
        Input("workflow-service-check-interval", "n_intervals"),
    )
    def store_node_types(n_intervals):
        """Fetch and store node type metadata from workflow service."""
        try:
            response = requests.get(f"{WORKFLOW_SERVICE_URL}/node-types", timeout=2)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.debug(f"Failed to fetch node types: {e}")
        return []

    @app.callback(
        Output("workflow-canvas", "elements", allow_duplicate=True),
        Input("current-workflow-data", "data"),
        prevent_initial_call=True,
    )
    def sync_canvas_with_workflow_data(workflow_data):
        """Sync canvas elements when workflow data changes (e.g., after loading)."""
        if not workflow_data:
            raise PreventUpdate

        from robomage.dashboard.components import WorkflowCanvasFactory

        renderer = WorkflowCanvasFactory.create("cytoscape")

        # Convert workflow dict to WorkflowElement objects
        elements_objs = renderer.workflow_to_elements(workflow_data)

        # Convert to plain dicts for JSON serialization
        elements = renderer._to_cytoscape_elements(elements_objs)

        logger.info(
            f"Synced canvas with workflow: {len(workflow_data.get('nodes', []))} nodes, {len(workflow_data.get('edges', []))} edges"
        )

        return elements

    @app.callback(
        Output("workflow-canvas", "elements", allow_duplicate=True),
        Output("current-workflow-data", "data", allow_duplicate=True),
        Input({"type": "node-palette-item", "node_type": ALL}, "n_clicks"),
        State({"type": "node-palette-item", "node_type": ALL}, "id"),
        State("workflow-canvas", "elements"),
        State("current-workflow-data", "data"),
        State("node-types-data", "data"),
        prevent_initial_call=True,
    )
    def add_node_to_canvas(
        n_clicks_list, button_ids, current_elements, current_workflow, node_types_data
    ):
        """Add a node to the canvas when palette item is clicked."""
        ctx = callback_context
        if not ctx.triggered or not any(n_clicks_list):
            raise PreventUpdate

        # Find which palette item was clicked
        triggered_prop = ctx.triggered[0]["prop_id"]
        if not triggered_prop or triggered_prop == ".":
            raise PreventUpdate

        # Extract the node type from triggered button
        import json as json_module

        triggered_id = json_module.loads(triggered_prop.split(".")[0])
        node_type = triggered_id["node_type"]

        # Find the node type metadata
        node_metadata = next(
            (nt for nt in (node_types_data or []) if nt["type"] == node_type), None
        )

        if not node_metadata:
            logger.warning(f"Node type metadata not found for: {node_type}")
            raise PreventUpdate

        # Generate unique node ID
        import uuid

        node_id = f"{node_type}_{str(uuid.uuid4())[:8]}"

        # Create default config from schema
        config_schema = node_metadata.get("config_schema", {})
        properties = config_schema.get("properties", {})
        config = {}
        for prop_name, prop_def in properties.items():
            if "default" in prop_def:
                config[prop_name] = prop_def["default"]

        # Calculate position (place new nodes in a cascading pattern)
        existing_nodes = [
            el for el in (current_elements or []) if "source" not in el["data"]
        ]
        base_x = 150
        base_y = 100
        offset = len(existing_nodes) * 30
        position = {"x": base_x + offset, "y": base_y + offset}

        # Create new node element using CytoscapeWorkflowRenderer
        from robomage.dashboard.components import WorkflowCanvasFactory

        renderer = WorkflowCanvasFactory.create("cytoscape")

        # Create workflow with new node
        new_node = {
            "id": node_id,
            "type": node_type,
            "label": node_metadata.get("name", node_type),
            "config": config,
            "position": position,
        }

        # Update workflow data
        workflow = current_workflow or {"nodes": [], "edges": []}
        workflow["nodes"] = workflow.get("nodes", []) + [new_node]

        # Convert to Cytoscape elements (WorkflowElement objects)
        new_elements_objs = renderer.workflow_to_elements(workflow)

        # Convert WorkflowElement objects to plain dicts for JSON serialization
        new_elements = renderer._to_cytoscape_elements(new_elements_objs)

        logger.info(f"Added node {node_id} ({node_type}) to canvas")

        return new_elements, workflow

    @app.callback(
        Output("selected-node-id", "data"),
        Output("workflow-node-properties", "children"),
        Input("workflow-canvas", "tapNodeData"),
        State("node-types-data", "data"),
        State("current-workflow-data", "data"),
    )
    def handle_node_selection(tap_node_data, node_types_data, current_workflow):
        """Handle node selection and display properties panel."""
        if not tap_node_data:
            return None, html.P(
                [
                    html.I(className="fas fa-mouse-pointer me-2"),
                    "Select a node to configure its properties",
                ],
                className="text-muted text-center mt-4",
            )

        node_id = tap_node_data.get("id")

        # Find node in workflow to get the actual node type
        workflow = current_workflow or {"nodes": [], "edges": []}
        node = next((n for n in workflow.get("nodes", []) if n["id"] == node_id), None)

        if not node:
            logger.warning(f"Node {node_id} not found in workflow data")
            raise PreventUpdate

        # Get node type from workflow data (not from tap event which may not have it)
        node_type = node.get("type")

        # Find node type metadata
        node_metadata = next(
            (nt for nt in (node_types_data or []) if nt["type"] == node_type), None
        )

        if not node_metadata:
            return node_id, html.Div(
                [
                    html.P(
                        f"Node type metadata not found for: {node_type}",
                        className="text-warning",
                    ),
                    html.Small(
                        f"Node ID: {node_id}",
                        className="text-muted d-block",
                    ),
                    html.Small(
                        "Make sure the workflow service is running.",
                        className="text-muted d-block mt-2",
                    ),
                ]
            )

        # Create configuration form using NodeConfigurator
        from robomage.dashboard.components import NodeConfigurator

        config_schema = node_metadata.get("config_schema", {})
        current_config = node.get("config", {})

        form = NodeConfigurator.create_config_form(
            node_id=node_id,
            node_type=node_type,
            schema=config_schema,
            current_config=current_config,
        )

        # Wrap in a nice panel with node info header and feedback area
        properties_panel = html.Div(
            [
                html.Div(
                    [
                        html.H6(
                            [
                                html.I(
                                    className=f"{node_metadata.get('icon', 'fas fa-cube')} me-2"
                                ),
                                node_metadata.get("name", node_type),
                            ]
                        ),
                        dbc.Badge(node_type, color="secondary", className="mb-2"),
                    ],
                    className="mb-3",
                ),
                html.Hr(),
                html.Div(
                    id={"type": "config-feedback", "node_id": node_id}, className="mb-2"
                ),
                form,
            ]
        )

        return node_id, properties_panel

    @app.callback(
        Output({"type": "config-feedback", "node_id": ALL}, "children"),
        Output("current-workflow-data", "data", allow_duplicate=True),
        Output("workflow-canvas", "elements", allow_duplicate=True),
        Input({"type": "apply-node-config", "node_id": ALL}, "n_clicks"),
        State({"type": "apply-node-config", "node_id": ALL}, "id"),
        State({"type": "node-config-input", "node_id": ALL, "prop": ALL}, "value"),
        State({"type": "node-config-input", "node_id": ALL, "prop": ALL}, "id"),
        State("current-workflow-data", "data"),
        State("node-types-data", "data"),
        prevent_initial_call=True,
    )
    def apply_node_configuration(
        n_clicks_list,
        button_ids,
        input_values,
        input_ids,
        current_workflow,
        node_types_data,
    ):
        """Apply configuration changes to a node."""
        ctx = callback_context
        if not ctx.triggered or not any(n_clicks_list or []):
            raise PreventUpdate

        # Find which button was clicked
        triggered_prop = ctx.triggered[0]["prop_id"]
        if not triggered_prop or triggered_prop == ".":
            raise PreventUpdate

        import json as json_module

        triggered_id = json_module.loads(triggered_prop.split(".")[0])
        node_id = triggered_id["node_id"]

        # Gather form values for this node
        updated_config = {}
        for i, input_id in enumerate(input_ids):
            if input_id["node_id"] == node_id:
                param_name = input_id["prop"]
                param_value = input_values[i]
                if param_value is not None:  # Skip None values
                    updated_config[param_name] = param_value

        # Validate configuration
        from robomage.dashboard.components import NodeConfigurator

        # Find node type metadata for validation
        node = next(
            (n for n in current_workflow.get("nodes", []) if n["id"] == node_id), None
        )

        if not node:
            feedback = dbc.Alert(
                "Node not found in workflow",
                color="danger",
                dismissable=True,
            )
            feedbacks = [
                feedback if btn_id["node_id"] == node_id else no_update
                for btn_id in button_ids
            ]
            return feedbacks, no_update, no_update

        node_type = node["type"]
        node_metadata = next(
            (nt for nt in (node_types_data or []) if nt["type"] == node_type), None
        )

        if not node_metadata:
            feedback = dbc.Alert(
                "Node type metadata not found",
                color="danger",
                dismissable=True,
            )
            feedbacks = [
                feedback if btn_id["node_id"] == node_id else no_update
                for btn_id in button_ids
            ]
            return feedbacks, no_update, no_update

        # Validate config against schema
        config_schema = node_metadata.get("config_schema", {})
        is_valid, errors = NodeConfigurator.validate_config(
            updated_config, config_schema
        )

        if not is_valid:
            error_msg = "; ".join(errors)
            feedback = dbc.Alert(
                [html.I(className="fas fa-exclamation-triangle me-2"), error_msg],
                color="warning",
                dismissable=True,
            )
            feedbacks = [
                feedback if btn_id["node_id"] == node_id else no_update
                for btn_id in button_ids
            ]
            return feedbacks, no_update, no_update

        # Update node configuration in workflow
        workflow = current_workflow.copy()
        for n in workflow.get("nodes", []):
            if n["id"] == node_id:
                n["config"] = updated_config
                break

        # Convert to canvas elements
        from robomage.dashboard.components import WorkflowCanvasFactory

        renderer = WorkflowCanvasFactory.create("cytoscape")
        new_elements_objs = renderer.workflow_to_elements(workflow)
        new_elements = renderer._to_cytoscape_elements(new_elements_objs)

        logger.info(f"Updated config for node {node_id}: {updated_config}")

        feedback = dbc.Alert(
            [
                html.I(className="fas fa-check me-2"),
                "Configuration applied successfully",
            ],
            color="success",
            dismissable=True,
            duration=3000,
        )

        # Return feedback for the specific node
        feedbacks = [
            feedback if btn_id["node_id"] == node_id else no_update
            for btn_id in button_ids
        ]

        return feedbacks, workflow, new_elements

    @app.callback(
        Output("workflow-canvas", "elements", allow_duplicate=True),
        Output("current-workflow-data", "data", allow_duplicate=True),
        Input("delete-selected-btn", "n_clicks"),
        State("workflow-canvas", "selectedNodeData"),
        State("workflow-canvas", "selectedEdgeData"),
        State("current-workflow-data", "data"),
        prevent_initial_call=True,
    )
    def delete_selected_elements(
        n_clicks, selected_nodes, selected_edges, current_workflow
    ):
        """Delete selected nodes and edges from canvas."""
        if not n_clicks:
            raise PreventUpdate

        if not selected_nodes and not selected_edges:
            logger.info("Delete clicked but nothing selected")
            raise PreventUpdate

        workflow = current_workflow or {"nodes": [], "edges": []}

        # Get IDs to delete
        node_ids_to_delete = {node["id"] for node in (selected_nodes or [])}
        edge_ids_to_delete = {edge["id"] for edge in (selected_edges or [])}

        # Filter out deleted elements
        workflow["nodes"] = [
            n for n in workflow.get("nodes", []) if n["id"] not in node_ids_to_delete
        ]

        # Also delete edges connected to deleted nodes
        workflow["edges"] = [
            e
            for e in workflow.get("edges", [])
            if (
                e["id"] not in edge_ids_to_delete
                and e.get("source") not in node_ids_to_delete
                and e.get("target") not in node_ids_to_delete
            )
        ]

        # Convert to elements
        from robomage.dashboard.components import WorkflowCanvasFactory

        renderer = WorkflowCanvasFactory.create("cytoscape")
        new_elements_objs = renderer.workflow_to_elements(workflow)

        # Convert WorkflowElement objects to plain dicts for JSON serialization
        new_elements = renderer._to_cytoscape_elements(new_elements_objs)

        logger.info(
            f"Deleted {len(node_ids_to_delete)} nodes and {len(edge_ids_to_delete)} edges"
        )

        return new_elements, workflow

    @app.callback(
        Output("workflow-validation-status", "children"),
        Input("current-workflow-data", "data"),
        Input("workflow-canvas", "elements"),
        State("node-types-data", "data"),
    )
    def validate_workflow(workflow_data, canvas_elements, node_types_data):
        """Validate workflow and show status."""
        if not workflow_data or not workflow_data.get("nodes"):
            return dbc.Alert(
                [
                    html.I(className="fas fa-info-circle me-2"),
                    "Add nodes to start building your workflow",
                ],
                color="info",
                className="py-2 mb-2",
            )

        from robomage.dashboard.components import WorkflowValidator

        # Extract valid node types from service data
        valid_node_types = None
        if node_types_data and isinstance(node_types_data, list):
            valid_node_types = {nt["type"] for nt in node_types_data if "type" in nt}

        is_valid, errors = WorkflowValidator.validate(workflow_data, valid_node_types)

        if is_valid:
            return dbc.Alert(
                [
                    html.I(className="fas fa-check-circle me-2"),
                    f"Workflow is valid ({len(workflow_data.get('nodes', []))} nodes, "
                    f"{len(workflow_data.get('edges', []))} edges)",
                ],
                color="success",
                className="py-2 mb-2",
            )
        else:
            # Check if errors are only about disconnected nodes (informational)
            disconnected_only = all("Disconnected nodes:" in err for err in errors)

            # Use info color for disconnected nodes (normal during construction)
            # Use warning for other validation issues
            alert_color = "info" if disconnected_only else "warning"
            alert_icon = (
                "fa-info-circle" if disconnected_only else "fa-exclamation-triangle"
            )

            return dbc.Alert(
                [
                    html.Div(
                        [
                            html.I(className=f"fas {alert_icon} me-2"),
                            html.Strong(
                                "Connect your nodes:"
                                if disconnected_only
                                else f"{len(errors)} validation error(s):"
                            ),
                        ],
                        className="mb-2",
                    ),
                    html.Ul(
                        [html.Li(err) for err in errors[:5]]
                    ),  # Show first 5 errors
                    (
                        html.Small(
                            f"... and {len(errors) - 5} more", className="text-muted"
                        )
                        if len(errors) > 5
                        else None
                    ),
                ],
                color=alert_color,
                className="py-2 mb-2",
            )

    @app.callback(
        Output("current-workflow-data", "data", allow_duplicate=True),
        Input("workflow-canvas", "elements"),
        State("current-workflow-data", "data"),
        prevent_initial_call=True,
    )
    def sync_canvas_to_workflow(canvas_elements, current_workflow):
        """Sync canvas element changes back to workflow data.

        This captures:
        - User-created edges (by dragging between nodes)
        - Node position changes (dragging nodes around)
        """
        if not canvas_elements or not current_workflow:
            raise PreventUpdate

        # Extract nodes and edges from canvas elements
        canvas_nodes = []
        canvas_edges = []

        for elem in canvas_elements:
            elem_data = elem.get("data", {})
            if "source" in elem_data and "target" in elem_data:
                # This is an edge
                canvas_edges.append(
                    {
                        "id": elem_data.get("id"),
                        "source": elem_data.get("source"),
                        "target": elem_data.get("target"),
                    }
                )
            else:
                # This is a node
                node_id = elem_data.get("id")
                if node_id:
                    # Find corresponding node in workflow to preserve config
                    existing_node = next(
                        (
                            n
                            for n in current_workflow.get("nodes", [])
                            if n["id"] == node_id
                        ),
                        None,
                    )
                    if existing_node:
                        # Update position from canvas
                        updated_node = existing_node.copy()
                        if "position" in elem:
                            updated_node["position"] = elem["position"]
                        canvas_nodes.append(updated_node)

        # Only update if there are actual changes
        current_edges = current_workflow.get("edges", [])
        current_nodes = current_workflow.get("nodes", [])

        # Check if edges changed (new edge created or deleted)
        if len(canvas_edges) != len(current_edges) or set(
            e["id"] for e in canvas_edges
        ) != set(e["id"] for e in current_edges):
            # Update workflow with new edge list
            updated_workflow = current_workflow.copy()
            updated_workflow["edges"] = canvas_edges
            updated_workflow["nodes"] = canvas_nodes if canvas_nodes else current_nodes

            logger.info(
                f"Canvas sync: {len(canvas_edges)} edges, {len(canvas_nodes)} nodes"
            )
            return updated_workflow

        raise PreventUpdate

    # Use clientside callback for reset view (direct JS access to Cytoscape)
    app.clientside_callback(
        """
        function(n_clicks) {
            if (!n_clicks) {
                return window.dash_clientside.no_update;
            }
            
            // Get the Cytoscape instance
            const cytoscape_component = document.getElementById('workflow-canvas');
            if (cytoscape_component && cytoscape_component._cyreg && cytoscape_component._cyreg.cy) {
                const cy = cytoscape_component._cyreg.cy;
                
                // Reset zoom and pan to fit all elements
                cy.fit();
                cy.zoom(1.0);
                cy.center();
                
                return true;
            }
            
            return window.dash_clientside.no_update;
        }
        """,
        Output("reset-canvas-view-btn", "n_clicks_timestamp"),
        Input("reset-canvas-view-btn", "n_clicks"),
        prevent_initial_call=True,
    )

    @app.callback(
        Output("add-connection-modal", "is_open"),
        Output("connection-source-dropdown", "options"),
        Output("connection-target-dropdown", "options"),
        Input("add-connection-btn", "n_clicks"),
        Input("cancel-connection-btn", "n_clicks"),
        Input("confirm-connection-btn", "n_clicks"),
        State("current-workflow-data", "data"),
        State("add-connection-modal", "is_open"),
        prevent_initial_call=True,
    )
    def toggle_connection_modal(
        add_clicks, cancel_clicks, confirm_clicks, workflow_data, is_open
    ):
        """Toggle connection modal and populate node dropdowns."""
        ctx = callback_context
        if not ctx.triggered:
            raise PreventUpdate

        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

        # Get node options from workflow
        node_options = []
        if workflow_data and workflow_data.get("nodes"):
            node_options = [
                {"label": f"{n.get('label', n['id'])} ({n['id']})", "value": n["id"]}
                for n in workflow_data["nodes"]
            ]

        if triggered_id == "add-connection-btn":
            # Open modal
            return True, node_options, node_options

        elif triggered_id in ["cancel-connection-btn", "confirm-connection-btn"]:
            # Close modal
            return False, node_options, node_options

        raise PreventUpdate

    @app.callback(
        Output("workflow-canvas", "elements", allow_duplicate=True),
        Output("current-workflow-data", "data", allow_duplicate=True),
        Output("connection-feedback", "children"),
        Input("confirm-connection-btn", "n_clicks"),
        State("connection-source-dropdown", "value"),
        State("connection-target-dropdown", "value"),
        State("current-workflow-data", "data"),
        prevent_initial_call=True,
    )
    def create_connection(n_clicks, source_id, target_id, workflow_data):
        """Create a new edge between two nodes."""
        if not n_clicks or not source_id or not target_id:
            raise PreventUpdate

        if source_id == target_id:
            return (
                no_update,
                no_update,
                dbc.Alert(
                    "Cannot connect a node to itself", color="danger", dismissable=True
                ),
            )

        # Check if edge already exists
        existing_edges = workflow_data.get("edges", [])
        if any(
            e["source"] == source_id and e["target"] == target_id
            for e in existing_edges
        ):
            return (
                no_update,
                no_update,
                dbc.Alert(
                    "Connection already exists", color="warning", dismissable=True
                ),
            )

        # Create new edge
        import uuid

        new_edge = {
            "id": f"edge_{str(uuid.uuid4())[:8]}",
            "source": source_id,
            "target": target_id,
        }

        # Update workflow
        workflow = workflow_data.copy()
        workflow["edges"] = workflow.get("edges", []) + [new_edge]

        # Convert to canvas elements
        from robomage.dashboard.components import WorkflowCanvasFactory

        renderer = WorkflowCanvasFactory.create("cytoscape")
        new_elements_objs = renderer.workflow_to_elements(workflow)
        new_elements = renderer._to_cytoscape_elements(new_elements_objs)

        logger.info(f"Created edge: {source_id} -> {target_id}")

        return (
            new_elements,
            workflow,
            dbc.Alert("Connection added successfully!", color="success", duration=2000),
        )

    @app.callback(
        Output("edit-edge-modal", "is_open"),
        Output("edge-info-display", "children"),
        Output("edge-target-dropdown", "options"),
        Output("edge-target-dropdown", "value"),
        Input("workflow-canvas", "tapEdgeData"),
        Input("cancel-edge-edit-btn", "n_clicks"),
        Input("delete-edge-btn", "n_clicks"),
        Input("confirm-edge-edit-btn", "n_clicks"),
        State("current-workflow-data", "data"),
        State("edit-edge-modal", "is_open"),
        prevent_initial_call=True,
    )
    def toggle_edge_edit_modal(
        tap_edge_data,
        cancel_clicks,
        delete_clicks,
        confirm_clicks,
        workflow_data,
        is_open,
    ):
        """Toggle edge edit modal when edge is clicked."""
        ctx = callback_context
        if not ctx.triggered:
            raise PreventUpdate

        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

        # Get node options from workflow
        node_options = []
        if workflow_data and workflow_data.get("nodes"):
            node_options = [
                {"label": f"{n.get('label', n['id'])} ({n['id']})", "value": n["id"]}
                for n in workflow_data["nodes"]
            ]

        if triggered_id == "workflow-canvas" and tap_edge_data:
            # Edge was clicked - open modal
            edge_source = tap_edge_data.get("source")
            edge_target = tap_edge_data.get("target")
            edge_id = tap_edge_data.get("id")

            # Find node labels
            source_label = edge_source
            target_label = edge_target
            if workflow_data:
                for node in workflow_data.get("nodes", []):
                    if node["id"] == edge_source:
                        source_label = node.get("label", edge_source)
                    if node["id"] == edge_target:
                        target_label = node.get("label", edge_target)

            edge_info = html.Div(
                [
                    html.P(
                        [
                            html.Strong("From: "),
                            f"{source_label} ({edge_source})",
                        ]
                    ),
                    html.P(
                        [
                            html.Strong("To: "),
                            f"{target_label} ({edge_target})",
                        ]
                    ),
                    html.Small(f"Edge ID: {edge_id}", className="text-muted"),
                ]
            )

            return True, edge_info, node_options, edge_target

        elif triggered_id in [
            "cancel-edge-edit-btn",
            "delete-edge-btn",
            "confirm-edge-edit-btn",
        ]:
            # Close modal
            return False, no_update, node_options, no_update

        raise PreventUpdate

    @app.callback(
        Output("workflow-canvas", "elements", allow_duplicate=True),
        Output("current-workflow-data", "data", allow_duplicate=True),
        Output("edge-edit-feedback", "children"),
        Input("delete-edge-btn", "n_clicks"),
        State("workflow-canvas", "tapEdgeData"),
        State("current-workflow-data", "data"),
        prevent_initial_call=True,
    )
    def delete_edge(n_clicks, tap_edge_data, workflow_data):
        """Delete the selected edge."""
        if not n_clicks or not tap_edge_data:
            raise PreventUpdate

        edge_id = tap_edge_data.get("id")

        # Remove edge from workflow
        workflow = workflow_data.copy()
        workflow["edges"] = [e for e in workflow.get("edges", []) if e["id"] != edge_id]

        # Convert to canvas elements
        from robomage.dashboard.components import WorkflowCanvasFactory

        renderer = WorkflowCanvasFactory.create("cytoscape")
        new_elements_objs = renderer.workflow_to_elements(workflow)
        new_elements = renderer._to_cytoscape_elements(new_elements_objs)

        logger.info(f"Deleted edge: {edge_id}")

        return (
            new_elements,
            workflow,
            dbc.Alert("Edge deleted!", color="success", duration=2000),
        )

    @app.callback(
        Output("workflow-canvas", "elements", allow_duplicate=True),
        Output("current-workflow-data", "data", allow_duplicate=True),
        Output("edge-edit-feedback", "children", allow_duplicate=True),
        Input("confirm-edge-edit-btn", "n_clicks"),
        State("workflow-canvas", "tapEdgeData"),
        State("edge-target-dropdown", "value"),
        State("current-workflow-data", "data"),
        prevent_initial_call=True,
    )
    def update_edge_target(n_clicks, tap_edge_data, new_target, workflow_data):
        """Update the target node of an edge."""
        if not n_clicks or not tap_edge_data or not new_target:
            raise PreventUpdate

        edge_id = tap_edge_data.get("id")
        old_target = tap_edge_data.get("target")

        if new_target == old_target:
            return (
                no_update,
                no_update,
                dbc.Alert("No change made", color="info", dismissable=True),
            )

        # Update edge target in workflow
        workflow = workflow_data.copy()
        for edge in workflow.get("edges", []):
            if edge["id"] == edge_id:
                edge["target"] = new_target
                break

        # Convert to canvas elements
        from robomage.dashboard.components import WorkflowCanvasFactory

        renderer = WorkflowCanvasFactory.create("cytoscape")
        new_elements_objs = renderer.workflow_to_elements(workflow)
        new_elements = renderer._to_cytoscape_elements(new_elements_objs)

        logger.info(f"Updated edge {edge_id}: target changed to {new_target}")

        return (
            new_elements,
            workflow,
            dbc.Alert("Connection updated!", color="success", duration=2000),
        )

    # JSON Editor Callbacks (Option A: Collapsible Panel)
    @app.callback(
        Output("json-editor-collapse", "is_open"),
        Output("json-toggle-text", "children"),
        Input("toggle-json-editor-btn", "n_clicks"),
        State("json-editor-collapse", "is_open"),
        prevent_initial_call=True,
    )
    def toggle_json_editor(n_clicks, is_open):
        """Toggle JSON editor visibility and update button text."""
        if not n_clicks:
            raise PreventUpdate
        
        new_state = not is_open
        button_text = "Hide JSON" if new_state else "Show JSON"
        
        logger.info(f"JSON editor toggled: {'open' if new_state else 'closed'}")
        return new_state, button_text

    @app.callback(
        Output("workflow-json-editor", "value"),
        Input("current-workflow-data", "data"),
        prevent_initial_call=False,
    )
    def sync_json_from_workflow(workflow_data):
        """Update JSON editor when workflow changes (via canvas or loads)."""
        if not workflow_data:
            return ""
        
        # Pretty-print JSON with 2-space indentation
        try:
            json_str = json.dumps(workflow_data, indent=2)
            return json_str
        except Exception as e:
            logger.error(f"Error serializing workflow to JSON: {e}")
            return f"Error: Could not serialize workflow\n{str(e)}"

    @app.callback(
        Output("current-workflow-data", "data", allow_duplicate=True),
        Output("json-validation-feedback", "children"),
        Input("apply-json-btn", "n_clicks"),
        State("workflow-json-editor", "value"),
        State("current-workflow-data", "data"),
        prevent_initial_call=True,
    )
    def apply_json_to_workflow(n_clicks, json_text, current_workflow):
        """Apply manually edited JSON to workflow (updates canvas)."""
        if not n_clicks:
            raise PreventUpdate
        
        if not json_text or not json_text.strip():
            return no_update, dbc.Alert(
                [
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    "JSON is empty"
                ],
                color="warning",
                dismissable=True,
            )
        
        try:
            # Parse JSON
            workflow = json.loads(json_text)
            
            # Validate structure
            if "nodes" not in workflow:
                return no_update, dbc.Alert(
                    [
                        html.I(className="fas fa-times-circle me-2"),
                        "Invalid workflow: missing 'nodes' key"
                    ],
                    color="danger",
                    dismissable=True,
                )
            
            if "edges" not in workflow:
                return no_update, dbc.Alert(
                    [
                        html.I(className="fas fa-times-circle me-2"),
                        "Invalid workflow: missing 'edges' key"
                    ],
                    color="danger",
                    dismissable=True,
                )
            
            # Validate using WorkflowValidator
            from robomage.dashboard.components import WorkflowValidator
            
            validator = WorkflowValidator()
            is_valid, errors = validator.validate(workflow)
            
            if not is_valid:
                error_list = html.Ul(
                    [html.Li(err) for err in errors],
                    className="mb-0 mt-2"
                )
                return no_update, dbc.Alert(
                    [
                        html.Strong([
                            html.I(className="fas fa-exclamation-triangle me-2"),
                            (
                                f"Validation failed "
                                f"({len(errors)} error"
                                f"{'s' if len(errors) > 1 else ''}):"
                            )
                        ]),
                        error_list,
                    ],
                    color="danger",
                    dismissable=True,
                )
            
            # Success - update workflow (auto-sync to canvas via callback)
            logger.info(
                f"Applied JSON to workflow: {len(workflow.get('nodes', []))} nodes, "
                f"{len(workflow.get('edges', []))} edges"
            )
            
            return workflow, dbc.Alert(
                [
                    html.I(className="fas fa-check-circle me-2"),
                    "JSON applied successfully! Canvas updated."
                ],
                color="success",
                dismissable=True,
                duration=3000,
            )
            
        except json.JSONDecodeError as e:
            return no_update, dbc.Alert(
                [
                    html.I(className="fas fa-times-circle me-2"),
                    html.Strong("Invalid JSON syntax:"),
                    html.Br(),
                    html.Code(str(e), style={"fontSize": "11px"}),
                ],
                color="danger",
                dismissable=True,
            )
        except Exception as e:
            logger.error(f"Error applying JSON to workflow: {e}")
            return no_update, dbc.Alert(
                [
                    html.I(className="fas fa-times-circle me-2"),
                    f"Error: {str(e)}"
                ],
                color="danger",
                dismissable=True,
            )
