"""
Workflow Builder Tab Layout

Provides interface for creating, managing, and executing analysis workflows.
Phase 1: JSON-based workflow editor with node palette and execution controls.
Future: Visual drag-and-drop interface with ReactFlow.
"""

import dash_bootstrap_components as dbc
from dash import dcc, html


def create_workflow_tab() -> html.Div:
    """
    Create the Workflow Builder tab.
    
    Phase 1 Implementation:
    - Node type palette (clickable cards)
    - JSON workflow editor (for MVP)
    - Workflow management (save/load/execute)
    - Execution log viewer
    - Service health indicator
    
    Returns:
        Workflow tab layout component
    """
    return html.Div(
        [
            dbc.Row(
                [
                    # Left sidebar - Node palette and templates
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
                                                    "Node Types",
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
                                            # Node palette (loaded dynamically from service)
                                            html.Div(id="workflow-node-palette"),
                                            html.Hr(),
                                            # Workflow templates
                                            html.H6("Quick Start Templates"),
                                            html.Div(id="workflow-templates"),
                                        ],
                                        style={"maxHeight": "700px", "overflowY": "auto"},
                                    ),
                                ],
                                className="h-100",
                            )
                        ],
                        width=3,
                    ),
                    # Center - Workflow editor and controls
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
                                                                    "Workflow Editor",
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
                                            # Workflow name input
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
                                            # Workflow JSON editor (Phase 1)
                                            html.Div(
                                                [
                                                    dbc.Label("Workflow Definition (JSON):"),
                                                    html.Small(
                                                        " Phase 1: Manual JSON editing (drag-and-drop coming in Phase 2)",
                                                        className="text-muted",
                                                    ),
                                                    dcc.Textarea(
                                                        id="workflow-json-editor",
                                                        value=get_default_workflow_json(),
                                                        style={
                                                            "width": "100%",
                                                            "height": "400px",
                                                            "fontFamily": "monospace",
                                                            "fontSize": "12px",
                                                        },
                                                        className="form-control mt-2",
                                                    ),
                                                    html.Small(
                                                        [
                                                            html.I(
                                                                className="fas fa-info-circle me-1"
                                                            ),
                                                            "Edit the JSON directly. Reference the node types on the left for available options.",
                                                        ],
                                                        className="text-info mt-1",
                                                    ),
                                                ]
                                            ),
                                        ]
                                    ),
                                ]
                            )
                        ],
                        width=6,
                    ),
                    # Right sidebar - Execution results and logs
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.H5(
                                                [
                                                    html.I(
                                                        className="fas fa-list-alt me-2"
                                                    ),
                                                    "Execution & Results",
                                                ]
                                            )
                                        ]
                                    ),
                                    dbc.CardBody(
                                        [
                                            dbc.Tabs(
                                                [
                                                    dbc.Tab(
                                                        label="Execution Log",
                                                        children=[
                                                            html.Div(
                                                                id="workflow-execution-log",
                                                                children=[
                                                                    html.P(
                                                                        "No workflow executed yet",
                                                                        className="text-muted mt-3",
                                                                    )
                                                                ],
                                                                style={
                                                                    "maxHeight": "600px",
                                                                    "overflowY": "auto",
                                                                },
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
            dcc.Store(id="current-workflow-data"),
            dcc.Store(id="workflow-execution-result"),
            dcc.Interval(
                id="workflow-service-check-interval",
                interval=5000,  # Check every 5 seconds
                n_intervals=0,
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


def get_default_workflow_json() -> str:
    """Get default workflow JSON template."""
    return """{
  "name": "Example Workflow",
  "description": "Load files and analyze peaks",
  "nodes": [
    {
      "id": "load_1",
      "type": "load_files",
      "label": "Load Data Files",
      "config": {
        "directory": "examples",
        "pattern": "*.chi"
      },
      "position": {"x": 100, "y": 100}
    },
    {
      "id": "analyze_1",
      "type": "peak_analysis",
      "label": "Detect Peaks",
      "config": {
        "profile_type": "gaussian",
        "prominence": 0.1,
        "distance": 5
      },
      "position": {"x": 400, "y": 100}
    },
    {
      "id": "export_1",
      "type": "export_csv",
      "label": "Export Results",
      "config": {
        "output_path": "workflow_results.csv",
        "format": "peaks"
      },
      "position": {"x": 700, "y": 100}
    }
  ],
  "edges": [
    {
      "id": "edge_1",
      "source": "load_1",
      "target": "analyze_1"
    },
    {
      "id": "edge_2",
      "source": "analyze_1",
      "target": "export_1"
    }
  ]
}"""
