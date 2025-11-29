"""
Abstract workflow canvas renderer.

Defines the protocol for rendering workflow graphs in different UI frameworks.
Implementations: Cytoscape (MVP), ReactFlow (future), D3.js (future), etc.

This abstraction enables swapping rendering backends without changing workflow logic.
"""

from abc import abstractmethod
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field


class WorkflowElement(BaseModel):
    """
    Generic representation of a workflow element (node or edge).

    This model is framework-agnostic and serves as the common data structure
    for all rendering implementations.
    """

    id: str = Field(..., description="Unique identifier for this element")
    type: str = Field(..., description="Element type: 'node' or 'edge'")
    data: dict[str, Any] = Field(
        default_factory=dict,
        description="Element-specific data (config, labels, status, etc.)",
    )
    position: dict[str, float] | None = Field(
        None, description="Position for nodes: {'x': float, 'y': float}"
    )
    source: str | None = Field(None, description="Source node ID for edges")
    target: str | None = Field(None, description="Target node ID for edges")

    model_config = ConfigDict(extra="allow")  # Allow additional fields


class CanvasEvent(BaseModel):
    """
    Event from canvas interaction.

    Normalized representation of user interactions with the workflow canvas,
    independent of the underlying UI framework.
    """

    event_type: str = Field(
        ..., description="Event type: 'node_click', 'edge_create', 'node_drag', etc."
    )
    element_id: str | None = Field(None, description="ID of affected element")
    element_data: dict[str, Any] | None = Field(
        None, description="Element data at time of event"
    )
    position: dict[str, float] | None = Field(
        None, description="Position data for drag/drop events"
    )

    model_config = ConfigDict(extra="allow")  # Allow additional fields


class WorkflowCanvasRenderer(Protocol):
    """
    Protocol for workflow canvas rendering.

    Any UI framework (Cytoscape, ReactFlow, D3) must implement this interface.
    This enables swapping rendering backends without changing workflow logic.

    Example usage:
        ```python
        # Create renderer (easy to swap implementation)
        factory = WorkflowCanvasFactory()
        renderer = factory.create("cytoscape")  # or "reactflow"

        # Convert workflow to elements
        elements = renderer.workflow_to_elements(workflow_dict)

        # Render canvas
        canvas_component = renderer.render(elements)

        # Parse user events
        event = renderer.parse_event(raw_event_data)
        ```
    """

    @abstractmethod
    def render(self, elements: list[WorkflowElement], **kwargs: Any) -> Any:
        """
        Render the workflow canvas component.

        Args:
            elements: List of nodes and edges to render
            **kwargs: Renderer-specific options (e.g., layout, styling)

        Returns:
            Framework-specific component (e.g., dash_cytoscape.Cytoscape)
        """
        ...

    @abstractmethod
    def parse_event(self, event_data: dict[str, Any] | None) -> CanvasEvent | None:
        """
        Parse framework-specific event into generic CanvasEvent.

        Args:
            event_data: Raw event from UI framework

        Returns:
            Normalized CanvasEvent or None if event cannot be parsed
        """
        ...

    @abstractmethod
    def create_stylesheet(self) -> Any:
        """
        Create framework-specific stylesheet for workflow elements.

        Defines visual styling for nodes, edges, states (running, completed, failed).

        Returns:
            Stylesheet configuration (format depends on framework)
        """
        ...

    @abstractmethod
    def workflow_to_elements(self, workflow: dict[str, Any]) -> list[WorkflowElement]:
        """
        Convert WorkflowDefinition to generic elements.

        Args:
            workflow: Workflow definition dict with 'nodes' and 'edges' keys

        Returns:
            List of WorkflowElement objects
        """
        ...

    @abstractmethod
    def elements_to_workflow(self, elements: list[WorkflowElement]) -> dict[str, Any]:
        """
        Convert generic elements back to WorkflowDefinition.

        Args:
            elements: List of WorkflowElement objects

        Returns:
            Workflow definition dict compatible with workflow engine
        """
        ...


class WorkflowCanvasFactory:
    """
    Factory for creating canvas renderers.

    Makes it easy to swap implementations:
        ```python
        factory = WorkflowCanvasFactory()
        renderer = factory.create("cytoscape")  # or "reactflow"
        ```

    Renderers self-register via:
        ```python
        WorkflowCanvasFactory.register("my_renderer", MyRendererClass)
        ```
    """

    _renderers: dict[str, type[WorkflowCanvasRenderer]] = {}

    @classmethod
    def register(cls, name: str, renderer_class: type[WorkflowCanvasRenderer]) -> None:
        """
        Register a renderer implementation.

        Args:
            name: Unique name for this renderer (e.g., "cytoscape", "reactflow")
            renderer_class: Class implementing WorkflowCanvasRenderer protocol
        """
        cls._renderers[name] = renderer_class

    @classmethod
    def create(cls, name: str = "cytoscape", **config: Any) -> WorkflowCanvasRenderer:
        """
        Create a renderer instance.

        Args:
            name: Renderer name (must be registered)
            **config: Configuration passed to renderer constructor

        Returns:
            Renderer instance

        Raises:
            ValueError: If renderer name is not registered
        """
        if name not in cls._renderers:
            available = ", ".join(cls.available_renderers())
            raise ValueError(
                f"Unknown renderer: {name}. Available renderers: {available}"
            )
        return cls._renderers[name](**config)

    @classmethod
    def available_renderers(cls) -> list[str]:
        """
        List available renderer names.

        Returns:
            List of registered renderer names
        """
        return list(cls._renderers.keys())

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """
        Check if a renderer is registered.

        Args:
            name: Renderer name to check

        Returns:
            True if registered, False otherwise
        """
        return name in cls._renderers
