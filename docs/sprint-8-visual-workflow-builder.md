# Sprint 8: Visual Workflow Builder (Phase 2)

**Status**: Planning  
**Date**: November 28, 2025  
**Target Duration**: 5-7 days  
**Branch**: `sprint-8-visual-workflow-builder`  
**Priority**: HIGH - Enables non-programmer workflow creation  
**Prerequisites**: Sprint 6 + Sprint 7 Complete ✅

---

## 🎯 Objective

Transform the JSON-only workflow editor into an **interactive drag-and-drop visual builder** using Dash Cytoscape, with **clean abstraction** to enable future UI framework changes.

### Success Criteria
- ✅ Drag nodes from palette onto canvas
- ✅ Connect nodes visually by dragging edges
- ✅ Click node to configure via dynamic forms
- ✅ Save/load workflows with visual layout preserved
- ✅ Execute workflows with visual progress indicators
- ✅ Validate workflows before execution (cycles, disconnected nodes)
- ✅ **Architecture supports swapping Cytoscape for ReactFlow/other frameworks**

---

## 🏗️ Architecture: Clean Separation of Concerns

### Design Principle: **Renderer Abstraction Pattern**

The key to painless future refactoring is to **separate workflow logic from rendering**.

```
┌─────────────────────────────────────────────────────────────┐
│                    Dashboard UI Layer                        │
│  (workflow_layout.py, workflow.py callbacks)                │
│                                                              │
│  - User interactions (button clicks, file uploads)          │
│  - Dash-specific callback wiring                            │
│  - Layout composition                                        │
└──────────────────┬──────────────────────────────────────────┘
                   │ uses
                   ▼
┌─────────────────────────────────────────────────────────────┐
│              Workflow Canvas Abstraction                     │
│  Location: src/robomage/dashboard/components/               │
│            workflow_canvas.py (NEW)                          │
│                                                              │
│  - Abstract base class: WorkflowCanvasRenderer              │
│  - Protocol: defines render(), get_elements(), etc.         │
│  - NO Cytoscape-specific code here!                         │
└──────────────────┬──────────────────────────────────────────┘
                   │ implemented by
                   ▼
┌─────────────────────────────────────────────────────────────┐
│           Cytoscape Implementation (Pluggable)               │
│  Location: src/robomage/dashboard/components/               │
│            cytoscape_renderer.py (NEW)                       │
│                                                              │
│  - CytoscapeWorkflowRenderer(WorkflowCanvasRenderer)        │
│  - Cytoscape-specific element formatting                    │
│  - Stylesheet definitions                                    │
│  - Event parsing (tap, drag, etc.)                          │
│  - Can be replaced with ReactFlowRenderer later!            │
└─────────────────────────────────────────────────────────────┘
```

### File Structure After Sprint 8

```
src/robomage/dashboard/
├── components/                          # NEW: Reusable UI components
│   ├── __init__.py
│   ├── workflow_canvas.py               # Abstract canvas renderer protocol
│   ├── cytoscape_renderer.py            # Cytoscape implementation
│   ├── node_configurator.py             # Dynamic form builder for node config
│   └── workflow_validator.py            # Workflow validation logic
│
├── layouts/
│   └── workflow_layout.py               # MODIFIED: Uses WorkflowCanvasRenderer
│
└── callbacks/
    └── workflow.py                      # MODIFIED: Uses abstract renderer API
```

---

## 📋 Implementation Plan - 7 Days

### **Day 1: Abstraction Layer & Renderer Protocol**

#### Task 1.1: Define Abstract Canvas Renderer
**File**: `src/robomage/dashboard/components/workflow_canvas.py`

```python
"""
Abstract workflow canvas renderer.

Defines the protocol for rendering workflow graphs in different UI frameworks.
Implementations: Cytoscape (MVP), ReactFlow (future), D3.js (future), etc.
"""

from abc import ABC, abstractmethod
from typing import Any, Protocol
from pydantic import BaseModel


class WorkflowElement(BaseModel):
    """Generic representation of a workflow element (node or edge)."""
    
    id: str
    type: str  # "node" or "edge"
    data: dict[str, Any]
    position: dict[str, float] | None = None  # For nodes
    source: str | None = None  # For edges
    target: str | None = None  # For edges


class CanvasEvent(BaseModel):
    """Event from canvas interaction."""
    
    event_type: str  # "node_click", "edge_create", "node_drag", etc.
    element_id: str | None = None
    element_data: dict[str, Any] | None = None
    position: dict[str, float] | None = None


class WorkflowCanvasRenderer(Protocol):
    """
    Protocol for workflow canvas rendering.
    
    Any UI framework (Cytoscape, ReactFlow, D3) must implement this interface.
    This enables swapping rendering backends without changing workflow logic.
    """
    
    @abstractmethod
    def render(self, elements: list[WorkflowElement], **kwargs) -> Any:
        """
        Render the workflow canvas component.
        
        Args:
            elements: List of nodes and edges to render
            **kwargs: Renderer-specific options
        
        Returns:
            Framework-specific component (e.g., dash_cytoscape.Cytoscape)
        """
        pass
    
    @abstractmethod
    def parse_event(self, event_data: dict | None) -> CanvasEvent | None:
        """
        Parse framework-specific event into generic CanvasEvent.
        
        Args:
            event_data: Raw event from UI framework
        
        Returns:
            Normalized CanvasEvent or None
        """
        pass
    
    @abstractmethod
    def create_stylesheet(self) -> Any:
        """
        Create framework-specific stylesheet for workflow elements.
        
        Returns:
            Stylesheet configuration
        """
        pass
    
    @abstractmethod
    def workflow_to_elements(self, workflow: dict) -> list[WorkflowElement]:
        """
        Convert WorkflowDefinition to generic elements.
        
        Args:
            workflow: Workflow definition dict
        
        Returns:
            List of WorkflowElement objects
        """
        pass
    
    @abstractmethod
    def elements_to_workflow(self, elements: list[WorkflowElement]) -> dict:
        """
        Convert generic elements back to WorkflowDefinition.
        
        Args:
            elements: List of WorkflowElement objects
        
        Returns:
            Workflow definition dict
        """
        pass


class WorkflowCanvasFactory:
    """
    Factory for creating canvas renderers.
    
    Makes it easy to swap implementations:
        factory = WorkflowCanvasFactory()
        renderer = factory.create("cytoscape")  # or "reactflow"
    """
    
    _renderers: dict[str, type[WorkflowCanvasRenderer]] = {}
    
    @classmethod
    def register(cls, name: str, renderer_class: type[WorkflowCanvasRenderer]):
        """Register a renderer implementation."""
        cls._renderers[name] = renderer_class
    
    @classmethod
    def create(cls, name: str = "cytoscape", **config) -> WorkflowCanvasRenderer:
        """Create a renderer instance."""
        if name not in cls._renderers:
            raise ValueError(f"Unknown renderer: {name}")
        return cls._renderers[name](**config)
    
    @classmethod
    def available_renderers(cls) -> list[str]:
        """List available renderer names."""
        return list(cls._renderers.keys())
```

**Deliverables**:
- ✅ Abstract protocol defined
- ✅ Generic WorkflowElement model
- ✅ Factory pattern for renderer swapping
- ✅ Complete type hints

---

### **Day 2: Cytoscape Renderer Implementation**

#### Task 2.1: Implement Cytoscape Renderer
**File**: `src/robomage/dashboard/components/cytoscape_renderer.py`

```python
"""
Cytoscape-based workflow canvas renderer.

This is ONE possible implementation of WorkflowCanvasRenderer.
Can be replaced with ReactFlowRenderer, D3Renderer, etc. without
changing workflow_layout.py or workflow.py callbacks.
"""

import dash_cytoscape as cyto
from typing import Any

from .workflow_canvas import (
    WorkflowCanvasRenderer,
    WorkflowElement,
    CanvasEvent,
    WorkflowCanvasFactory,
)


class CytoscapeWorkflowRenderer(WorkflowCanvasRenderer):
    """Cytoscape implementation of workflow canvas."""
    
    def __init__(
        self,
        width: str = "100%",
        height: str = "600px",
        enable_physics: bool = False
    ):
        self.width = width
        self.height = height
        self.enable_physics = enable_physics
    
    def render(self, elements: list[WorkflowElement], **kwargs) -> cyto.Cytoscape:
        """
        Render workflow as Cytoscape component.
        
        Args:
            elements: Generic workflow elements
            **kwargs: Additional Cytoscape options
        
        Returns:
            dash_cytoscape.Cytoscape component
        """
        cyto_elements = self._to_cytoscape_elements(elements)
        
        return cyto.Cytoscape(
            id=kwargs.get("id", "workflow-canvas"),
            elements=cyto_elements,
            style={"width": self.width, "height": self.height},
            stylesheet=self.create_stylesheet(),
            layout=kwargs.get("layout", {
                "name": "preset" if not self.enable_physics else "cose",
                "animate": True,
                "animationDuration": 300
            }),
            # Enable user interactions
            userZoomingEnabled=True,
            userPanningEnabled=True,
            boxSelectionEnabled=False,
            autoungrabify=False,
        )
    
    def create_stylesheet(self) -> list[dict]:
        """Create Cytoscape stylesheet for workflow elements."""
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
                }
            },
            # Selected node
            {
                "selector": "node:selected",
                "style": {
                    "border-width": 4,
                    "border-color": "#FF6B6B",
                    "background-color": "#E85D5D",
                }
            },
            # Node category colors
            {
                "selector": "node[category='data']",
                "style": {"background-color": "#4ECDC4"}
            },
            {
                "selector": "node[category='analysis']",
                "style": {"background-color": "#95E1D3"}
            },
            {
                "selector": "node[category='transform']",
                "style": {"background-color": "#FFE66D"}
            },
            {
                "selector": "node[category='output']",
                "style": {"background-color": "#FF6B6B"}
            },
            # Execution status colors
            {
                "selector": "node[status='running']",
                "style": {
                    "background-color": "#FFA500",
                    "border-color": "#FF8C00",
                }
            },
            {
                "selector": "node[status='completed']",
                "style": {
                    "background-color": "#4CAF50",
                    "border-color": "#388E3C",
                }
            },
            {
                "selector": "node[status='failed']",
                "style": {
                    "background-color": "#F44336",
                    "border-color": "#C62828",
                }
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
                }
            },
            {
                "selector": "edge:selected",
                "style": {
                    "line-color": "#FF6B6B",
                    "target-arrow-color": "#FF6B6B",
                    "width": 4,
                }
            },
        ]
    
    def parse_event(self, event_data: dict | None) -> CanvasEvent | None:
        """Parse Cytoscape event into generic CanvasEvent."""
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
    
    def workflow_to_elements(self, workflow: dict) -> list[WorkflowElement]:
        """Convert WorkflowDefinition to generic elements."""
        elements = []
        
        # Convert nodes
        for node in workflow.get("nodes", []):
            elements.append(WorkflowElement(
                id=node["id"],
                type="node",
                data={
                    "label": node.get("label", node.get("type")),
                    "node_type": node.get("type"),
                    "category": self._get_node_category(node.get("type")),
                    "config": node.get("config", {}),
                },
                position=node.get("position", {"x": 0, "y": 0})
            ))
        
        # Convert edges
        for edge in workflow.get("edges", []):
            elements.append(WorkflowElement(
                id=edge["id"],
                type="edge",
                source=edge["source"],
                target=edge["target"],
                data={}
            ))
        
        return elements
    
    def elements_to_workflow(self, elements: list[WorkflowElement]) -> dict:
        """Convert generic elements back to WorkflowDefinition."""
        nodes = []
        edges = []
        
        for elem in elements:
            if elem.type == "node":
                nodes.append({
                    "id": elem.id,
                    "type": elem.data.get("node_type"),
                    "label": elem.data.get("label"),
                    "config": elem.data.get("config", {}),
                    "position": elem.position or {"x": 0, "y": 0}
                })
            elif elem.type == "edge":
                edges.append({
                    "id": elem.id,
                    "source": elem.source,
                    "target": elem.target,
                })
        
        return {
            "nodes": nodes,
            "edges": edges,
        }
    
    def _to_cytoscape_elements(self, elements: list[WorkflowElement]) -> list[dict]:
        """Convert generic elements to Cytoscape format."""
        cyto_elements = []
        
        for elem in elements:
            if elem.type == "node":
                cyto_elements.append({
                    "data": {
                        "id": elem.id,
                        **elem.data,
                    },
                    "position": elem.position,
                    "classes": elem.data.get("category", "")
                })
            elif elem.type == "edge":
                cyto_elements.append({
                    "data": {
                        "id": elem.id,
                        "source": elem.source,
                        "target": elem.target,
                        **elem.data,
                    }
                })
        
        return cyto_elements
    
    def _get_node_category(self, node_type: str) -> str:
        """Determine category from node type."""
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
        }
        return category_map.get(node_type, "data")


# Register this renderer with the factory
WorkflowCanvasFactory.register("cytoscape", CytoscapeWorkflowRenderer)
```

**Deliverables**:
- ✅ Complete Cytoscape implementation
- ✅ Styling with category colors
- ✅ Event parsing
- ✅ Bi-directional workflow conversion
- ✅ Registered with factory

---

### **Day 3: Node Configuration UI**

#### Task 3.1: Dynamic Form Builder
**File**: `src/robomage/dashboard/components/node_configurator.py`

```python
"""
Dynamic node configuration form builder.

Creates forms for configuring workflow nodes based on their schema.
Framework-agnostic - uses Dash Bootstrap Components.
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
from typing import Any


class NodeConfigurator:
    """
    Builds dynamic configuration forms for workflow nodes.
    
    Uses node type metadata from workflow service to generate
    appropriate input fields (text, number, dropdown, etc.).
    """
    
    @staticmethod
    def create_config_form(
        node_id: str,
        node_type: str,
        current_config: dict[str, Any],
        schema: dict[str, Any]
    ) -> html.Div:
        """
        Create configuration form for a node.
        
        Args:
            node_id: Unique node identifier
            node_type: Node type (e.g., "peak_analysis")
            current_config: Current configuration values
            schema: JSON schema for configuration
        
        Returns:
            Dash component with form fields
        """
        if not schema or "properties" not in schema:
            return html.Div([
                html.P("No configuration needed", className="text-muted")
            ])
        
        form_fields = []
        
        for prop_name, prop_schema in schema["properties"].items():
            field = NodeConfigurator._create_field(
                node_id=node_id,
                prop_name=prop_name,
                prop_schema=prop_schema,
                current_value=current_config.get(prop_name)
            )
            form_fields.append(field)
        
        return html.Div([
            html.H6(f"Configure {node_type}", className="mb-3"),
            *form_fields,
            html.Hr(),
            dbc.Button(
                "Apply Changes",
                id={"type": "apply-node-config", "node_id": node_id},
                color="primary",
                size="sm",
                className="w-100"
            )
        ])
    
    @staticmethod
    def _create_field(
        node_id: str,
        prop_name: str,
        prop_schema: dict,
        current_value: Any
    ) -> dbc.FormGroup:
        """Create form field based on property schema."""
        field_type = prop_schema.get("type", "string")
        description = prop_schema.get("description", "")
        default = prop_schema.get("default")
        enum_values = prop_schema.get("enum")
        
        # Use current value or default
        value = current_value if current_value is not None else default
        
        label = dbc.Label(
            [
                prop_name.replace("_", " ").title(),
                html.Small(f" - {description}", className="text-muted")
                if description else None
            ]
        )
        
        # Choose input type based on schema
        if enum_values:
            # Dropdown for enum values
            input_field = dcc.Dropdown(
                id={"type": "node-config-input", "node_id": node_id, "prop": prop_name},
                options=[{"label": v, "value": v} for v in enum_values],
                value=value,
                clearable=False,
            )
        elif field_type == "number":
            # Numeric input
            input_field = dbc.Input(
                id={"type": "node-config-input", "node_id": node_id, "prop": prop_name},
                type="number",
                value=value,
                step=prop_schema.get("multipleOf", "any"),
                min=prop_schema.get("minimum"),
                max=prop_schema.get("maximum"),
            )
        elif field_type == "boolean":
            # Checkbox
            input_field = dbc.Checkbox(
                id={"type": "node-config-input", "node_id": node_id, "prop": prop_name},
                value=value if value is not None else False,
            )
        else:
            # Text input
            input_field = dbc.Input(
                id={"type": "node-config-input", "node_id": node_id, "prop": prop_name},
                type="text",
                value=value or "",
                placeholder=prop_schema.get("placeholder", ""),
            )
        
        return dbc.FormGroup([label, input_field], className="mb-3")
    
    @staticmethod
    def parse_form_data(form_values: dict[str, Any]) -> dict[str, Any]:
        """
        Parse form values into config dict.
        
        Args:
            form_values: Dict of {prop_name: value}
        
        Returns:
            Validated config dict
        """
        # Strip None values and empty strings
        return {
            k: v for k, v in form_values.items()
            if v is not None and v != ""
        }
```

**Deliverables**:
- ✅ Dynamic form generation from JSON schema
- ✅ Support for common field types (text, number, dropdown, checkbox)
- ✅ Form validation
- ✅ Clean separation from rendering logic

---

### **Day 4: Workflow Validation**

#### Task 4.1: Workflow Validator
**File**: `src/robomage/dashboard/components/workflow_validator.py`

```python
"""
Workflow validation logic.

Validates workflow structure before execution.
Framework-agnostic - pure Python logic.
"""

from typing import Any
from collections import defaultdict, deque


class WorkflowValidator:
    """
    Validates workflow structure and configuration.
    
    Checks for:
    - Cycles (DAG requirement)
    - Disconnected nodes
    - Invalid connections (type mismatches)
    - Missing required configuration
    """
    
    @staticmethod
    def validate(workflow: dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate a workflow definition.
        
        Args:
            workflow: Workflow definition dict
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check for empty workflow
        if not workflow.get("nodes"):
            errors.append("Workflow has no nodes")
            return False, errors
        
        # Check for cycles
        if WorkflowValidator._has_cycles(workflow):
            errors.append("Workflow contains cycles (must be a DAG)")
        
        # Check for disconnected nodes
        disconnected = WorkflowValidator._find_disconnected_nodes(workflow)
        if disconnected:
            errors.append(f"Disconnected nodes: {', '.join(disconnected)}")
        
        # Check for missing configuration
        missing_config = WorkflowValidator._check_required_config(workflow)
        if missing_config:
            errors.extend(missing_config)
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _has_cycles(workflow: dict[str, Any]) -> bool:
        """Check if workflow has cycles using DFS."""
        nodes = {node["id"] for node in workflow.get("nodes", [])}
        edges = workflow.get("edges", [])
        
        # Build adjacency list
        graph = defaultdict(list)
        for edge in edges:
            graph[edge["source"]].append(edge["target"])
        
        # DFS with recursion stack
        visited = set()
        rec_stack = set()
        
        def has_cycle_dfs(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            
            for neighbor in graph[node_id]:
                if neighbor not in visited:
                    if has_cycle_dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node_id)
            return False
        
        for node_id in nodes:
            if node_id not in visited:
                if has_cycle_dfs(node_id):
                    return True
        
        return False
    
    @staticmethod
    def _find_disconnected_nodes(workflow: dict[str, Any]) -> list[str]:
        """Find nodes not connected to any edges."""
        nodes = {node["id"] for node in workflow.get("nodes", [])}
        edges = workflow.get("edges", [])
        
        connected = set()
        for edge in edges:
            connected.add(edge["source"])
            connected.add(edge["target"])
        
        return list(nodes - connected)
    
    @staticmethod
    def _check_required_config(workflow: dict[str, Any]) -> list[str]:
        """Check for nodes missing required configuration."""
        errors = []
        
        # Define required config per node type
        required_config = {
            "load_files": ["directory", "pattern"],
            "filter_q_range": ["q_min", "q_max"],
            "peak_analysis": ["profile_type"],
            "export_csv": ["output_path"],
        }
        
        for node in workflow.get("nodes", []):
            node_type = node.get("type")
            config = node.get("config", {})
            
            if node_type in required_config:
                for required_field in required_config[node_type]:
                    if required_field not in config or not config[required_field]:
                        errors.append(
                            f"Node '{node['id']}' missing required config: {required_field}"
                        )
        
        return errors
```

**Deliverables**:
- ✅ Cycle detection (DAG validation)
- ✅ Disconnected node detection
- ✅ Required configuration validation
- ✅ Clear error messages

---

### **Day 5: Integration - Layout & Callbacks**

#### Task 5.1: Update Workflow Layout
**File**: `src/robomage/dashboard/layouts/workflow_layout.py` (MODIFIED)

Key changes:
1. Replace JSON textarea with canvas renderer
2. Add node palette as draggable source
3. Add properties panel for selected node
4. Keep backward compatibility

```python
# In create_workflow_tab()

from ..components.workflow_canvas import WorkflowCanvasFactory
from ..components.node_configurator import NodeConfigurator

# Create renderer (easy to swap: "cytoscape" → "reactflow")
renderer = WorkflowCanvasFactory.create("cytoscape")

# Center column - Visual canvas instead of JSON editor
dbc.Col([
    dbc.Card([
        dbc.CardHeader([...]),  # Same header
        dbc.CardBody([
            # REPLACE textarea with canvas
            html.Div(id="workflow-canvas-container"),
            
            # Hidden stores for workflow state
            dcc.Store(id="workflow-elements-store"),
            dcc.Store(id="selected-node-id"),
        ])
    ])
], width=6),

# Right column - Properties panel
dbc.Col([
    dbc.Card([
        dbc.CardHeader("Node Properties"),
        dbc.CardBody([
            html.Div(id="node-properties-panel")
        ])
    ])
], width=3),
```

#### Task 5.2: Update Callbacks
**File**: `src/robomage/dashboard/callbacks/workflow.py` (MODIFIED)

Add new callbacks:
1. Render canvas from elements store
2. Handle node drag from palette
3. Handle edge creation (click source, click target)
4. Update properties panel on node select
5. Apply config changes to node

```python
from ..components.workflow_canvas import WorkflowCanvasFactory
from ..components.node_configurator import NodeConfigurator
from ..components.workflow_validator import WorkflowValidator

def register_visual_workflow_callbacks(app):
    """Register callbacks for visual workflow builder."""
    
    renderer = WorkflowCanvasFactory.create("cytoscape")
    
    @app.callback(
        Output("workflow-canvas-container", "children"),
        Input("workflow-elements-store", "data"),
    )
    def render_canvas(elements_data):
        """Render workflow canvas from element data."""
        if not elements_data:
            elements_data = []
        
        elements = [WorkflowElement(**e) for e in elements_data]
        return renderer.render(elements, id="workflow-canvas")
    
    @app.callback(
        Output("node-properties-panel", "children"),
        Input("workflow-canvas", "selectedNodeData"),
        State("workflow-node-types", "data"),
    )
    def show_node_properties(selected_nodes, node_types):
        """Display config form for selected node."""
        if not selected_nodes or len(selected_nodes) == 0:
            return html.P("Select a node to configure", className="text-muted")
        
        node_data = selected_nodes[0]
        node_type = node_data.get("node_type")
        
        # Get schema from node types
        schema = next(
            (nt["config_schema"] for nt in node_types if nt["type"] == node_type),
            {}
        )
        
        return NodeConfigurator.create_config_form(
            node_id=node_data["id"],
            node_type=node_type,
            current_config=node_data.get("config", {}),
            schema=schema
        )
    
    # ... more callbacks for edge creation, validation, etc.
```

**Deliverables**:
- ✅ Visual canvas replaces JSON editor
- ✅ Drag nodes from palette
- ✅ Click to create edges
- ✅ Properties panel for configuration
- ✅ All workflow logic framework-agnostic

---

### **Day 6: Execution Visualization**

#### Task 6.1: Execution Status Updates
**File**: `src/robomage/dashboard/callbacks/workflow.py` (ADD)

```python
@app.callback(
    Output("workflow-elements-store", "data", allow_duplicate=True),
    Input("workflow-execution-result", "data"),
    State("workflow-elements-store", "data"),
    prevent_initial_call=True
)
def update_node_execution_status(execution_result, current_elements):
    """
    Update node status colors during/after execution.
    
    Maps execution status to node data:
    - pending → gray
    - running → orange
    - completed → green
    - failed → red
    """
    if not execution_result or not current_elements:
        return current_elements
    
    # Parse execution results
    node_results = execution_result.get("node_results", [])
    
    # Update element status
    updated_elements = []
    for elem_data in current_elements:
        if elem_data["type"] == "node":
            node_id = elem_data["id"]
            
            # Find this node's execution status
            node_result = next(
                (nr for nr in node_results if nr["node_id"] == node_id),
                None
            )
            
            if node_result:
                elem_data["data"]["status"] = node_result["status"]
        
        updated_elements.append(elem_data)
    
    return updated_elements
```

**Deliverables**:
- ✅ Real-time node status updates
- ✅ Color-coded execution visualization
- ✅ Click executed node to see output

---

### **Day 7: Testing, Polish & Documentation**

#### Task 7.1: Comprehensive Tests
**File**: `tests/test_visual_workflow_builder.py` (NEW)

```python
"""Tests for visual workflow builder components."""

import pytest
from src.robomage.dashboard.components.workflow_canvas import (
    WorkflowElement,
    WorkflowCanvasFactory,
)
from src.robomage.dashboard.components.cytoscape_renderer import (
    CytoscapeWorkflowRenderer
)
from src.robomage.dashboard.components.workflow_validator import WorkflowValidator


def test_renderer_factory():
    """Test renderer factory pattern."""
    assert "cytoscape" in WorkflowCanvasFactory.available_renderers()
    renderer = WorkflowCanvasFactory.create("cytoscape")
    assert isinstance(renderer, CytoscapeWorkflowRenderer)


def test_workflow_to_elements():
    """Test workflow definition to generic elements conversion."""
    renderer = CytoscapeWorkflowRenderer()
    
    workflow = {
        "nodes": [
            {"id": "n1", "type": "load_files", "label": "Load", "position": {"x": 0, "y": 0}},
            {"id": "n2", "type": "peak_analysis", "label": "Analyze", "position": {"x": 100, "y": 0}},
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2"}
        ]
    }
    
    elements = renderer.workflow_to_elements(workflow)
    
    assert len(elements) == 3  # 2 nodes + 1 edge
    assert elements[0].type == "node"
    assert elements[0].id == "n1"
    assert elements[2].type == "edge"


def test_cycle_detection():
    """Test workflow cycle detection."""
    workflow_with_cycle = {
        "nodes": [
            {"id": "n1", "type": "load_files"},
            {"id": "n2", "type": "peak_analysis"},
            {"id": "n3", "type": "export_csv"},
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2"},
            {"id": "e2", "source": "n2", "target": "n3"},
            {"id": "e3", "source": "n3", "target": "n1"},  # Creates cycle!
        ]
    }
    
    is_valid, errors = WorkflowValidator.validate(workflow_with_cycle)
    assert not is_valid
    assert any("cycle" in err.lower() for err in errors)


def test_disconnected_nodes():
    """Test disconnected node detection."""
    workflow_disconnected = {
        "nodes": [
            {"id": "n1", "type": "load_files"},
            {"id": "n2", "type": "peak_analysis"},
            {"id": "n3", "type": "export_csv"},  # Not connected!
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2"},
        ]
    }
    
    is_valid, errors = WorkflowValidator.validate(workflow_disconnected)
    assert not is_valid
    assert any("disconnected" in err.lower() for err in errors)


def test_node_configurator_form_generation():
    """Test dynamic form generation."""
    from src.robomage.dashboard.components.node_configurator import NodeConfigurator
    
    schema = {
        "properties": {
            "prominence": {
                "type": "number",
                "description": "Peak prominence threshold",
                "default": 0.1
            },
            "profile_type": {
                "type": "string",
                "enum": ["gaussian", "lorentzian", "voigt"]
            }
        }
    }
    
    form = NodeConfigurator.create_config_form(
        node_id="test_node",
        node_type="peak_analysis",
        current_config={},
        schema=schema
    )
    
    # Check form was created
    assert form is not None
    # More detailed checks on form structure...
```

#### Task 7.2: Update pixi.toml
**File**: `pixi.toml` (MODIFIED)

```toml
# Add dash-cytoscape dependency
[dependencies]
dash-cytoscape = ">=1.0.0"
```

#### Task 7.3: Documentation
**File**: `docs/visual-workflow-builder-guide.md` (NEW)

- User guide with screenshots
- How to drag nodes
- How to create connections
- How to configure nodes
- How to validate and execute
- Troubleshooting

**Deliverables**:
- ✅ 15+ unit tests
- ✅ Integration tests
- ✅ User documentation
- ✅ All existing tests still pass

---

## 🔄 Architecture Benefits: Future Refactoring

### Swapping Cytoscape for ReactFlow

If you later decide ReactFlow provides better UX:

**Step 1**: Implement ReactFlowRenderer
```python
# src/robomage/dashboard/components/reactflow_renderer.py

class ReactFlowWorkflowRenderer(WorkflowCanvasRenderer):
    """ReactFlow implementation."""
    
    def render(self, elements, **kwargs):
        # Return React component via dash-extensions
        pass
    
    # Implement other protocol methods...

# Register with factory
WorkflowCanvasFactory.register("reactflow", ReactFlowWorkflowRenderer)
```

**Step 2**: Change one line in layout
```python
# workflow_layout.py

# OLD:
renderer = WorkflowCanvasFactory.create("cytoscape")

# NEW:
renderer = WorkflowCanvasFactory.create("reactflow")
```

**That's it!** All workflow logic, validation, configuration UI stays the same.

### Benefits of This Design

1. **Zero callback changes** - Callbacks use generic WorkflowElement, not Cytoscape-specific data
2. **Reusable components** - NodeConfigurator, WorkflowValidator work with any renderer
3. **Easy A/B testing** - Can even let users choose renderer in settings
4. **Clean codebase** - Cytoscape code isolated to one file
5. **Type safety** - Protocol ensures all renderers implement required methods

---

## 📋 Dependencies

### New Python Packages

```toml
# Add to pixi.toml
[dependencies]
dash-cytoscape = ">=1.0.0"
```

That's the only new dependency! Everything else uses existing packages.

---

## 🎯 Success Metrics

### Functional Requirements
- ✅ Drag 8+ node types from palette to canvas
- ✅ Create edges by clicking source → target
- ✅ Configure nodes via dynamic forms
- ✅ Validate workflows before execution
- ✅ Visual execution status (color-coded nodes)
- ✅ Save/load workflows with visual layout

### Technical Requirements
- ✅ All existing tests pass (175 tests)
- ✅ 15+ new tests for visual builder
- ✅ Code quality: ruff, mypy passing
- ✅ Clean abstraction: swap renderer in <5 minutes
- ✅ No Cytoscape code outside cytoscape_renderer.py

### User Experience
- ✅ Non-programmers can build workflows without JSON
- ✅ Visual validation errors (highlight invalid nodes)
- ✅ Responsive UI (<100ms for node operations)
- ✅ Professional appearance matching dashboard style

---

## 🚀 Post-Sprint Enhancements

### Phase 3 Features (Future)
- **Auto-layout**: Automatic node positioning
- **Minimap**: Overview of large workflows
- **Undo/Redo**: Workflow editing history
- **Node grouping**: Organize related nodes
- **Copy/Paste**: Duplicate node subgraphs
- **Templates**: Pre-built workflow snippets
- **Keyboard shortcuts**: Power user features

### Alternative Renderers (Future)
- **ReactFlow**: Better drag-and-drop UX
- **D3.js**: Custom visualizations
- **Mermaid**: Export workflows as diagrams

---

## 📁 Files to Create/Modify

### New Files (6)
1. `src/robomage/dashboard/components/__init__.py`
2. `src/robomage/dashboard/components/workflow_canvas.py` - Abstract protocol
3. `src/robomage/dashboard/components/cytoscape_renderer.py` - Cytoscape impl
4. `src/robomage/dashboard/components/node_configurator.py` - Form builder
5. `src/robomage/dashboard/components/workflow_validator.py` - Validation logic
6. `tests/test_visual_workflow_builder.py` - Comprehensive tests

### Modified Files (3)
1. `src/robomage/dashboard/layouts/workflow_layout.py` - Use renderer
2. `src/robomage/dashboard/callbacks/workflow.py` - Visual callbacks
3. `pixi.toml` - Add dash-cytoscape

### Documentation (2)
1. `docs/sprint-8-visual-workflow-builder.md` - This plan (exists)
2. `docs/visual-workflow-builder-guide.md` - User guide (Day 7)

---

## ✅ Ready to Start!

**Next Steps**:
1. Review and approve this plan
2. Create `sprint-8-visual-workflow-builder` branch
3. Add dash-cytoscape to pixi.toml
4. Start with Day 1 (abstraction layer)
5. Daily commits and testing

**Estimated Timeline**: 5-7 days for full implementation + testing

**Questions?** Ready to begin when you are! 🚀
