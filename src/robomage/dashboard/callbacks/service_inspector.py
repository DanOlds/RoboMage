"""
Service Inspector Callbacks

Handles all callbacks for the Service Inspector tab including:
- Service discovery and health monitoring
- Service selection
- API testing console
- OpenAPI schema fetching
"""

import json
import logging
import time
from typing import Any

import dash
import dash_bootstrap_components as dbc
import requests
from dash import ALL, Input, Output, State, ctx, html
from dash.exceptions import PreventUpdate

from robomage.clients.base_service_client import BaseServiceClient, ServiceError
from robomage.dashboard.components.service_card import (
    create_service_card,
    create_service_list_empty_state,
)
from robomage.dashboard.components.service_detail_panel import (
    create_service_detail_panel,
)
from robomage.service_registry import get_registry
from robomage.service_registry.models import ServiceMetadata

logger = logging.getLogger(__name__)


# ==============================================================================
# Helper Functions (not callbacks)
# ==============================================================================


def check_service_health(service: ServiceMetadata) -> dict[str, Any]:
    """
    Check health status of a service.
    
    Args:
        service: Service metadata
    
    Returns:
        Dict with status, response_time_ms, details, error
    """
    try:
        client = BaseServiceClient(service_metadata=service, timeout=2.0)
        start = time.time()
        health_response = client.health_check()
        response_time = (time.time() - start) * 1000
        
        return {
            "status": "healthy",
            "response_time_ms": response_time,
            "details": health_response,
            "error": None,
        }
    except ServiceError as e:
        return {
            "status": "unhealthy",
            "response_time_ms": None,
            "details": {},
            "error": str(e),
        }
    except Exception as e:
        logger.error(f"Unexpected error checking health for {service.name}: {e}")
        return {
            "status": "unhealthy",
            "response_time_ms": None,
            "details": {},
            "error": f"Unexpected error: {str(e)}",
        }


def fetch_openapi_schema(service_metadata: dict[str, Any]) -> dict[str, Any] | None:
    """
    Fetch OpenAPI schema from service /docs endpoint.
    
    Args:
        service_metadata: Service metadata dict
    
    Returns:
        OpenAPI schema dict or None if unavailable
    """
    try:
        host = service_metadata.get("host", "127.0.0.1")
        port = service_metadata.get("port")
        base_url = f"http://{host}:{port}"
        
        # Try to fetch OpenAPI JSON schema
        # FastAPI exposes this at /openapi.json
        response = requests.get(f"{base_url}/openapi.json", timeout=2.0)
        response.raise_for_status()
        
        return response.json()
        
    except Exception as e:
        logger.debug(f"Could not fetch OpenAPI schema: {e}")
        return None


# ==============================================================================
# Callback Registration
# ==============================================================================


def register_callbacks(app: dash.Dash) -> None:
    """
    Register all service inspector callbacks.
    
    Args:
        app: Dash application instance
    """
    
    @app.callback(
        [
            Output("service-inspector-data", "data"),
            Output("service-status-summary", "children"),
        ],
        [
            Input("service-health-interval", "n_intervals"),
            Input("service-inspector-refresh-btn", "n_clicks"),
            Input("main-tabs", "active_tab"),
        ],
        prevent_initial_call=False,
    )
    def discover_and_monitor_services(n_intervals, n_clicks, active_tab):
        """Discover services and check their health status."""
        # Only run when Service Inspector tab is active
        if active_tab != "service-inspector":
            raise PreventUpdate
        
        try:
            # Get all registered services
            registry = get_registry()
            registry.reload()  # Reload to catch newly added services
            services = registry.get_all_services()
            
            logger.info(f"Discovered {len(services)} services")
            
            # Check health of each service
            service_data = {}
            healthy_count = 0
            unhealthy_count = 0
            
            for service in services:
                health_info = check_service_health(service)
                
                service_data[service.name] = {
                    "metadata": service.model_dump(),
                    "health": health_info,
                }
                
                if health_info["status"] == "healthy":
                    healthy_count += 1
                else:
                    unhealthy_count += 1
            
            # Generate status summary
            total = len(services)
            if total == 0:
                summary = "No services discovered"
            else:
                summary = (
                    f"{total} service{'s' if total != 1 else ''} discovered | "
                    f"{healthy_count} healthy | "
                    f"{unhealthy_count} down"
                )
            
            return service_data, summary
            
        except Exception as e:
            logger.error(f"Error discovering services: {e}")
            return {}, f"Error discovering services: {str(e)}"
    
    @app.callback(
        [
            Output("service-list-container", "children"),
            Output("service-type-filter", "options"),
        ],
        [
            Input("service-inspector-data", "data"),
            Input("service-search-input", "value"),
            Input("service-type-filter", "value"),
            Input("selected-service-id", "data"),
        ],
    )
    def update_service_list(service_data, search_term, type_filter, selected_id):
        """Update the service list based on filters and selection."""
        if not service_data:
            return [create_service_list_empty_state()], []
        
        # Extract service types for filter dropdown
        service_types = set()
        for data in service_data.values():
            service_types.add(data["metadata"]["service_type"])
        
        type_options = [
            {"label": stype.capitalize(), "value": stype}
            for stype in sorted(service_types)
        ]
        
        # Filter services
        filtered_services = []
        for service_id, data in service_data.items():
            metadata = data["metadata"]
            health = data["health"]
            
            # Apply search filter
            if search_term:
                search_lower = search_term.lower()
                if (
                    search_lower not in metadata.get("name", "").lower()
                    and search_lower not in metadata.get("display_name", "").lower()
                    and search_lower not in metadata.get("description", "").lower()
                ):
                    continue
            
            # Apply type filter
            if type_filter and metadata.get("service_type") != type_filter:
                continue
            
            filtered_services.append((service_id, metadata, health))
        
        # Sort by name
        filtered_services.sort(key=lambda x: x[1].get("display_name", x[0]))
        
        # Create service cards
        if not filtered_services:
            return [create_service_list_empty_state()], type_options
        
        cards = []
        for service_id, metadata, health in filtered_services:
            card = create_service_card(
                service_id=service_id,
                display_name=metadata.get("display_name", service_id),
                service_type=metadata.get("service_type", "unknown"),
                port=metadata.get("port", 0),
                health_status=health.get("status", "unknown"),
                response_time_ms=health.get("response_time_ms"),
                is_selected=(service_id == selected_id),
            )
            cards.append(card)
        
        return cards, type_options
    
    @app.callback(
        Output("selected-service-id", "data"),
        Input({"type": "service-card-btn", "service_id": ALL}, "n_clicks"),
        prevent_initial_call=True,
    )
    def select_service(n_clicks_list):
        """Handle service card selection."""
        if not ctx.triggered_id:
            raise PreventUpdate
        
        # Get the service_id from the triggered button
        service_id = ctx.triggered_id.get("service_id")
        if not service_id:
            raise PreventUpdate
        
        return service_id
    
    @app.callback(
        [
            Output("service-detail-panel", "children"),
            Output("service-detail-title", "children"),
        ],
        [
            Input("selected-service-id", "data"),
            Input("service-inspector-data", "data"),
        ],
    )
    def display_service_details(selected_id, service_data):
        """Display detailed information for selected service."""
        if not selected_id or not service_data or selected_id not in service_data:
            return (
                dbc.Alert(
                    [
                        html.I(className="fas fa-hand-pointer me-2"),
                        "Select a service from the list to view details",
                    ],
                    color="light",
                ),
                "Service Details",
            )
        
        data = service_data[selected_id]
        metadata = data["metadata"]
        health = data["health"]
        
        # Fetch OpenAPI schema if service is healthy
        openapi_schema = None
        if health["status"] == "healthy":
            openapi_schema = fetch_openapi_schema(metadata)
        
        # Create detail panel
        detail_panel = create_service_detail_panel(
            service_data=metadata,
            health_data=health,
            openapi_schema=openapi_schema,
        )
        
        # Update title
        title = f"Service Details: {metadata.get('display_name', selected_id)}"
        
        return detail_panel, title
    
    @app.callback(
        Output("test-response-display", "children"),
        Input("test-send-request-btn", "n_clicks"),
        [
            State("selected-service-id", "data"),
            State("service-inspector-data", "data"),
            State("test-method-selector", "value"),
            State("test-endpoint-selector", "value"),
            State("test-request-body", "value"),
        ],
        prevent_initial_call=True,
    )
    def send_test_request(
        n_clicks, selected_id, service_data, method, endpoint, request_body
    ):
        """Send a test request to the selected service."""
        if not n_clicks or not selected_id or not service_data:
            raise PreventUpdate
        
        if selected_id not in service_data:
            raise PreventUpdate
        
        metadata = service_data[selected_id]["metadata"]
        host = metadata.get("host", "127.0.0.1")
        port = metadata.get("port")
        base_url = f"http://{host}:{port}"
        full_url = f"{base_url}{endpoint}"
        
        # Parse request body if provided
        request_data = None
        if request_body and request_body.strip():
            try:
                request_data = json.loads(request_body)
            except json.JSONDecodeError as e:
                return dbc.Alert(
                    [
                        html.I(className="fas fa-exclamation-triangle me-2"),
                        html.Strong("Invalid JSON in request body"),
                        html.Br(),
                        html.Small(str(e), className="text-muted"),
                    ],
                    color="danger",
                )
        
        # Send request
        try:
            start_time = time.time()
            
            if method == "GET":
                response = requests.get(full_url, timeout=10.0)
            elif method == "POST":
                response = requests.post(full_url, json=request_data, timeout=10.0)
            elif method == "PUT":
                response = requests.put(full_url, json=request_data, timeout=10.0)
            elif method == "DELETE":
                response = requests.delete(full_url, timeout=10.0)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            # Determine status color
            if 200 <= response.status_code < 300:
                status_color = "success"
            elif 300 <= response.status_code < 400:
                status_color = "info"
            elif 400 <= response.status_code < 500:
                status_color = "warning"
            else:
                status_color = "danger"
            
            # Parse response body
            try:
                response_json = response.json()
                response_text = json.dumps(response_json, indent=2)
            except Exception:
                response_text = response.text
            
            # Build response display
            return html.Div(
                [
                    dbc.Alert(
                        [
                            html.I(className="fas fa-check-circle me-2"),
                            html.Strong(f"Status: {response.status_code}"),
                            html.Br(),
                            html.Small(f"Response time: {elapsed_ms:.2f} ms"),
                        ],
                        color=status_color,
                    ),
                    html.Label("Response Body:", className="fw-bold mt-2"),
                    html.Pre(
                        html.Code(response_text),
                        className="bg-light p-3 rounded",
                        style={"maxHeight": "400px", "overflowY": "auto"},
                    ),
                    html.Label("Response Headers:", className="fw-bold mt-2"),
                    html.Pre(
                        html.Code(
                            "\n".join(f"{k}: {v}" for k, v in response.headers.items())
                        ),
                        className="bg-light p-2 rounded",
                        style={"maxHeight": "200px", "overflowY": "auto"},
                    ),
                ]
            )
            
        except requests.exceptions.Timeout:
            return dbc.Alert(
                [
                    html.I(className="fas fa-clock me-2"),
                    html.Strong("Request Timeout"),
                    html.Br(),
                    html.Small(
                        "The request took too long to respond",  # noqa: E501
                        className="text-muted",
                    ),
                ],
                color="warning",
            )
        except requests.exceptions.ConnectionError as e:
            return dbc.Alert(
                [
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    html.Strong("Connection Error"),
                    html.Br(),
                    html.Small(str(e), className="text-muted"),
                ],
                color="danger",
            )
        except Exception as e:
            logger.error(f"Error sending test request: {e}")
            return dbc.Alert(
                [
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    html.Strong("Error"),
                    html.Br(),
                    html.Small(str(e), className="text-muted"),
                ],
                color="danger",
            )
    
    @app.callback(
        Output("add-service-modal", "is_open"),
        [
            Input("service-inspector-add-btn", "n_clicks"),
            Input("add-service-cancel", "n_clicks"),
            Input("add-service-confirm", "n_clicks"),
        ],
        State("add-service-modal", "is_open"),
        prevent_initial_call=True,
    )
    def toggle_add_service_modal(open_clicks, cancel_clicks, confirm_clicks, is_open):
        """Toggle the add service modal."""
        if ctx.triggered_id in ["service-inspector-add-btn"]:
            return not is_open
        elif ctx.triggered_id in ["add-service-cancel", "add-service-confirm"]:
            return False
        return is_open
    
    @app.callback(
        Output("add-service-feedback", "children"),
        Input("add-service-confirm", "n_clicks"),
        [
            State("add-service-name", "value"),
            State("add-service-display-name", "value"),
            State("add-service-url", "value"),
            State("add-service-type", "value"),
        ],
        prevent_initial_call=True,
    )
    def add_custom_service(n_clicks, name, display_name, url, service_type):
        """Add a custom service (manual registration)."""
        if not n_clicks:
            raise PreventUpdate
        
        # Validate inputs
        if not name or not display_name or not url:
            return dbc.Alert(
                [
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    "Please fill in all required fields",
                ],
                color="warning",
            )
        
        # For MVP, just show success message
        # Future: Actually register the service
        return dbc.Alert(
            [
                html.I(className="fas fa-info-circle me-2"),
                "Manual service registration coming soon! ",
                html.Br(),
                html.Small(
                    "For now, add services to services/registry.json",
                    className="text-muted",
                ),
            ],
            color="info",
        )
