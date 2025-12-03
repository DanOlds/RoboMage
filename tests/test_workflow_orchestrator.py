"""
Tests for Workflow Orchestrator

Tests the core DAG execution engine including:
- Topological sorting
- Node execution
- Data flow between nodes
- Error handling
- Cycle detection
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
    NodePosition,
    WorkflowDefinition,
    WorkflowEdge,
    WorkflowNode,
)
from src.robomage.orchestrator import ExecutionContext, WorkflowOrchestrator


class TestExecutionContext:
    """Test execution context for data flow management."""

    def test_store_and_retrieve_output(self):
        """Test storing and retrieving node outputs."""
        context = ExecutionContext()

        # Store output
        test_data = {"result": 42}
        context.set_node_output("node1", test_data)

        # Retrieve output
        retrieved = context.get_node_output("node1")
        assert retrieved == test_data

    def test_get_nonexistent_output_returns_none(self):
        """Test retrieving non-existent output returns None."""
        context = ExecutionContext()
        assert context.get_node_output("nonexistent") is None

    def test_metadata_storage(self):
        """Test storing metadata in context."""
        context = ExecutionContext()
        context.metadata["key"] = "value"
        assert context.metadata["key"] == "value"

    def test_get_all_outputs(self):
        """Test retrieving all outputs at once."""
        context = ExecutionContext()
        context.set_node_output("node1", {"a": 1})
        context.set_node_output("node2", {"b": 2})

        all_outputs = context.get_all_outputs()
        assert len(all_outputs) == 2
        assert "node1" in all_outputs
        assert "node2" in all_outputs


class TestWorkflowOrchestrator:
    """Test workflow orchestrator functionality."""

    def test_register_node_handler(self):
        """Test registering node handlers."""
        orchestrator = WorkflowOrchestrator()

        async def test_handler(config, inputs, context):
            return {"result": 42}

        orchestrator.register_node_handler("test_node", test_handler)
        assert "test_node" in orchestrator.node_handlers
        assert orchestrator.node_handlers["test_node"] == test_handler

    def test_topological_sort_simple_chain(self):
        """Test topological sort with simple linear chain."""
        orchestrator = WorkflowOrchestrator()

        workflow = WorkflowDefinition(
            name="Simple Chain",
            nodes=[
                WorkflowNode(
                    id="node1",
                    type="test",
                    label="Node 1",
                    position=NodePosition(x=0, y=0),
                ),
                WorkflowNode(
                    id="node2",
                    type="test",
                    label="Node 2",
                    position=NodePosition(x=1, y=0),
                ),
                WorkflowNode(
                    id="node3",
                    type="test",
                    label="Node 3",
                    position=NodePosition(x=2, y=0),
                ),
            ],
            edges=[
                WorkflowEdge(id="e1", source="node1", target="node2"),
                WorkflowEdge(id="e2", source="node2", target="node3"),
            ],
        )

        sorted_nodes = orchestrator._topological_sort(workflow)
        node_ids = [n.id for n in sorted_nodes]

        # Verify correct ordering
        assert node_ids.index("node1") < node_ids.index("node2")
        assert node_ids.index("node2") < node_ids.index("node3")
        assert len(sorted_nodes) == 3

    def test_topological_sort_parallel_branches(self):
        """Test topological sort with parallel branches."""
        orchestrator = WorkflowOrchestrator()

        workflow = WorkflowDefinition(
            name="Parallel Branches",
            nodes=[
                WorkflowNode(
                    id="root",
                    type="test",
                    label="Root",
                    position=NodePosition(x=0, y=0),
                ),
                WorkflowNode(
                    id="branch1",
                    type="test",
                    label="Branch 1",
                    position=NodePosition(x=1, y=0),
                ),
                WorkflowNode(
                    id="branch2",
                    type="test",
                    label="Branch 2",
                    position=NodePosition(x=1, y=1),
                ),
                WorkflowNode(
                    id="merge",
                    type="test",
                    label="Merge",
                    position=NodePosition(x=2, y=0),
                ),
            ],
            edges=[
                WorkflowEdge(id="e1", source="root", target="branch1"),
                WorkflowEdge(id="e2", source="root", target="branch2"),
                WorkflowEdge(id="e3", source="branch1", target="merge"),
                WorkflowEdge(id="e4", source="branch2", target="merge"),
            ],
        )

        sorted_nodes = orchestrator._topological_sort(workflow)
        node_ids = [n.id for n in sorted_nodes]

        # Verify root comes first
        assert node_ids[0] == "root"
        # Verify merge comes last
        assert node_ids[-1] == "merge"
        # Verify branches come after root and before merge
        assert node_ids.index("branch1") > node_ids.index("root")
        assert node_ids.index("branch2") > node_ids.index("root")
        assert node_ids.index("branch1") < node_ids.index("merge")
        assert node_ids.index("branch2") < node_ids.index("merge")

    def test_topological_sort_detects_cycle(self):
        """Test that topological sort detects and rejects cycles."""
        orchestrator = WorkflowOrchestrator()

        # Create workflow with cycle: node1 -> node2 -> node3 -> node1
        workflow = WorkflowDefinition(
            name="Cycle Workflow",
            nodes=[
                WorkflowNode(
                    id="node1",
                    type="test",
                    label="Node 1",
                    position=NodePosition(x=0, y=0),
                ),
                WorkflowNode(
                    id="node2",
                    type="test",
                    label="Node 2",
                    position=NodePosition(x=1, y=0),
                ),
                WorkflowNode(
                    id="node3",
                    type="test",
                    label="Node 3",
                    position=NodePosition(x=2, y=0),
                ),
            ],
            edges=[
                WorkflowEdge(id="e1", source="node1", target="node2"),
                WorkflowEdge(id="e2", source="node2", target="node3"),
                WorkflowEdge(id="e3", source="node3", target="node1"),  # Creates cycle
            ],
        )

        with pytest.raises(ValueError, match="contains cycles"):
            orchestrator._topological_sort(workflow)

    @pytest.mark.asyncio
    async def test_simple_workflow_execution(self):
        """Test executing a simple two-node workflow."""
        orchestrator = WorkflowOrchestrator()

        # Register test handlers
        async def handler_1(config, inputs, context):
            return {"value": 42}

        async def handler_2(config, inputs, context):
            input_val = inputs["input"]["value"]
            return {"result": input_val * 2}

        orchestrator.register_node_handler("test_1", handler_1)
        orchestrator.register_node_handler("test_2", handler_2)

        # Create workflow
        workflow = WorkflowDefinition(
            name="Test Workflow",
            nodes=[
                WorkflowNode(
                    id="node1",
                    type="test_1",
                    label="Node 1",
                    position=NodePosition(x=0, y=0),
                ),
                WorkflowNode(
                    id="node2",
                    type="test_2",
                    label="Node 2",
                    position=NodePosition(x=100, y=0),
                ),
            ],
            edges=[WorkflowEdge(id="edge1", source="node1", target="node2")],
        )

        # Execute
        result = await orchestrator.execute_workflow(workflow)

        # Verify results
        assert result.status == ExecutionStatus.COMPLETED
        assert len(result.node_results) == 2
        assert result.error is None
        assert "node1" in result.final_output
        assert "node2" in result.final_output
        assert result.final_output["node2"]["result"] == 84

    @pytest.mark.asyncio
    async def test_workflow_execution_with_node_failure(self):
        """Test workflow handles node execution failure gracefully."""
        orchestrator = WorkflowOrchestrator()

        # Mock input handler (no-op)
        async def input_handler(config, inputs, context):
            return {}

        # Handler that raises an error
        async def failing_handler(config, inputs, context):
            raise ValueError("Intentional failure for testing")

        orchestrator.register_node_handler("input_node", input_handler)
        orchestrator.register_node_handler("failing_node", failing_handler)

        # Create workflow with connected nodes
        workflow = WorkflowDefinition(
            name="Failing Workflow",
            nodes=[
                WorkflowNode(
                    id="input",
                    type="input_node",
                    label="Input",
                    position=NodePosition(x=0, y=0),
                ),
                WorkflowNode(
                    id="node1",
                    type="failing_node",
                    label="Failing Node",
                    position=NodePosition(x=100, y=0),
                )
            ],
            edges=[
                WorkflowEdge(id="edge1", source="input", target="node1")
            ],
        )

        # Execute
        result = await orchestrator.execute_workflow(workflow)

        # Verify failure is captured
        assert result.status == ExecutionStatus.FAILED
        assert result.error is not None
        assert "Intentional failure" in result.error
        assert len(result.node_results) == 2  # input + node1
        # Find the failing node result
        failing_result = [r for r in result.node_results if r.node_id == "node1"][0]
        assert failing_result.status == ExecutionStatus.FAILED

    @pytest.mark.asyncio
    async def test_workflow_with_missing_handler(self):
        """Test workflow fails gracefully when node handler is missing."""
        orchestrator = WorkflowOrchestrator()

        # Mock input handler (no-op)
        async def input_handler(config, inputs, context):
            return {}

        orchestrator.register_node_handler("input_node", input_handler)

        # Create workflow with unregistered node type (connected to input)
        workflow = WorkflowDefinition(
            name="Missing Handler Workflow",
            nodes=[
                WorkflowNode(
                    id="input",
                    type="input_node",
                    label="Input",
                    position=NodePosition(x=0, y=0),
                ),
                WorkflowNode(
                    id="node1",
                    type="unregistered_type",
                    label="Unknown Node",
                    position=NodePosition(x=100, y=0),
                )
            ],
            edges=[
                WorkflowEdge(id="edge1", source="input", target="node1")
            ],
        )

        # Execute
        result = await orchestrator.execute_workflow(workflow)

        # Verify failure
        assert result.status == ExecutionStatus.FAILED
        assert "No handler registered" in result.error

    @pytest.mark.asyncio
    async def test_data_flow_between_nodes(self):
        """Test data flows correctly between connected nodes."""
        orchestrator = WorkflowOrchestrator()

        # Handlers that pass data forward
        async def source_handler(config, inputs, context):
            return {"data": [1, 2, 3]}

        async def transform_handler(config, inputs, context):
            data = inputs["input"]["data"]
            return {"data": [x * 2 for x in data]}

        async def sink_handler(config, inputs, context):
            data = inputs["input"]["data"]
            return {"sum": sum(data)}

        orchestrator.register_node_handler("source", source_handler)
        orchestrator.register_node_handler("transform", transform_handler)
        orchestrator.register_node_handler("sink", sink_handler)

        # Create workflow: source -> transform -> sink
        workflow = WorkflowDefinition(
            name="Data Flow Test",
            nodes=[
                WorkflowNode(
                    id="source",
                    type="source",
                    label="Source",
                    position=NodePosition(x=0, y=0),
                ),
                WorkflowNode(
                    id="transform",
                    type="transform",
                    label="Transform",
                    position=NodePosition(x=1, y=0),
                ),
                WorkflowNode(
                    id="sink",
                    type="sink",
                    label="Sink",
                    position=NodePosition(x=2, y=0),
                ),
            ],
            edges=[
                WorkflowEdge(id="e1", source="source", target="transform"),
                WorkflowEdge(id="e2", source="transform", target="sink"),
            ],
        )

        # Execute
        result = await orchestrator.execute_workflow(workflow)

        # Verify data flowed correctly
        assert result.status == ExecutionStatus.COMPLETED
        # Source produces [1, 2, 3]
        # Transform doubles to [2, 4, 6]
        # Sink sums to 12
        assert result.final_output["sink"]["sum"] == 12

    @pytest.mark.asyncio
    async def test_initial_context_passed_to_handlers(self):
        """Test that initial context is available to node handlers."""
        orchestrator = WorkflowOrchestrator()

        # Mock input handler (no-op)
        async def input_handler(config, inputs, context):
            return {}

        # Handler that reads from context
        async def context_reader(config, inputs, context):
            return {"from_context": context.metadata.get("test_key")}

        orchestrator.register_node_handler("input_node", input_handler)
        orchestrator.register_node_handler("reader", context_reader)

        workflow = WorkflowDefinition(
            name="Context Test",
            nodes=[
                WorkflowNode(
                    id="input",
                    type="input_node",
                    label="Input",
                    position=NodePosition(x=0, y=0),
                ),
                WorkflowNode(
                    id="node1",
                    type="reader",
                    label="Reader",
                    position=NodePosition(x=100, y=0),
                )
            ],
            edges=[
                WorkflowEdge(id="edge1", source="input", target="node1")
            ],
        )

        # Execute with initial context
        result = await orchestrator.execute_workflow(
            workflow, initial_context={"test_key": "test_value"}
        )

        assert result.status == ExecutionStatus.COMPLETED
        assert result.final_output["node1"]["from_context"] == "test_value"

    @pytest.mark.asyncio
    async def test_execution_timing_recorded(self):
        """Test that execution timing is recorded in results."""
        orchestrator = WorkflowOrchestrator()

        # Mock input handler (no-op)
        async def input_handler(config, inputs, context):
            return {}

        async def simple_handler(config, inputs, context):
            return {"done": True}

        orchestrator.register_node_handler("input_node", input_handler)
        orchestrator.register_node_handler("simple", simple_handler)

        workflow = WorkflowDefinition(
            name="Timing Test",
            nodes=[
                WorkflowNode(
                    id="input",
                    type="input_node",
                    label="Input",
                    position=NodePosition(x=0, y=0),
                ),
                WorkflowNode(
                    id="node1",
                    type="simple",
                    label="Simple",
                    position=NodePosition(x=100, y=0),
                )
            ],
            edges=[
                WorkflowEdge(id="edge1", source="input", target="node1")
            ],
        )

        result = await orchestrator.execute_workflow(workflow)

        # Verify timing information
        assert result.started_at is not None
        assert result.completed_at is not None
        assert result.total_duration_ms is not None
        assert result.total_duration_ms > 0
        assert result.completed_at > result.started_at

        # Verify node timing (check node1, not input)
        assert len(result.node_results) == 2  # input + node1
        node_result = [r for r in result.node_results if r.node_id == "node1"][0]
        assert node_result.started_at is not None
        assert node_result.completed_at is not None
        assert node_result.duration_ms is not None
        assert node_result.duration_ms > 0
