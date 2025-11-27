#!/usr/bin/env python
"""
Test full output serialization in workflow execution.

This script verifies that when store_full_outputs=True, the orchestrator
stores complete DiffractionData objects in execution results instead of summaries.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from services.workflow_engine.models import (
    NodePosition,
    WorkflowDefinition,
    WorkflowNode,
)
from src.robomage.orchestrator import WorkflowOrchestrator


async def test_full_serialization():
    """Test that store_full_outputs=True stores complete DiffractionData."""

    # Create simple workflow that loads files
    workflow = WorkflowDefinition(
        name="Test Full Serialization",
        description="Load files to test full output storage",
        nodes=[
            WorkflowNode(
                id="load_1",
                type="load_files",
                label="Load Data Files",
                config={"directory": "examples", "pattern": "*.chi"},
                position=NodePosition(x=100, y=100),
            )
        ],
        edges=[],
    )

    # Create orchestrator and register handlers
    orchestrator = WorkflowOrchestrator()

    from src.robomage.workflow.nodes import data_nodes

    orchestrator.register_node_handler("load_files", data_nodes.load_files_handler)

    print("🧪 Testing full output serialization...")
    print()

    # Test WITHOUT full outputs (default)
    print("1️⃣ Testing with store_full_outputs=False (default)")
    result_summary = await orchestrator.execute_workflow(
        workflow, store_full_outputs=False
    )

    if result_summary.node_results:
        output = result_summary.node_results[0].output
        print(f"   Output type: {type(output)}")
        print(
            f"   Output keys: {list(output.keys()) if isinstance(output, dict) else 'N/A'}"
        )
        if isinstance(output, dict) and "summary" in output:
            print(f"   Contains summary: Yes (length: {len(output['summary'])} chars)")
        print()

    # Test WITH full outputs
    print("2️⃣ Testing with store_full_outputs=True")
    result_full = await orchestrator.execute_workflow(workflow, store_full_outputs=True)

    if result_full.node_results:
        output = result_full.node_results[0].output
        print(f"   Output type: {type(output)}")

        # Check if it's a list of dicts (full DiffractionData serialization)
        if isinstance(output, list) and len(output) > 0:
            print(f"   Output is list with {len(output)} items")
            first_item = output[0]
            print(f"   First item type: {type(first_item)}")

            if isinstance(first_item, dict):
                print(f"   First item keys: {list(first_item.keys())[:10]}")
                if "q_values" in first_item:
                    print("   ✅ SUCCESS: Found q_values in output!")
                    print(f"   q_values length: {len(first_item['q_values'])}")
                    print(f"   Has intensities: {'intensities' in first_item}")
                    print(f"   Has filename: {'filename' in first_item}")
                else:
                    print("   ❌ FAILED: q_values not found in output")
        else:
            print(f"   ❌ FAILED: Expected list of dicts, got: {type(output)}")

    print()
    print("✅ Test complete!")


if __name__ == "__main__":
    asyncio.run(test_full_serialization())
