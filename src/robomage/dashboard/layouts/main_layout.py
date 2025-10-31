"""
Main Dashboard Layout

Primary layout for the RoboMage dashboard with file upload,
data visualization, and analysis controls.
"""

import dash_bootstrap_components as dbc
from dash import dcc, html


def create_main_layout() -> html.Div:
    """
    Create the main dashboard layout.

    Returns:
        Main dashboard layout component
    """
    return dbc.Container(
        [
            # Header
            create_header(),
            html.Hr(),
            # Main content area
            dbc.Row(
                [
                    # Left sidebar - File controls
                    dbc.Col([create_file_controls()], width=3),
                    # Center - Main visualization
                    dbc.Col([create_plot_area()], width=6),
                    # Right sidebar - Analysis controls
                    dbc.Col([create_analysis_controls()], width=3),
                ]
            ),
            # Status bar
            html.Hr(),
            create_status_bar(),
            # Hidden div to store data
            dcc.Store(id="file-data-store"),
            dcc.Store(id="analysis-results-store"),
        ],
        fluid=True,
    )


def create_header() -> dbc.Row:
    """Create the dashboard header."""
    return dbc.Row(
        [
            dbc.Col(
                [
                    html.H1(
                        [
                            html.I(className="fas fa-chart-line me-2"),
                            "RoboMage Dashboard",
                        ],
                        className="text-primary",
                    ),
                    html.P(
                        "Interactive powder diffraction analysis and visualization",
                        className="text-muted",
                    ),
                ],
                width=8,
            ),
            dbc.Col(
                [
                    dbc.Badge("Sprint 4 - Phase 1", color="info", className="me-2"),
                    dbc.Badge("v0.1.0", color="secondary"),
                ],
                width=4,
                className="d-flex align-items-center justify-content-end",
            ),
        ]
    )


def create_file_controls() -> dbc.Card:
    """Create file loading and management controls."""
    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.H5(
                        [html.I(className="fas fa-folder-open me-2"), "File Management"]
                    )
                ]
            ),
            dbc.CardBody(
                [
                    # File upload area
                    html.Div(
                        [
                            html.H6("Load Diffraction Data", className="mb-3"),
                            # File upload component
                            dcc.Upload(
                                id="upload-data",
                                children=html.Div(
                                    [
                                        html.I(
                                            className=(
                                                "fas fa-cloud-upload-alt fa-2x mb-2"
                                            )
                                        ),
                                        html.Br(),
                                        "Drag & Drop or ",
                                        html.A(
                                            "Select Files",
                                            href="#",
                                            className="text-primary",
                                        ),
                                    ],
                                    className="text-center",
                                ),
                                style={
                                    "width": "100%",
                                    "height": "100px",
                                    "lineHeight": "100px",
                                    "borderWidth": "2px",
                                    "borderStyle": "dashed",
                                    "borderRadius": "10px",
                                    "borderColor": "#007bff",
                                    "backgroundColor": "#f8f9fa",
                                },
                                multiple=True,
                            ),
                            html.Hr(),
                            # File list
                            html.H6("Loaded Files", className="mb-2"),
                            html.Div(
                                id="file-list",
                                children=[
                                    html.P(
                                        "No files loaded", className="text-muted small"
                                    )
                                ],
                            ),
                            html.Hr(),
                            # File info
                            html.H6("File Information", className="mb-2"),
                            html.Div(
                                id="file-info",
                                children=[
                                    html.P(
                                        "Select a file to view details",
                                        className="text-muted small",
                                    )
                                ],
                            ),
                        ]
                    )
                ]
            ),
        ]
    )


def create_plot_area() -> dbc.Card:
    """Create the main plotting area."""
    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.H5(
                        [
                            html.I(className="fas fa-chart-area me-2"),
                            "Diffraction Pattern",
                        ]
                    ),
                    dbc.ButtonGroup(
                        [
                            dbc.Button(
                                [html.I(className="fas fa-expand me-1"), "Fullscreen"],
                                size="sm",
                                color="outline-secondary",
                                id="fullscreen-btn",
                            ),
                            dbc.Button(
                                [html.I(className="fas fa-download me-1"), "Export"],
                                size="sm",
                                color="outline-primary",
                                id="export-btn",
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
                    # Main plot
                    dcc.Graph(
                        id="main-plot",
                        config={
                            "displayModeBar": True,
                            "displaylogo": False,
                            "modeBarButtonsToRemove": ["lasso2d", "select2d"],
                            "toImageButtonOptions": {
                                "format": "png",
                                "filename": "diffraction_pattern",
                                "height": 600,
                                "width": 800,
                                "scale": 2,
                            },
                        },
                        style={"height": "500px"},
                    ),
                    # Plot controls
                    html.Hr(),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Label("X-axis:", className="small fw-bold"),
                                    dcc.Dropdown(
                                        id="x-axis-selector",
                                        options=[
                                            {"label": "Q (Å⁻¹)", "value": "q"},
                                            {
                                                "label": "2θ (degrees)",
                                                "value": "two_theta",
                                            },
                                            {
                                                "label": "d-spacing (Å)",
                                                "value": "d_spacing",
                                            },
                                        ],
                                        value="q",
                                        clearable=False,
                                    ),
                                ],
                                width=4,
                            ),
                            dbc.Col(
                                [
                                    html.Label("Y-axis:", className="small fw-bold"),
                                    dcc.Dropdown(
                                        id="y-axis-selector",
                                        options=[
                                            {"label": "Raw Intensity", "value": "raw"},
                                            {
                                                "label": "Normalized",
                                                "value": "normalized",
                                            },
                                            {"label": "Log Scale", "value": "log"},
                                        ],
                                        value="raw",
                                        clearable=False,
                                    ),
                                ],
                                width=4,
                            ),
                            dbc.Col(
                                [
                                    html.Label("Plot Type:", className="small fw-bold"),
                                    dcc.Dropdown(
                                        id="plot-type-selector",
                                        options=[
                                            {"label": "Line Plot", "value": "line"},
                                            {"label": "Scatter", "value": "scatter"},
                                            {"label": "Filled Area", "value": "area"},
                                        ],
                                        value="line",
                                        clearable=False,
                                    ),
                                ],
                                width=4,
                            ),
                        ]
                    ),
                ]
            ),
        ]
    )


def create_analysis_controls() -> dbc.Card:
    """Create analysis parameter controls."""
    return dbc.Card(
        [
            dbc.CardHeader(
                [html.H5([html.I(className="fas fa-cogs me-2"), "Analysis Controls"])]
            ),
            dbc.CardBody(
                [
                    # Peak analysis section
                    html.Div(
                        [
                            html.H6("Peak Analysis", className="mb-3"),
                            # Service status
                            dbc.Alert(
                                [
                                    html.I(className="fas fa-info-circle me-2"),
                                    "Service integration coming in Phase 2",
                                ],
                                color="info",
                                className="small",
                            ),
                            # Analysis parameters (disabled for Phase 1)
                            html.Div(
                                [
                                    html.Label(
                                        "Detection Sensitivity:",
                                        className="small fw-bold",
                                    ),
                                    dcc.Slider(
                                        id="sensitivity-slider",
                                        min=0.1,
                                        max=2.0,
                                        step=0.1,
                                        value=1.0,
                                        marks={
                                            i / 10: str(i / 10) for i in range(1, 21, 5)
                                        },
                                        disabled=True,
                                    ),
                                    html.Br(),
                                    html.Label(
                                        "Profile Type:", className="small fw-bold"
                                    ),
                                    dcc.Dropdown(
                                        id="profile-selector",
                                        options=[
                                            {"label": "Gaussian", "value": "gaussian"},
                                            {
                                                "label": "Lorentzian",
                                                "value": "lorentzian",
                                            },
                                            {"label": "Voigt", "value": "voigt"},
                                        ],
                                        value="gaussian",
                                        disabled=True,
                                    ),
                                    html.Br(),
                                    dbc.Button(
                                        [
                                            html.I(className="fas fa-play me-1"),
                                            "Run Analysis",
                                        ],
                                        color="primary",
                                        className="w-100",
                                        disabled=True,
                                    ),
                                ],
                                className="mb-3",
                            ),
                            html.Hr(),
                            # Results summary
                            html.H6("Results Summary", className="mb-2"),
                            html.Div(
                                id="analysis-summary",
                                children=[
                                    html.P(
                                        "No analysis results",
                                        className="text-muted small",
                                    )
                                ],
                            ),
                        ]
                    )
                ]
            ),
        ]
    )


def create_status_bar() -> dbc.Row:
    """Create the status bar."""
    return dbc.Row(
        [
            dbc.Col(
                [
                    html.Small(
                        [
                            html.I(className="fas fa-circle text-success me-1"),
                            html.Span("Dashboard Ready", id="status-text"),
                        ],
                        className="text-muted",
                    )
                ],
                width=6,
            ),
            dbc.Col(
                [
                    html.Small(
                        [
                            html.Span(
                                "Peak Analysis Service: ", className="text-muted"
                            ),
                            html.Span(
                                "Not Connected",
                                id="service-status",
                                className="text-warning",
                            ),
                        ]
                    )
                ],
                width=6,
                className="text-end",
            ),
        ]
    )
