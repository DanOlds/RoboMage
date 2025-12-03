"""
Service Card Component

Reusable card component for displaying service information in the inspector list.
"""

import dash_bootstrap_components as dbc
from dash import html


def create_service_card(
    service_id: str,
    display_name: str,
    service_type: str,
    port: int,
    health_status: str,
    response_time_ms: float = None,
    is_selected: bool = False,
) -> html.Div:
    """
    Create a card component for a service in the inspector list.

    Args:
        service_id: Unique service identifier
        display_name: Human-readable service name
        service_type: Type of service (analysis, orchestration, etc.)
        port: Service port number
        health_status: Health status ('healthy', 'unhealthy', 'unknown')
        response_time_ms: Response time in milliseconds (optional)
        is_selected: Whether this service is currently selected

    Returns:
        Clickable card component for the service
    """
    # Health indicator styling
    health_colors = {
        "healthy": "success",
        "unhealthy": "danger",
        "unknown": "secondary",
        "checking": "warning",
    }
    health_icons = {
        "healthy": "fas fa-check-circle",
        "unhealthy": "fas fa-times-circle",
        "unknown": "fas fa-question-circle",
        "checking": "fas fa-spinner fa-spin",
    }

    health_color = health_colors.get(health_status, "secondary")
    health_icon = health_icons.get(health_status, "fas fa-question-circle")

    # Type badge colors
    type_colors = {
        "analysis": "primary",
        "orchestration": "primary",  # Changed from "info" to match detail panel
        "transform": "success",
        "utility": "warning",
        "other": "secondary",
    }
    type_color = type_colors.get(service_type, "secondary")

    # Selected state styling
    card_color = "primary" if is_selected else "light"
    border_width = "2px" if is_selected else "1px"

    # Response time badge (if healthy)
    response_badge = None
    if health_status == "healthy" and response_time_ms is not None:
        if response_time_ms < 50:
            badge_color = "success"
        elif response_time_ms < 200:
            badge_color = "info"
        elif response_time_ms < 500:
            badge_color = "warning"
        else:
            badge_color = "danger"

        response_badge = dbc.Badge(
            f"{response_time_ms:.0f}ms",
            color=badge_color,
            className="float-end",
        )

    # Build card content
    card_body = dbc.CardBody(
        [
            # Header row: name + health indicator
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H6(
                                [
                                    html.I(
                                        className=f"{health_icon} me-2",
                                        style={
                                            "color": f"var(--bs-{health_color})"
                                        },
                                    ),
                                    display_name,
                                ],
                                className="mb-1",
                                style={"fontSize": "0.95rem"},
                            ),
                        ],
                        width=12,
                    ),
                ]
            ),
            # Type and port row
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Badge(
                                service_type,
                                color=type_color,
                                className="me-2",
                            ),
                            html.Small(
                                f"Port {port}",
                                className="text-muted",
                            ),
                        ],
                        width=8,
                    ),
                    dbc.Col(
                        [response_badge] if response_badge else [],
                        width=4,
                    ),
                ],
                className="mt-1",
            ),
        ],
        className="p-2",
    )

    # Wrap card in clickable div
    return html.Div(
        [
            dbc.Card(
                [card_body],
                className="mb-2",
                style={
                    "borderColor": card_color,
                    "borderWidth": border_width,
                },
            ),
        ],
        id={"type": "service-card-btn", "service_id": service_id},
        n_clicks=0,
        style={"cursor": "pointer"},
    )


def create_service_list_empty_state() -> dbc.Alert:
    """Create empty state for service list."""
    return dbc.Alert(
        [
            html.I(className="fas fa-exclamation-triangle me-2"),
            html.Div(
                [
                    html.P("No services discovered", className="mb-1 fw-bold"),
                    html.Small(
                        [
                            "Start a service with: ",
                            html.Code("python services/<service_name>/main.py"),
                        ],
                        className="text-muted",
                    ),
                ]
            ),
        ],
        color="warning",
    )


def create_service_list_loading() -> dbc.Alert:
    """Create loading state for service list."""
    return dbc.Alert(
        [
            html.I(className="fas fa-spinner fa-spin me-2"),
            "Discovering services...",
        ],
        color="light",
    )
