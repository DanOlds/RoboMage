"""
Cytoscape-based workflow canvas renderer.

This is ONE possible implementation of WorkflowCanvasRenderer.
Can be replaced with ReactFlowRenderer, D3Renderer, etc. without
changing workflow_layout.py or workflow.py callbacks.
"""

from typing import Any

import dash_cytoscape as cyto

from .workflow_canvas import (
    CanvasEvent,
    WorkflowCanvasFactory,
    WorkflowCanvasRenderer,
    WorkflowElement,
)


class CytoscapeWorkflowRenderer(WorkflowCanvasRenderer):
    """
    Cytoscape implementation of workflow canvas.

    Provides drag-and-drop visual workflow building using dash-cytoscape.
    Supports node categorization, execution status visualization, and
    professional styling.

    Example:
        ```python
        renderer = CytoscapeWorkflowRenderer(
            width="100%", height="600px", enable_physics=False
        )
        canvas = renderer.render(elements, id="workflow-canvas")
        ```
    """

    def __init__(
        self,
        width: str = "100%",
        height: str = "600px",
        enable_physics: bool = False,
    ):
        """
        Initialize Cytoscape renderer.

        Args:
            width: CSS width of canvas
            height: CSS height of canvas
            enable_physics: Enable force-directed layout (False = manual positioning)
        """
        self.width = width
        self.height = height
        self.enable_physics = enable_physics

    def render(self, elements: list[WorkflowElement], **kwargs: Any) -> cyto.Cytoscape:
        """
        Render workflow as Cytoscape component.

        Args:
            elements: Generic workflow elements
            **kwargs: Additional Cytoscape options
                - id: Component ID (default: "workflow-canvas")
                - layout: Layout configuration (default: preset or cose)

        Returns:
            dash_cytoscape.Cytoscape component
        """
        cyto_elements = self._to_cytoscape_elements(elements)

        # Default layout based on physics setting
        default_layout = (
            {"name": "cose", "animate": True, "animationDuration": 300}
            if self.enable_physics
            else {"name": "preset"}
        )

        return cyto.Cytoscape(
            id=kwargs.get("id", "workflow-canvas"),
            elements=cyto_elements,
            style={"width": self.width, "height": self.height},
            stylesheet=self.create_stylesheet(),
            layout=kwargs.get("layout", default_layout),
            # Enable user interactions
            userZoomingEnabled=True,
            userPanningEnabled=True,
            boxSelectionEnabled=False,
            autoungrabify=False,
        )

    def create_stylesheet(self) -> list[dict[str, Any]]:
        """
        Create Cytoscape stylesheet for workflow elements.

        Defines visual styling for:
        - Default nodes and edges
        - Selected elements
        - Node categories (data, analysis, transform, output)
        - Execution status (running, completed, failed)

        Returns:
            List of style dictionaries
        """
        return [
            # Default node style
            {
                "selector": "node",
                "style": {
                    "label": "data(label)",
                    "background-color": "#4A90E2",
                    "color": "#fff",
                    "text-valign": "center",
                    "text-halign": "center",
                    "width": "120px",
                    "height": "60px",
                    "shape": "roundrectangle",
                    "font-size": "12px",
                    "border-width": 2,
                    "border-color": "#2E5C8A",
                },
            },
            # Selected node
            {
                "selector": "node:selected",
                "style": {
                    "border-width": 4,
                    "border-color": "#FF6B6B",
                    "background-color": "#E85D5D",
                },
            },
            # Node category colors
            {
                "selector": "node[category='data']",
                "style": {"background-color": "#4ECDC4", "border-color": "#3AAFA9"},
            },
            {
                "selector": "node[category='analysis']",
                "style": {"background-color": "#95E1D3", "border-color": "#7BCFC0"},
            },
            {
                "selector": "node[category='transform']",
                "style": {"background-color": "#FFE66D", "border-color": "#E6CF5D"},
            },
            {
                "selector": "node[category='output']",
                "style": {"background-color": "#FF6B6B", "border-color": "#E65555"},
            },
            # Execution status colors
            {
                "selector": "node[status='running']",
                "style": {
                    "background-color": "#FFA500",
                    "border-color": "#FF8C00",
                    "border-width": 4,
                },
            },
            {
                "selector": "node[status='completed']",
                "style": {
                    "background-color": "#4CAF50",
                    "border-color": "#388E3C",
                    "border-width": 4,
                },
            },
            {
                "selector": "node[status='failed']",
                "style": {
                    "background-color": "#F44336",
                    "border-color": "#C62828",
                    "border-width": 4,
                },
            },
            # Edge styles
            {
                "selector": "edge",
                "style": {
                    "width": 3,
                    "line-color": "#9CA3AF",
                    "target-arrow-color": "#9CA3AF",
                    "target-arrow-shape": "triangle",
                    "curve-style": "bezier",
                    "arrow-scale": 1.5,
                },
            },
            {
                "selector": "edge:selected",
                "style": {
                    "line-color": "#FF6B6B",
                    "target-arrow-color": "#FF6B6B",
                    "width": 4,
                },
            },
        ]

    def parse_event(self, event_data: dict[str, Any] | None) -> CanvasEvent | None:
        """
        Parse Cytoscape event into generic CanvasEvent.

        Args:
            event_data: Raw event from Cytoscape (contains 'type' and optional 'target')

        Returns:
            Normalized CanvasEvent or None if event cannot be parsed

        Example Cytoscape events:
            - {"type": "tap", "target": {"group": "nodes", "data": {...}}}
            - {"type": "drag", "target": {"position": {"x": 100, "y": 200}}}
        """
        if not event_data:
            return None

        # Cytoscape events have 'type' and optional 'target'
        event_type = event_data.get("type")
        target = event_data.get("target", {})

        # Map Cytoscape events to generic events
        event_map = {
            "tap": "node_click" if target.get("group") == "nodes" else "edge_click",
            "drag": "node_drag",
            "add": "element_add",
            "remove": "element_remove",
        }

        generic_type = event_map.get(event_type, event_type)

        return CanvasEvent(
            event_type=generic_type,
            element_id=target.get("data", {}).get("id"),
            element_data=target.get("data"),
            position=target.get("position"),
        )

    def workflow_to_elements(self, workflow: dict[str, Any]) -> list[WorkflowElement]:
        """
        Convert WorkflowDefinition to generic elements.

        Args:
            workflow: Workflow definition dict with 'nodes' and 'edges' keys

        Returns:
            List of WorkflowElement objects

        Example workflow:
            ```python
            {
                "nodes": [
                    {
                        "id": "n1",
                        "type": "load_files",
                        "label": "Load Data",
                        "position": {"x": 0, "y": 0},
                        "config": {...},
                    }
                ],
                "edges": [{"id": "e1", "source": "n1", "target": "n2"}],
            }
            ```
        """
        elements = []

        # Convert nodes
        for node in workflow.get("nodes", []):
            elements.append(
                WorkflowElement(
                    id=node["id"],
                    type="node",
                    data={
                        "label": node.get("label", node.get("type")),
                        "node_type": node.get("type"),
                        "category": self._get_node_category(node.get("type")),
                        "config": node.get("config", {}),
                    },
                    position=node.get("position", {"x": 0, "y": 0}),
                )
            )

        # Convert edges
        for edge in workflow.get("edges", []):
            elements.append(
                WorkflowElement(
                    id=edge["id"],
                    type="edge",
                    source=edge["source"],
                    target=edge["target"],
                    data={},
                )
            )

        return elements

    def elements_to_workflow(self, elements: list[WorkflowElement]) -> dict[str, Any]:
        """
        Convert generic elements back to WorkflowDefinition.

        Args:
            elements: List of WorkflowElement objects

        Returns:
            Workflow definition dict compatible with workflow engine
        """
        nodes = []
        edges = []

        for elem in elements:
            if elem.type == "node":
                nodes.append(
                    {
                        "id": elem.id,
                        "type": elem.data.get("node_type"),
                        "label": elem.data.get("label"),
                        "config": elem.data.get("config", {}),
                        "position": elem.position or {"x": 0, "y": 0},
                    }
                )
            elif elem.type == "edge":
                edges.append(
                    {
                        "id": elem.id,
                        "source": elem.source,
                        "target": elem.target,
                    }
                )

        return {
            "nodes": nodes,
            "edges": edges,
        }

    def _to_cytoscape_elements(
        self, elements: list[WorkflowElement]
    ) -> list[dict[str, Any]]:
        """
        Convert generic elements to Cytoscape format.

        Args:
            elements: List of WorkflowElement objects

        Returns:
            List of Cytoscape element dictionaries
        """
        cyto_elements = []

        for elem in elements:
            if elem.type == "node":
                cyto_elements.append(
                    {
                        "data": {
                            "id": elem.id,
                            **elem.data,
                        },
                        "position": elem.position,
                        "classes": elem.data.get("category", ""),
                    }
                )
            elif elem.type == "edge":
                cyto_elements.append(
                    {
                        "data": {
                            "id": elem.id,
                            "source": elem.source,
                            "target": elem.target,
                            **elem.data,
                        }
                    }
                )

        return cyto_elements

    def _get_node_category(self, node_type: str | None) -> str:
        """
        Determine category from node type.

        Args:
            node_type: Node type string (e.g., "load_files", "peak_analysis")

        Returns:
            Category string ("data", "analysis", "transform", "output")
        """
        category_map = {
            "load_files": "data",
            "load_session": "data",
            "filter_q_range": "transform",
            "normalize": "transform",
            "peak_analysis": "analysis",
            "statistics": "analysis",
            "export_csv": "output",
            "export_json": "output",
            "plot_results": "output",
            "save_to_session": "output",
        }
        return category_map.get(node_type or "", "data")


# Auto-register this renderer with the factory when module is imported
WorkflowCanvasFactory.register("cytoscape", CytoscapeWorkflowRenderer)
