#!/usr/bin/env python
"""
Test workflow execution to debug issues.

Run this script with the workflow service running to see detailed error output.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from services.workflow_engine.models import WorkflowDefinition, WorkflowNode, WorkflowEdge, NodePosition
from src.robomage.orchestrator import WorkflowOrchestrator


async def test_workflow():
    """Test the example workflow execution."""
    
    # Create the default workflow
    workflow = WorkflowDefinition(
        name="Example Workflow",
        description="Load files and analyze peaks",
        nodes=[
            WorkflowNode(
                id="load_1",
                type="load_files",
                label="Load Data Files",
                config={
                    "directory": "examples",
                    "pattern": "*.chi"
                },
                position=NodePosition(x=100, y=100)
            ),
            WorkflowNode(
                id="analyze_1",
                type="peak_analysis",
                label="Detect Peaks",
                config={
                    "profile_type": "gaussian",
                    "prominence": 0.1,
                    "distance": 5
                },
                position=NodePosition(x=400, y=100)
            ),
            WorkflowNode(
                id="export_1",
                type="export_csv",
                label="Export Results",
                config={
                    "output_path": "workflow_results.csv",
                    "format": "peaks"
                },
                position=NodePosition(x=700, y=100)
            )
        ],
        edges=[
            WorkflowEdge(
                id="edge_1",
                source="load_1",
                target="analyze_1"
            ),
            WorkflowEdge(
                id="edge_2",
                source="analyze_1",
                target="export_1"
            )
        ]
    )
    
    # Create orchestrator and register handlers
    orchestrator = WorkflowOrchestrator()
    
    from src.robomage.workflow.nodes import analysis_nodes, data_nodes, output_nodes
    
    orchestrator.register_node_handler("load_files", data_nodes.load_files_handler)
    orchestrator.register_node_handler("filter_q_range", data_nodes.filter_q_range_handler)
    orchestrator.register_node_handler("normalize", data_nodes.normalize_handler)
    orchestrator.register_node_handler("peak_analysis", analysis_nodes.peak_analysis_handler)
    orchestrator.register_node_handler("statistics", analysis_nodes.statistics_handler)
    orchestrator.register_node_handler("export_csv", output_nodes.export_csv_handler)
    orchestrator.register_node_handler("export_json", output_nodes.export_json_handler)
    orchestrator.register_node_handler("save_results", output_nodes.save_results_handler)
    
    print("🚀 Testing workflow execution...")
    print(f"Workflow: {workflow.name}")
    print(f"Nodes: {[n.id for n in workflow.nodes]}")
    print()
    
    try:
        # Execute workflow
        result = await orchestrator.execute_workflow(workflow)
        
        print()
        print(f"✅ Workflow completed: {result.status}")
        print(f"Execution ID: {result.execution_id}")
        print(f"Duration: {result.total_duration_ms:.1f} ms")
        print()
        print("Node Results:")
        for nr in result.node_results:
            status_icon = "✅" if nr.status == "completed" else "❌"
            print(f"  {status_icon} {nr.node_id}: {nr.status} ({nr.duration_ms:.1f} ms)")
            if nr.error:
                print(f"     Error: {nr.error}")
        
        # Try to serialize the result
        print()
        print("🔍 Testing serialization...")
        result_dict = result.model_dump()
        print(f"✅ Serialization successful!")
        print(f"Final output keys: {list(result.final_output.keys()) if result.final_output else 'None'}")
        
        return result
        
    except Exception as e:
        print(f"❌ Workflow execution failed!")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = asyncio.run(test_workflow())
    sys.exit(0 if result else 1)
