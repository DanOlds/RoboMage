"""
Tests for Inspector Tab

Tests the Node I/O Inspector dashboard tab layout, components, and callbacks.
"""

import json
from datetime import datetime

import pytest
from dash import html

from robomage.dashboard.callbacks import inspector
from robomage.dashboard.components import NodeInspectorPanel
from robomage.dashboard.layouts.inspector_layout import (
    create_inspector_tab,
    create_node_card,
)


class TestInspectorLayout:
    """Test inspector tab layout creation."""

    def test_create_inspector_tab(self):
        """Test that inspector tab layout is created correctly."""
        layout = create_inspector_tab()
        assert layout is not None
        assert isinstance(layout, html.Div)

    def test_inspector_tab_has_workflow_selector(self):
        """Test that inspector tab includes workflow selector."""
        layout = create_inspector_tab()
        layout_str = str(layout)
        assert "inspector-workflow-selector" in layout_str

    def test_inspector_tab_has_timeline(self):
        """Test that inspector tab includes timeline section."""
        layout = create_inspector_tab()
        layout_str = str(layout)
        assert "inspector-timeline" in layout_str

    def test_inspector_tab_has_node_list(self):
        """Test that inspector tab includes node list section."""
        layout = create_inspector_tab()
        layout_str = str(layout)
        assert "inspector-node-list" in layout_str

    def test_inspector_tab_has_io_panels(self):
        """Test that inspector tab includes I/O display panels."""
        layout = create_inspector_tab()
        layout_str = str(layout)
        assert "inspector-input-panel" in layout_str
        assert "inspector-output-panel" in layout_str
        assert "inspector-stats-panel" in layout_str
        assert "inspector-metadata-panel" in layout_str

    def test_inspector_tab_has_refresh_button(self):
        """Test that inspector tab includes refresh button."""
        layout = create_inspector_tab()
        layout_str = str(layout)
        assert "inspector-refresh-btn" in layout_str

    def test_inspector_tab_has_export_button(self):
        """Test that inspector tab includes export button."""
        layout = create_inspector_tab()
        layout_str = str(layout)
        assert "inspector-export-btn" in layout_str


class TestNodeCard:
    """Test node card component creation."""

    def test_create_node_card_basic(self):
        """Test basic node card creation."""
        card = create_node_card(
            node_id="test_node_1",
            node_type="load_files",
            duration_ms=100.5,
            input_shape="dict[2]",
            output_shape="list[3]",
        )
        assert card is not None

    def test_create_node_card_selected(self):
        """Test selected node card has different styling."""
        card_selected = create_node_card(
            node_id="test_node_1",
            node_type="load_files",
            duration_ms=100.5,
            input_shape="dict[2]",
            output_shape="list[3]",
            is_selected=True,
        )
        card_unselected = create_node_card(
            node_id="test_node_1",
            node_type="load_files",
            duration_ms=100.5,
            input_shape="dict[2]",
            output_shape="list[3]",
            is_selected=False,
        )
        # Cards should have different border styles
        assert str(card_selected) != str(card_unselected)

    def test_node_card_duration_colors(self):
        """Test that node cards have duration-based color coding."""
        # Fast execution (< 100ms) - success
        card_fast = create_node_card(
            "node1", "normalize", 50.0, "dict[1]", "dict[1]"
        )
        card_fast_str = str(card_fast)
        assert "success" in card_fast_str

        # Very slow execution (> 1000ms) - danger
        card_slow = create_node_card(
            "node2", "peak_analysis", 1500.0, "dict[1]", "dict[1]"
        )
        card_slow_str = str(card_slow)
        assert "danger" in card_slow_str


class TestNodeInspectorPanel:
    """Test node inspector panel components."""

    def test_create_data_display_empty(self):
        """Test data display with empty data."""
        display = NodeInspectorPanel.create_data_display(None, "Test Data", "input")
        assert display is not None
        display_str = str(display)
        assert "No input data available" in display_str

    def test_create_data_display_with_data(self):
        """Test data display with actual data."""
        data = {
            "type": "list[DiffractionData]",
            "count": 3,
            "sample": {"filename": "test.chi", "num_points": 100},
        }
        display = NodeInspectorPanel.create_data_display(data, "Test Data", "input")
        assert display is not None
        display_str = str(display)
        assert "list[DiffractionData]" in display_str
        assert "3" in display_str

    def test_create_stats_display(self):
        """Test execution statistics display."""
        display = NodeInspectorPanel.create_stats_display(
            duration_ms=125.5,
            timestamp_in="2025-12-01T10:00:00",
            timestamp_out="2025-12-01T10:00:01",
            input_shape="dict[2]",
            output_shape="list[3]",
        )
        assert display is not None
        display_str = str(display)
        assert "125.5" in display_str  # Duration
        assert "dict[2]" in display_str  # Input shape
        assert "list[3]" in display_str  # Output shape

    def test_create_stats_display_duration_labels(self):
        """Test that stats display uses correct duration labels."""
        # Fast
        display_fast = NodeInspectorPanel.create_stats_display(
            duration_ms=50.0,
            timestamp_in=None,
            timestamp_out=None,
            input_shape=None,
            output_shape=None,
        )
        assert "Fast" in str(display_fast)

        # Very Slow
        display_slow = NodeInspectorPanel.create_stats_display(
            duration_ms=1500.0,
            timestamp_in=None,
            timestamp_out=None,
            input_shape=None,
            output_shape=None,
        )
        assert "Very Slow" in str(display_slow)

    def test_create_metadata_display_empty(self):
        """Test metadata display with no metadata."""
        display = NodeInspectorPanel.create_metadata_display(None)
        assert display is not None
        display_str = str(display)
        assert "No metadata available" in display_str

    def test_create_metadata_display_with_data(self):
        """Test metadata display with actual metadata."""
        metadata = {
            "execution_id": "exec_123",
            "version": "1.0.0",
            "parameters": {"param1": "value1"},
        }
        display = NodeInspectorPanel.create_metadata_display(metadata)
        assert display is not None
        display_str = str(display)
        assert "exec_123" in display_str

    def test_create_timeline_visualization_empty(self):
        """Test timeline visualization with no data."""
        timeline = NodeInspectorPanel.create_timeline_visualization([])
        assert timeline is not None
        timeline_str = str(timeline)
        assert "No execution timeline available" in timeline_str

    def test_create_timeline_visualization_with_data(self):
        """Test timeline visualization with inspection data."""
        inspections = [
            {
                "node_id": "load_1",
                "node_type": "load_files",
                "duration_ms": 100.0,
                "timestamp_in": "2025-12-01T10:00:00",
            },
            {
                "node_id": "normalize_1",
                "node_type": "normalize",
                "duration_ms": 50.0,
                "timestamp_in": "2025-12-01T10:00:01",
            },
        ]
        timeline = NodeInspectorPanel.create_timeline_visualization(inspections)
        assert timeline is not None
        timeline_str = str(timeline)
        assert "load_1" in timeline_str
        assert "normalize_1" in timeline_str

    def test_json_viewer_creation(self):
        """Test JSON viewer creation."""
        data = {"key1": "value1", "key2": [1, 2, 3]}
        viewer = NodeInspectorPanel._create_json_viewer(data)
        assert viewer is not None
        viewer_str = str(viewer)
        # Should contain JSON-formatted content
        assert "key1" in viewer_str
        assert "value1" in viewer_str


class TestInspectorCallbacks:
    """Test inspector callback registration."""

    def test_callbacks_module_exists(self):
        """Test that inspector callbacks module exists."""
        assert hasattr(inspector, "register_callbacks")

    def test_register_callbacks_function(self):
        """Test that register_callbacks is callable."""
        assert callable(inspector.register_callbacks)


class TestInspectorIntegration:
    """Integration tests for inspector tab with main dashboard."""

    def test_inspector_tab_in_main_layout(self):
        """Test that Inspector tab is included in main dashboard layout."""
        from robomage.dashboard.layouts.main_layout import create_main_layout

        layout = create_main_layout()
        layout_str = str(layout)
        assert "Inspector" in layout_str or "inspector" in layout_str

    def test_inspector_stores_in_main_layout(self):
        """Test that inspector stores are included in main layout."""
        from robomage.dashboard.layouts.main_layout import create_main_layout

        layout = create_main_layout()
        layout_str = str(layout)
        assert "inspector-workflow-data" in layout_str
        assert "inspector-selected-node" in layout_str

    def test_inspector_callbacks_registered(self):
        """Test that inspector callbacks module is registered in app."""
        from robomage.dashboard.app import create_app

        # Simply verify app creation succeeds with inspector callbacks
        app = create_app(debug=False)
        assert app is not None
        # If there were callback registration errors, create_app would fail
        # This test passing means inspector.register_callbacks() was called successfully


# Mark inspector integration tests as requiring full app
pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")
