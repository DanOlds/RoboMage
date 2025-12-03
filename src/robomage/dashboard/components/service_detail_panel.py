"""
Service Detail Panel Component

Tabbed detail view for displaying comprehensive service information.
"""

import json
from typing import Any

import dash_bootstrap_components as dbc
from dash import dcc, html


def create_service_detail_panel(
    service_data: dict[str, Any],
    health_data: dict[str, Any],
    openapi_schema: dict[str, Any] | None = None,
    active_tab: str = "overview-tab",
) -> html.Div:
    """
    Create a detailed view panel for a selected service.

    Args:
        service_data: Service metadata dictionary
        health_data: Health check response data
        openapi_schema: OpenAPI/Swagger schema (optional)
        active_tab: Currently active tab ID (default: "overview-tab")

    Returns:
        Tabbed detail panel component
    """
    # Extract service info (unused for now - reserved for future enhancements)
    _ = service_data.get("name", "Unknown")  # noqa: F841
    port = service_data.get("port", "N/A")
    host = service_data.get("host", "127.0.0.1")
    base_url = f"http://{host}:{port}"

    # Build tabs
    tabs = [
        create_overview_tab(service_data, health_data),
        create_endpoints_tab(service_data, base_url),
        create_health_tab(health_data, base_url),
        create_api_docs_tab(openapi_schema, base_url),
        create_testing_console_tab(service_data, base_url),
    ]

    return dbc.Tabs(
        tabs,
        id="service-detail-tabs",
        active_tab=active_tab,
    )


def create_overview_tab(
    service_data: dict[str, Any], health_data: dict[str, Any]
) -> dbc.Tab:
    """Create Overview tab with service metadata."""
    # Extract data
    display_name = service_data.get("display_name", "Unknown")
    description = service_data.get("description", "No description")
    version = service_data.get("version", "Unknown")
    service_type = service_data.get("service_type", "unknown")
    port = service_data.get("port", "N/A")
    host = service_data.get("host", "127.0.0.1")
    startup_command = service_data.get("startup_command", "N/A")

    # Dependencies
    dependencies = service_data.get("dependencies", {})
    python_version = dependencies.get("python", "N/A")
    packages = dependencies.get("packages", [])

    # Integration settings
    workflow_integration = service_data.get("workflow_integration", {})
    dashboard_integration = service_data.get("dashboard_integration", {})

    return dbc.Tab(
        label="📋 Overview",
        tab_id="overview-tab",
        children=[
            html.Div(
                [
                    # Basic information
                    html.H5("Basic Information", className="mt-3 mb-3"),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Label("Display Name:", className="fw-bold"),
                                    html.P(display_name),
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [
                                    html.Label("Version:", className="fw-bold"),
                                    html.P(version),
                                ],
                                width=6,
                            ),
                        ]
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Label("Type:", className="fw-bold"),
                                    html.P(
                                        dbc.Badge(
                                            service_type,
                                            color="primary",
                                        )
                                    ),
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [
                                    html.Label("Port:", className="fw-bold"),
                                    html.P(f"{port} ({host})"),
                                ],
                                width=6,
                            ),
                        ]
                    ),
                    html.Label("Description:", className="fw-bold"),
                    html.P(description, className="text-muted"),
                    html.Hr(),
                    # Startup command
                    html.H5("Startup", className="mb-3"),
                    html.Label("Command:", className="fw-bold"),
                    html.Pre(
                        html.Code(startup_command),
                        className="bg-light p-2 rounded",
                    ),
                    html.Hr(),
                    # Dependencies
                    html.H5("Dependencies", className="mb-3"),
                    html.Label("Python Version:", className="fw-bold"),
                    html.P(python_version),
                    html.Label("Required Packages:", className="fw-bold"),
                    html.Ul(
                        [html.Li(pkg) for pkg in packages]
                        if packages
                        else [html.Li("None specified", className="text-muted")]
                    ),
                    html.Hr(),
                    # Integration settings
                    html.H5("Integration Settings", className="mb-3"),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Label(
                                        "Workflow Integration:", className="fw-bold"
                                    ),
                                    html.P(
                                        dbc.Badge(
                                            "Enabled"
                                            if workflow_integration.get(
                                                "enabled", False
                                            )
                                            else "Disabled",
                                            color="success"
                                            if workflow_integration.get(
                                                "enabled", False
                                            )
                                            else "secondary",
                                        )
                                    ),
                                    html.Small(
                                        f"Node types: {', '.join(workflow_integration.get('node_types', []))}"  # noqa: E501
                                        if workflow_integration.get("node_types")
                                        else "No node types",
                                        className="text-muted",
                                    ),
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [
                                    html.Label(
                                        "Dashboard Integration:", className="fw-bold"
                                    ),
                                    html.P(
                                        dbc.Badge(
                                            "Enabled"
                                            if dashboard_integration.get(
                                                "enabled", True
                                            )
                                            else "Disabled",
                                            color="success"
                                            if dashboard_integration.get(
                                                "enabled", True
                                            )
                                            else "secondary",
                                        )
                                    ),
                                    html.Small(
                                        f"Tab: {dashboard_integration.get('tab_name', 'N/A')}"  # noqa: E501
                                        if dashboard_integration.get("tab_name")
                                        else "No dedicated tab",
                                        className="text-muted",
                                    ),
                                ],
                                width=6,
                            ),
                        ]
                    ),
                ],
                className="p-3",
            )
        ],
    )


def create_endpoints_tab(
    service_data: dict[str, Any], base_url: str
) -> dbc.Tab:
    """Create Endpoints tab with API endpoint information."""
    endpoints = service_data.get("endpoints", {})

    endpoint_items = []
    for name, path in endpoints.items():
        full_url = f"{base_url}{path}"
        endpoint_items.append(
            dbc.ListGroupItem(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Strong(name.upper()),
                                    html.Br(),
                                    html.Code(path, className="text-muted"),
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
                                                        className="fas fa-copy me-1"
                                                    ),
                                                    "Copy",
                                                ],
                                                size="sm",
                                                color="secondary",
                                                outline=True,
                                                id={
                                                    "type": "copy-url-btn",
                                                    "url": full_url,
                                                },
                                            ),
                                            dbc.Button(
                                                [
                                                    html.I(
                                                        className="fas fa-external-link-alt me-1"  # noqa: E501
                                                    ),
                                                    "Open",
                                                ],
                                                size="sm",
                                                color="primary",
                                                outline=True,
                                                href=full_url,
                                                target="_blank",
                                                disabled=(name not in ["docs", "root"]),
                                            ),
                                        ]
                                    ),
                                ],
                                width=6,
                                className="text-end",
                            ),
                        ]
                    ),
                ],
                className="mb-2",
            )
        )

    return dbc.Tab(
        label="🔗 Endpoints",
        tab_id="endpoints-tab",
        children=[
            html.Div(
                [
                    html.H5("API Endpoints", className="mt-3 mb-3"),
                    dbc.ListGroup(
                        endpoint_items
                        if endpoint_items
                        else [
                            dbc.ListGroupItem(
                                "No endpoints defined", className="text-muted"
                            )
                        ]
                    ),
                    html.Hr(),
                    dbc.Alert(
                        [
                            html.I(className="fas fa-info-circle me-2"),
                            "Base URL: ",
                            html.Code(base_url),
                        ],
                        color="info",
                    ),
                ],
                className="p-3",
            )
        ],
    )


def create_health_tab(health_data: dict[str, Any], base_url: str) -> dbc.Tab:
    """Create Health tab with service health metrics."""
    status = health_data.get("status", "unknown")
    response_time = health_data.get("response_time_ms")
    error = health_data.get("error")
    details = health_data.get("details", {})

    # Status indicator
    if status == "healthy":
        status_alert = dbc.Alert(
            [
                html.I(className="fas fa-check-circle me-2"),
                html.Strong("Service is healthy"),
            ],
            color="success",
        )
    else:
        status_alert = dbc.Alert(
            [
                html.I(className="fas fa-times-circle me-2"),
                html.Strong("Service is unhealthy"),
                html.Br(),
                html.Small(error if error else "Unknown error", className="text-muted"),
            ],
            color="danger",
        )

    return dbc.Tab(
        label="💚 Health",
        tab_id="health-tab",
        children=[
            html.Div(
                [
                    html.H5("Health Status", className="mt-3 mb-3"),
                    status_alert,
                    # Response time
                    html.Label("Response Time:", className="fw-bold mt-3"),
                    html.P(
                        f"{response_time:.2f} ms"
                        if response_time is not None
                        else "N/A"
                    ),
                    # Health check details
                    html.Label("Health Check Details:", className="fw-bold mt-3"),
                    html.Pre(
                        html.Code(json.dumps(details, indent=2)),
                        className="bg-light p-3 rounded",
                        style={"maxHeight": "300px", "overflowY": "auto"},
                    )
                    if details
                    else html.P("No additional details", className="text-muted"),
                    html.Hr(),
                    dbc.Alert(
                        [
                            html.I(className="fas fa-sync me-2"),
                            "Health checks update every 5 seconds",
                        ],
                        color="info",
                    ),
                ],
                className="p-3",
            )
        ],
    )


def create_api_docs_tab(
    openapi_schema: dict[str, Any] | None, base_url: str
) -> dbc.Tab:
    """Create API Documentation tab with OpenAPI schema display."""
    if not openapi_schema:
        content = dbc.Alert(
            [
                html.I(className="fas fa-info-circle me-2"),
                html.Div(
                    [
                        html.P("OpenAPI schema not available", className="mb-1"),
                        html.Small(
                            [
                                "Visit ",
                                html.A(
                                    f"{base_url}/docs",
                                    href=f"{base_url}/docs",
                                    target="_blank",
                                ),
                                " for interactive API documentation",
                            ],
                            className="text-muted",
                        ),
                    ]
                ),
            ],
            color="warning",
        )
    else:
        # Display OpenAPI schema
        info = openapi_schema.get("info", {})
        paths = openapi_schema.get("paths", {})

        content = html.Div(
            [
                html.H5("API Information", className="mb-3"),
                html.Label("Title:", className="fw-bold"),
                html.P(info.get("title", "N/A")),
                html.Label("Version:", className="fw-bold"),
                html.P(info.get("version", "N/A")),
                html.Label("Description:", className="fw-bold"),
                html.P(info.get("description", "N/A"), className="text-muted"),
                html.Hr(),
                html.H5("Available Endpoints", className="mb-3"),
                create_openapi_paths_display(paths),
                html.Hr(),
                html.Label("Full Schema:", className="fw-bold"),
                html.Pre(
                    html.Code(json.dumps(openapi_schema, indent=2)),
                    className="bg-light p-3 rounded",
                    style={"maxHeight": "400px", "overflowY": "auto"},
                ),
            ]
        )

    return dbc.Tab(
        label="📚 API Docs",
        tab_id="api-docs-tab",
        children=[html.Div([content], className="p-3")],
    )


def create_openapi_paths_display(paths: dict[str, Any]) -> dbc.Accordion:
    """Create accordion display for OpenAPI paths."""
    accordion_items = []

    for path, methods in paths.items():
        for method, details in methods.items():
            if method in ["get", "post", "put", "delete", "patch"]:
                summary = details.get("summary", "No summary")
                description = details.get("description", "No description")

                # Method badge color
                method_colors = {
                    "get": "primary",
                    "post": "success",
                    "put": "warning",
                    "delete": "danger",
                    "patch": "info",
                }

                accordion_items.append(
                    dbc.AccordionItem(
                        [
                            html.P(description, className="mb-2"),
                            html.Label("Request Body:", className="fw-bold mt-2"),
                            html.Pre(
                                html.Code(
                                    json.dumps(
                                        details.get("requestBody", "None"), indent=2
                                    )
                                ),
                                className="bg-light p-2 rounded",
                            )
                            if "requestBody" in details
                            else html.P("None", className="text-muted"),
                            html.Label("Responses:", className="fw-bold mt-2"),
                            html.Pre(
                                html.Code(
                                    json.dumps(details.get("responses", {}), indent=2)
                                ),
                                className="bg-light p-2 rounded",
                            ),
                        ],
                        title=html.Div(
                            [
                                dbc.Badge(
                                    method.upper(),
                                    color=method_colors.get(method, "secondary"),
                                    className="me-2",
                                ),
                                html.Code(path, className="me-2"),
                                html.Small(summary, className="text-muted"),
                            ]
                        ),
                    )
                )

    return (
        dbc.Accordion(accordion_items, start_collapsed=True)
        if accordion_items
        else html.P("No endpoints found", className="text-muted")
    )


def create_testing_console_tab(
    service_data: dict[str, Any],
    base_url: str,
) -> dbc.Tab:
    """Create Testing Console tab for interactive API testing."""
    endpoints = service_data.get("endpoints", {})
    endpoint_options = [
        {"label": f"{name.upper()} {path}", "value": path}
        for name, path in endpoints.items()
    ]

    return dbc.Tab(
        label="🧪 Test Console",
        tab_id="testing-tab",
        children=[
            html.Div(
                [
                    html.H5("API Testing Console", className="mt-3 mb-3"),
                    dbc.Alert(
                        [
                            html.I(className="fas fa-info-circle me-2"),
                            "Send custom requests to test the service API",
                        ],
                        color="info",
                    ),
                    # Request builder
                    dbc.Card(
                        [
                            dbc.CardHeader(
                                html.H6(
                                    [
                                        html.I(className="fas fa-paper-plane me-2"),
                                        "Request",
                                    ]
                                )
                            ),
                            dbc.CardBody(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    html.Label(
                                                        "Method:", className="fw-bold"
                                                    ),
                                                    dcc.Dropdown(
                                                        id="test-method-selector",
                                                        options=[
                                                            {
                                                                "label": "GET",
                                                                "value": "GET",
                                                            },
                                                            {
                                                                "label": "POST",
                                                                "value": "POST",
                                                            },
                                                            {
                                                                "label": "PUT",
                                                                "value": "PUT",
                                                            },
                                                            {
                                                                "label": "DELETE",
                                                                "value": "DELETE",
                                                            },
                                                        ],
                                                        value="POST",
                                                        clearable=False,
                                                    ),
                                                ],
                                                width=3,
                                            ),
                                            dbc.Col(
                                                [
                                                    html.Label(
                                                        "Endpoint:", className="fw-bold"
                                                    ),
                                                    dcc.Dropdown(
                                                        id="test-endpoint-selector",
                                                        options=endpoint_options,
                                                        value=(
                                                            endpoint_options[0]["value"]
                                                            if endpoint_options
                                                            else None
                                                        ),
                                                        clearable=False,
                                                    ),
                                                ],
                                                width=9,
                                            ),
                                        ],
                                        className="mb-3",
                                    ),
                                    html.Label(
                                        "Request Body (JSON):",  # noqa: E501
                                        className="fw-bold",
                                    ),
                                    dcc.Textarea(
                                        id="test-request-body",
                                        placeholder='{\n  "key": "value"\n}',
                                        style={
                                            "width": "100%",
                                            "height": "200px",
                                            "fontFamily": "monospace",
                                        },
                                        className="form-control",
                                    ),
                                    dbc.Button(
                                        [
                                            html.I(className="fas fa-play me-2"),
                                            "Send Request",
                                        ],
                                        id="test-send-request-btn",
                                        color="primary",
                                        className="mt-3",
                                    ),
                                ]
                            ),
                        ],
                        className="mb-3",
                    ),
                    # Response display
                    dbc.Card(
                        [
                            dbc.CardHeader(
                                html.H6(
                                    [
                                        html.I(className="fas fa-reply me-2"),
                                        "Response",
                                    ]
                                )
                            ),
                            dbc.CardBody(
                                [
                                    html.Div(
                                        id="test-response-display",
                                        children=[
                                            html.P(
                                                "Response will appear here after sending a request",  # noqa: E501
                                                className="text-muted",
                                            )
                                        ],
                                    )
                                ]
                            ),
                        ]
                    ),
                ],
                className="p-3",
            )
        ],
    )
