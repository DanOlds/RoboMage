"""
Node I/O Inspector Tab Layout

Interactive visualization of data flowing through workflow nodes.
Week 2 Day 3: Node I/O Inspector visualization UI.
"""

# ruff: noqa: E501
# Line length exceptions for Dash UI code where breaking lines hurts readability

import dash_bootstrap_components as dbc
from dash import dcc, html


def create_inspector_tab() -> html.Div:
    """
    Create the Node I/O Inspector tab with data flow visualization.

    Week 2 Day 3 Implementation:
    - Workflow execution selector
    - Node-by-node execution timeline
    - Input/Output data display panels
    - Execution statistics and metadata
    - JSON data viewer with expansion
    - Data shape summaries

    Returns:
        Inspector tab layout component
    """
    return html.Div(
        [
            # Header with workflow selector
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H4(
                                [
                                    html.I(className="fas fa-microscope me-2"),
                                    "Node I/O Inspector",
                                ],
                                className="text-primary",
                            ),
                            html.P(
                                "Visualize data flowing through workflow nodes during execution",
                                className="text-muted",
                            ),
                        ],
                        width=8,
                    ),
                    dbc.Col(
                        [
                            dbc.ButtonGroup(
                                [
                                    dbc.Button(
                                        [
                                            html.I(className="fas fa-sync me-2"),
                                            "Refresh",
                                        ],
                                        id="inspector-refresh-btn",
                                        color="primary",
                                        size="sm",
                                        outline=True,
                                    ),
                                    dbc.Button(
                                        [
                                            html.I(className="fas fa-download me-2"),
                                            "Export",
                                        ],
                                        id="inspector-export-btn",
                                        color="info",
                                        size="sm",
                                        outline=True,
                                    ),
                                ],
                                className="float-end",
                            ),
                        ],
                        width=4,
                        className="d-flex align-items-center justify-content-end",
                    ),
                ],
                className="mb-3",
            ),
            # Workflow selector row
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.H6(
                                                [
                                                    html.I(
                                                        className="fas fa-project-diagram me-2"
                                                    ),
                                                    "Select Workflow Execution",
                                                ]
                                            )
                                        ]
                                    ),
                                    dbc.CardBody(
                                        [
                                            html.Label(
                                                "Workflow:",
                                                className="fw-bold mb-2",
                                            ),
                                            dcc.Dropdown(
                                                id="inspector-workflow-selector",
                                                placeholder="Choose a workflow execution to inspect...",
                                                clearable=False,
                                            ),
                                            html.Div(
                                                id="inspector-workflow-info",
                                                className="mt-2",
                                            ),
                                        ]
                                    ),
                                ]
                            )
                        ],
                        width=12,
                    ),
                ],
                className="mb-3",
            ),
            # Main content area
            dbc.Row(
                [
                    # Left sidebar - Node list and timeline
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.H6(
                                                [
                                                    html.I(
                                                        className="fas fa-stream me-2"
                                                    ),
                                                    "Execution Timeline",
                                                ]
                                            )
                                        ]
                                    ),
                                    dbc.CardBody(
                                        [
                                            # Timeline visualization
                                            html.Div(
                                                id="inspector-timeline",
                                                children=[
                                                    dbc.Alert(
                                                        [
                                                            html.I(
                                                                className="fas fa-info-circle me-2"
                                                            ),
                                                            "Select a workflow execution to view timeline",
                                                        ],
                                                        color="info",
                                                    )
                                                ],
                                            ),
                                            html.Hr(),
                                            # Node list
                                            html.H6(
                                                "Nodes", className="fw-bold mb-2"
                                            ),
                                            html.Div(
                                                id="inspector-node-list",
                                                children=[
                                                    html.P(
                                                        "No nodes to display",
                                                        className="text-muted text-center",
                                                    )
                                                ],
                                                style={
                                                    "maxHeight": "400px",
                                                    "overflowY": "auto",
                                                },
                                            ),
                                        ]
                                    ),
                                ],
                                style={"height": "100%"},
                            )
                        ],
                        width=3,
                    ),
                    # Right main panel - I/O data display
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.H6(
                                                [
                                                    html.I(
                                                        className="fas fa-exchange-alt me-2"
                                                    ),
                                                    "Node Input/Output Data",
                                                ]
                                            )
                                        ]
                                    ),
                                    dbc.CardBody(
                                        [
                                            # Tabbed interface for I/O and stats
                                            dbc.Tabs(
                                                [
                                                    dbc.Tab(
                                                        label="📥 Input",
                                                        tab_id="input-tab",
                                                        children=[
                                                            html.Div(
                                                                id="inspector-input-panel",
                                                                className="p-3",
                                                                children=[
                                                                    dbc.Alert(
                                                                        [
                                                                            html.I(
                                                                                className="fas fa-hand-pointer me-2"
                                                                            ),
                                                                            "Select a node to view its input data",
                                                                        ],
                                                                        color="light",
                                                                    )
                                                                ],
                                                            )
                                                        ],
                                                    ),
                                                    dbc.Tab(
                                                        label="📤 Output",
                                                        tab_id="output-tab",
                                                        children=[
                                                            html.Div(
                                                                id="inspector-output-panel",
                                                                className="p-3",
                                                                children=[
                                                                    dbc.Alert(
                                                                        [
                                                                            html.I(
                                                                                className="fas fa-hand-pointer me-2"
                                                                            ),
                                                                            "Select a node to view its output data",
                                                                        ],
                                                                        color="light",
                                                                    )
                                                                ],
                                                            )
                                                        ],
                                                    ),
                                                    dbc.Tab(
                                                        label="📊 Statistics",
                                                        tab_id="stats-tab",
                                                        children=[
                                                            html.Div(
                                                                id="inspector-stats-panel",
                                                                className="p-3",
                                                                children=[
                                                                    dbc.Alert(
                                                                        [
                                                                            html.I(
                                                                                className="fas fa-hand-pointer me-2"
                                                                            ),
                                                                            "Select a node to view execution statistics",
                                                                        ],
                                                                        color="light",
                                                                    )
                                                                ],
                                                            )
                                                        ],
                                                    ),
                                                    dbc.Tab(
                                                        label="🔧 Metadata",
                                                        tab_id="metadata-tab",
                                                        children=[
                                                            html.Div(
                                                                id="inspector-metadata-panel",
                                                                className="p-3",
                                                                children=[
                                                                    dbc.Alert(
                                                                        [
                                                                            html.I(
                                                                                className="fas fa-hand-pointer me-2"
                                                                            ),
                                                                            "Select a node to view execution metadata",
                                                                        ],
                                                                        color="light",
                                                                    )
                                                                ],
                                                            )
                                                        ],
                                                    ),
                                                ],
                                                id="inspector-data-tabs",
                                                active_tab="input-tab",
                                            ),
                                        ],
                                        style={
                                            "minHeight": "600px",
                                            "maxHeight": "800px",
                                            "overflowY": "auto",
                                        },
                                    ),
                                ]
                            )
                        ],
                        width=9,
                    ),
                ],
            ),
        ],
        className="p-3",
    )


def create_node_card(
    node_id: str,
    node_type: str,
    duration_ms: float,
    input_shape: str,
    output_shape: str,
    is_selected: bool = False,
) -> dbc.Card:
    """
    Create a card component for a workflow node in the inspector.

    Args:
        node_id: Unique node identifier
        node_type: Type of the node (load_files, peak_analysis, etc.)
        duration_ms: Execution duration in milliseconds
        input_shape: Summary of input data shape
        output_shape: Summary of output data shape
        is_selected: Whether this node is currently selected

    Returns:
        Card component for the node
    """
    # Color-code by duration
    if duration_ms < 100:
        duration_color = "success"
    elif duration_ms < 500:
        duration_color = "info"
    elif duration_ms < 1000:
        duration_color = "warning"
    else:
        duration_color = "danger"

    # Icon by node type
    node_icons = {
        "load_files": "fas fa-file-import",
        "normalize": "fas fa-adjust",
        "peak_analysis": "fas fa-mountain",
        "export_csv": "fas fa-file-export",
        "background_subtraction": "fas fa-minus-circle",
        "smoothing": "fas fa-wave-square",
    }
    icon = node_icons.get(node_type, "fas fa-cube")

    card_color = "primary" if is_selected else "light"
    border_style = "2px solid" if is_selected else "1px solid"

    # Wrap card in a clickable div since dbc.Card doesn't have n_clicks
    return html.Div(
        dbc.Card(
            [
                dbc.CardBody(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.H6(
                                            [
                                                html.I(className=f"{icon} me-2"),
                                                node_id,
                                            ],
                                            className="mb-1",
                                        ),
                                        html.Small(
                                            node_type,
                                            className="text-muted",
                                        ),
                                    ],
                                    width=8,
                                ),
                                dbc.Col(
                                    [
                                        dbc.Badge(
                                            f"{duration_ms:.1f}ms",
                                            color=duration_color,
                                            className="float-end",
                                        ),
                                    ],
                                    width=4,
                                ),
                            ]
                        ),
                        html.Hr(className="my-2"),
                        html.Div(
                            [
                                html.Small(
                                    [
                                        html.I(className="fas fa-arrow-right me-1"),
                                        f"In: {input_shape}",
                                    ],
                                    className="d-block text-muted",
                                ),
                                html.Small(
                                    [
                                        html.I(className="fas fa-arrow-left me-1"),
                                        f"Out: {output_shape}",
                                    ],
                                    className="d-block text-muted",
                                ),
                            ]
                        ),
                    ]
                )
            ],
            className="mb-2 h-100",
            style={
                "borderColor": card_color,
                "borderWidth": border_style,
                "cursor": "pointer",
            },
        ),
        id={"type": "inspector-node-card", "node_id": node_id},
        className="cursor-pointer",
        style={"cursor": "pointer"},
    )
