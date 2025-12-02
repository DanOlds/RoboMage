"""Service Registry Module.

This module provides a centralized registry for discovering and managing
microservices in the RoboMage framework. Services can be registered via
configuration files and discovered automatically.

Example:
    >>> from robomage.service_registry import ServiceRegistry
    >>> registry = ServiceRegistry()
    >>> peak_service = registry.get_service("peak_analysis")
    >>> print(f"{peak_service.display_name} on port {peak_service.port}")
"""

from robomage.service_registry.models import (
    DashboardIntegration,
    EndpointConfig,
    ServiceDependencies,
    ServiceMetadata,
    WorkflowIntegration,
)
from robomage.service_registry.registry import ServiceRegistry

__all__ = [
    "ServiceRegistry",
    "ServiceMetadata",
    "EndpointConfig",
    "ServiceDependencies",
    "WorkflowIntegration",
    "DashboardIntegration",
]
