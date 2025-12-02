"""
Node Registry System

Automatic discovery and registration of workflow nodes without modifying service code.

This registry enables a plugin architecture where:
- Built-in nodes are automatically registered
- Custom nodes can be dropped into src/robomage/workflow/nodes/custom/
- No modification to main.py required
- Metadata is co-located with handler functions

Usage Patterns:

    1. Decorator Pattern (Recommended):
        @register_node(
            type="my_node",
            category="analysis",
            name="My Custom Node",
            description="Does something cool",
            icon="fas fa-star"
        )
        async def my_node_handler(config, inputs, context):
            return result

    2. Explicit Registration:
        from robomage.workflow.nodes.registry import NodeRegistry
        
        NodeRegistry.register(
            type="my_node",
            handler=my_node_handler,
            metadata=NodeTypeMetadata(...)
        )

    3. Auto-Discovery (automatic):
        # Just import the module, decorated nodes auto-register
        import robomage.workflow.nodes.custom

Author: RoboMage Team
Date: December 1, 2025
"""

import importlib
import logging
import pkgutil
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)


class NodeTypeMetadata:
    """
    Metadata for a node type used in UI palette.
    
    Attributes:
        type: Unique node type identifier (e.g., "peak_analysis")
        category: Category for organization ("data", "analysis", "transform", "output", "custom")
        name: Human-readable display name
        description: Brief description of what the node does
        icon: Font Awesome icon class (e.g., "fas fa-mountain")
        inputs: List of input specifications
        outputs: List of output specifications
        config_schema: JSON Schema for configuration parameters
    """
    
    def __init__(
        self,
        type: str,
        category: str,
        name: str,
        description: str,
        icon: str = "fas fa-cube",
        inputs: list[dict[str, str]] | None = None,
        outputs: list[dict[str, str]] | None = None,
        config_schema: dict[str, Any] | None = None,
    ):
        self.type = type
        self.category = category
        self.name = name
        self.description = description
        self.icon = icon
        self.inputs = inputs or []
        self.outputs = outputs or []
        self.config_schema = config_schema or {"type": "object", "properties": {}}
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API serialization."""
        return {
            "type": self.type,
            "category": self.category,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "config_schema": self.config_schema,
        }


class NodeRegistry:
    """
    Central registry for workflow node handlers and metadata.
    
    Singleton pattern - all registrations go to the same global registry.
    """
    
    _handlers: dict[str, Callable] = {}
    _metadata: dict[str, NodeTypeMetadata] = {}
    
    @classmethod
    def register(
        cls,
        type: str,
        handler: Callable,
        metadata: NodeTypeMetadata,
    ) -> None:
        """
        Register a node handler with its metadata.
        
        Args:
            type: Unique node type identifier
            handler: Async handler function
            metadata: Node metadata for UI
            
        Raises:
            ValueError: If node type already registered
        """
        if type in cls._handlers:
            logger.warning(f"Node type '{type}' is already registered, overwriting")
        
        cls._handlers[type] = handler
        cls._metadata[type] = metadata
        logger.info(f"Registered node: {type} ({metadata.name})")
    
    @classmethod
    def get_handler(cls, type: str) -> Callable | None:
        """Get handler function for a node type."""
        return cls._handlers.get(type)
    
    @classmethod
    def get_metadata(cls, type: str) -> NodeTypeMetadata | None:
        """Get metadata for a node type."""
        return cls._metadata.get(type)
    
    @classmethod
    def get_all_handlers(cls) -> dict[str, Callable]:
        """Get all registered handlers."""
        return cls._handlers.copy()
    
    @classmethod
    def get_all_metadata(cls) -> list[NodeTypeMetadata]:
        """Get metadata for all registered node types."""
        return list(cls._metadata.values())
    
    @classmethod
    def get_node_types(cls) -> list[str]:
        """Get list of registered node type identifiers."""
        return list(cls._handlers.keys())
    
    @classmethod
    def is_registered(cls, type: str) -> bool:
        """Check if a node type is registered."""
        return type in cls._handlers
    
    @classmethod
    def clear(cls) -> None:
        """Clear all registrations (mainly for testing)."""
        cls._handlers.clear()
        cls._metadata.clear()
        logger.info("Cleared node registry")
    
    @classmethod
    def discover_and_register_all(cls) -> None:
        """
        Auto-discover and register all nodes.
        
        Searches:
        1. Built-in nodes: src/robomage/workflow/nodes/*.py
        2. Custom nodes: src/robomage/workflow/nodes/custom/*.py
        3. Service nodes: From service registry workflow_integration
        
        Any module with decorated handlers will auto-register.
        """
        logger.info("Starting node auto-discovery...")
        
        # Import built-in node modules
        # Try both relative and absolute imports for compatibility
        try:
            # Try relative import first (when imported as robomage.workflow.nodes.registry)
            from . import analysis_nodes, data_nodes, output_nodes
            logger.info("Loaded built-in node modules (relative import)")
        except ImportError:
            try:
                # Try absolute import (when imported as src.robomage.workflow.nodes.registry)
                import src.robomage.workflow.nodes.analysis_nodes as analysis_nodes
                import src.robomage.workflow.nodes.data_nodes as data_nodes
                import src.robomage.workflow.nodes.output_nodes as output_nodes
                logger.info("Loaded built-in node modules (absolute import)")
            except ImportError as e:
                logger.warning(f"Failed to import built-in nodes: {e}")
        
        # Discover and import custom nodes
        cls._discover_custom_nodes()
        
        # Discover and register service-provided nodes
        cls._discover_service_nodes()
        
        logger.info(f"Node discovery complete: {len(cls._handlers)} nodes registered")
        logger.info(f"Registered nodes: {', '.join(sorted(cls.get_node_types()))}")
    
    @classmethod
    def _discover_custom_nodes(cls) -> None:
        """Discover and import custom nodes from custom/ directory."""
        # Try both import paths
        custom_package = None
        try:
            import robomage.workflow.nodes.custom as custom_package
        except ImportError:
            try:
                import src.robomage.workflow.nodes.custom as custom_package
            except ImportError:
                logger.debug("No custom nodes directory found")
                return
        
        if custom_package is None:
            return
            
        # Get path to custom nodes directory
        custom_path = Path(custom_package.__file__).parent
        
        # Find all Python modules in custom/
        for finder, name, ispkg in pkgutil.iter_modules([str(custom_path)]):
            if name.startswith("_"):
                continue  # Skip __init__ and private modules
            
            try:
                # Try both import paths
                module_name = f"robomage.workflow.nodes.custom.{name}"
                try:
                    importlib.import_module(module_name)
                except ImportError:
                    module_name = f"src.robomage.workflow.nodes.custom.{name}"
                    importlib.import_module(module_name)
                
                logger.info(f"Loaded custom node module: {name}")
            except Exception as e:
                logger.error(f"Failed to load custom node {name}: {e}")
    
    @classmethod
    def _discover_service_nodes(cls) -> None:
        """
        Discover and register nodes from services in the service registry.
        
        Services with workflow_integration.enabled=true and node_types specified
        will have placeholder nodes registered that delegate to the service.
        """
        try:
            from robomage.service_registry import ServiceRegistry
            from robomage.workflow.nodes.service_node import create_service_node_handler
            
            logger.info("Discovering service-provided nodes...")
            
            # Load service registry
            registry = ServiceRegistry()
            registry.load_registry()
            
            # Find services with workflow integration
            for service in registry.get_all_services():
                if not service.workflow_integration.enabled:
                    continue
                
                if not service.workflow_integration.node_types:
                    continue
                
                logger.info(
                    f"Service '{service.name}' provides {len(service.workflow_integration.node_types)} node types"
                )
                
                # Register each node type from the service
                for node_type in service.workflow_integration.node_types:
                    # Check if already registered (built-in takes precedence)
                    if cls.is_registered(node_type):
                        logger.debug(
                            f"Node type '{node_type}' already registered, skipping service version"
                        )
                        continue
                    
                    # Create and register service node handler
                    handler = create_service_node_handler(service, node_type)
                    
                    # Create metadata for service node
                    metadata = NodeTypeMetadata(
                        type=node_type,
                        category=service.service_type,  # Use service type as category
                        name=f"{node_type.replace('_', ' ').title()}",
                        description=f"{service.display_name} - {node_type}",
                        icon=service.dashboard_integration.icon,
                        inputs=[{"name": "data", "type": "DiffractionData[]"}],
                        outputs=[{"name": "results", "type": "AnalysisResults"}],
                        config_schema={
                            "type": "object",
                            "properties": {
                                "service_url": {
                                    "type": "string",
                                    "default": service.get_base_url(),
                                    "description": "Service endpoint URL",
                                }
                            },
                        },
                    )
                    
                    cls.register(type=node_type, handler=handler, metadata=metadata)
                    logger.info(f"Registered service node: {node_type} from {service.name}")
            
        except ImportError as e:
            logger.debug(f"Service registry not available, skipping service nodes: {e}")
        except Exception as e:
            logger.warning(f"Failed to discover service nodes: {e}")


def register_node(
    type: str,
    category: str,
    name: str,
    description: str,
    icon: str = "fas fa-cube",
    inputs: list[dict[str, str]] | None = None,
    outputs: list[dict[str, str]] | None = None,
    config_schema: dict[str, Any] | None = None,
) -> Callable:
    """
    Decorator to register a node handler with metadata.
    
    Usage:
        @register_node(
            type="my_node",
            category="analysis",
            name="My Analysis",
            description="Does custom analysis",
            icon="fas fa-star",
            inputs=[{"name": "input", "type": "DiffractionData[]"}],
            outputs=[{"name": "output", "type": "AnalysisResults[]"}],
            config_schema={
                "type": "object",
                "properties": {
                    "threshold": {"type": "number", "default": 0.5}
                }
            }
        )
        async def my_node_handler(config, inputs, context):
            # Implementation
            return results
    
    Args:
        type: Unique node type identifier
        category: Category ("data", "analysis", "transform", "output", "custom")
        name: Display name
        description: Brief description
        icon: Font Awesome icon class
        inputs: Input specifications
        outputs: Output specifications
        config_schema: JSON Schema for configuration
        
    Returns:
        Decorator function
    """
    def decorator(handler: Callable) -> Callable:
        """Actual decorator that registers the handler."""
        metadata = NodeTypeMetadata(
            type=type,
            category=category,
            name=name,
            description=description,
            icon=icon,
            inputs=inputs,
            outputs=outputs,
            config_schema=config_schema,
        )
        
        NodeRegistry.register(
            type=type,
            handler=handler,
            metadata=metadata,
        )
        
        return handler
    
    return decorator


# Convenience function for manual registration
def register_node_handler(
    type: str,
    handler: Callable,
    category: str,
    name: str,
    description: str,
    icon: str = "fas fa-cube",
    inputs: list[dict[str, str]] | None = None,
    outputs: list[dict[str, str]] | None = None,
    config_schema: dict[str, Any] | None = None,
) -> None:
    """
    Manually register a node handler (non-decorator approach).
    
    Use this when you can't use the decorator (e.g., registering
    existing functions you don't control).
    
    Args:
        type: Unique node type identifier
        handler: Async handler function
        category: Category for organization
        name: Display name
        description: Brief description
        icon: Font Awesome icon class
        inputs: Input specifications
        outputs: Output specifications
        config_schema: JSON Schema for configuration
    """
    metadata = NodeTypeMetadata(
        type=type,
        category=category,
        name=name,
        description=description,
        icon=icon,
        inputs=inputs,
        outputs=outputs,
        config_schema=config_schema,
    )
    
    NodeRegistry.register(type=type, handler=handler, metadata=metadata)
