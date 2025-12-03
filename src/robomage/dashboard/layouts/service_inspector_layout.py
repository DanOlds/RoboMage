"""
Service Inspector Tab Layout

Interactive visualization and testing interface for RoboMage microservices.
Provides service discovery, health monitoring, API documentation, and testing console.
"""

# ruff: noqa: E501
# Line length exceptions for Dash UI code where breaking lines hurts readability

import dash_bootstrap_components as dbc
from dash import dcc, html


def create_service_inspector_tab() -> html.Div:
    """
    Create the Service Inspector tab with service monitoring and testing.

    Features:
    - Auto-discovery of registered services
    - Real-time health monitoring (5s refresh)
    - Service metadata display
    - API documentation viewer (OpenAPI support)
    - Interactive testing console
    - Manual service registration (optional)

    Returns:
        Service Inspector tab layout component
    """
    return html.Div(
        [
            # Header with refresh/export buttons
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H4(
                                [
                                    html.I(className="fas fa-network-wired me-2"),
                                    "Service Inspector",
                                ],
                                className="text-primary",
                            ),
                            html.P(
                                "Monitor, inspect, and test microservices in the RoboMage ecosystem",
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
                                        id="service-inspector-refresh-btn",
                                        color="primary",
                                        size="sm",
                                        outline=True,
                                    ),
                                    dbc.Button(
                                        [
                                            html.I(className="fas fa-plus me-2"),
                                            "Add Service",
                                        ],
                                        id="service-inspector-add-btn",
                                        color="success",
                                        size="sm",
                                        outline=True,
                                    ),
                                    dbc.Button(
                                        [
                                            html.I(className="fas fa-download me-2"),
                                            "Export",
                                        ],
                                        id="service-inspector-export-btn",
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
            # Status summary bar
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Alert(
                                [
                                    html.I(className="fas fa-info-circle me-2"),
                                    html.Span(
                                        "Discovering services...",
                                        id="service-status-summary",
                                    ),
                                ],
                                color="info",
                                className="mb-0",
                            ),
                        ],
                        width=12,
                    ),
                ],
                className="mb-3",
            ),
            # Main content area
            dbc.Row(
                [
                    # Left sidebar - Service list
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.H6(
                                                [
                                                    html.I(
                                                        className="fas fa-server me-2"
                                                    ),
                                                    "Discovered Services",
                                                ]
                                            )
                                        ]
                                    ),
                                    dbc.CardBody(
                                        [
                                            # Search box
                                            dbc.Input(
                                                id="service-search-input",
                                                placeholder="Search services...",
                                                type="text",
                                                className="mb-3",
                                            ),
                                            # Service type filter
                                            dbc.Label(
                                                "Filter by type:",
                                                className="fw-bold mb-2",
                                            ),
                                            dcc.Dropdown(
                                                id="service-type-filter",
                                                options=[],  # Populated dynamically
                                                placeholder="All types",
                                                clearable=True,
                                                className="mb-3",
                                            ),
                                            html.Hr(),
                                            # Service list
                                            html.Div(
                                                id="service-list-container",
                                                children=[
                                                    dbc.Alert(
                                                        [
                                                            html.I(
                                                                className="fas fa-search me-2"
                                                            ),
                                                            "Discovering services...",
                                                        ],
                                                        color="light",
                                                    )
                                                ],
                                                style={
                                                    "maxHeight": "500px",
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
                    # Right main panel - Service details
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.H6(
                                                [
                                                    html.I(
                                                        className="fas fa-info-circle me-2"
                                                    ),
                                                    html.Span(
                                                        "Service Details",
                                                        id="service-detail-title",
                                                    ),
                                                ]
                                            )
                                        ]
                                    ),
                                    dbc.CardBody(
                                        [
                                            html.Div(
                                                id="service-detail-panel",
                                                children=[
                                                    dbc.Alert(
                                                        [
                                                            html.I(
                                                                className="fas fa-hand-pointer me-2"
                                                            ),
                                                            "Select a service from the list to view details",
                                                        ],
                                                        color="light",
                                                    )
                                                ],
                                                style={
                                                    "minHeight": "600px",
                                                    "maxHeight": "800px",
                                                    "overflowY": "auto",
                                                },
                                            ),
                                        ]
                                    ),
                                ]
                            )
                        ],
                        width=9,
                    ),
                ],
            ),
            # Data stores
            dcc.Store(id="service-inspector-data"),  # All service metadata + health
            dcc.Store(id="selected-service-id"),  # Currently selected service
            # Auto-refresh interval (5 seconds)
            dcc.Interval(
                id="service-health-interval",
                interval=5000,  # 5 seconds
                n_intervals=0,
            ),
            # Modal for adding custom service
            create_add_service_modal(),
        ],
        className="p-3",
    )


def create_add_service_modal() -> dbc.Modal:
    """Create modal for manually adding a service."""
    return dbc.Modal(
        [
            dbc.ModalHeader(
                dbc.ModalTitle(
                    [
                        html.I(className="fas fa-plus me-2"),
                        "Add Custom Service",
                    ]
                )
            ),
            dbc.ModalBody(
                [
                    dbc.Alert(
                        [
                            html.I(className="fas fa-info-circle me-2"),
                            "Manually register a service that's not in the auto-discovery registry.",
                        ],
                        color="info",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Label("Service Name *", className="fw-bold"),
                                    dbc.Input(
                                        id="add-service-name",
                                        placeholder="e.g., custom_analyzer",
                                        type="text",
                                    ),
                                    html.Small(
                                        "Lowercase, no spaces",
                                        className="text-muted",
                                    ),
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [
                                    html.Label("Display Name *", className="fw-bold"),
                                    dbc.Input(
                                        id="add-service-display-name",
                                        placeholder="e.g., Custom Analyzer",
                                        type="text",
                                    ),
                                ],
                                width=6,
                            ),
                        ],
                        className="mb-3",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Label("Base URL *", className="fw-bold"),
                                    dbc.Input(
                                        id="add-service-url",
                                        placeholder="http://localhost:8003",
                                        type="url",
                                    ),
                                    html.Small(
                                        "Full URL including http:// and port",
                                        className="text-muted",
                                    ),
                                ],
                                width=8,
                            ),
                            dbc.Col(
                                [
                                    html.Label("Type", className="fw-bold"),
                                    dcc.Dropdown(
                                        id="add-service-type",
                                        options=[
                                            {"label": "Analysis", "value": "analysis"},
                                            {
                                                "label": "Transform",
                                                "value": "transform",
                                            },
                                            {
                                                "label": "Orchestration",
                                                "value": "orchestration",
                                            },
                                            {"label": "Utility", "value": "utility"},
                                            {"label": "Other", "value": "other"},
                                        ],
                                        value="analysis",
                                        clearable=False,
                                    ),
                                ],
                                width=4,
                            ),
                        ],
                        className="mb-3",
                    ),
                    html.Div(id="add-service-feedback"),
                ]
            ),
            dbc.ModalFooter(
                [
                    dbc.Button("Cancel", id="add-service-cancel", color="secondary"),
                    dbc.Button(
                        "Add Service",
                        id="add-service-confirm",
                        color="success",
                    ),
                ]
            ),
        ],
        id="add-service-modal",
        is_open=False,
        size="lg",
    )
