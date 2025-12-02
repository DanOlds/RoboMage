"""
Workflow Builder Tab Layout

Visual drag-and-drop workflow editor with Cytoscape canvas.
Sprint 8 Phase 2: Full visual workflow builder with node palette,
properties panel, and validation.
"""

# ruff: noqa: E501
# Line length exceptions for Dash UI code where breaking lines hurts readability

from pathlib import Path

import dash_bootstrap_components as dbc
from dash import dcc, html

from robomage.dashboard.components import WorkflowCanvasFactory


def create_workflow_tab() -> html.Div:
    """
    Create the Workflow Builder tab with visual canvas.

    Sprint 8 Phase 2 Implementation:
    - Visual Cytoscape canvas for drag-and-drop workflow creation
    - Node type palette (fetched from workflow service)
    - Properties panel with dynamic forms (NodeConfigurator)
    - Validation panel with real-time feedback (WorkflowValidator)
    - Workflow management (save/load/execute)
    - Execution log viewer
    - Service health indicator

    Returns:
        Workflow tab layout component
    """
    # Get Cytoscape renderer
    renderer = WorkflowCanvasFactory.create("cytoscape")

    # Get default workflow and convert to WorkflowElement objects
    default_workflow = get_default_workflow()
    initial_elements = renderer.workflow_to_elements(default_workflow)

    return html.Div(
        [
            dbc.Row(
                [
                    # Left sidebar - Node palette
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.H5(
                                                [
                                                    html.I(
                                                        className="fas fa-puzzle-piece me-2"
                                                    ),
                                                    "Node Palette",
                                                ]
                                            )
                                        ]
                                    ),
                                    dbc.CardBody(
                                        [
                                            # Service health indicator
                                            html.Div(
                                                id="workflow-service-status",
                                                children=[
                                                    create_service_status_indicator()
                                                ],
                                                className="mb-3",
                                            ),
                                            html.Hr(),
                                            # Instructions
                                            dbc.Alert(
                                                [
                                                    html.I(
                                                        className="fas fa-info-circle me-2"
                                                    ),
                                                    "Click a node below to add it to the canvas",
                                                ],
                                                color="info",
                                                className="py-2 mb-3",
                                            ),
                                            # Node palette (loaded dynamically from service)
                                            html.Div(
                                                id="workflow-node-palette",
                                                children=[
                                                    html.P(
                                                        "Loading node types...",
                                                        className="text-muted text-center",
                                                    )
                                                ],
                                            ),
                                        ],
                                        style={
                                            "maxHeight": "700px",
                                            "overflowY": "auto",
                                        },
                                    ),
                                ],
                                className="h-100",
                            )
                        ],
                        width=3,
                    ),
                    # Center - Workflow canvas
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            html.H5(
                                                                [
                                                                    html.I(
                                                                        className="fas fa-project-diagram me-2"
                                                                    ),
                                                                    "Workflow Canvas",
                                                                ]
                                                            )
                                                        ],
                                                        width=6,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dbc.ButtonGroup(
                                                                [
                                                                    dbc.Button(
                                                                        [
                                                                            html.I(
                                                                                className="fas fa-file me-1"
                                                                            ),
                                                                            "New",
                                                                        ],
                                                                        id="new-workflow-btn",
                                                                        color="info",
                                                                        size="sm",
                                                                    ),
                                                                    dbc.Button(
                                                                        [
                                                                            html.I(
                                                                                className="fas fa-folder-open me-1"
                                                                            ),
                                                                            "Load",
                                                                        ],
                                                                        id="load-workflow-btn",
                                                                        color="secondary",
                                                                        size="sm",
                                                                    ),
                                                                    dbc.Button(
                                                                        [
                                                                            html.I(
                                                                                className="fas fa-save me-1"
                                                                            ),
                                                                            "Save",
                                                                        ],
                                                                        id="save-workflow-btn",
                                                                        color="primary",
                                                                        size="sm",
                                                                    ),
                                                                ],
                                                                className="me-2",
                                                            ),
                                                            dbc.Button(
                                                                [
                                                                    html.I(
                                                                        className="fas fa-play me-1"
                                                                    ),
                                                                    "Execute",
                                                                ],
                                                                id="execute-workflow-btn",
                                                                color="success",
                                                                size="sm",
                                                            ),
                                                        ],
                                                        width=6,
                                                        className="text-end",
                                                    ),
                                                ]
                                            )
                                        ]
                                    ),
                                    dbc.CardBody(
                                        [
                                            # Workflow metadata
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("Workflow Name:"),
                                                            dbc.Input(
                                                                id="workflow-name-input",
                                                                placeholder="Enter workflow name...",
                                                                value="My Workflow",
                                                                className="mb-2",
                                                            ),
                                                        ],
                                                        width=6,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("Description:"),
                                                            dbc.Input(
                                                                id="workflow-description-input",
                                                                placeholder="Workflow description...",
                                                                className="mb-2",
                                                            ),
                                                        ],
                                                        width=6,
                                                    ),
                                                ]
                                            ),
                                            html.Hr(),
                                            # Validation status
                                            html.Div(
                                                id="workflow-validation-status",
                                                className="mb-2",
                                            ),
                                            # Cytoscape canvas
                                            html.Div(
                                                renderer.render(
                                                    elements=initial_elements,
                                                    id="workflow-canvas",
                                                ),
                                                style={
                                                    "height": "500px",
                                                    "border": "1px solid #ddd",
                                                },
                                            ),
                                            # Canvas controls
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            dbc.ButtonGroup(
                                                                [
                                                                    dbc.Button(
                                                                        [
                                                                            html.I(
                                                                                className="fas fa-link me-1"
                                                                            ),
                                                                            "Add Connection",
                                                                        ],
                                                                        id="add-connection-btn",
                                                                        color="primary",
                                                                        size="sm",
                                                                        outline=True,
                                                                    ),
                                                                    dbc.Button(
                                                                        [
                                                                            html.I(
                                                                                className="fas fa-trash me-1"
                                                                            ),
                                                                            "Delete Selected",
                                                                        ],
                                                                        id="delete-selected-btn",
                                                                        color="danger",
                                                                        size="sm",
                                                                        outline=True,
                                                                    ),
                                                                    dbc.Button(
                                                                        [
                                                                            html.I(
                                                                                className="fas fa-compress-arrows-alt me-1"
                                                                            ),
                                                                            "Reset View",
                                                                        ],
                                                                        id="reset-canvas-view-btn",
                                                                        color="secondary",
                                                                        size="sm",
                                                                        outline=True,
                                                                    ),
                                                                    dbc.Button(
                                                                        [
                                                                            html.I(
                                                                                className="fas fa-code me-1"
                                                                            ),
                                                                            html.Span(
                                                                                id="json-toggle-text",
                                                                                children="Show JSON",
                                                                            ),
                                                                        ],
                                                                        id="toggle-json-editor-btn",
                                                                        color="secondary",
                                                                        size="sm",
                                                                        outline=True,
                                                                    ),
                                                                ],
                                                                className="mt-2",
                                                            ),
                                                        ]
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            html.Small(
                                                                "Click nodes to configure • Drag to move • Use 'Add Connection' to link nodes",
                                                                className="text-muted mt-3 d-block text-end",
                                                            ),
                                                        ]
                                                    ),
                                                ]
                                            ),
                                            # JSON Editor (collapsible)
                                            dbc.Collapse(
                                                dbc.Card(
                                                    [
                                                        dbc.CardHeader(
                                                            [
                                                                html.H6(
                                                                    [
                                                                        html.I(
                                                                            className="fas fa-code me-2"
                                                                        ),
                                                                        "JSON Editor",
                                                                        dbc.Badge(
                                                                            "Advanced",
                                                                            color="warning",
                                                                            className="ms-2",
                                                                        ),
                                                                    ]
                                                                )
                                                            ]
                                                        ),
                                                        dbc.CardBody(
                                                            [
                                                                dcc.Textarea(
                                                                    id="workflow-json-editor",
                                                                    placeholder="Workflow JSON will appear here...",
                                                                    style={
                                                                        "width": "100%",
                                                                        "height": "400px",
                                                                        "fontFamily": "Consolas, Monaco, monospace",
                                                                        "fontSize": "12px",
                                                                        "border": "1px solid #ccc",
                                                                        "borderRadius": "4px",
                                                                        "padding": "10px",
                                                                    },
                                                                ),
                                                                dbc.Row(
                                                                    [
                                                                        dbc.Col(
                                                                            [
                                                                                html.Div(
                                                                                    id="json-validation-feedback"
                                                                                )
                                                                            ]
                                                                        ),
                                                                        dbc.Col(
                                                                            [
                                                                                dbc.Button(
                                                                                    [
                                                                                        html.I(
                                                                                            className="fas fa-sync me-1"
                                                                                        ),
                                                                                        "Apply JSON",
                                                                                    ],
                                                                                    id="apply-json-btn",
                                                                                    color="primary",
                                                                                    size="sm",
                                                                                    className="float-end",
                                                                                )
                                                                            ],
                                                                            width="auto",
                                                                        ),
                                                                    ],
                                                                    className="mt-2",
                                                                ),
                                                            ]
                                                        ),
                                                    ],
                                                    className="mt-2",
                                                ),
                                                id="json-editor-collapse",
                                                is_open=False,
                                            ),
                                        ]
                                    ),
                                ]
                            )
                        ],
                        width=6,
                    ),
                    # Right sidebar - Properties & Results
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.H5(
                                                [
                                                    html.I(
                                                        className="fas fa-cogs me-2"
                                                    ),
                                                    "Properties & Results",
                                                ]
                                            )
                                        ]
                                    ),
                                    dbc.CardBody(
                                        [
                                            dbc.Tabs(
                                                [
                                                    dbc.Tab(
                                                        label="Node Properties",
                                                        children=[
                                                            html.Div(
                                                                id="workflow-node-properties",
                                                                children=[
                                                                    html.P(
                                                                        [
                                                                            html.I(
                                                                                className="fas fa-mouse-pointer me-2"
                                                                            ),
                                                                            "Select a node to configure its properties",
                                                                        ],
                                                                        className="text-muted text-center mt-4",
                                                                    )
                                                                ],
                                                                className="mt-3",
                                                                style={
                                                                    "maxHeight": "600px",
                                                                    "overflowY": "auto",
                                                                },
                                                            )
                                                        ],
                                                    ),
                                                    dbc.Tab(
                                                        label="Execution Log",
                                                        children=[
                                                            html.Div(
                                                                [
                                                                    # Alert for save-to-session feedback
                                                                    dbc.Alert(
                                                                        id="save-to-session-alert",
                                                                        is_open=False,
                                                                        duration=6000,
                                                                        dismissable=True,
                                                                    ),
                                                                    # Save to session button
                                                                    dbc.Button(
                                                                        [
                                                                            html.I(
                                                                                className="fas fa-save me-2"
                                                                            ),
                                                                            "Save Results to Current Session",
                                                                        ],
                                                                        id="save-results-to-session-btn",
                                                                        color="success",
                                                                        size="sm",
                                                                        className="mb-3 w-100",
                                                                    ),
                                                                    # Execution log
                                                                    html.Div(
                                                                        id="workflow-execution-log",
                                                                        children=[
                                                                            html.P(
                                                                                "No workflow executed yet",
                                                                                className="text-muted mt-3",
                                                                            )
                                                                        ],
                                                                        style={
                                                                            "maxHeight": "550px",
                                                                            "overflowY": "auto",
                                                                        },
                                                                    ),
                                                                ]
                                                            )
                                                        ],
                                                    ),
                                                    dbc.Tab(
                                                        label="Saved Workflows",
                                                        children=[
                                                            html.Div(
                                                                id="saved-workflows-list",
                                                                className="mt-3",
                                                            )
                                                        ],
                                                    ),
                                                ],
                                            )
                                        ],
                                        style={"maxHeight": "700px"},
                                    ),
                                ],
                                className="h-100",
                            )
                        ],
                        width=3,
                    ),
                ],
                className="mt-3",
            ),
            # Hidden stores
            dcc.Store(id="current-workflow-data", data=default_workflow),
            dcc.Store(id="workflow-execution-result"),
            dcc.Store(
                id="selected-node-id"
            ),  # Track selected node for properties panel
            dcc.Store(id="node-types-data"),  # Store node type metadata from service
            dcc.Interval(
                id="workflow-service-check-interval",
                interval=5000,  # Check every 5 seconds
                n_intervals=0,
            ),
            # Add Connection Modal
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Add Connection Between Nodes")),
                    dbc.ModalBody(
                        [
                            dbc.Label("From Node:"),
                            dcc.Dropdown(
                                id="connection-source-dropdown",
                                placeholder="Select source node...",
                                className="mb-3",
                            ),
                            dbc.Label("To Node:"),
                            dcc.Dropdown(
                                id="connection-target-dropdown",
                                placeholder="Select target node...",
                                className="mb-3",
                            ),
                            html.Div(id="connection-feedback"),
                        ]
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button(
                                "Cancel",
                                id="cancel-connection-btn",
                                color="secondary",
                                className="me-2",
                            ),
                            dbc.Button(
                                "Add Connection",
                                id="confirm-connection-btn",
                                color="primary",
                            ),
                        ]
                    ),
                ],
                id="add-connection-modal",
                is_open=False,
            ),
            # Edit Edge Modal
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Edit Connection")),
                    dbc.ModalBody(
                        [
                            html.Div(id="edge-info-display"),
                            html.Hr(),
                            dbc.Label("Change Target Node:"),
                            dcc.Dropdown(
                                id="edge-target-dropdown",
                                placeholder="Select new target...",
                                className="mb-3",
                            ),
                            html.Div(id="edge-edit-feedback"),
                        ]
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button(
                                [html.I(className="fas fa-trash me-1"), "Delete Edge"],
                                id="delete-edge-btn",
                                color="danger",
                                outline=True,
                                className="me-auto",
                            ),
                            dbc.Button(
                                "Cancel",
                                id="cancel-edge-edit-btn",
                                color="secondary",
                                className="me-2",
                            ),
                            dbc.Button(
                                "Update Connection",
                                id="confirm-edge-edit-btn",
                                color="primary",
                            ),
                        ]
                    ),
                ],
                id="edit-edge-modal",
                is_open=False,
            ),
            # Load Workflow Modal
            dbc.Modal(
                [
                    dbc.ModalHeader(
                        dbc.ModalTitle(
                            [
                                html.I(className="fas fa-folder-open me-2"),
                                "Load Workflow",
                            ]
                        )
                    ),
                    dbc.ModalBody(
                        [
                            html.P(
                                "Select a workflow to load onto the canvas:",
                                className="fw-bold mb-3",
                            ),
                            html.Div(id="load-workflow-list-container"),
                            html.Div(id="load-workflow-modal-feedback"),
                        ]
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button(
                                "Cancel",
                                id="load-workflow-modal-cancel",
                                color="secondary",
                            ),
                        ]
                    ),
                ],
                id="load-workflow-modal",
                is_open=False,
                size="lg",
            ),
            # Save Workflow Modal
            dbc.Modal(
                [
                    dbc.ModalHeader(
                        dbc.ModalTitle(
                            [html.I(className="fas fa-save me-2"), "Save Workflow"]
                        )
                    ),
                    dbc.ModalBody(
                        [
                            dbc.Label(
                                "Workflow Name *", html_for="save-workflow-name-input"
                            ),
                            dbc.Input(
                                id="save-workflow-name-input",
                                placeholder="Enter workflow name...",
                                type="text",
                                required=True,
                                className="mb-3",
                            ),
                            dbc.Label(
                                "Description",
                                html_for="save-workflow-description-input",
                            ),
                            dbc.Textarea(
                                id="save-workflow-description-input",
                                placeholder="Optional: Describe this workflow...",
                                style={"height": "100px"},
                                className="mb-3",
                            ),
                            html.Div(id="save-workflow-modal-feedback"),
                        ]
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button(
                                "Cancel",
                                id="save-workflow-modal-cancel",
                                color="secondary",
                                className="me-2",
                            ),
                            dbc.Button(
                                "Save",
                                id="save-workflow-modal-confirm",
                                color="primary",
                            ),
                        ]
                    ),
                ],
                id="save-workflow-modal",
                is_open=False,
            ),
        ]
    )


def create_service_status_indicator() -> html.Div:
    """Create service health status indicator."""
    return html.Div(
        [
            dbc.Alert(
                [
                    html.I(className="fas fa-spinner fa-spin me-2"),
                    "Checking workflow service...",
                ],
                color="info",
                className="mb-0 py-2",
            )
        ]
    )


def get_default_workflow() -> dict:
    """Get default workflow structure for initial canvas state."""
    # Get absolute path to examples directory
    project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
    examples_dir = str(project_root / "examples")

    return {
        "name": "Example Workflow",
        "description": "Load files and analyze peaks",
        "nodes": [
            {
                "id": "load_1",
                "type": "load_files",
                "label": "Load Data Files",
                "config": {
                    "directory": examples_dir,
                    "pattern": "*.chi",
                },
                "position": {"x": 100, "y": 100},
            },
            {
                "id": "analyze_1",
                "type": "peak_analysis",
                "label": "Detect Peaks",
                "config": {
                    "profile_type": "gaussian",
                    "prominence": 0.1,
                    "distance": 5,
                },
                "position": {"x": 400, "y": 100},
            },
            {
                "id": "export_1",
                "type": "export_csv",
                "label": "Export Results",
                "config": {
                    "output_path": "workflow_results.csv",
                    "format": "peaks",
                },
                "position": {"x": 700, "y": 100},
            },
        ],
        "edges": [
            {"id": "edge_1", "source": "load_1", "target": "analyze_1"},
            {"id": "edge_2", "source": "analyze_1", "target": "export_1"},
        ],
    }


def create_node_palette_card(node_type: dict) -> dbc.Card:
    """
    Create a clickable card for a node type in the palette.

    Args:
        node_type: Node type metadata from workflow service

    Returns:
        Dash Bootstrap Card component
    """
    # Category color mapping
    category_colors = {
        "data": "primary",
        "transform": "warning",
        "analysis": "success",
        "output": "danger",
    }

    color = category_colors.get(node_type.get("category", ""), "secondary")

    return dbc.Card(
        [
            dbc.CardBody(
                [
                    html.Div(
                        [
                            html.I(
                                className=f"{node_type.get('icon', 'fas fa-cube')} fa-2x mb-2"
                            ),
                            html.H6(node_type.get("name", "Unknown"), className="mb-1"),
                            html.Small(
                                node_type.get("description", ""),
                                className="text-muted",
                            ),
                        ],
                        className="text-center",
                    )
                ],
                className="py-2",
            )
        ],
        id={"type": "node-palette-card", "node_type": node_type.get("type", "")},
        color=color,
        outline=True,
        className="mb-2 node-palette-card",
        style={"cursor": "pointer"},
    )


def get_default_workflow_json() -> str:
    """Get default workflow JSON template with absolute paths."""
    # Get absolute path to examples directory
    # __file__ is src/robomage/dashboard/layouts/workflow_layout.py
    # Need to go up 5 levels to get to project root
    project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
    examples_dir = str(project_root / "examples")

    return f"""{{
  "name": "Example Workflow",
  "description": "Load files and analyze peaks",
  "nodes": [
    {{
      "id": "load_1",
      "type": "load_files",
      "label": "Load Data Files",
      "config": {{
        "directory": "{examples_dir}",
        "pattern": "*.chi"
      }},
      "position": {{"x": 100, "y": 100}}
    }},
    {{
      "id": "analyze_1",
      "type": "peak_analysis",
      "label": "Detect Peaks",
      "config": {{
        "profile_type": "gaussian",
        "prominence": 0.1,
        "distance": 5
      }},
      "position": {{"x": 400, "y": 100}}
    }},
    {{
      "id": "export_1",
      "type": "export_csv",
      "label": "Export Results",
      "config": {{
        "output_path": "workflow_results.csv",
        "format": "peaks"
      }},
      "position": {{"x": 700, "y": 100}}
    }}
  ],
  "edges": [
    {{
      "id": "edge_1",
      "source": "load_1",
      "target": "analyze_1"
    }},
    {{
      "id": "edge_2",
      "source": "analyze_1",
      "target": "export_1"
    }}
  ]
}}"""
