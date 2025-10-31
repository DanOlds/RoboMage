"""
Test cases for the RoboMage Dashboard

Tests the dashboard components, callbacks, and basic functionality.
"""

import pytest


def test_dashboard_imports():
    """Test that dashboard components can be imported successfully."""
    from robomage.dashboard.app import create_app

    # Test app creation
    app = create_app()
    assert app is not None
    assert app.title == "RoboMage Dashboard"


def test_main_layout_creation():
    """Test that the main layout can be created."""
    from robomage.dashboard.layouts.main_layout import create_main_layout

    layout = create_main_layout()
    assert layout is not None

    # Check that layout contains expected components
    layout_str = str(layout)
    assert "RoboMage Dashboard" in layout_str
    assert "File Management" in layout_str
    assert "Diffraction Pattern" in layout_str
    assert "Analysis Controls" in layout_str


def test_file_parsing():
    """Test file parsing functionality."""
    import base64

    from robomage.dashboard.callbacks.file_upload import parse_uploaded_file

    # Create a simple test file content
    test_data = "# Test diffraction data\n1.0 100\n2.0 200\n3.0 150\n"
    encoded_content = base64.b64encode(test_data.encode()).decode()
    content = f"data:text/plain;base64,{encoded_content}"

    result = parse_uploaded_file(content, "test.chi")

    assert result is not None
    assert result["filename"] == "test.chi"
    assert result["num_points"] == 3
    assert result["q"] == [1.0, 2.0, 3.0]
    assert result["intensity"] == [100, 200, 150]


def test_plotting_functions():
    """Test plotting utility functions."""

    from robomage.dashboard.callbacks.plotting import (
        create_empty_plot,
        get_x_data,
        get_y_data,
    )

    # Test data
    test_data = {"q": [1.0, 2.0, 3.0], "intensity": [100, 200, 150]}

    # Test X-axis conversions
    x_data, x_label = get_x_data(test_data, "q")
    assert x_data == [1.0, 2.0, 3.0]
    assert x_label == "Q (Å⁻¹)"

    # Test Y-axis conversions
    y_data, y_label = get_y_data(test_data, "raw")
    assert y_data == [100, 200, 150]
    assert y_label == "Intensity (counts)"

    # Test empty plot creation
    fig = create_empty_plot()
    assert fig is not None


if __name__ == "__main__":
    pytest.main([__file__])
