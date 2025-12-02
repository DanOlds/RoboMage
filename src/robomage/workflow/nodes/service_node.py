"""Service Node - Generic Workflow Node for Service Integration.

This module provides a generic workflow node handler that can delegate execution
to any microservice registered in the service registry. This enables services to
provide workflow nodes without writing custom node handlers.

Pattern:
    Service defines node_types in service.json → NodeRegistry discovers them →
    Service node handler routes to service API → Results integrated into workflow

Example:
    # Service metadata (service.json)
    {
        "workflow_integration": {
            "enabled": true,
            "node_types": ["peak_analysis", "background_subtraction"]
        }
    }
    
    # Auto-registered as workflow nodes
    # No additional code needed!
"""

import logging
from typing import Any, Callable, Dict

from robomage.clients.base_service_client import BaseServiceClient, ServiceError
from robomage.service_registry.models import ServiceMetadata

logger = logging.getLogger(__name__)


def create_service_node_handler(
    service: ServiceMetadata,
    node_type: str,
) -> Callable:
    """Create a workflow node handler that delegates to a service.

    This factory function creates an async handler that:
    1. Accepts standard workflow node inputs (config, inputs, context)
    2. Serializes data for the service API
    3. Calls the service via HTTP
    4. Deserializes and returns results

    Args:
        service: Service metadata from registry
        node_type: Node type identifier

    Returns:
        Async handler function compatible with workflow orchestrator

    Example:
        >>> from robomage.service_registry import ServiceRegistry
        >>> registry = ServiceRegistry()
        >>> registry.load_registry()
        >>> service = registry.get_service("peak_analysis")
        >>> handler = create_service_node_handler(service, "peak_analysis")
        >>> # Handler can now be registered with workflow orchestrator
    """

    async def service_node_handler(
        config: Dict[str, Any],
        inputs: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute node by calling the backing service.

        Args:
            config: Node configuration from workflow definition
            inputs: Input data from predecessor nodes
            context: Workflow execution context

        Returns:
            Results from service execution

        Raises:
            ServiceError: If service call fails
            ValueError: If required inputs missing
        """
        logger.info(f"Executing service node: {node_type} via {service.name}")

        # Get service URL from config or use default
        service_url = config.get("service_url", service.get_base_url())

        # Create service client
        client = BaseServiceClient(
            base_url=service_url,
            timeout=config.get("timeout", 60.0),
        )

        try:
            # Prepare request data
            # Different services may have different API patterns
            # For now, use a generic pattern that works with most services
            request_data = {
                "node_type": node_type,
                "config": config,
                "inputs": inputs,
                "context": context,
            }

            # Determine endpoint based on node type and service
            # Most analysis services use /analyze endpoint
            endpoint = config.get("endpoint", "/analyze")

            # Call service
            logger.debug(f"Calling {service.name} at {endpoint}")
            response = client.post(endpoint, data=request_data)

            logger.info(f"Service node {node_type} completed successfully")
            return response

        except ServiceError as e:
            logger.error(f"Service error in {node_type}: {e.message}")
            raise RuntimeError(
                f"Service {service.name} failed: {e.message}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error in service node {node_type}: {e}")
            raise RuntimeError(
                f"Service node {node_type} failed: {str(e)}"
            ) from e
        finally:
            client.close()

    # Set metadata on the handler for introspection
    service_node_handler.__name__ = f"{node_type}_service_handler"
    service_node_handler.__doc__ = (
        f"Service node handler for {node_type}\n"
        f"Delegates to: {service.display_name}\n"
        f"Service URL: {service.get_base_url()}"
    )

    return service_node_handler


def create_peak_analysis_service_handler(service: ServiceMetadata) -> Callable:
    """Create a specialized handler for peak analysis service.

    This is a more specific handler that knows the peak analysis API structure.
    It serves as an example of how to create service-specific handlers when
    the generic handler isn't sufficient.

    Args:
        service: Peak analysis service metadata

    Returns:
        Async handler function for peak analysis

    Example:
        This function demonstrates the pattern for service-specific handlers:
        - Custom request formatting
        - Custom response parsing
        - Service-specific error handling
    """

    async def peak_analysis_handler(
        config: Dict[str, Any],
        inputs: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute peak analysis via service."""
        logger.info("Executing peak analysis service node")

        # Get diffraction data from inputs
        data_files = inputs.get("data", [])
        if not data_files:
            raise ValueError("Peak analysis requires 'data' input")

        # Create client
        client = BaseServiceClient(
            service_metadata=service,
            timeout=config.get("timeout", 60.0),
        )

        try:
            all_results = []

            # Process each file
            for file_data in data_files:
                # Prepare analysis request in peak service format
                request = {
                    "data": {
                        "q_values": file_data.get("q_values", []),
                        "intensities": file_data.get("intensities", []),
                        "metadata": file_data.get("metadata", {}),
                    },
                    "config": {
                        "prominence": config.get("prominence", 0.1),
                        "distance": config.get("distance", 5),
                        "profile": config.get("profile", "gaussian"),
                    },
                }

                # Call peak analysis service
                response = client.post("/analyze", data=request)
                all_results.append(response)

            return {"results": all_results, "status": "success"}

        except ServiceError as e:
            logger.error(f"Peak analysis service error: {e.message}")
            raise RuntimeError(f"Peak analysis failed: {e.message}") from e
        finally:
            client.close()

    return peak_analysis_handler
