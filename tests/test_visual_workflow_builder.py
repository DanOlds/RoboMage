"""
Tests for visual workflow builder components.

Tests the abstraction layer and renderer protocol.
"""

from typing import Any

import pytest

from src.robomage.dashboard.components.cytoscape_renderer import (
    CytoscapeWorkflowRenderer,
)
from src.robomage.dashboard.components.node_configurator import NodeConfigurator
from src.robomage.dashboard.components.workflow_canvas import (
    CanvasEvent,
    WorkflowCanvasFactory,
    WorkflowElement,
)


class MockWorkflowRenderer:
    """Mock renderer for testing factory pattern."""

    def __init__(self, **config: Any):
        self.config = config

    def render(self, elements: list[WorkflowElement], **kwargs: Any) -> Any:
        return {"elements": elements, "kwargs": kwargs}

    def parse_event(self, event_data: dict[str, Any] | None) -> CanvasEvent | None:
        if not event_data:
            return None
        return CanvasEvent(
            event_type=event_data.get("type", "unknown"),
            element_id=event_data.get("id"),
        )

    def create_stylesheet(self) -> Any:
        return {"mock": "stylesheet"}

    def workflow_to_elements(self, workflow: dict[str, Any]) -> list[WorkflowElement]:
        elements = []
        for node in workflow.get("nodes", []):
            elements.append(
                WorkflowElement(
                    id=node["id"],
                    type="node",
                    data={"label": node.get("label", "")},
                    position=node.get("position"),
                )
            )
        for edge in workflow.get("edges", []):
            elements.append(
                WorkflowElement(
                    id=edge["id"],
                    type="edge",
                    source=edge["source"],
                    target=edge["target"],
                )
            )
        return elements

    def elements_to_workflow(self, elements: list[WorkflowElement]) -> dict[str, Any]:
        nodes = []
        edges = []
        for elem in elements:
            if elem.type == "node":
                nodes.append(
                    {
                        "id": elem.id,
                        "label": elem.data.get("label", ""),
                        "position": elem.position,
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
        return {"nodes": nodes, "edges": edges}


def test_workflow_element_creation():
    """Test WorkflowElement model creation."""
    # Node element
    node = WorkflowElement(
        id="n1",
        type="node",
        data={"label": "Test Node", "node_type": "load_files"},
        position={"x": 100.0, "y": 200.0},
    )

    assert node.id == "n1"
    assert node.type == "node"
    assert node.data["label"] == "Test Node"
    assert node.position == {"x": 100.0, "y": 200.0}
    assert node.source is None
    assert node.target is None

    # Edge element
    edge = WorkflowElement(
        id="e1",
        type="edge",
        source="n1",
        target="n2",
    )

    assert edge.id == "e1"
    assert edge.type == "edge"
    assert edge.source == "n1"
    assert edge.target == "n2"
    assert edge.position is None


def test_canvas_event_creation():
    """Test CanvasEvent model creation."""
    event = CanvasEvent(
        event_type="node_click",
        element_id="n1",
        element_data={"label": "Test"},
        position={"x": 150.0, "y": 250.0},
    )

    assert event.event_type == "node_click"
    assert event.element_id == "n1"
    assert event.element_data == {"label": "Test"}
    assert event.position == {"x": 150.0, "y": 250.0}


def test_workflow_canvas_factory_registration():
    """Test renderer factory registration."""
    # Register mock renderer
    WorkflowCanvasFactory.register("mock", MockWorkflowRenderer)

    # Check registration
    assert "mock" in WorkflowCanvasFactory.available_renderers()
    assert WorkflowCanvasFactory.is_registered("mock")
    assert not WorkflowCanvasFactory.is_registered("nonexistent")


def test_workflow_canvas_factory_create():
    """Test renderer factory creation."""
    # Register mock renderer
    WorkflowCanvasFactory.register("mock", MockWorkflowRenderer)

    # Create renderer
    renderer = WorkflowCanvasFactory.create("mock", test_config="value")

    assert isinstance(renderer, MockWorkflowRenderer)
    assert renderer.config == {"test_config": "value"}


def test_workflow_canvas_factory_unknown_renderer():
    """Test factory raises error for unknown renderer."""
    with pytest.raises(ValueError, match="Unknown renderer"):
        WorkflowCanvasFactory.create("nonexistent")


def test_mock_renderer_workflow_to_elements():
    """Test workflow to elements conversion."""
    renderer = MockWorkflowRenderer()

    workflow = {
        "nodes": [
            {"id": "n1", "label": "Load Files", "position": {"x": 0, "y": 0}},
            {"id": "n2", "label": "Analyze", "position": {"x": 100, "y": 0}},
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2"},
        ],
    }

    elements = renderer.workflow_to_elements(workflow)

    assert len(elements) == 3  # 2 nodes + 1 edge
    assert elements[0].type == "node"
    assert elements[0].id == "n1"
    assert elements[0].data["label"] == "Load Files"
    assert elements[1].type == "node"
    assert elements[1].id == "n2"
    assert elements[2].type == "edge"
    assert elements[2].source == "n1"
    assert elements[2].target == "n2"


def test_mock_renderer_elements_to_workflow():
    """Test elements to workflow conversion."""
    renderer = MockWorkflowRenderer()

    elements = [
        WorkflowElement(
            id="n1",
            type="node",
            data={"label": "Load Files"},
            position={"x": 0, "y": 0},
        ),
        WorkflowElement(
            id="n2",
            type="node",
            data={"label": "Analyze"},
            position={"x": 100, "y": 0},
        ),
        WorkflowElement(
            id="e1",
            type="edge",
            source="n1",
            target="n2",
        ),
    ]

    workflow = renderer.elements_to_workflow(elements)

    assert len(workflow["nodes"]) == 2
    assert len(workflow["edges"]) == 1
    assert workflow["nodes"][0]["id"] == "n1"
    assert workflow["nodes"][0]["label"] == "Load Files"
    assert workflow["edges"][0]["source"] == "n1"
    assert workflow["edges"][0]["target"] == "n2"


def test_mock_renderer_parse_event():
    """Test event parsing."""
    renderer = MockWorkflowRenderer()

    # Valid event
    event_data = {"type": "node_click", "id": "n1"}
    event = renderer.parse_event(event_data)

    assert event is not None
    assert event.event_type == "node_click"
    assert event.element_id == "n1"

    # None event
    assert renderer.parse_event(None) is None


def test_workflow_element_with_extra_fields():
    """Test WorkflowElement allows extra fields."""
    # This tests Pydantic config extra='allow'
    element = WorkflowElement(
        id="n1",
        type="node",
        data={"label": "Test"},
        custom_field="custom_value",  # Extra field
    )

    # Extra fields should be stored
    assert hasattr(element, "custom_field")


# ============================================================================
# Cytoscape Renderer Tests
# ============================================================================


def test_cytoscape_renderer_registration():
    """Test that CytoscapeWorkflowRenderer auto-registers with factory."""
    assert "cytoscape" in WorkflowCanvasFactory.available_renderers()
    assert WorkflowCanvasFactory.is_registered("cytoscape")


def test_cytoscape_renderer_creation():
    """Test creating CytoscapeWorkflowRenderer via factory."""
    renderer = WorkflowCanvasFactory.create("cytoscape")
    assert isinstance(renderer, CytoscapeWorkflowRenderer)

    # Test with custom config
    renderer = WorkflowCanvasFactory.create(
        "cytoscape", width="800px", height="400px", enable_physics=True
    )
    assert renderer.width == "800px"
    assert renderer.height == "400px"
    assert renderer.enable_physics is True


def test_cytoscape_renderer_workflow_to_elements():
    """Test Cytoscape-specific workflow to elements conversion."""
    renderer = CytoscapeWorkflowRenderer()

    workflow = {
        "nodes": [
            {
                "id": "n1",
                "type": "load_files",
                "label": "Load Files",
                "position": {"x": 0, "y": 0},
                "config": {"directory": "/data"},
            },
            {
                "id": "n2",
                "type": "peak_analysis",
                "label": "Analyze Peaks",
                "position": {"x": 200, "y": 0},
                "config": {"prominence": 0.1},
            },
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2"},
        ],
    }

    elements = renderer.workflow_to_elements(workflow)

    # Check node conversion
    assert len(elements) == 3  # 2 nodes + 1 edge
    node1 = elements[0]
    assert node1.type == "node"
    assert node1.id == "n1"
    assert node1.data["label"] == "Load Files"
    assert node1.data["node_type"] == "load_files"
    assert node1.data["category"] == "data"  # Category determined by node type
    assert node1.data["config"] == {"directory": "/data"}
    assert node1.position == {"x": 0, "y": 0}

    node2 = elements[1]
    assert node2.data["node_type"] == "peak_analysis"
    assert node2.data["category"] == "analysis"

    # Check edge conversion
    edge = elements[2]
    assert edge.type == "edge"
    assert edge.source == "n1"
    assert edge.target == "n2"


def test_cytoscape_renderer_elements_to_workflow():
    """Test Cytoscape-specific elements to workflow conversion."""
    renderer = CytoscapeWorkflowRenderer()

    elements = [
        WorkflowElement(
            id="n1",
            type="node",
            data={
                "label": "Load Files",
                "node_type": "load_files",
                "category": "data",
                "config": {"directory": "/data"},
            },
            position={"x": 0, "y": 0},
        ),
        WorkflowElement(
            id="n2",
            type="node",
            data={
                "label": "Analyze",
                "node_type": "peak_analysis",
                "category": "analysis",
                "config": {"prominence": 0.1},
            },
            position={"x": 200, "y": 0},
        ),
        WorkflowElement(
            id="e1",
            type="edge",
            source="n1",
            target="n2",
        ),
    ]

    workflow = renderer.elements_to_workflow(elements)

    # Check nodes
    assert len(workflow["nodes"]) == 2
    assert workflow["nodes"][0]["id"] == "n1"
    assert workflow["nodes"][0]["type"] == "load_files"
    assert workflow["nodes"][0]["label"] == "Load Files"
    assert workflow["nodes"][0]["config"] == {"directory": "/data"}
    assert workflow["nodes"][0]["position"] == {"x": 0, "y": 0}

    # Check edges
    assert len(workflow["edges"]) == 1
    assert workflow["edges"][0]["id"] == "e1"
    assert workflow["edges"][0]["source"] == "n1"
    assert workflow["edges"][0]["target"] == "n2"


def test_cytoscape_renderer_parse_event_node_click():
    """Test parsing Cytoscape node click event."""
    renderer = CytoscapeWorkflowRenderer()

    cyto_event = {
        "type": "tap",
        "target": {
            "group": "nodes",
            "data": {"id": "n1", "label": "Load Files"},
            "position": {"x": 100, "y": 200},
        },
    }

    event = renderer.parse_event(cyto_event)

    assert event is not None
    assert event.event_type == "node_click"
    assert event.element_id == "n1"
    assert event.element_data == {"id": "n1", "label": "Load Files"}
    assert event.position == {"x": 100, "y": 200}


def test_cytoscape_renderer_parse_event_edge_click():
    """Test parsing Cytoscape edge click event."""
    renderer = CytoscapeWorkflowRenderer()

    cyto_event = {
        "type": "tap",
        "target": {
            "group": "edges",
            "data": {"id": "e1", "source": "n1", "target": "n2"},
        },
    }

    event = renderer.parse_event(cyto_event)

    assert event is not None
    assert event.event_type == "edge_click"
    assert event.element_id == "e1"


def test_cytoscape_renderer_parse_event_drag():
    """Test parsing Cytoscape drag event."""
    renderer = CytoscapeWorkflowRenderer()

    cyto_event = {
        "type": "drag",
        "target": {
            "data": {"id": "n1"},
            "position": {"x": 150, "y": 250},
        },
    }

    event = renderer.parse_event(cyto_event)

    assert event is not None
    assert event.event_type == "node_drag"
    assert event.element_id == "n1"
    assert event.position == {"x": 150, "y": 250}


def test_cytoscape_renderer_parse_event_none():
    """Test parsing None event data."""
    renderer = CytoscapeWorkflowRenderer()
    assert renderer.parse_event(None) is None


def test_cytoscape_renderer_create_stylesheet():
    """Test Cytoscape stylesheet creation."""
    renderer = CytoscapeWorkflowRenderer()
    stylesheet = renderer.create_stylesheet()

    # Should be a list of style dictionaries
    assert isinstance(stylesheet, list)
    assert len(stylesheet) > 0

    # Check for key selectors
    selectors = [style["selector"] for style in stylesheet]
    assert "node" in selectors
    assert "edge" in selectors
    assert "node:selected" in selectors

    # Check for category styles
    assert "node[category='data']" in selectors
    assert "node[category='analysis']" in selectors
    assert "node[category='transform']" in selectors
    assert "node[category='output']" in selectors

    # Check for status styles
    assert "node[status='running']" in selectors
    assert "node[status='completed']" in selectors
    assert "node[status='failed']" in selectors


def test_cytoscape_renderer_render():
    """Test Cytoscape component rendering."""
    renderer = CytoscapeWorkflowRenderer(width="600px", height="400px")

    elements = [
        WorkflowElement(
            id="n1",
            type="node",
            data={"label": "Test Node", "category": "data"},
            position={"x": 0, "y": 0},
        ),
    ]

    component = renderer.render(elements, id="test-canvas")

    # Check component properties
    assert hasattr(component, "id")
    assert component.id == "test-canvas"
    assert component.style["width"] == "600px"
    assert component.style["height"] == "400px"

    # Check elements are converted
    assert len(component.elements) == 1


def test_cytoscape_node_category_mapping():
    """Test node type to category mapping."""
    renderer = CytoscapeWorkflowRenderer()

    # Test data category
    assert renderer._get_node_category("load_files") == "data"
    assert renderer._get_node_category("load_session") == "data"

    # Test analysis category
    assert renderer._get_node_category("peak_analysis") == "analysis"
    assert renderer._get_node_category("statistics") == "analysis"

    # Test transform category
    assert renderer._get_node_category("filter_q_range") == "transform"
    assert renderer._get_node_category("normalize") == "transform"

    # Test output category
    assert renderer._get_node_category("export_csv") == "output"
    assert renderer._get_node_category("export_json") == "output"
    assert renderer._get_node_category("save_to_session") == "output"

    # Test unknown/default
    assert renderer._get_node_category("unknown_type") == "data"
    assert renderer._get_node_category(None) == "data"


def test_cytoscape_to_cytoscape_elements():
    """Test internal conversion to Cytoscape format."""
    renderer = CytoscapeWorkflowRenderer()

    elements = [
        WorkflowElement(
            id="n1",
            type="node",
            data={"label": "Test", "category": "data"},
            position={"x": 100, "y": 200},
        ),
        WorkflowElement(
            id="e1",
            type="edge",
            source="n1",
            target="n2",
            data={"custom": "value"},
        ),
    ]

    cyto_elements = renderer._to_cytoscape_elements(elements)

    # Check node conversion
    assert len(cyto_elements) == 2
    node = cyto_elements[0]
    assert node["data"]["id"] == "n1"
    assert node["data"]["label"] == "Test"
    assert node["position"] == {"x": 100, "y": 200}
    assert node["classes"] == "data"

    # Check edge conversion
    edge = cyto_elements[1]
    assert edge["data"]["id"] == "e1"
    assert edge["data"]["source"] == "n1"
    assert edge["data"]["target"] == "n2"
    assert edge["data"]["custom"] == "value"


# ============================================================================
# Node Configurator Tests
# ============================================================================


def test_node_configurator_empty_schema():
    """Test NodeConfigurator with empty/missing schema."""
    form = NodeConfigurator.create_config_form(
        node_id="test_node",
        node_type="test_type",
        current_config={},
        schema={},
    )

    # Should return a simple "no config needed" message
    assert form is not None


def test_node_configurator_text_field():
    """Test creating text input field."""
    schema = {
        "properties": {
            "directory": {
                "type": "string",
                "description": "Directory path",
                "placeholder": "/data/files",
            }
        }
    }

    form = NodeConfigurator.create_config_form(
        node_id="test_node",
        node_type="load_files",
        current_config={},
        schema=schema,
    )

    assert form is not None


def test_node_configurator_number_field():
    """Test creating numeric input field."""
    schema = {
        "properties": {
            "prominence": {
                "type": "number",
                "description": "Peak prominence",
                "default": 0.1,
                "minimum": 0.01,
                "maximum": 1.0,
            }
        }
    }

    form = NodeConfigurator.create_config_form(
        node_id="test_node",
        node_type="peak_analysis",
        current_config={},
        schema=schema,
    )

    assert form is not None


def test_node_configurator_enum_field():
    """Test creating dropdown/enum field."""
    schema = {
        "properties": {
            "profile_type": {
                "type": "string",
                "enum": ["gaussian", "lorentzian", "voigt"],
                "default": "gaussian",
                "description": "Peak profile shape",
            }
        }
    }

    form = NodeConfigurator.create_config_form(
        node_id="test_node",
        node_type="peak_analysis",
        current_config={"profile_type": "lorentzian"},
        schema=schema,
    )

    assert form is not None


def test_node_configurator_boolean_field():
    """Test creating checkbox/boolean field."""
    schema = {
        "properties": {
            "normalize": {
                "type": "boolean",
                "description": "Normalize intensity values",
                "default": False,
            }
        }
    }

    form = NodeConfigurator.create_config_form(
        node_id="test_node",
        node_type="transform",
        current_config={},
        schema=schema,
    )

    assert form is not None


def test_node_configurator_integer_field():
    """Test creating integer input field."""
    schema = {
        "properties": {
            "min_distance": {
                "type": "integer",
                "description": "Minimum peak distance",
                "default": 5,
                "minimum": 1,
                "maximum": 100,
            }
        }
    }

    form = NodeConfigurator.create_config_form(
        node_id="test_node",
        node_type="peak_analysis",
        current_config={},
        schema=schema,
    )

    assert form is not None


def test_node_configurator_array_field():
    """Test creating array input field."""
    schema = {
        "properties": {
            "wavelengths": {
                "type": "array",
                "description": "List of wavelengths",
            }
        }
    }

    form = NodeConfigurator.create_config_form(
        node_id="test_node",
        node_type="multi_wavelength",
        current_config={"wavelengths": [1.5406, 0.7107]},
        schema=schema,
    )

    assert form is not None


def test_node_configurator_multiple_fields():
    """Test form with multiple fields of different types."""
    schema = {
        "properties": {
            "directory": {"type": "string", "description": "Data directory"},
            "pattern": {
                "type": "string",
                "default": "*.chi",
                "description": "File pattern",
            },
            "recursive": {
                "type": "boolean",
                "default": False,
                "description": "Search recursively",
            },
            "max_files": {
                "type": "integer",
                "minimum": 1,
                "maximum": 1000,
                "default": 100,
            },
        }
    }

    form = NodeConfigurator.create_config_form(
        node_id="test_node",
        node_type="load_files",
        current_config={
            "directory": "/data",
            "pattern": "*.xy",
            "recursive": True,
            "max_files": 50,
        },
        schema=schema,
    )

    assert form is not None


def test_node_configurator_parse_form_data():
    """Test parsing form data."""
    form_data = {
        "prominence": 0.15,
        "profile_type": "gaussian",
        "min_distance": 5,
        "normalize": True,
        "empty_field": "",  # Should be removed
        "none_field": None,  # Should be removed
    }

    parsed = NodeConfigurator.parse_form_data(form_data)

    assert "prominence" in parsed
    assert parsed["prominence"] == 0.15
    assert "profile_type" in parsed
    assert "min_distance" in parsed
    assert "normalize" in parsed
    assert "empty_field" not in parsed  # Removed
    assert "none_field" not in parsed  # Removed


def test_node_configurator_validate_config_valid():
    """Test validating valid configuration."""
    schema = {
        "properties": {
            "prominence": {
                "type": "number",
                "minimum": 0.01,
                "maximum": 1.0,
            },
            "profile_type": {
                "type": "string",
                "enum": ["gaussian", "lorentzian", "voigt"],
            },
        },
        "required": ["prominence"],
    }

    config = {
        "prominence": 0.15,
        "profile_type": "gaussian",
    }

    is_valid, errors = NodeConfigurator.validate_config(config, schema)

    assert is_valid is True
    assert len(errors) == 0


def test_node_configurator_validate_config_missing_required():
    """Test validation fails for missing required field."""
    schema = {
        "properties": {
            "directory": {"type": "string"},
        },
        "required": ["directory"],
    }

    config = {}

    is_valid, errors = NodeConfigurator.validate_config(config, schema)

    assert is_valid is False
    assert len(errors) > 0
    assert any("directory" in err and "required" in err for err in errors)


def test_node_configurator_validate_config_below_minimum():
    """Test validation fails for value below minimum."""
    schema = {
        "properties": {
            "prominence": {"type": "number", "minimum": 0.01},
        }
    }

    config = {"prominence": 0.005}  # Below minimum

    is_valid, errors = NodeConfigurator.validate_config(config, schema)

    assert is_valid is False
    assert len(errors) > 0
    assert any("prominence" in err and "minimum" in err for err in errors)


def test_node_configurator_validate_config_above_maximum():
    """Test validation fails for value above maximum."""
    schema = {
        "properties": {
            "prominence": {"type": "number", "maximum": 1.0},
        }
    }

    config = {"prominence": 1.5}  # Above maximum

    is_valid, errors = NodeConfigurator.validate_config(config, schema)

    assert is_valid is False
    assert len(errors) > 0
    assert any("prominence" in err and "maximum" in err for err in errors)


def test_node_configurator_validate_config_invalid_enum():
    """Test validation fails for invalid enum value."""
    schema = {
        "properties": {
            "profile_type": {
                "type": "string",
                "enum": ["gaussian", "lorentzian", "voigt"],
            },
        }
    }

    config = {"profile_type": "invalid"}

    is_valid, errors = NodeConfigurator.validate_config(config, schema)

    assert is_valid is False
    assert len(errors) > 0
    assert any(
        "profile_type" in err and "not in allowed values" in err for err in errors
    )


def test_node_configurator_validate_config_wrong_type():
    """Test validation fails for wrong type."""
    schema = {
        "properties": {
            "prominence": {"type": "number"},
            "normalize": {"type": "boolean"},
        }
    }

    config = {
        "prominence": "not a number",  # Should be number
        "normalize": "yes",  # Should be boolean
    }

    is_valid, errors = NodeConfigurator.validate_config(config, schema)

    assert is_valid is False
    assert len(errors) >= 2  # At least 2 type errors


def test_node_configurator_validate_config_pattern():
    """Test validation with regex pattern."""
    schema = {
        "properties": {
            "pattern": {
                "type": "string",
                "pattern": r"^\*\.\w+$",  # e.g., *.chi, *.xy
            },
        }
    }

    # Valid pattern
    config_valid = {"pattern": "*.chi"}
    is_valid, errors = NodeConfigurator.validate_config(config_valid, schema)
    assert is_valid is True

    # Invalid pattern
    config_invalid = {"pattern": "invalid"}
    is_valid, errors = NodeConfigurator.validate_config(config_invalid, schema)
    assert is_valid is False
    assert any("pattern" in err for err in errors)


def test_node_configurator_get_field_help_text_number():
    """Test help text generation for number field."""
    schema = {
        "type": "number",
        "minimum": 0.01,
        "maximum": 1.0,
        "default": 0.1,
    }

    help_text = NodeConfigurator.get_field_help_text(schema)

    assert "Number" in help_text or "between" in help_text
    assert "0.01" in help_text
    assert "1.0" in help_text
    assert "0.1" in help_text


def test_node_configurator_get_field_help_text_enum():
    """Test help text generation for enum field."""
    schema = {
        "type": "string",
        "enum": ["gaussian", "lorentzian", "voigt"],
        "default": "gaussian",
    }

    help_text = NodeConfigurator.get_field_help_text(schema)

    assert "gaussian" in help_text
    assert "lorentzian" in help_text
    assert "voigt" in help_text


def test_node_configurator_get_field_help_text_boolean():
    """Test help text generation for boolean field."""
    schema = {
        "type": "boolean",
        "default": True,
    }

    help_text = NodeConfigurator.get_field_help_text(schema)

    assert "True" in help_text or "False" in help_text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
