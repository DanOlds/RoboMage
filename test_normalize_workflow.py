#!/usr/bin/env python3
"""
Test script to reproduce normalize node issue.

This creates a simple workflow: load_files → normalize → peak_analysis

NOTE: This is a STANDALONE script, not a pytest test.
Run directly with: pixi run python test_normalize_workflow.py
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Setup logging to see debug messages
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from robomage.orchestrator import WorkflowOrchestrator
from robomage.workflow.nodes import data_nodes, analysis_nodes

# Import workflow models
sys.path.insert(0, str(Path(__file__).parent / "services"))
from workflow_engine.models import (
    WorkflowDefinition,
    WorkflowNode,
    WorkflowEdge,
    NodePosition,
)


async def test_normalize_workflow():
    """Test workflow with normalize node."""

    # Create orchestrator
    orchestrator = WorkflowOrchestrator()

    # Register node handlers
    orchestrator.register_node_handler("load_files", data_nodes.load_files_handler)
    orchestrator.register_node_handler("normalize", data_nodes.normalize_handler)
    orchestrator.register_node_handler(
        "peak_analysis", analysis_nodes.peak_analysis_handler
    )

    # Create test workflow using Pydantic models
    workflow = WorkflowDefinition(
        id="test_normalize",
        name="Test Normalize Workflow",
        description="Test load_files → normalize → peak_analysis",
        nodes=[
            WorkflowNode(
                id="load_1",
                type="load_files",
                label="Load Test Data",
                config={"directory": "examples", "pattern": "*.chi"},
                position=NodePosition(x=100, y=100),
            ),
            WorkflowNode(
                id="normalize_1",
                type="normalize",
                label="Normalize",
                config={"method": "max"},
                position=NodePosition(x=300, y=100),
            ),
            WorkflowNode(
                id="analyze_1",
                type="peak_analysis",
                label="Peak Analysis",
                config={"profile": "gaussian", "prominence": 0.1, "distance": 5},
                position=NodePosition(x=500, y=100),
            ),
        ],
        edges=[
            WorkflowEdge(
                id="edge_1",
                source="load_1",
                target="normalize_1",
                source_handle=None,
                target_handle=None,
            ),
            WorkflowEdge(
                id="edge_2",
                source="normalize_1",
                target="analyze_1",
                source_handle=None,
                target_handle=None,
            ),
        ],
    )

    print("\n" + "=" * 80)
    print("TESTING WORKFLOW: load_files → normalize → peak_analysis")
    print("=" * 80 + "\n")

    print("Workflow definition:")
    print(workflow.model_dump_json(indent=2))
    print("\n" + "=" * 80 + "\n")

    # Execute workflow
    try:
        result = await orchestrator.execute_workflow(workflow)

        print("\n" + "=" * 80)
        print("EXECUTION RESULT:")
        print("=" * 80 + "\n")
        print(f"Status: {result.status}")
        print(f"Completed at: {result.completed_at}")

        print("\nNode Results:")
        for node_result in result.node_results:
            print(f"\n  {node_result.node_id} ({node_result.node_type}):")
            print(f"    Status: {node_result.status}")
            print(f"    Duration: {node_result.duration_ms:.1f} ms")
            if node_result.error:
                print(f"    ERROR: {node_result.error}")
            if node_result.output:
                output_type = type(node_result.output).__name__
                if isinstance(node_result.output, list):
                    print(
                        f"    Output: {output_type} with {len(node_result.output)} items"
                    )
                else:
                    print(f"    Output: {output_type}")

        print("\n" + "=" * 80 + "\n")

        if result.status == "failed":
            print("❌ WORKFLOW FAILED")
            return 1
        else:
            print("✅ WORKFLOW SUCCEEDED")
            return 0

    except Exception as e:
        print(f"\n❌ EXCEPTION: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(test_normalize_workflow())
    sys.exit(exit_code)
