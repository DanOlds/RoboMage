"""
Main Dashboard Layout

Phase 1.5: Professional tab-based layout for the RoboMage dashboard
with Data Import, Visualization, and Analysis tabs.
"""

import dash_bootstrap_components as dbc
from dash import dcc, html


def create_main_layout() -> html.Div:
    """
    Create the main dashboard layout with tab-based interface.

    Returns:
        Main dashboard layout component with 3 tabs
    """
    return dbc.Container(
        [
            # Header
            create_header(),
            html.Hr(),
            # Tab-based interface
            dbc.Tabs(
                [
                    dbc.Tab(
                        label="📁 Data Import",
                        tab_id="import",
                        children=[create_import_tab()],
                    ),
                    dbc.Tab(
                        label="📊 Visualization",
                        tab_id="visualization",
                        children=[create_visualization_tab()],
                    ),
                    dbc.Tab(
                        label="🔬 Analysis",
                        tab_id="analysis",
                        children=[create_analysis_tab()],
                    ),
                ],
                id="main-tabs",
                active_tab="import",
                className="mt-3",
            ),
            # Status bar
            html.Hr(),
            create_status_bar(),
            # Session management modals
            create_save_session_modal(),
            create_load_session_modal(),
            create_manage_sessions_modal(),
            # Data stores for inter-tab communication
            dcc.Store(id="file-data-store"),
            dcc.Store(id="wavelength-store"),
            dcc.Store(id="analysis-results-store"),
            # Session management stores
            dcc.Store(id="current-session-id"),
        ],
        fluid=True,
    )


def create_header() -> dbc.Row:
    """Create the dashboard header with session management buttons."""
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
                width=6,
            ),
            dbc.Col(
                [
                    # Session management buttons
                    dbc.ButtonGroup(
                        [
                            dbc.Button(
                                [html.I(className="fas fa-save me-2"), "Save Session"],
                                id="save-session-button",
                                color="success",
                                size="sm",
                                className="me-1",
                            ),
                            dbc.Button(
                                [
                                    html.I(className="fas fa-folder-open me-2"),
                                    "Load Session",
                                ],
                                id="load-session-button",
                                color="primary",
                                size="sm",
                                className="me-1",
                            ),
                            dbc.Button(
                                [html.I(className="fas fa-list me-2"), "Manage"],
                                id="manage-sessions-button",
                                color="info",
                                size="sm",
                            ),
                        ],
                        className="mb-2",
                    ),
                ],
                width=4,
                className="d-flex align-items-center justify-content-end flex-column",
            ),
            dbc.Col(
                [
                    dbc.Badge("Sprint 5 - Persistence", color="info", className="me-2"),
                    dbc.Badge("v0.2.0", color="secondary"),
                ],
                width=2,
                className="d-flex align-items-center justify-content-end",
            ),
        ]
    )


def create_import_tab() -> html.Div:
    """Create the Data Import tab content."""
    _icon_class = "fas fa-cloud-upload-alt fa-3x mb-3"
    _text_class = "text-muted"
    return html.Div(
        [
            dbc.Row(
                [
                    # File upload section
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.H5(
                                                [
                                                    html.I(
                                                        className=(
                                                            "fas fa-folder-open me-2"
                                                        )
                                                    ),
                                                    "File Upload",
                                                ]
                                            )
                                        ]
                                    ),
                                    dbc.CardBody(
                                        [
                                            dcc.Upload(
                                                id="upload-data",
                                                children=html.Div(
                                                    [
                                                        html.I(className=_icon_class),
                                                        html.Br(),
                                                        html.H5(
                                                            "Drag & Drop or "
                                                            "Select Files",
                                                        ),
                                                        html.P(
                                                            [
                                                                "Supported formats:",
                                                                html.Br(),
                                                                ".chi, .dat, .xy",
                                                            ],
                                                            className=_text_class,
                                                        ),
                                                    ],
                                                    className="text-center p-4",
                                                ),
                                                style={
                                                    "width": "100%",
                                                    "height": "200px",
                                                    "lineHeight": "40px",
                                                    "borderWidth": "2px",
                                                    "borderStyle": "dashed",
                                                    "borderRadius": "10px",
                                                    "borderColor": "#007bff",
                                                    "backgroundColor": "#f8f9fa",
                                                },
                                                multiple=True,
                                            ),
                                        ]
                                    ),
                                ]
                            )
                        ],
                        width=6,
                    ),
                    # Wavelength selection section
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.H5(
                                                [
                                                    html.I(
                                                        className=(
                                                            "fas fa-wave-square me-2"
                                                        ),
                                                    ),
                                                    "Wavelength Settings",
                                                ]
                                            )
                                        ]
                                    ),
                                    dbc.CardBody(
                                        [
                                            html.Label(
                                                "X-ray Source:",
                                                className="fw-bold mb-2",
                                            ),
                                            dcc.Dropdown(
                                                id="wavelength-selector",
                                                options=[
                                                    {
                                                        "label": (
                                                            "Synchrotron (0.1665 Å) - "
                                                            "74.5 keV"
                                                        ),
                                                        "value": 0.1665,
                                                    },
                                                    {
                                                        "label": (
                                                            "Cu Kα (1.5406 Å) - "
                                                            "8.05 keV"
                                                        ),
                                                        "value": 1.5406,
                                                    },
                                                    {
                                                        "label": (
                                                            "Mo Kα (0.7107 Å) - "
                                                            "17.44 keV"
                                                        ),
                                                        "value": 0.7107,
                                                    },
                                                    {
                                                        "label": (
                                                            "Cr Kα (2.2897 Å) - "
                                                            "5.41 keV"
                                                        ),
                                                        "value": 2.2897,
                                                    },
                                                    {
                                                        "label": "Custom...",
                                                        "value": "custom",
                                                    },
                                                ],
                                                value=0.1665,
                                                # Default to synchrotron as specified
                                                clearable=False,
                                                className="mb-3",
                                            ),
                                            # Custom wavelength input
                                            # (hidden by default)
                                            html.Div(
                                                [
                                                    html.Label(
                                                        "Custom Wavelength (Å):",
                                                        className="fw-bold mb-2",
                                                    ),
                                                    dbc.Input(
                                                        id="custom-wavelength-input",
                                                        type="number",
                                                        placeholder=(
                                                            "Enter wavelength in Å"
                                                        ),
                                                        step=0.0001,
                                                        min=0.1,
                                                        max=10.0,
                                                    ),
                                                ],
                                                id="custom-wavelength-div",
                                                style={"display": "none"},
                                            ),
                                            html.Hr(),
                                            # Current wavelength display
                                            dbc.Alert(
                                                [
                                                    html.I(
                                                        className=(
                                                            "fas fa-info-circle me-2"
                                                        ),
                                                    ),
                                                    html.Span(
                                                        "Current wavelength: ",
                                                        className="fw-bold",
                                                    ),
                                                    html.Span(
                                                        "0.1665 Å",
                                                        id="current-wavelength-display",
                                                    ),
                                                ],
                                                color="info",
                                                className="mb-0",
                                            ),
                                        ]
                                    ),
                                ]
                            )
                        ],
                        width=6,
                    ),
                ]
            ),
            html.Br(),
            # Loaded files section
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
                                                        className="fas fa-files me-2"
                                                    ),
                                                    "Loaded Files",
                                                ]
                                            )
                                        ]
                                    ),
                                    dbc.CardBody(
                                        [
                                            html.Div(
                                                id="file-list",
                                                children=[
                                                    html.P(
                                                        "No files loaded",
                                                        className=(
                                                            "text-muted text-center"
                                                        ),
                                                    )
                                                ],
                                            )
                                        ]
                                    ),
                                ]
                            )
                        ],
                        width=8,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.H5(
                                                [
                                                    html.I(
                                                        className=(
                                                            "fas fa-info-circle me-2"
                                                        ),
                                                    ),
                                                    "File Information",
                                                ]
                                            )
                                        ]
                                    ),
                                    dbc.CardBody(
                                        [
                                            html.Div(
                                                id="file-info",
                                                children=[
                                                    html.P(
                                                        "Select a file to view details",
                                                        className=(
                                                            "text-muted text-center"
                                                        ),
                                                    )
                                                ],
                                            )
                                        ]
                                    ),
                                ]
                            )
                        ],
                        width=4,
                    ),
                ]
            ),
        ],
        className="mt-3",
    )


def create_save_session_modal() -> dbc.Modal:
    """Create modal for saving current session."""
    return dbc.Modal(
        [
            dbc.ModalHeader(
                dbc.ModalTitle([html.I(className="fas fa-save me-2"), "Save Session"])
            ),
            dbc.ModalBody(
                [
                    dbc.Label("Session Name *", html_for="session-name-input"),
                    dbc.Input(
                        id="session-name-input",
                        placeholder="Enter a unique session name...",
                        type="text",
                        required=True,
                    ),
                    dbc.FormText("Give your session a descriptive name"),
                    html.Br(),
                    dbc.Label("Description", html_for="session-description-input"),
                    dbc.Textarea(
                        id="session-description-input",
                        placeholder="Optional: Describe what this session contains...",
                        style={"height": "100px"},
                    ),
                    html.Br(),
                    html.Div(id="save-session-feedback"),
                ]
            ),
            dbc.ModalFooter(
                [
                    dbc.Button("Cancel", id="save-session-cancel", color="secondary"),
                    dbc.Button(
                        "Save",
                        id="save-session-confirm",
                        color="success",
                    ),
                ]
            ),
        ],
        id="save-session-modal",
        is_open=False,
        size="lg",
    )


def create_load_session_modal() -> dbc.Modal:
    """Create modal for loading a saved session."""
    return dbc.Modal(
        [
            dbc.ModalHeader(
                dbc.ModalTitle(
                    [html.I(className="fas fa-folder-open me-2"), "Load Session"]
                )
            ),
            dbc.ModalBody(
                [
                    html.P(
                        "Select a session to load:",
                        className="fw-bold mb-3",
                    ),
                    html.Div(id="session-list-container"),
                    html.Div(id="load-session-feedback"),
                ]
            ),
            dbc.ModalFooter(
                [
                    dbc.Button("Cancel", id="load-session-cancel", color="secondary"),
                ]
            ),
        ],
        id="load-session-modal",
        is_open=False,
        size="xl",
    )


def create_manage_sessions_modal() -> dbc.Modal:
    """Create modal for managing saved sessions."""
    return dbc.Modal(
        [
            dbc.ModalHeader(
                dbc.ModalTitle(
                    [html.I(className="fas fa-list me-2"), "Manage Sessions"]
                )
            ),
            dbc.ModalBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.P(
                                        "Saved Sessions:",
                                        className="fw-bold mb-3",
                                    ),
                                ],
                                width=8,
                            ),
                            dbc.Col(
                                [
                                    dbc.Button(
                                        [
                                            html.I(className="fas fa-sync me-2"),
                                            "Refresh",
                                        ],
                                        id="refresh-sessions-button",
                                        color="info",
                                        size="sm",
                                    ),
                                ],
                                width=4,
                                className="text-end",
                            ),
                        ]
                    ),
                    html.Div(id="manage-sessions-container"),
                    html.Div(id="manage-sessions-feedback"),
                ]
            ),
            dbc.ModalFooter(
                [
                    dbc.Button("Close", id="manage-sessions-close", color="secondary"),
                ]
            ),
        ],
        id="manage-sessions-modal",
        is_open=False,
        size="xl",
    )


def create_visualization_tab() -> html.Div:
    """Create the Visualization tab content."""
    return html.Div(
        [
            # Main plot area
            dbc.Card(
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
                                        [
                                            html.I(className="fas fa-expand me-1"),
                                            "Fullscreen",
                                        ],
                                        size="sm",
                                        color="outline-secondary",
                                        id="fullscreen-btn",
                                    ),
                                    dbc.Button(
                                        [
                                            html.I(className="fas fa-download me-1"),
                                            "Export",
                                        ],
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
                        ]
                    ),
                ]
            ),
            html.Br(),
            # Plot controls
            dbc.Card(
                [
                    dbc.CardHeader(
                        [
                            html.H5(
                                [
                                    html.I(className="fas fa-sliders-h me-2"),
                                    "Plot Controls",
                                ]
                            )
                        ]
                    ),
                    dbc.CardBody(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Label("X-axis:", className="fw-bold"),
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
                                            html.Label("Y-axis:", className="fw-bold"),
                                            dcc.Dropdown(
                                                id="y-axis-selector",
                                                options=[
                                                    {
                                                        "label": "Raw Intensity",
                                                        "value": "raw",
                                                    },
                                                    {
                                                        "label": "Normalized",
                                                        "value": "normalized",
                                                    },
                                                    {
                                                        "label": "Log Scale",
                                                        "value": "log",
                                                    },
                                                ],
                                                value="raw",
                                                clearable=False,
                                            ),
                                        ],
                                        width=4,
                                    ),
                                    dbc.Col(
                                        [
                                            html.Label(
                                                "Plot Type:", className="fw-bold"
                                            ),
                                            dcc.Dropdown(
                                                id="plot-type-selector",
                                                options=[
                                                    {
                                                        "label": "Line Plot",
                                                        "value": "line",
                                                    },
                                                    {
                                                        "label": "Scatter Points",
                                                        "value": "scatter",
                                                    },
                                                    {
                                                        "label": (
                                                            "Filled Area (Stacked)"
                                                        ),
                                                        "value": "area",
                                                    },
                                                ],
                                                value="line",
                                                clearable=False,
                                            ),
                                        ],
                                        width=4,
                                    ),
                                ]
                            ),
                            html.Hr(),
                            # Plot statistics
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.H6(
                                                "Plot Statistics", className="fw-bold"
                                            ),
                                            html.Div(
                                                id="plot-statistics",
                                                children=[
                                                    html.P(
                                                        "Load data to view statistics",
                                                        className="text-muted",
                                                    )
                                                ],
                                            ),
                                        ],
                                        width=12,
                                    ),
                                ]
                            ),
                        ]
                    ),
                ]
            ),
        ],
        className="p-3",
    )


def create_analysis_tab() -> html.Div:
    """Create the Analysis tab content with peak analysis integration."""
    return html.Div(
        [
            dbc.Row(
                [
                    # Peak analysis controls
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.H5(
                                                [
                                                    html.I(
                                                        className="fas fa-mountain me-2"
                                                    ),
                                                    "Peak Analysis Controls",
                                                ]
                                            )
                                        ]
                                    ),
                                    dbc.CardBody(
                                        [
                                            # Analysis parameters
                                            html.Div(
                                                [
                                                    html.Label(
                                                        "Profile Type:",
                                                        className="fw-bold",
                                                    ),
                                                    dcc.Dropdown(
                                                        id="profile-selector",
                                                        options=[
                                                            {
                                                                "label": "Gaussian",
                                                                "value": "gaussian",
                                                            },
                                                            {
                                                                "label": "Lorentzian",
                                                                "value": "lorentzian",
                                                            },
                                                            {
                                                                "label": "Voigt",
                                                                "value": "voigt",
                                                            },
                                                        ],
                                                        value="gaussian",
                                                        clearable=False,
                                                        className="mb-3",
                                                    ),
                                                    html.Label(
                                                        "Minimum Prominence:",
                                                        className="fw-bold",
                                                    ),
                                                    html.Small(
                                                        (
                                                            "Relative peak prominence "
                                                            "(0-1)"
                                                        ),
                                                        className=(
                                                            "text-muted d-block mb-1"
                                                        ),
                                                    ),
                                                    dcc.Input(
                                                        id="min-prominence-input",
                                                        type="number",
                                                        min=0.001,
                                                        max=1.0,
                                                        step=0.01,
                                                        value=0.01,
                                                        className="form-control mb-3",
                                                    ),
                                                    html.Label(
                                                        "Minimum Distance (Å⁻¹):",
                                                        className="fw-bold",
                                                    ),
                                                    html.Small(
                                                        "Minimum Q-space between peaks",
                                                        className=(
                                                            "text-muted d-block mb-1"
                                                        ),
                                                    ),
                                                    dcc.Input(
                                                        id="min-distance-input",
                                                        type="number",
                                                        min=0.01,
                                                        max=5.0,
                                                        step=0.01,
                                                        value=0.1,
                                                        className="form-control mb-3",
                                                    ),
                                                    html.Label(
                                                        "Detection Sensitivity:",
                                                        className="fw-bold",
                                                    ),
                                                    dcc.Slider(
                                                        id="sensitivity-slider",
                                                        min=0.1,
                                                        max=2.0,
                                                        step=0.1,
                                                        value=1.0,
                                                        marks={
                                                            0.5: "0.5",
                                                            1.0: "1.0",
                                                            1.5: "1.5",
                                                            2.0: "2.0",
                                                        },
                                                        className="mb-4",
                                                    ),
                                                    dbc.Button(
                                                        [
                                                            html.I(
                                                                className=(
                                                                    "fas fa-play me-2"
                                                                )
                                                            ),
                                                            "Run Analysis",
                                                        ],
                                                        id="run-analysis-btn",
                                                        color="primary",
                                                        size="lg",
                                                        className="w-100",
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
                    # Results area
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.H5(
                                                [
                                                    html.I(
                                                        className=(
                                                            "fas fa-chart-bar me-2"
                                                        )
                                                    ),
                                                    "Analysis Results",
                                                ]
                                            )
                                        ]
                                    ),
                                    dbc.CardBody(
                                        [
                                            html.Div(
                                                id="analysis-summary",
                                                children=[
                                                    dbc.Alert(
                                                        [
                                                            html.I(
                                                                className=(
                                                                    "fas "
                                                                    "fa-info-circle "
                                                                    "me-2"
                                                                )
                                                            ),
                                                            (
                                                                "Click 'Run Analysis'"
                                                                " to detect peaks in"
                                                                " your data."
                                                            ),
                                                            html.Br(),
                                                            html.Small(
                                                                "Make sure files are "
                                                                "loaded in the Data "
                                                                "Import tab.",
                                                                className="text-muted",
                                                            ),
                                                        ],
                                                        color="info",
                                                    )
                                                ],
                                            )
                                        ],
                                        style={
                                            "maxHeight": "500px",
                                            "overflowY": "auto",
                                        },
                                    ),
                                ]
                            )
                        ],
                        width=6,
                    ),
                ]
            ),
            html.Br(),
            # Service connection status
            dbc.Card(
                [
                    dbc.CardHeader(
                        [
                            html.H5(
                                [
                                    html.I(className="fas fa-server me-2"),
                                    "Service Status",
                                ]
                            )
                        ]
                    ),
                    dbc.CardBody(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.P(
                                                "Peak Analysis Service:",
                                                className=("fw-bold mb-1"),
                                            ),
                                            dbc.Badge(
                                                [
                                                    html.I(
                                                        className=(
                                                            "fas fa-times-circle me-1"
                                                        )
                                                    ),
                                                    "Not Connected",
                                                ],
                                                color="warning",
                                                id="service-status-badge",
                                            ),
                                        ],
                                        width=8,
                                    ),
                                    dbc.Col(
                                        [
                                            html.Small(
                                                [
                                                    "Start service: ",
                                                    html.Code(
                                                        "python services/peak_analysis/"
                                                        "main.py",
                                                        className="text-muted",
                                                    ),
                                                ],
                                                className="text-muted",
                                            ),
                                        ],
                                        width=4,
                                        className="d-flex align-items-center",
                                    ),
                                ]
                            ),
                        ]
                    ),
                ]
            ),
        ],
        className="p-3",
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
