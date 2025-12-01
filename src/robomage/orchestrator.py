"""
Workflow Orchestrator - DAG Execution Engine

Executes multi-step diffraction analysis workflows by coordinating node execution,
managing data flow between nodes, and handling errors gracefully.

The orchestrator implements a directed acyclic graph (DAG) executor that:
- Topologically sorts nodes to determine valid execution order
- Executes nodes asynchronously with proper dependency management
- Manages data flow through an execution context
- Provides error handling and partial rollback capabilities
- Emits progress events for UI updates

Architecture:
    WorkflowOrchestrator manages the overall execution lifecycle:
    - Registers node type handlers
    - Validates workflow definitions
    - Executes workflows with proper ordering
    - Tracks execution state and results

    ExecutionContext manages data flow between nodes:
    - Stores node outputs
    - Retrieves inputs for dependent nodes
    - Maintains execution metadata

Usage:
    # Create orchestrator
    orchestrator = WorkflowOrchestrator()

    # Register node handlers
    orchestrator.register_node_handler("load_files", load_files_handler)
    orchestrator.register_node_handler("peak_analysis", peak_analysis_handler)

    # Execute workflow
    result = await orchestrator.execute_workflow(workflow_definition)

    # Check results
    if result.status == ExecutionStatus.COMPLETED:
        print(f"Success! Output: {result.final_output}")

Integration:
    - Called by the workflow service (services/workflow_engine/main.py)
    - Uses node handlers from src/robomage/workflow/nodes/
    - Integrates with RoboMage data pipeline and services
"""

import logging
from collections import defaultdict, deque
from collections.abc import Callable
from datetime import datetime
from typing import Any

from robomage.inspection.models import NodeIOSnapshot

logger = logging.getLogger(__name__)


class ExecutionContext:
    """
    Manages data flow between workflow nodes.

    The context stores outputs from executed nodes and provides them as
    inputs to dependent nodes. It also maintains metadata about the
    execution environment.
    """

    def __init__(self) -> None:
        """Initialize execution context."""
        self.data: dict[str, Any] = {}  # node_id -> output data
        self.metadata: dict[str, Any] = {}  # execution metadata

    def set_node_output(self, node_id: str, output: Any) -> None:
        """
        Store output from a node execution.

        Args:
            node_id: Unique node identifier
            output: Node output data (any type)
        """
        self.data[node_id] = output
        logger.debug(f"Stored output for node {node_id}")

    def get_node_output(self, node_id: str) -> Any:
        """
        Retrieve output from a previously executed node.

        Args:
            node_id: Node identifier

        Returns:
            Node output data or None if not found
        """
        return self.data.get(node_id)

    def get_all_outputs(self) -> dict[str, Any]:
        """Get all node outputs."""
        return self.data.copy()


class WorkflowOrchestrator:
    """
    Executes workflows as directed acyclic graphs (DAGs).

    Features:
    - Topological sorting for correct execution order
    - Async execution of nodes
    - Error handling with partial results
    - Progress tracking via callbacks
    - Cycle detection and validation
    - Optional I/O inspection for debugging and analysis

    The orchestrator is responsible for:
    1. Validating workflow structure (no cycles, valid connections)
    2. Determining execution order via topological sort
    3. Managing node execution with proper input/output handling
    4. Collecting results and error states
    5. Emitting progress updates for UI feedback
    6. Optionally capturing I/O data for inspection
    """

    def __init__(self, enable_inspection: bool = False) -> None:
        """
        Initialize workflow orchestrator.

        Args:
            enable_inspection: If True, capture input/output data for each node
                             execution. Useful for debugging but adds overhead.
                             Default is False for production use.
        """
        self.node_handlers: dict[str, Callable] = {}
        self._execution_callbacks: list[Callable] = []
        self.enable_inspection = enable_inspection
        self.inspection_data: dict[str, NodeIOSnapshot] = {}

        if enable_inspection:
            logger.info("Inspection mode ENABLED - I/O data will be captured")

    def register_node_handler(self, node_type: str, handler: Callable) -> None:
        """
        Register a handler function for a node type.

        Node handlers are async functions with signature:
            async def handler(config: dict, inputs: dict, context: ExecutionContext) -> Any

        Args:
            node_type: Node type identifier (e.g., 'load_files', 'peak_analysis')
            handler: Async function that executes the node logic
        """
        self.node_handlers[node_type] = handler
        logger.info(f"Registered handler for node type: {node_type}")

    def on_progress(self, callback: Callable) -> None:
        """
        Register callback for execution progress updates.

        Callbacks will be called with (execution_id, node_result) after each node completes.

        Args:
            callback: Async function with signature (execution_id: str, node_result: NodeExecutionResult)
        """
        self._execution_callbacks.append(callback)

    def _serialize_for_inspection(self, data: Any) -> dict[str, Any]:
        """
        Serialize data for inspection storage with intelligent summarization.

        Creates a JSON-compatible representation of data suitable for storage
        and later inspection. For large or complex objects, stores summaries
        and samples rather than complete data to avoid excessive memory usage.

        This method is optimized for common workflow data types:
        - DiffractionData objects: Store summary + sample
        - Lists of objects: Store count + first item sample
        - Dicts: Store structure and sizes
        - Primitives: Store as-is

        Args:
            data: Data to serialize (any type)

        Returns:
            JSON-serializable dict with data summary

        Example:
            # For list of DiffractionData objects
            serialized = self._serialize_for_inspection(diffraction_files)
            # Returns: {
            #   "type": "list[DiffractionData]",
            #   "count": 3,
            #   "sample": {...first item data...},
            #   "items_summary": ["file1.chi", "file2.chi", "file3.chi"]
            # }
        """
        if data is None:
            return {"type": "None", "value": None}

        # Handle primitives directly
        if isinstance(data, (str, int, float, bool)):
            return {"type": type(data).__name__, "value": data}

        # Handle lists
        if isinstance(data, list):
            if not data:
                return {"type": "list", "count": 0}

            # Get type info from first item
            first_item = data[0]
            item_type = type(first_item).__name__

            result = {
                "type": f"list[{item_type}]",
                "count": len(data),
            }

            # For Pydantic models, serialize first item
            if hasattr(first_item, "model_dump"):
                result["sample"] = first_item.model_dump()

                # If it's DiffractionData, extract filenames
                if hasattr(first_item, "filename"):
                    result["items_summary"] = [
                        getattr(item, "filename", f"item_{i}")
                        for i, item in enumerate(data)
                    ]

            # For dicts, serialize first item
            elif isinstance(first_item, dict):
                result["sample"] = first_item

            # For primitives, store all (if reasonable size)
            elif isinstance(first_item, (str, int, float, bool)) and len(data) <= 100:
                result["values"] = data

            return result

        # Handle dicts
        if isinstance(data, dict):
            result = {
                "type": "dict",
                "keys": list(data.keys()),
                "count": len(data),
            }

            # Recursively serialize dict values (but limit depth)
            serialized_values = {}
            for key, value in data.items():
                if isinstance(value, (str, int, float, bool, type(None))):
                    serialized_values[key] = value
                elif isinstance(value, (list, dict)):
                    # One level of recursion for nested structures
                    serialized_values[key] = self._serialize_for_inspection(value)
                else:
                    serialized_values[key] = {
                        "type": type(value).__name__,
                        "repr": str(value)[:100],
                    }

            result["values"] = serialized_values
            return result

        # Handle Pydantic models
        if hasattr(data, "model_dump"):
            return {
                "type": type(data).__name__,
                "data": data.model_dump(),
            }

        # Fallback: store type and repr
        return {
            "type": type(data).__name__,
            "repr": str(data)[:500],  # Limit size
        }

    def _make_serializable(self, obj: Any, _seen: set | None = None) -> Any:
        """
        Convert complex objects to JSON-serializable format.

        Handles common non-serializable types like DiffractionData objects,
        NumPy arrays, and nested structures. Protects against circular references.

        Args:
            obj: Object to serialize
            _seen: Set of object IDs already processed (for circular reference detection)

        Returns:
            JSON-serializable version of the object
        """
        # Initialize seen set for circular reference detection
        if _seen is None:
            _seen = set()

        # Check for circular references
        obj_id = id(obj)
        if obj_id in _seen:
            return "<circular reference>"

        try:
            import numpy as np  # type: ignore[import]
        except ImportError:
            np = None  # type: ignore[assignment]

        # Handle None
        if obj is None:
            return None

        # Handle primitive types (no need to track these)
        if isinstance(obj, (str, int, float, bool)):
            return obj

        # Add to seen set for complex types
        _seen.add(obj_id)

        try:
            # Handle dict recursively
            if isinstance(obj, dict):
                return {k: self._make_serializable(v, _seen) for k, v in obj.items()}

            # Handle list/tuple recursively
            if isinstance(obj, (list, tuple)):
                return [self._make_serializable(item, _seen) for item in obj]

            # Handle numpy arrays
            if np and isinstance(obj, np.ndarray):
                return obj.tolist()

            # Handle datetime objects
            if isinstance(obj, datetime):
                return obj.isoformat()

            # Handle DiffractionData objects
            if hasattr(obj, "to_dict"):
                return self._make_serializable(obj.to_dict(), _seen)

            # Handle Pydantic models
            if hasattr(obj, "model_dump"):
                return self._make_serializable(obj.model_dump(), _seen)

            # For other objects, convert to safe string representation
            return f"<{type(obj).__name__}>"

        except Exception as e:
            logger.warning(f"Failed to serialize {type(obj).__name__}: {e}")
            return f"<{type(obj).__name__}: serialization error>"
        finally:
            # Remove from seen set when done
            _seen.discard(obj_id)

    async def execute_workflow(
        self,
        workflow: Any,
        initial_context: dict[str, Any] | None = None,
        store_full_outputs: bool = False,
    ) -> Any:
        """
        Execute a complete workflow.

        Args:
            workflow: WorkflowDefinition with nodes and edges
            initial_context: Optional initial data/configuration
            store_full_outputs: If True, store complete serialized outputs instead of summaries.
                               Warning: Can create large results for DiffractionData objects.

        Returns:
            WorkflowExecutionResult with status and outputs

        Raises:
            ValueError: If workflow contains cycles or invalid structure
        """
        # Handle imports from services directory
        # In production: services.workflow_engine is in PYTHONPATH
        # In tests: Need to add services directory to path
        try:
            from services.workflow_engine.models import (
                ExecutionStatus,
                WorkflowExecutionResult,
            )
        except ModuleNotFoundError:
            # Fallback for test environment
            import sys
            from pathlib import Path

            services_path = Path(__file__).parent.parent.parent / "services"
            if services_path.exists() and str(services_path) not in sys.path:
                sys.path.insert(0, str(services_path))

            from workflow_engine.models import (  # type: ignore
                ExecutionStatus,
                WorkflowExecutionResult,
            )

        execution_id = f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        started_at = datetime.now()

        # Handle both dict and object workflow representations
        workflow_name = getattr(
            workflow,
            "name",
            workflow.get("name", "unnamed")
            if isinstance(workflow, dict)
            else "unnamed",
        )

        logger.info(
            f"Starting workflow execution: {execution_id} for workflow: {workflow_name}"
        )

        # Initialize context
        context = ExecutionContext()
        if initial_context:
            context.metadata.update(initial_context)

        # Store serialization mode in context for node execution
        context.metadata["_store_full_outputs"] = store_full_outputs

        try:
            # Build execution graph and validate
            execution_order = self._topological_sort(workflow)
            logger.info(
                f"Execution order determined: {[n.id for n in execution_order]}"
            )

            # Execute nodes in order
            node_results = []
            for node in execution_order:
                node_result = await self._execute_node(node, context, workflow)
                node_results.append(node_result)

                if node_result.status == ExecutionStatus.FAILED:
                    error_msg = (
                        f"Node {node.id} ({node.label}) failed: {node_result.error}"
                    )
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)

                # Emit progress update
                for callback in self._execution_callbacks:
                    try:
                        await callback(execution_id, node_result)
                    except Exception as e:
                        logger.warning(f"Progress callback failed: {e}")

            # Success - workflow completed
            completed_at = datetime.now()
            duration_ms = (completed_at - started_at).total_seconds() * 1000

            logger.info(
                f"Workflow {execution_id} completed successfully in {duration_ms:.1f}ms"
            )

            # Get final output but make it JSON-serializable
            all_outputs = context.get_all_outputs()
            final_output = self._make_serializable(all_outputs)

            # Include inspection data if enabled
            inspections_serialized = None
            if self.enable_inspection and self.inspection_data:
                inspections_serialized = []
                for snapshot in self.inspection_data.values():
                    inspections_serialized.append(snapshot.model_dump(mode="json"))
                logger.info(
                    f"Captured {len(inspections_serialized)} inspection snapshots"
                )

            return WorkflowExecutionResult(
                execution_id=execution_id,
                workflow_id=workflow.id or "unknown",
                status=ExecutionStatus.COMPLETED,
                started_at=started_at,
                completed_at=completed_at,
                node_results=node_results,
                final_output=final_output,
                error=None,
                total_duration_ms=duration_ms,
                inspections=inspections_serialized,
            )

        except Exception as e:
            # Workflow failed
            completed_at = datetime.now()
            duration_ms = (completed_at - started_at).total_seconds() * 1000

            logger.error(
                f"Workflow {execution_id} failed after {duration_ms:.1f}ms: {e}",
                exc_info=True,
            )

            # Include inspection data even on failure (helps debug)
            inspections_serialized = None
            if self.enable_inspection and self.inspection_data:
                inspections_serialized = []
                for snapshot in self.inspection_data.values():
                    inspections_serialized.append(snapshot.model_dump(mode="json"))

            return WorkflowExecutionResult(
                execution_id=execution_id,
                workflow_id=workflow.id or "unknown",
                status=ExecutionStatus.FAILED,
                started_at=started_at,
                completed_at=completed_at,
                node_results=node_results if "node_results" in locals() else [],
                final_output=None,
                error=str(e),
                total_duration_ms=duration_ms,
                inspections=inspections_serialized,
            )

    def _topological_sort(self, workflow: Any) -> list[Any]:
        """
        Sort nodes in valid execution order using Kahn's algorithm.

        Topological sorting ensures that nodes are executed only after all
        their dependencies have completed. This is essential for DAG execution.

        Args:
            workflow: WorkflowDefinition with nodes and edges

        Returns:
            List of nodes in valid execution order

        Raises:
            ValueError: If workflow contains cycles (not a valid DAG)
        """
        # Build adjacency list and in-degree map
        graph = defaultdict(list)
        in_degree = defaultdict(int)

        # Create node lookup
        nodes_by_id = {node.id: node for node in workflow.nodes}

        # Initialize in_degree for all nodes
        for node in workflow.nodes:
            in_degree[node.id] = 0

        # Build graph from edges
        for edge in workflow.edges:
            graph[edge.source].append(edge.target)
            in_degree[edge.target] += 1

        # Kahn's algorithm for topological sort
        queue = deque([node_id for node_id in in_degree if in_degree[node_id] == 0])
        sorted_nodes = []

        while queue:
            current_id = queue.popleft()
            sorted_nodes.append(nodes_by_id[current_id])

            # Process neighbors
            for neighbor_id in graph[current_id]:
                in_degree[neighbor_id] -= 1
                if in_degree[neighbor_id] == 0:
                    queue.append(neighbor_id)

        # Check for cycles
        if len(sorted_nodes) != len(workflow.nodes):
            raise ValueError(
                "Workflow contains cycles - cannot execute. "
                "Ensure all edges form a directed acyclic graph (DAG)."
            )

        return sorted_nodes

    async def _execute_node(
        self, node: Any, context: ExecutionContext, workflow: Any
    ) -> Any:
        """
        Execute a single node in the workflow.

        Args:
            node: WorkflowNode to execute
            context: ExecutionContext for data flow
            workflow: Complete workflow definition (for finding inputs)

        Returns:
            NodeExecutionResult with status and output
        """
        # Handle imports with fallback for test environment
        try:
            from services.workflow_engine.models import (
                ExecutionStatus,
                NodeExecutionResult,
            )
        except ModuleNotFoundError:
            import sys
            from pathlib import Path

            services_path = Path(__file__).parent.parent.parent / "services"
            if services_path.exists() and str(services_path) not in sys.path:
                sys.path.insert(0, str(services_path))
            from workflow_engine.models import ExecutionStatus, NodeExecutionResult  # type: ignore

        logger.info(f"Executing node: {node.id} ({node.type}) - {node.label}")
        started_at = datetime.now()

        # Initialize inspection snapshot if enabled
        if self.enable_inspection:
            snapshot = NodeIOSnapshot(
                node_id=node.id,
                node_type=node.type,
                timestamp_in=started_at,
            )
            self.inspection_data[node.id] = snapshot

        try:
            # Get handler for this node type
            handler = self.node_handlers.get(node.type)
            if not handler:
                raise ValueError(
                    f"No handler registered for node type: {node.type}. "
                    f"Available types: {list(self.node_handlers.keys())}"
                )

            # Collect inputs from predecessor nodes
            inputs = self._collect_node_inputs(node, context, workflow)

            # Capture input data if inspection enabled
            if self.enable_inspection:
                self.inspection_data[
                    node.id
                ].input_data = self._serialize_for_inspection(inputs)

            # Execute handler
            logger.debug(f"Calling handler for {node.id} with config: {node.config}")
            output = await handler(node.config, inputs, context)

            # Store output in context for downstream nodes
            context.set_node_output(node.id, output)

            # Capture output data if inspection enabled
            if self.enable_inspection:
                self.inspection_data[
                    node.id
                ].output_data = self._serialize_for_inspection(output)
                self.inspection_data[node.id].timestamp_out = datetime.now()
                self.inspection_data[node.id].duration_ms = (
                    datetime.now() - started_at
                ).total_seconds() * 1000

            # Calculate duration
            completed_at = datetime.now()
            duration_ms = (completed_at - started_at).total_seconds() * 1000

            logger.info(f"Node {node.id} completed successfully in {duration_ms:.1f}ms")

            # Debug: Print node type to verify it's being captured
            print(f"🔍 ORCHESTRATOR: Node {node.id} type={node.type}")

            # Check if we should store full outputs
            store_full = context.metadata.get("_store_full_outputs", False)

            # Create output for node result
            output_data = None
            if output:
                try:
                    if store_full:
                        # Store complete serialized output
                        output_data = self._make_serializable(output)
                    else:
                        # Store summary only (default behavior)
                        serialized = self._make_serializable(output)
                        summary_str = str(serialized)[:500]  # Limit size
                        output_data = {
                            "summary": summary_str,
                            "type": type(output).__name__,
                        }
                except Exception as e:
                    logger.warning(
                        f"Failed to serialize output for node {node.id}: {e}"
                    )
                    output_data = {
                        "summary": f"<{type(output).__name__}>",
                        "type": type(output).__name__,
                    }

            return NodeExecutionResult(
                node_id=node.id,
                node_type=node.type,
                status=ExecutionStatus.COMPLETED,
                started_at=started_at,
                completed_at=completed_at,
                output=output_data,
                error=None,
                duration_ms=duration_ms,
            )

        except Exception as e:
            # Node execution failed
            completed_at = datetime.now()
            duration_ms = (completed_at - started_at).total_seconds() * 1000

            logger.error(
                f"Node {node.id} failed after {duration_ms:.1f}ms: {e}", exc_info=True
            )

            return NodeExecutionResult(
                node_id=node.id,
                node_type=node.type,
                status=ExecutionStatus.FAILED,
                started_at=started_at,
                completed_at=completed_at,
                output=None,
                error=str(e),
                duration_ms=duration_ms,
            )

    def _collect_node_inputs(
        self, node: Any, context: ExecutionContext, workflow: Any
    ) -> dict[str, Any]:
        """
        Collect inputs from predecessor nodes.

        Finds all edges pointing to this node and retrieves the corresponding
        outputs from the execution context.

        Args:
            node: WorkflowNode to collect inputs for
            context: ExecutionContext with stored outputs
            workflow: Complete workflow definition

        Returns:
            Dictionary mapping input names to data from predecessor nodes
        """
        inputs = {}

        # Find edges pointing to this node
        for edge in workflow.edges:
            if edge.target == node.id:
                source_output = context.get_node_output(edge.source)
                input_key = edge.target_handle or "input"
                inputs[input_key] = source_output

                logger.debug(
                    f"Collected input '{input_key}' for node {node.id} from {edge.source}: "
                    f"type={type(source_output).__name__}, "
                    f"len={len(source_output) if isinstance(source_output, (list, dict)) else 'N/A'}"
                )

        return inputs
