"""
Tests for visual workflow builder components.

Tests the abstraction layer and renderer protocol.
"""

from typing import Any

import pytest

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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
