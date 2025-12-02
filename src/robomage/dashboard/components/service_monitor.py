"""Generic Service Monitor Component.

This module provides reusable components for monitoring and displaying
the health status of registered microservices in the RoboMage dashboard.
"""

import logging
from typing import Any, Dict, List, Optional

import dash_bootstrap_components as dbc
from dash import html

from robomage.clients.base_service_client import BaseServiceClient, ServiceError
from robomage.service_registry import ServiceRegistry
from robomage.service_registry.models import ServiceMetadata

logger = logging.getLogger(__name__)


def create_service_status_badge(
    service: ServiceMetadata,
    is_connected: bool,
    additional_info: Optional[str] = None,
) -> dbc.Badge:
    """Create a status badge for a service.

    Args:
        service: Service metadata
        is_connected: Whether service is currently connected
        additional_info: Optional additional status information

    Returns:
        Dash Bootstrap Badge component
    """
    if is_connected:
        icon = html.I(className="fas fa-check-circle me-1")
        text = "Connected"
        color = "success"
    else:
        icon = html.I(className="fas fa-times-circle me-1")
        text = "Not Connected"
        color = "warning"

    if additional_info:
        text = f"{text} • {additional_info}"

    return dbc.Badge(
        [icon, text],
        color=color,
        className="ms-2",
    )


def create_service_status_row(
    service: ServiceMetadata,
    badge_id: str,
    show_startup_command: bool = True,
) -> html.Div:
    """Create a status row for a service.

    Args:
        service: Service metadata
        badge_id: HTML ID for the status badge
        show_startup_command: Whether to show startup command when disconnected

    Returns:
        Dash HTML Div component
    """
    return html.Div(
        [
            html.Div(
                [
                    html.I(className=f"{service.dashboard_integration.icon} me-2"),
                    html.Strong(f"{service.display_name}:"),
                    html.Span(id=badge_id),
                ],
                className="d-flex align-items-center",
            ),
            html.Div(
                id=f"{badge_id}-startup-help",
                className="ms-4 mt-1 small text-muted",
            )
            if show_startup_command
            else None,
        ],
        className="mb-2",
    )


def create_service_status_panel(
    registry: Optional[ServiceRegistry] = None,
    service_filter: Optional[str] = None,
) -> html.Div:
    """Create a status panel for all registered services.

    Args:
        registry: ServiceRegistry instance (creates new if None)
        service_filter: Optional service type filter (e.g., 'analysis')

    Returns:
        Dash HTML Div component with service status panel
    """
    if registry is None:
        registry = ServiceRegistry()
        try:
            registry.load_registry()
        except Exception as e:
            logger.error(f"Failed to load service registry: {e}")
            return html.Div(
                dbc.Alert(
                    "Failed to load service registry",
                    color="danger",
                ),
                className="mb-3",
            )

    # Get services
    if service_filter:
        services = registry.get_services_by_type(service_filter)
    else:
        services = registry.get_all_services()

    if not services:
        return html.Div(
            dbc.Alert(
                "No services registered",
                color="info",
            ),
            className="mb-3",
        )

    # Create status rows for each service
    status_rows = []
    for service in services:
        if not service.dashboard_integration.enabled:
            continue

        badge_id = f"service-status-{service.name}"
        status_rows.append(
            create_service_status_row(
                service=service,
                badge_id=badge_id,
                show_startup_command=True,
            )
        )

    return html.Div(
        status_rows,
        className="service-status-panel",
    )


def check_service_health(
    service: ServiceMetadata,
    timeout: float = 2.0,
) -> Dict[str, Any]:
    """Check health of a specific service.

    Args:
        service: Service metadata
        timeout: Request timeout in seconds

    Returns:
        Dictionary with:
            - is_connected: bool
            - status_data: Optional health response data
            - error: Optional error message
    """
    try:
        client = BaseServiceClient(
            service_metadata=service,
            timeout=timeout,
        )
        health_data = client.health_check()

        return {
            "is_connected": True,
            "status_data": health_data,
            "error": None,
        }
    except ServiceError as e:
        logger.debug(f"Service {service.name} not available: {e.message}")
        return {
            "is_connected": False,
            "status_data": None,
            "error": e.message,
        }
    except Exception as e:
        logger.debug(f"Unexpected error checking {service.name}: {e}")
        return {
            "is_connected": False,
            "status_data": None,
            "error": str(e),
        }


def create_service_badge_outputs(
    service: ServiceMetadata,
    health_result: Dict[str, Any],
) -> tuple:
    """Create badge and help text outputs for a service.

    Args:
        service: Service metadata
        health_result: Result from check_service_health()

    Returns:
        Tuple of (badge_component, help_text_component)
    """
    is_connected = health_result["is_connected"]
    status_data = health_result.get("status_data", {})

    # Extract additional info from health data if available
    additional_info = None
    if is_connected and status_data:
        # Try to extract useful info from health response
        if "version" in status_data:
            additional_info = f"v{status_data['version']}"
        elif "workflows_count" in status_data:  # Workflow service
            additional_info = (
                f"{status_data['workflows_count']} workflows, "
                f"{status_data.get('node_types_registered', 0)} nodes"
            )

    badge = create_service_status_badge(
        service=service,
        is_connected=is_connected,
        additional_info=additional_info,
    )

    # Create help text for disconnected services
    if not is_connected:
        help_text = html.Div(
            [
                html.I(className="fas fa-info-circle me-1"),
                "Start with: ",
                html.Code(
                    service.format_startup_command(),
                    className="ms-1",
                ),
            ],
            className="text-muted small",
        )
    else:
        help_text = None

    return badge, help_text


def get_all_service_badge_ids(
    registry: Optional[ServiceRegistry] = None,
) -> List[str]:
    """Get list of all service badge IDs for callback registration.

    Args:
        registry: ServiceRegistry instance (creates new if None)

    Returns:
        List of badge ID strings
    """
    if registry is None:
        registry = ServiceRegistry()
        try:
            registry.load_registry()
        except Exception:
            return []

    badge_ids = []
    for service in registry.get_all_services():
        if service.dashboard_integration.enabled:
            badge_ids.append(f"service-status-{service.name}")

    return badge_ids


def check_all_services_health(
    registry: Optional[ServiceRegistry] = None,
    timeout: float = 2.0,
) -> Dict[str, Dict[str, Any]]:
    """Check health of all registered services.

    Args:
        registry: ServiceRegistry instance (creates new if None)
        timeout: Request timeout in seconds

    Returns:
        Dictionary mapping service names to health results
    """
    if registry is None:
        registry = ServiceRegistry()
        try:
            registry.load_registry()
        except Exception as e:
            logger.error(f"Failed to load service registry: {e}")
            return {}

    results = {}
    for service in registry.get_all_services():
        if service.dashboard_integration.enabled:
            results[service.name] = check_service_health(service, timeout)

    return results
