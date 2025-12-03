"""
Test Sprint 6 Days 5-6: Complete workflow-session integration with full serialization.

This test verifies that workflows can save results to sessions via the dashboard,
testing the complete data flow from workflow execution through session persistence.
"""

import sys
from pathlib import Path

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from services.workflow_engine.models import (
    ExecutionStatus,
    NodeExecutionResult,
    NodePosition,
    WorkflowDefinition,
    WorkflowNode,
)
from src.robomage.orchestrator import WorkflowOrchestrator
from src.robomage.workflow.nodes import data_nodes


# Import Edge model
from services.workflow_engine.models import WorkflowDefinition


# Register a mock input handler for workflow connection
async def mock_input_handler(config, inputs, context):
    """Mock input node that does nothing (just enables workflow graph connectivity)."""
    return {}


class TestWorkflowSessionFullSerialization:
    """Test that workflow execution results contain full DiffractionData for session saves."""

    @pytest.mark.asyncio
    async def test_orchestrator_full_serialization_mode(self):
        """Test that store_full_outputs=True serializes complete DiffractionData."""
        # Create workflow that loads files
        workflow = WorkflowDefinition(
            name="Test Full Serialization",
            description="Test full output storage",
            nodes=[
                WorkflowNode(
                    id="input",
                    type="mock_input",
                    label="Input",
                    config={},
                    position=NodePosition(x=50, y=100),
                ),
                WorkflowNode(
                    id="load_1",
                    type="load_files",
                    label="Load Files",
                    config={
                        "directory": str(Path(__file__).parent.parent / "examples"),
                        "pattern": "*.chi",
                    },
                    position=NodePosition(x=100, y=100),
                )
            ],
            edges=[
                {
                    "id": "edge1",
                    "source": "input",
                    "target": "load_1"
                }
            ],
        )

        orchestrator = WorkflowOrchestrator()
        orchestrator.register_node_handler("mock_input", mock_input_handler)
        orchestrator.register_node_handler("load_files", data_nodes.load_files_handler)

        # Execute with full serialization
        result = await orchestrator.execute_workflow(workflow, store_full_outputs=True)

        # Verify execution succeeded
        assert result.status.value == "completed"
        assert len(result.node_results) == 2  # input + load_1

        # Verify output contains full data (check load_1, not input)
        node_result = result.node_results[1]  # Changed from [0] to [1]
        assert node_result.node_id == "load_1"
        assert node_result.output is not None
        assert isinstance(node_result.output, list)
        assert len(node_result.output) > 0

        # Verify first item is complete DiffractionData dict
        first_file = node_result.output[0]
        assert isinstance(first_file, dict)
        assert "q_values" in first_file
        assert "intensities" in first_file
        assert "filename" in first_file

        # Verify data is complete (not truncated)
        assert len(first_file["q_values"]) > 500  # More than summary truncation limit
        assert len(first_file["intensities"]) > 500

    @pytest.mark.asyncio
    async def test_orchestrator_summary_mode_default(self):
        """Test that default mode (store_full_outputs=False) stores summaries."""
        workflow = WorkflowDefinition(
            name="Test Summary Mode",
            description="Test default summary storage",
            nodes=[
                WorkflowNode(
                    id="input",
                    type="mock_input",
                    label="Input",
                    config={},
                    position=NodePosition(x=50, y=100),
                ),
                WorkflowNode(
                    id="load_1",
                    type="load_files",
                    label="Load Files",
                    config={
                        "directory": str(Path(__file__).parent.parent / "examples"),
                        "pattern": "*.chi",
                    },
                    position=NodePosition(x=100, y=100),
                )
            ],
            edges=[
                {
                    "id": "edge2",
                    "source": "input",
                    "target": "load_1"
                }
            ],
        )

        orchestrator = WorkflowOrchestrator()
        orchestrator.register_node_handler("mock_input", mock_input_handler)
        orchestrator.register_node_handler("load_files", data_nodes.load_files_handler)

        # Execute with default (summary) mode
        result = await orchestrator.execute_workflow(workflow, store_full_outputs=False)

        # Verify execution succeeded
        assert result.status.value == "completed"
        assert len(result.node_results) == 2  # input + load_1

        # Verify output is a summary dict (check load_1, not input)
        node_result = result.node_results[1]  # Changed from [0] to [1]
        assert node_result.output is not None
        assert isinstance(node_result.output, dict)
        assert "summary" in node_result.output
        assert "type" in node_result.output
        assert len(node_result.output["summary"]) <= 500  # Truncated

    def test_dashboard_callback_extracts_full_data(self):
        """Test that dashboard callback can extract DiffractionData from full results."""
        from datetime import datetime

        import numpy as np

        from robomage.data.models import DiffractionData

        # Simulate execution results with full serialization
        execution_results = {
            "execution_id": "exec_test",
            "status": "completed",
            "node_results": [
                {
                    "node_id": "load_1",
                    "status": "completed",
                    "output": [
                        {
                            "q_values": [0.5, 0.6, 0.7],
                            "intensities": [100.0, 120.0, 110.0],
                            "filename": "test.chi",
                            "wavelength": 0.1665,
                            "sample_name": None,
                            "timestamp": datetime.now().isoformat(),
                            "temperature": None,
                            "statistics": {
                                "min_intensity": 100.0,
                                "max_intensity": 120.0,
                                "mean_intensity": 110.0,
                                "std_intensity": 10.0,
                            },
                        }
                    ],
                }
            ],
        }

        # Extract data (simulating dashboard callback logic)
        node_results = execution_results.get("node_results", [])
        diffraction_data_list = []

        for node_result in node_results:
            output = node_result.get("output")
            if isinstance(output, list):
                for item in output:
                    if isinstance(item, dict) and "q_values" in item:
                        # Convert lists to numpy arrays (as dashboard would receive from JSON)
                        item["q_values"] = np.array(item["q_values"])
                        item["intensities"] = np.array(item["intensities"])
                        # Reconstruct DiffractionData
                        data = DiffractionData(**item)
                        diffraction_data_list.append(data)

        # Verify extraction succeeded
        assert len(diffraction_data_list) == 1
        data = diffraction_data_list[0]
        assert isinstance(data, DiffractionData)
        assert data.filename == "test.chi"
        assert data.wavelength == 0.1665
        assert len(data.q_values) == 3
        assert len(data.intensities) == 3


class TestNodeExecutionResultModel:
    """Test that NodeExecutionResult model accepts both dict and list outputs."""

    def test_accepts_dict_output(self):
        """Verify model accepts dict output (summary mode)."""
        from datetime import datetime

        result = NodeExecutionResult(
            node_id="test_1",
            status=ExecutionStatus.COMPLETED,
            started_at=datetime.now(),
            output={"summary": "test data", "type": "list"},
        )

        assert isinstance(result.output, dict)
        assert "summary" in result.output

    def test_accepts_list_output(self):
        """Verify model accepts list output (full serialization mode)."""
        from datetime import datetime

        result = NodeExecutionResult(
            node_id="test_1",
            status=ExecutionStatus.COMPLETED,
            started_at=datetime.now(),
            output=[
                {"q_values": [1, 2, 3], "intensities": [4, 5, 6]},
                {"q_values": [7, 8, 9], "intensities": [10, 11, 12]},
            ],
        )

        assert isinstance(result.output, list)
        assert len(result.output) == 2
        assert "q_values" in result.output[0]
