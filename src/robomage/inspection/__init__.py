"""
Node I/O Inspection Module

Provides data models and utilities for capturing and analyzing data flowing
through workflow nodes during execution.

This module enables developers and users to:
- Inspect inputs and outputs of individual workflow nodes
- Debug data flow issues in complex workflows
- Understand data transformations between processing steps
- Profile workflow execution performance

Usage:
    # Enable inspection in orchestrator
    orchestrator = WorkflowOrchestrator(enable_inspection=True)

    # Execute workflow
    result = await orchestrator.execute_workflow(workflow)

    # Access inspection data
    for node_id, snapshot in orchestrator.inspection_data.items():
        print(f"Node {node_id}: {snapshot.duration_ms}ms")
        print(f"  Input: {snapshot.input_summary}")
        print(f"  Output: {snapshot.output_summary}")

Components:
    NodeIOSnapshot: Captures input/output data for a single node execution
    InspectionMetadata: Additional timing and execution context information
"""

from robomage.inspection.models import InspectionMetadata, NodeIOSnapshot

__all__ = ["NodeIOSnapshot", "InspectionMetadata"]
