"""Service Registry Module.

This module provides a centralized registry for discovering and managing
microservices in the RoboMage framework. Services can be registered via
configuration files and discovered automatically.

Example:
    >>> from robomage.service_registry import get_registry
    >>> registry = get_registry()
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

# Singleton instance for convenience
_registry_instance = None


def get_registry() -> ServiceRegistry:
    """
    Get the global ServiceRegistry instance (singleton).
    
    This is a convenience function that maintains a single registry instance
    across the application. The registry is lazily initialized on first access.
    
    Returns:
        ServiceRegistry: The global registry instance
        
    Example:
        >>> from robomage.service_registry import get_registry
        >>> registry = get_registry()
        >>> services = registry.list_services()
    """
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ServiceRegistry()
    return _registry_instance


__all__ = [
    "ServiceRegistry",
    "ServiceMetadata",
    "EndpointConfig",
    "ServiceDependencies",
    "WorkflowIntegration",
    "DashboardIntegration",
    "get_registry",
]
