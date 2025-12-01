"""
Test Suite for Custom Node Examples

Comprehensive tests demonstrating testing patterns for workflow nodes:
- Unit tests for individual handlers
- Integration tests for workflows
- Mock data fixtures
- Error handling validation
- Configuration testing

Run with:
    pixi run python -m pytest examples/custom_nodes/test_custom_nodes.py -v

Author: RoboMage Team
Date: December 1, 2025
"""

import json
from pathlib import Path

import numpy as np
import pytest

from robomage.data.models import DiffractionData
from robomage.orchestrator import ExecutionContext, WorkflowOrchestrator

# Import handlers to test
from examples.custom_nodes.background_subtraction_node import (
    background_analysis_handler,
    background_subtraction_handler,
)
from examples.custom_nodes.peak_width_analysis_node import peak_width_analysis_handler
from examples.custom_nodes.template_node import (
    template_node_handler,
    template_transform_handler,
)

# ==============================================================================
# FIXTURES
# ==============================================================================


@pytest.fixture
def sample_diffraction_data():
    """Create sample DiffractionData for testing."""
    q_values = np.linspace(2.0, 8.0, 200)

    # Create synthetic pattern with peaks
    intensity = (
        1000 * np.exp(-((q_values - 3.5) ** 2) / 0.05)  # Peak 1
        + 800 * np.exp(-((q_values - 5.2) ** 2) / 0.08)  # Peak 2
        + 600 * np.exp(-((q_values - 7.0) ** 2) / 0.06)  # Peak 3
        + 50 * q_values  # Linear background
        + np.random.rand(200) * 20  # Noise
    )

    return DiffractionData(
        q_values=q_values,
        intensities=intensity,
        filename="test_sample.chi",
        sample_name="Synthetic Test Sample",
    )


@pytest.fixture
def sample_peak_results():
    """Create sample peak analysis results for testing width analysis."""
    return [
        {
            "filename": "test_sample.chi",
            "peaks_detected": 3,
            "peaks_fitted": 3,
            "overall_r_squared": 0.95,
            "peak_list": [
                {
                    "position": 3.5,
                    "d_spacing": 1.8,
                    "height": 1000.0,
                    "width": 0.2,
                    "area": 200.0,
                    "r_squared": 0.98,
                },
                {
                    "position": 5.2,
                    "d_spacing": 1.2,
                    "height": 800.0,
                    "width": 0.25,
                    "area": 200.0,
                    "r_squared": 0.96,
                },
                {
                    "position": 7.0,
                    "d_spacing": 0.9,
                    "height": 600.0,
                    "width": 0.22,
                    "area": 132.0,
                    "r_squared": 0.94,
                },
            ],
        }
    ]


@pytest.fixture
def execution_context():
    """Create fresh ExecutionContext for each test."""
    return ExecutionContext()


# ==============================================================================
# TEMPLATE NODE TESTS
# ==============================================================================


class TestTemplateNode:
    """Tests for template_node_handler."""

    @pytest.mark.asyncio
    async def test_basic_functionality(self, sample_diffraction_data, execution_context):
        """Test basic template node operation."""
        config = {"scale_factor": 2.0, "description": "Test scaling"}
        inputs = {"input": [sample_diffraction_data]}

        result = await template_node_handler(config, inputs, execution_context)

        assert len(result) == 1
        assert result[0]["filename"] == "test_sample.chi"
        assert result[0]["scale_factor"] == 2.0
        assert result[0]["description"] == "Test scaling"
        assert result[0]["scaled_max"] == pytest.approx(
            result[0]["original_max"] * 2.0, rel=0.01
        )

    @pytest.mark.asyncio
    async def test_default_config(self, sample_diffraction_data, execution_context):
        """Test template node with default configuration."""
        config = {}  # No parameters
        inputs = {"input": [sample_diffraction_data]}

        result = await template_node_handler(config, inputs, execution_context)

        assert len(result) == 1
        assert result[0]["scale_factor"] == 1.0  # Default value
        assert "description" in result[0]

    @pytest.mark.asyncio
    async def test_invalid_scale_factor(self, sample_diffraction_data, execution_context):
        """Test validation of scale_factor parameter."""
        config = {"scale_factor": -1.0}  # Invalid (negative)
        inputs = {"input": [sample_diffraction_data]}

        with pytest.raises(ValueError, match="scale_factor must be positive"):
            await template_node_handler(config, inputs, execution_context)

    @pytest.mark.asyncio
    async def test_missing_input(self, execution_context):
        """Test error handling for missing input."""
        config = {"scale_factor": 1.0}
        inputs = {}  # No input

        with pytest.raises(ValueError, match="No input data"):
            await template_node_handler(config, inputs, execution_context)

    @pytest.mark.asyncio
    async def test_empty_input(self, execution_context):
        """Test error handling for empty input list."""
        config = {"scale_factor": 1.0}
        inputs = {"input": []}  # Empty list

        with pytest.raises(ValueError, match="No input data"):
            await template_node_handler(config, inputs, execution_context)

    @pytest.mark.asyncio
    async def test_multiple_files(self, sample_diffraction_data, execution_context):
        """Test processing multiple files."""
        # Create second file with different data
        data2 = DiffractionData(
            q_values=sample_diffraction_data.q_values,
            intensities=sample_diffraction_data.intensities * 0.5,
            filename="test_sample_2.chi",
            sample_name="Sample 2",
        )

        config = {"scale_factor": 3.0}
        inputs = {"input": [sample_diffraction_data, data2]}

        result = await template_node_handler(config, inputs, execution_context)

        assert len(result) == 2
        assert result[0]["filename"] == "test_sample.chi"
        assert result[1]["filename"] == "test_sample_2.chi"
        assert all(r["scale_factor"] == 3.0 for r in result)


class TestTemplateTransformNode:
    """Tests for template_transform_handler."""

    @pytest.mark.asyncio
    async def test_returns_diffraction_data(
        self, sample_diffraction_data, execution_context
    ):
        """Test that transform handler returns DiffractionData objects."""
        config = {"scale_factor": 2.0}
        inputs = {"input": [sample_diffraction_data]}

        result = await template_transform_handler(config, inputs, execution_context)

        assert len(result) == 1
        assert isinstance(result[0], DiffractionData)
        assert result[0].filename == sample_diffraction_data.filename

    @pytest.mark.asyncio
    async def test_intensity_scaling(self, sample_diffraction_data, execution_context):
        """Test that intensities are correctly scaled."""
        scale = 2.5
        config = {"scale_factor": scale}
        inputs = {"input": [sample_diffraction_data]}

        result = await template_transform_handler(config, inputs, execution_context)

        expected = sample_diffraction_data.intensities * scale
        np.testing.assert_array_almost_equal(result[0].intensities, expected)


# ==============================================================================
# BACKGROUND SUBTRACTION NODE TESTS
# ==============================================================================


class TestBackgroundSubtractionNode:
    """Tests for background_subtraction_handler."""

    @pytest.mark.asyncio
    async def test_linear_background(self, sample_diffraction_data, execution_context):
        """Test linear background subtraction."""
        config = {"method": "linear", "q_fit_min": 2.0, "q_fit_max": 3.0}
        inputs = {"input": [sample_diffraction_data]}

        result = await background_subtraction_handler(config, inputs, execution_context)

        assert len(result) == 1
        assert isinstance(result[0], DiffractionData)

        # Background-subtracted intensities should be lower
        assert result[0].intensities.max() < sample_diffraction_data.intensities.max()

    @pytest.mark.asyncio
    async def test_constant_background(self, sample_diffraction_data, execution_context):
        """Test constant background subtraction."""
        config = {"method": "constant"}
        inputs = {"input": [sample_diffraction_data]}

        result = await background_subtraction_handler(config, inputs, execution_context)

        assert len(result) == 1
        assert isinstance(result[0], DiffractionData)

    @pytest.mark.asyncio
    async def test_polynomial_background(
        self, sample_diffraction_data, execution_context
    ):
        """Test polynomial background subtraction."""
        config = {"method": "polynomial", "polynomial_degree": 2}
        inputs = {"input": [sample_diffraction_data]}

        result = await background_subtraction_handler(config, inputs, execution_context)

        assert len(result) == 1
        assert isinstance(result[0], DiffractionData)

    @pytest.mark.asyncio
    async def test_invalid_method(self, sample_diffraction_data, execution_context):
        """Test error for invalid background method."""
        config = {"method": "invalid_method"}
        inputs = {"input": [sample_diffraction_data]}

        with pytest.raises(ValueError, match="Invalid method"):
            await background_subtraction_handler(config, inputs, execution_context)

    @pytest.mark.asyncio
    async def test_invalid_q_range(self, sample_diffraction_data, execution_context):
        """Test error for invalid Q-range."""
        config = {"method": "linear", "q_fit_min": 5.0, "q_fit_max": 3.0}  # min > max
        inputs = {"input": [sample_diffraction_data]}

        with pytest.raises(ValueError, match="Invalid Q range"):
            await background_subtraction_handler(config, inputs, execution_context)

    @pytest.mark.asyncio
    async def test_metadata_preservation(
        self, sample_diffraction_data, execution_context
    ):
        """Test that metadata is preserved."""
        config = {"method": "linear"}
        inputs = {"input": [sample_diffraction_data]}

        result = await background_subtraction_handler(config, inputs, execution_context)

        assert result[0].filename == sample_diffraction_data.filename
        assert result[0].sample_name == sample_diffraction_data.sample_name
        np.testing.assert_array_equal(result[0].q_values, sample_diffraction_data.q_values)

    @pytest.mark.asyncio
    async def test_return_backgrounds(self, sample_diffraction_data, execution_context):
        """Test storing backgrounds in context."""
        config = {"method": "linear", "return_backgrounds": True}
        inputs = {"input": [sample_diffraction_data]}

        result = await background_subtraction_handler(config, inputs, execution_context)

        assert "backgrounds" in execution_context.metadata
        bg_data = execution_context.metadata["backgrounds"]
        assert len(bg_data) == 1
        assert "background" in bg_data[0]
        assert "r_squared" in bg_data[0]


class TestBackgroundAnalysisNode:
    """Tests for background_analysis_handler."""

    @pytest.mark.asyncio
    async def test_returns_analysis_dict(
        self, sample_diffraction_data, execution_context
    ):
        """Test that analysis handler returns structured dictionaries."""
        config = {"method": "linear"}
        inputs = {"input": [sample_diffraction_data]}

        result = await background_analysis_handler(config, inputs, execution_context)

        assert len(result) == 1
        assert isinstance(result[0], dict)
        assert "filename" in result[0]
        assert "method" in result[0]
        assert "r_squared" in result[0]
        assert "background_max" in result[0]

    @pytest.mark.asyncio
    async def test_linear_parameters(self, sample_diffraction_data, execution_context):
        """Test that linear method includes slope and intercept."""
        config = {"method": "linear"}
        inputs = {"input": [sample_diffraction_data]}

        result = await background_analysis_handler(config, inputs, execution_context)

        assert "slope" in result[0]
        assert "intercept" in result[0]


# ==============================================================================
# PEAK WIDTH ANALYSIS NODE TESTS
# ==============================================================================


class TestPeakWidthAnalysisNode:
    """Tests for peak_width_analysis_handler."""

    @pytest.mark.asyncio
    async def test_basic_functionality(
        self, sample_diffraction_data, sample_peak_results, execution_context
    ):
        """Test basic peak width analysis."""
        config = {"fit_profile": "gaussian", "window_size": 0.5}
        inputs = {"files": [sample_diffraction_data], "peak_results": sample_peak_results}

        result = await peak_width_analysis_handler(config, inputs, execution_context)

        assert len(result) == 1
        assert result[0]["filename"] == "test_sample.chi"
        assert result[0]["num_peaks_analyzed"] > 0
        assert "peaks" in result[0]
        assert "statistics" in result[0]

    @pytest.mark.asyncio
    async def test_classification(
        self, sample_diffraction_data, sample_peak_results, execution_context
    ):
        """Test peak width classification."""
        config = {
            "fit_profile": "gaussian",
            "classify_widths": True,
            "narrow_threshold": 0.1,
            "broad_threshold": 0.3,
        }
        inputs = {"files": [sample_diffraction_data], "peak_results": sample_peak_results}

        result = await peak_width_analysis_handler(config, inputs, execution_context)

        assert "classification_counts" in result[0]
        counts = result[0]["classification_counts"]
        assert "narrow" in counts
        assert "medium" in counts
        assert "broad" in counts

    @pytest.mark.asyncio
    async def test_statistics_calculation(
        self, sample_diffraction_data, sample_peak_results, execution_context
    ):
        """Test statistical summary calculation."""
        config = {"fit_profile": "gaussian"}
        inputs = {"files": [sample_diffraction_data], "peak_results": sample_peak_results}

        result = await peak_width_analysis_handler(config, inputs, execution_context)

        stats = result[0]["statistics"]
        assert "mean_fwhm" in stats
        assert "std_fwhm" in stats
        assert "min_fwhm" in stats
        assert "max_fwhm" in stats
        assert "median_fwhm" in stats

        # Verify statistics are reasonable
        assert stats["min_fwhm"] <= stats["median_fwhm"] <= stats["max_fwhm"]

    @pytest.mark.asyncio
    async def test_invalid_profile(
        self, sample_diffraction_data, sample_peak_results, execution_context
    ):
        """Test error for invalid fit profile."""
        config = {"fit_profile": "invalid_profile"}
        inputs = {"files": [sample_diffraction_data], "peak_results": sample_peak_results}

        with pytest.raises(ValueError, match="Invalid fit_profile"):
            await peak_width_analysis_handler(config, inputs, execution_context)

    @pytest.mark.asyncio
    async def test_missing_files_input(self, sample_peak_results, execution_context):
        """Test error for missing files input."""
        config = {"fit_profile": "gaussian"}
        inputs = {"peak_results": sample_peak_results}  # No files

        with pytest.raises(ValueError, match="No diffraction files"):
            await peak_width_analysis_handler(config, inputs, execution_context)

    @pytest.mark.asyncio
    async def test_missing_peak_results(
        self, sample_diffraction_data, execution_context
    ):
        """Test error for missing peak results."""
        config = {"fit_profile": "gaussian"}
        inputs = {"files": [sample_diffraction_data]}  # No peak results

        with pytest.raises(ValueError, match="No peak analysis results"):
            await peak_width_analysis_handler(config, inputs, execution_context)

    @pytest.mark.asyncio
    async def test_min_height_filtering(
        self, sample_diffraction_data, sample_peak_results, execution_context
    ):
        """Test filtering peaks by minimum height."""
        config = {"fit_profile": "gaussian", "min_height": 900.0}  # Filter out peaks < 900
        inputs = {"files": [sample_diffraction_data], "peak_results": sample_peak_results}

        result = await peak_width_analysis_handler(config, inputs, execution_context)

        # Should only analyze peak with height >= 900 (first peak: 1000)
        assert result[0]["num_peaks_analyzed"] <= 1


# ==============================================================================
# INTEGRATION TESTS
# ==============================================================================


class TestWorkflowIntegration:
    """Integration tests for workflows using custom nodes."""

    @pytest.mark.asyncio
    async def test_simple_workflow(self, sample_diffraction_data):
        """Test simple workflow: load → template → background subtract."""
        # Import workflow models
        try:
            from services.workflow_engine.models import (
                WorkflowDefinition,
                WorkflowNode,
                WorkflowEdge,
                NodePosition,
            )
        except ImportError:
            pytest.skip("Workflow models not available in test environment")

        # Create orchestrator
        orch = WorkflowOrchestrator()

        # Register nodes (use transform handler which returns DiffractionData)
        orch.register_node_handler("template_node", template_transform_handler)
        orch.register_node_handler(
            "background_subtraction", background_subtraction_handler
        )

        # Mock load_files handler that returns our test data
        async def mock_load_handler(config, inputs, context):
            return [sample_diffraction_data]

        orch.register_node_handler("load_files", mock_load_handler)

        # Define workflow using Pydantic models
        workflow = WorkflowDefinition(
            name="Test Workflow",
            description="Test simple workflow",
            nodes=[
                WorkflowNode(
                    id="load_1",
                    type="load_files",
                    label="Load Files",
                    config={},
                    position=NodePosition(x=100, y=100),
                ),
                WorkflowNode(
                    id="template_1",
                    type="template_node",
                    label="Template",
                    config={"scale_factor": 1.0},
                    position=NodePosition(x=300, y=100),
                ),
                WorkflowNode(
                    id="bg_sub_1",
                    type="background_subtraction",
                    label="Background Subtract",
                    config={"method": "linear"},
                    position=NodePosition(x=500, y=100),
                ),
            ],
            edges=[
                WorkflowEdge(
                    id="e1", source="load_1", target="template_1"
                ),
                WorkflowEdge(
                    id="e2", source="template_1", target="bg_sub_1"
                ),
            ],
        )

        # Execute workflow
        result = await orch.execute_workflow(workflow)

        assert result.status.value == "completed"
        # Verify we have node results for each node
        assert len(result.node_results) == 3
        
        # Find the background subtraction result
        bg_result = next(
            (r for r in result.node_results if r.node_id == "bg_sub_1"), None
        )
        assert bg_result is not None
        assert bg_result.status.value == "completed"

    @pytest.mark.asyncio
    async def test_workflow_with_inspection(self, sample_diffraction_data):
        """Test workflow with inspection enabled."""
        # Import workflow models
        try:
            from services.workflow_engine.models import (
                WorkflowDefinition,
                WorkflowNode,
                WorkflowEdge,
                NodePosition,
            )
        except ImportError:
            pytest.skip("Workflow models not available in test environment")

        # Create orchestrator with inspection
        orch = WorkflowOrchestrator(enable_inspection=True)

        # Register template node
        orch.register_node_handler("template_node", template_transform_handler)

        # Mock loader
        async def mock_load_handler(config, inputs, context):
            return [sample_diffraction_data]

        orch.register_node_handler("load_files", mock_load_handler)

        # Simple workflow
        workflow = WorkflowDefinition(
            name="Inspection Test",
            description="Test workflow with inspection",
            nodes=[
                WorkflowNode(
                    id="load_1",
                    type="load_files",
                    label="Load",
                    config={},
                    position=NodePosition(x=100, y=100),
                ),
                WorkflowNode(
                    id="template_1",
                    type="template_node",
                    label="Template",
                    config={"scale_factor": 2.0},
                    position=NodePosition(x=300, y=100),
                ),
            ],
            edges=[
                WorkflowEdge(id="e1", source="load_1", target="template_1")
            ],
        )

        # Execute
        result = await orch.execute_workflow(workflow)

        # Verify inspection data was captured
        assert len(orch.inspection_data) > 0
        assert "template_1" in orch.inspection_data


# ==============================================================================
# EXAMPLE WORKFLOW TEST
# ==============================================================================


@pytest.mark.asyncio
async def test_example_workflow_loads():
    """Test that example_workflow.json is valid and can be loaded."""
    workflow_path = Path(__file__).parent / "example_workflow.json"

    assert workflow_path.exists(), f"Workflow file not found: {workflow_path}"

    with open(workflow_path) as f:
        workflow = json.load(f)

    # Validate structure
    assert "nodes" in workflow
    assert "edges" in workflow
    assert len(workflow["nodes"]) > 0
    assert len(workflow["edges"]) > 0

    # Check node types match our handlers
    expected_types = {
        "load_files",
        "template_node",
        "background_subtraction",
        "peak_analysis",
        "peak_width_analysis",
        "export_csv",
        "export_json",
    }

    node_types = {node["type"] for node in workflow["nodes"]}
    custom_types = {"template_node", "background_subtraction", "peak_width_analysis"}

    assert custom_types.issubset(
        node_types
    ), f"Expected custom node types {custom_types} in workflow"


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v"])
