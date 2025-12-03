"""
GSAS-II Refinement Tab Layout

Dedicated interface for testing and developing GSAS-II Rietveld refinement workflows.
Provides standalone refinement capabilities without using the workflow builder.

Features:
    - CHI/XY diffraction data upload
    - CIF structure file selection
    - Instrument parameter file selection
    - Interactive refinement configuration
    - Real-time results display
    - Service health monitoring
"""

import dash_bootstrap_components as dbc
from dash import dcc, html


def create_gsasii_tab() -> html.Div:
    """
    Create the GSAS-II Refinement tab content.

    Returns:
        Tab layout with file selection, configuration, and results display
    """
    return html.Div(
        [
            # Service status banner
            dbc.Alert(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.I(className="fas fa-server me-2"),
                                    html.Strong("GSAS-II Service:"),
                                ],
                                width=2,
                            ),
                            dbc.Col(
                                [
                                    dbc.Badge(
                                        [
                                            html.I(
                                                className="fas fa-times-circle me-1"
                                            ),
                                            "Not Connected",
                                        ],
                                        color="warning",
                                        id="gsasii-service-status-badge",
                                        className="me-2",
                                    ),
                                    html.Small(
                                        "Checking service health...",
                                        id="gsasii-service-status-text",
                                        className="text-muted",
                                    ),
                                ],
                                width=8,
                            ),
                            dbc.Col(
                                [
                                    dbc.Button(
                                        [html.I(className="fas fa-sync me-1"), "Refresh"],
                                        id="gsasii-health-check-btn",
                                        color="link",
                                        size="sm",
                                    ),
                                ],
                                width=2,
                                className="text-end",
                            ),
                        ]
                    ),
                ],
                id="gsasii-service-alert",
                color="info",
                className="mb-3",
            ),
            # Main content area
            dbc.Row(
                [
                    # Left column: File selection
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.H5(
                                                [
                                                    html.I(
                                                        className="fas fa-folder-open me-2"
                                                    ),
                                                    "Data Files",
                                                ]
                                            )
                                        ]
                                    ),
                                    dbc.CardBody(
                                        [
                                            # CHI/XY data file upload
                                            html.Label(
                                                "Diffraction Data (.chi/.xy):",
                                                className="fw-bold mb-2",
                                            ),
                                            dcc.Upload(
                                                id="gsasii-chi-upload",
                                                children=html.Div(
                                                    [
                                                        html.I(
                                                            className="fas fa-cloud-upload-alt fa-2x mb-2"
                                                        ),
                                                        html.Br(),
                                                        html.Small(
                                                            "Click or drag CHI/XY file"
                                                        ),
                                                    ],
                                                    className="text-center p-3",
                                                ),
                                                style={
                                                    "borderWidth": "2px",
                                                    "borderStyle": "dashed",
                                                    "borderRadius": "5px",
                                                    "borderColor": "#007bff",
                                                    "backgroundColor": "#f8f9fa",
                                                },
                                                className="mb-3",
                                            ),
                                            html.Div(
                                                id="gsasii-chi-upload-status",
                                                className="mb-3",
                                            ),
                                            html.Hr(),
                                            # CIF file selection
                                            html.Label(
                                                "Structure File (.cif):",
                                                className="fw-bold mb-2",
                                            ),
                                            dcc.Dropdown(
                                                id="gsasii-cif-select",
                                                options=[
                                                    {
                                                        "label": "LaB6 SRM 660c",
                                                        "value": "LaB6_SRM_660c.CIF",
                                                    },
                                                    {
                                                        "label": "LMT-AlNbO (3)",
                                                        "value": "3_LMTAlNbO-10_start.cif",
                                                    },
                                                    {
                                                        "label": "LMT-GaNbO (4)",
                                                        "value": "4_LMTGaNbO-10_start.cif",
                                                    },
                                                ],
                                                value="LaB6_SRM_660c.CIF",
                                                clearable=False,
                                                className="mb-3",
                                            ),
                                            # Instrument parameter file selection
                                            html.Label(
                                                "Instrument Parameters:",
                                                className="fw-bold mb-2",
                                            ),
                                            dcc.Dropdown(
                                                id="gsasii-inst-select",
                                                options=[
                                                    {
                                                        "label": "PDF 1m (Synchrotron)",
                                                        "value": "PDF_1m.instprm",
                                                    },
                                                    {
                                                        "label": "Dummy Instrument",
                                                        "value": "dummy_instr.instprm",
                                                    },
                                                ],
                                                value="PDF_1m.instprm",
                                                clearable=False,
                                                className="mb-3",
                                            ),
                                            # Phase name input
                                            html.Label(
                                                "Phase Name:",
                                                className="fw-bold mb-2",
                                            ),
                                            dbc.Input(
                                                id="gsasii-phase-name",
                                                type="text",
                                                value="LaB6",
                                                placeholder="Enter phase name...",
                                                className="mb-3",
                                            ),
                                        ]
                                    ),
                                ]
                            )
                        ],
                        width=4,
                    ),
                    # Middle column: Refinement configuration
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.H5(
                                                [
                                                    html.I(
                                                        className="fas fa-sliders-h me-2"
                                                    ),
                                                    "Refinement Settings",
                                                ]
                                            )
                                        ]
                                    ),
                                    dbc.CardBody(
                                        [
                                            # Cycles slider
                                            html.Label(
                                                "Refinement Cycles:",
                                                className="fw-bold mb-2",
                                            ),
                                            dcc.Slider(
                                                id="gsasii-cycles-slider",
                                                min=0,
                                                max=20,
                                                step=1,
                                                value=5,
                                                marks={
                                                    0: "0",
                                                    5: "5",
                                                    10: "10",
                                                    15: "15",
                                                    20: "20",
                                                },
                                                tooltip={
                                                    "placement": "bottom",
                                                    "always_visible": True,
                                                },
                                                className="mb-4",
                                            ),
                                            html.Hr(),
                                            # Refinement flags
                                            html.Label(
                                                "Refinement Options:",
                                                className="fw-bold mb-2",
                                            ),
                                            dbc.Checklist(
                                                id="gsasii-refine-flags",
                                                options=[
                                                    {
                                                        "label": " Refine background",
                                                        "value": "background",
                                                    },
                                                    {
                                                        "label": " Refine cell parameters",
                                                        "value": "cell",
                                                    },
                                                    {
                                                        "label": " Refine size/strain",
                                                        "value": "size_strain",
                                                    },
                                                ],
                                                value=["background", "cell"],
                                                className="mb-3",
                                            ),
                                            html.Hr(),
                                            # Q-range limits
                                            html.Label(
                                                "Q-range Limits (Å⁻¹):",
                                                className="fw-bold mb-2",
                                            ),
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            html.Label(
                                                                "Min:", className="small"
                                                            ),
                                                            dbc.Input(
                                                                id="gsasii-q-min",
                                                                type="number",
                                                                value=0.5,
                                                                step=0.1,
                                                                min=0,
                                                                size="sm",
                                                            ),
                                                        ],
                                                        width=6,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            html.Label(
                                                                "Max:", className="small"
                                                            ),
                                                            dbc.Input(
                                                                id="gsasii-q-max",
                                                                type="number",
                                                                value=16.0,
                                                                step=0.1,
                                                                min=0,
                                                                size="sm",
                                                            ),
                                                        ],
                                                        width=6,
                                                    ),
                                                ]
                                            ),
                                            html.Hr(),
                                            # Run button
                                            dbc.Button(
                                                [
                                                    html.I(className="fas fa-play me-2"),
                                                    "Run Refinement",
                                                ],
                                                id="gsasii-run-btn",
                                                color="primary",
                                                size="lg",
                                                className="w-100 mt-3",
                                            ),
                                            # Progress indicator
                                            dbc.Spinner(
                                                html.Div(id="gsasii-progress"),
                                                color="primary",
                                                spinner_style={"marginTop": "20px"},
                                            ),
                                        ]
                                    ),
                                ]
                            )
                        ],
                        width=4,
                    ),
                    # Right column: Quick help
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.H5(
                                                [
                                                    html.I(
                                                        className="fas fa-info-circle me-2"
                                                    ),
                                                    "Quick Guide",
                                                ]
                                            )
                                        ]
                                    ),
                                    dbc.CardBody(
                                        [
                                            html.H6("Getting Started:", className="fw-bold"),
                                            html.Ol(
                                                [
                                                    html.Li("Upload diffraction data (.chi or .xy)"),
                                                    html.Li("Select structure file (CIF)"),
                                                    html.Li("Select instrument parameters"),
                                                    html.Li("Configure refinement settings"),
                                                    html.Li("Click 'Run Refinement'"),
                                                ],
                                                className="small",
                                            ),
                                            html.Hr(),
                                            html.H6("Default Settings:", className="fw-bold"),
                                            html.Ul(
                                                [
                                                    html.Li(
                                                        "Phase: LaB6 (SRM 660c standard)",
                                                        className="small",
                                                    ),
                                                    html.Li("Cycles: 5", className="small"),
                                                    html.Li(
                                                        "Q-range: 0.5 - 16.0 Å⁻¹",
                                                        className="small",
                                                    ),
                                                    html.Li(
                                                        "Background: 6 coefficients",
                                                        className="small",
                                                    ),
                                                ],
                                            ),
                                            html.Hr(),
                                            html.H6("Expected Results:", className="fw-bold"),
                                            html.Ul(
                                                [
                                                    html.Li(
                                                        "LaB6: a ≈ 4.157 Å", className="small"
                                                    ),
                                                    html.Li(
                                                        "Rwp ≈ 7-8%", className="small"
                                                    ),
                                                    html.Li(
                                                        "Execution: ~4-5 seconds",
                                                        className="small",
                                                    ),
                                                ],
                                            ),
                                        ]
                                    ),
                                ]
                            )
                        ],
                        width=4,
                    ),
                ],
                className="mb-3",
            ),
            # Debug panel (collapsible)
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.H5(
                                                [
                                                    html.I(className="fas fa-bug me-2"),
                                                    "Debug Information",
                                                ],
                                                className="d-inline",
                                            ),
                                            dbc.Button(
                                                [
                                                    html.I(className="fas fa-chevron-down me-1"),
                                                    "Show/Hide",
                                                ],
                                                id="gsasii-toggle-debug-btn",
                                                color="link",
                                                size="sm",
                                                className="float-end",
                                            ),
                                        ],
                                        className="d-flex justify-content-between align-items-center",
                                    ),
                                    dbc.Collapse(
                                        dbc.CardBody(
                                            [
                                                dbc.Tabs(
                                                    [
                                                        dbc.Tab(
                                                            [
                                                                html.Pre(
                                                                    id="gsasii-debug-request",
                                                                    children="No request sent yet",
                                                                    style={
                                                                        "backgroundColor": "#f8f9fa",
                                                                        "padding": "10px",
                                                                        "borderRadius": "5px",
                                                                        "maxHeight": "400px",
                                                                        "overflowY": "auto",
                                                                        "fontSize": "12px",
                                                                    },
                                                                )
                                                            ],
                                                            label="Request JSON",
                                                            tab_id="request-tab",
                                                        ),
                                                        dbc.Tab(
                                                            [
                                                                html.Pre(
                                                                    id="gsasii-debug-response",
                                                                    children="No response received yet",
                                                                    style={
                                                                        "backgroundColor": "#f8f9fa",
                                                                        "padding": "10px",
                                                                        "borderRadius": "5px",
                                                                        "maxHeight": "400px",
                                                                        "overflowY": "auto",
                                                                        "fontSize": "12px",
                                                                    },
                                                                )
                                                            ],
                                                            label="Response JSON",
                                                            tab_id="response-tab",
                                                        ),
                                                        dbc.Tab(
                                                            [
                                                                html.Div(
                                                                    id="gsasii-debug-summary",
                                                                    children=[
                                                                        dbc.Alert(
                                                                            "Run a refinement to see debug info",
                                                                            color="info",
                                                                        )
                                                                    ],
                                                                )
                                                            ],
                                                            label="Summary",
                                                            tab_id="summary-tab",
                                                        ),
                                                    ],
                                                    id="gsasii-debug-tabs",
                                                    active_tab="request-tab",
                                                ),
                                            ]
                                        ),
                                        id="gsasii-debug-collapse",
                                        is_open=False,
                                    ),
                                ]
                            )
                        ],
                        width=12,
                    ),
                ]
            ),
            html.Br(),
            # Results area
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.H5(
                                                [
                                                    html.I(
                                                        className="fas fa-chart-bar me-2"
                                                    ),
                                                    "Refinement Results",
                                                ]
                                            ),
                                            dbc.ButtonGroup(
                                                [
                                                    dbc.Button(
                                                        [
                                                            html.I(
                                                                className="fas fa-download me-1"
                                                            ),
                                                            "Download GPX",
                                                        ],
                                                        id="gsasii-download-gpx-btn",
                                                        color="outline-primary",
                                                        size="sm",
                                                        disabled=True,
                                                    ),
                                                    dbc.Button(
                                                        [
                                                            html.I(
                                                                className="fas fa-image me-1"
                                                            ),
                                                            "Save Plot",
                                                        ],
                                                        id="gsasii-download-plot-btn",
                                                        color="outline-secondary",
                                                        size="sm",
                                                        disabled=True,
                                                    ),
                                                ],
                                                size="sm",
                                                className="ms-auto",
                                            ),
                                        ],
                                        className="d-flex justify-content-between align-items-center",
                                    ),
                                    dbc.CardBody(
                                        [
                                            html.Div(
                                                id="gsasii-results-container",
                                                children=[
                                                    dbc.Alert(
                                                        [
                                                            html.I(
                                                                className="fas fa-info-circle me-2"
                                                            ),
                                                            "Run a refinement to see results here.",
                                                        ],
                                                        color="info",
                                                    )
                                                ],
                                            )
                                        ],
                                        style={
                                            "maxHeight": "600px",
                                            "overflowY": "auto",
                                        },
                                    ),
                                ]
                            )
                        ],
                        width=12,
                    ),
                ]
            ),
            # Hidden stores for data management
            dcc.Store(id="gsasii-chi-data-store"),
            dcc.Store(id="gsasii-refinement-result-store"),
            dcc.Store(id="gsasii-debug-request-store"),
            dcc.Store(id="gsasii-debug-response-store"),
            # Interval for health check
            dcc.Interval(
                id="gsasii-health-interval",
                interval=10000,  # Check every 10 seconds
                n_intervals=0,
            ),
        ],
        className="p-3",
    )
