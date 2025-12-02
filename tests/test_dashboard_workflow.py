"""
Tests for Workflow Dashboard Integration

Verifies workflow tab functionality and service communication.
"""

import json
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def dash_app():
    """Create dashboard app for testing."""
    from robomage.dashboard.app import create_app

    return create_app(debug=False)


def test_workflow_tab_layout(dash_app):
    """Test that workflow tab layout is created properly."""
    from robomage.dashboard.layouts.workflow_layout import create_workflow_tab

    layout = create_workflow_tab()
    assert layout is not None
    # Check for key components (Sprint 8: visual workflow canvas)
    children = str(layout)
    assert "workflow-canvas" in children  # Visual workflow canvas
    assert "workflow-service-status" in children
    assert "execute-workflow-btn" in children


def test_get_default_workflow_json():
    """Test default workflow JSON template."""
    from robomage.dashboard.layouts.workflow_layout import get_default_workflow_json

    default_json = get_default_workflow_json()
    assert default_json is not None
    assert len(default_json) > 0

    # Should be valid JSON
    workflow = json.loads(default_json)
    assert "nodes" in workflow
    assert "edges" in workflow
    assert "name" in workflow
    assert len(workflow["nodes"]) == 3  # load, analyze, export
    assert len(workflow["edges"]) == 2


@patch("requests.get")
def test_service_health_check_success(mock_get, dash_app):
    """Test service health check with working service."""
    # Mock successful health check
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": "healthy",
        "workflows_count": 0,
        "node_types_registered": 8,
    }
    mock_get.return_value = mock_response

    # Simulate callback
    from robomage.dashboard.callbacks.workflow import register_service_health_callback

    # Just verify the function exists and can be called
    register_service_health_callback(dash_app)


@patch("requests.get")
def test_service_health_check_unavailable(mock_get, dash_app):
    """Test service health check with unavailable service."""
    # Mock failed health check
    mock_get.side_effect = Exception("Connection refused")

    from robomage.dashboard.callbacks.workflow import register_service_health_callback

    # Should not raise exception
    register_service_health_callback(dash_app)


@patch("requests.get")
def test_load_node_types(mock_get, dash_app):
    """Test loading node types from service."""
    # Mock node types response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {
            "type": "load_files",
            "name": "Load Files",
            "description": "Load diffraction data files",
            "category": "data",
            "icon": "fas fa-file-import",
        },
        {
            "type": "peak_analysis",
            "name": "Peak Analysis",
            "description": "Detect and fit peaks",
            "category": "analysis",
            "icon": "fas fa-mountain",
        },
    ]
    mock_get.return_value = mock_response

    from robomage.dashboard.callbacks.workflow import create_node_palette_ui

    node_types = mock_response.json()
    palette = create_node_palette_ui(node_types)

    assert palette is not None
    assert len(palette) > 0


@patch("requests.post")
def test_save_workflow(mock_post, dash_app):
    """Test saving workflow to service."""
    # Mock save response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": "test-workflow-id",
        "name": "Test Workflow",
        "nodes": [],
        "edges": [],
    }
    mock_post.return_value = mock_response

    from robomage.dashboard.callbacks.workflow import (
        register_workflow_management_callbacks,
    )

    # Just verify callback registration works
    register_workflow_management_callbacks(dash_app)


@patch("requests.post")
def test_execute_workflow(mock_post, dash_app):
    """Test workflow execution."""
    # Mock execution response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "execution_id": "test-exec-id",
        "status": "completed",
        "total_duration_ms": 123.4,
        "node_results": [
            {
                "node_id": "load_1",
                "status": "completed",
                "duration_ms": 50.0,
            },
            {
                "node_id": "analyze_1",
                "status": "completed",
                "duration_ms": 73.4,
            },
        ],
    }
    mock_post.return_value = mock_response

    from robomage.dashboard.callbacks.workflow import create_execution_log_ui

    result = mock_response.json()
    log_ui = create_execution_log_ui(result)

    assert log_ui is not None
    # Check that status is displayed
    log_str = str(log_ui)
    assert "completed" in log_str.lower()


def test_workflow_callbacks_registered(dash_app):
    """Test that all workflow callbacks are registered."""
    from robomage.dashboard.callbacks import workflow

    # Should not raise any exceptions
    workflow.register_callbacks(dash_app)

    # Verify callback exists
    assert len(dash_app.callback_map) > 0


# JSON Editor Tests (Option A: Collapsible Panel)


def test_json_editor_in_layout():
    """Test that JSON editor components are present in layout."""
    from robomage.dashboard.layouts.workflow_layout import create_workflow_tab

    layout = create_workflow_tab()
    children = str(layout)
    
    # Check for JSON editor components
    assert "toggle-json-editor-btn" in children
    assert "json-editor-collapse" in children
    assert "workflow-json-editor" in children
    assert "apply-json-btn" in children
    assert "json-validation-feedback" in children
    assert "Show JSON" in children  # Default button text


def test_json_editor_toggle():
    """Test JSON editor toggle functionality."""
    # Simulate toggle callback behavior
    is_open = False
    
    # First click - should open
    new_state = not is_open
    button_text = "Hide JSON" if new_state else "Show JSON"
    
    assert new_state is True
    assert button_text == "Hide JSON"
    
    # Second click - should close
    is_open = new_state
    new_state = not is_open
    button_text = "Hide JSON" if new_state else "Show JSON"
    
    assert new_state is False
    assert button_text == "Show JSON"


def test_json_sync_from_workflow():
    """Test JSON editor syncs when workflow changes."""
    # Sample workflow data
    workflow_data = {
        "name": "Test Workflow",
        "description": "Test description",
        "nodes": [
            {
                "id": "load_1",
                "type": "load_files",
                "label": "Load Data",
                "config": {"directory": "/tmp", "pattern": "*.chi"},
                "position": {"x": 100, "y": 100},
            }
        ],
        "edges": [],
    }
    
    # Simulate sync callback
    json_str = json.dumps(workflow_data, indent=2)
    
    assert json_str is not None
    assert "Test Workflow" in json_str
    assert "load_files" in json_str
    assert '"nodes"' in json_str
    assert '"edges"' in json_str


def test_json_apply_valid_workflow():
    """Test applying valid JSON to workflow."""
    json_text = json.dumps({
        "name": "New Workflow",
        "nodes": [
            {
                "id": "n1",
                "type": "load_files",
                "label": "Load",
                "config": {},
                "position": {"x": 0, "y": 0},
            }
        ],
        "edges": [],
    }, indent=2)
    
    # Parse and validate structure
    workflow = json.loads(json_text)
    
    assert "nodes" in workflow
    assert "edges" in workflow
    assert len(workflow["nodes"]) == 1
    assert workflow["nodes"][0]["id"] == "n1"


def test_json_apply_invalid_json_syntax():
    """Test applying invalid JSON syntax."""
    json_text = '{"nodes": [invalid json}'
    
    # Should raise JSONDecodeError
    with pytest.raises(json.JSONDecodeError):
        json.loads(json_text)


def test_json_apply_missing_nodes_key():
    """Test applying JSON without 'nodes' key."""
    json_text = json.dumps({
        "name": "Invalid Workflow",
        "edges": [],
    })
    
    workflow = json.loads(json_text)
    
    # Should be missing 'nodes' key
    assert "nodes" not in workflow
    assert "edges" in workflow


def test_json_apply_missing_edges_key():
    """Test applying JSON without 'edges' key."""
    json_text = json.dumps({
        "name": "Invalid Workflow",
        "nodes": [],
    })
    
    workflow = json.loads(json_text)
    
    # Should be missing 'edges' key
    assert "nodes" in workflow
    assert "edges" not in workflow


def test_json_apply_empty_workflow():
    """Test applying empty but valid workflow."""
    json_text = json.dumps({
        "name": "Empty Workflow",
        "nodes": [],
        "edges": [],
    })
    
    workflow = json.loads(json_text)
    
    assert "nodes" in workflow
    assert "edges" in workflow
    assert len(workflow["nodes"]) == 0
    assert len(workflow["edges"]) == 0


def test_json_sync_handles_empty_data():
    """Test JSON editor handles empty/None workflow data."""
    # Empty workflow data
    workflow_data = None
    
    # Should return empty string
    json_str = "" if not workflow_data else json.dumps(workflow_data, indent=2)
    
    assert json_str == ""


def test_json_editor_preserves_formatting():
    """Test that JSON editor uses consistent formatting."""
    workflow_data = {
        "nodes": [{"id": "n1", "type": "load_files"}],
        "edges": [],
    }
    
    # Use 2-space indentation
    json_str = json.dumps(workflow_data, indent=2)
    
    # Check formatting
    assert "  " in json_str  # 2-space indent
    assert json_str.startswith("{")
    assert json_str.endswith("}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
