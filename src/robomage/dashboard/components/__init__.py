"""
Dashboard UI components.

Reusable components for the RoboMage dashboard, including:
- Workflow canvas renderers (Cytoscape, future: ReactFlow, D3)
- Node configuration forms
- Workflow validation
- Node I/O inspector panels
"""

from .cytoscape_renderer import CytoscapeWorkflowRenderer
from .node_configurator import NodeConfigurator
from .node_inspector_panel import NodeInspectorPanel
from .workflow_canvas import (
    CanvasEvent,
    WorkflowCanvasFactory,
    WorkflowCanvasRenderer,
    WorkflowElement,
)
from .workflow_validator import WorkflowValidator

__all__ = [
    "WorkflowCanvasRenderer",
    "WorkflowElement",
    "CanvasEvent",
    "WorkflowCanvasFactory",
    "CytoscapeWorkflowRenderer",
    "NodeConfigurator",
    "WorkflowValidator",
    "NodeInspectorPanel",
]
