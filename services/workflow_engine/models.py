"""
Workflow Engine Data Models

Pydantic models for workflow definitions, execution tracking, and node metadata.
These models define the JSON API contract for the workflow service.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class NodePosition(BaseModel):
    """UI position for ReactFlow rendering."""

    model_config = ConfigDict(json_schema_extra={"example": {"x": 100.0, "y": 150.0}})

    x: float = Field(..., description="X coordinate on canvas")
    y: float = Field(..., description="Y coordinate on canvas")


class WorkflowNode(BaseModel):
    """Single node in a workflow graph."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "node_1",
                "type": "load_files",
                "label": "Load CHI Files",
                "config": {"pattern": "*.chi", "directory": "/data"},
                "position": {"x": 100, "y": 100},
            }
        }
    )

    id: str = Field(..., description="Unique node identifier within workflow")
    type: str = Field(
        ..., description="Node type (e.g., 'load_files', 'peak_analysis')"
    )
    label: str = Field(..., description="User-friendly node label")
    config: dict[str, Any] = Field(
        default_factory=dict, description="Node-specific configuration parameters"
    )
    position: NodePosition = Field(..., description="Position on canvas for UI")


class WorkflowEdge(BaseModel):
    """Connection between two nodes in the workflow graph."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "edge_1",
                "source": "node_1",
                "target": "node_2",
                "source_handle": "output",
                "target_handle": "input",
            }
        }
    )

    id: str = Field(..., description="Unique edge identifier")
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    source_handle: str | None = Field(None, description="Source output port (optional)")
    target_handle: str | None = Field(None, description="Target input port (optional)")


class WorkflowDefinition(BaseModel):
    """Complete workflow specification with nodes and edges."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Batch Peak Analysis",
                "description": "Load multiple files and detect peaks",
                "nodes": [
                    {
                        "id": "load_1",
                        "type": "load_files",
                        "label": "Load Data",
                        "config": {"pattern": "*.chi", "directory": "."},
                        "position": {"x": 100, "y": 100},
                    },
                    {
                        "id": "analyze_1",
                        "type": "peak_analysis",
                        "label": "Detect Peaks",
                        "config": {"profile": "gaussian", "prominence": 0.1},
                        "position": {"x": 400, "y": 100},
                    },
                ],
                "edges": [{"id": "edge_1", "source": "load_1", "target": "analyze_1"}],
            }
        }
    )

    id: str | None = Field(None, description="Workflow ID (assigned by system)")
    name: str = Field(..., description="Workflow name", min_length=1, max_length=200)
    description: str = Field(
        default="", description="Workflow description", max_length=1000
    )
    nodes: list[WorkflowNode] = Field(..., description="Workflow nodes")
    edges: list[WorkflowEdge] = Field(..., description="Node connections")
    created_at: datetime | None = Field(None, description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")


class ExecutionStatus(str, Enum):
    """Workflow execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NodeExecutionResult(BaseModel):
    """Result from executing a single node."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "node_id": "load_1",
                "status": "completed",
                "started_at": "2025-11-25T10:30:00",
                "completed_at": "2025-11-25T10:30:01",
                "output": {"files_loaded": 5},
                "error": None,
                "duration_ms": 1250.5,
            }
        }
    )

    node_id: str = Field(..., description="Node identifier")
    node_type: str | None = Field(
        None, description="Node type (e.g., 'load_files', 'peak_analysis')"
    )
    status: ExecutionStatus = Field(..., description="Node execution status")
    started_at: datetime = Field(..., description="Execution start time")
    completed_at: datetime | None = Field(None, description="Execution completion time")
    output: dict[str, Any] | list[Any] | None = Field(
        None,
        description="Node output data (dict for summaries, list for full serialization)",
    )
    error: str | None = Field(None, description="Error message if failed")
    duration_ms: float | None = Field(
        None, description="Execution duration in milliseconds"
    )


class WorkflowExecutionResult(BaseModel):
    """Result from executing a complete workflow."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "execution_id": "exec_20251125_103000",
                "workflow_id": "wf_123",
                "status": "completed",
                "started_at": "2025-11-25T10:30:00",
                "completed_at": "2025-11-25T10:30:15",
                "node_results": [],
                "final_output": {"total_peaks": 45, "files_processed": 5},
                "error": None,
                "total_duration_ms": 15234.7,
                "inspections": [],
            }
        }
    )

    execution_id: str = Field(..., description="Unique execution identifier")
    workflow_id: str = Field(..., description="Workflow definition ID")
    status: ExecutionStatus = Field(..., description="Overall execution status")
    started_at: datetime = Field(..., description="Execution start time")
    completed_at: datetime | None = Field(None, description="Execution completion time")
    node_results: list[NodeExecutionResult] = Field(
        default_factory=list, description="Results from each node execution"
    )
    final_output: dict[str, Any] | None = Field(
        None, description="Final workflow output"
    )
    error: str | None = Field(None, description="Error message if workflow failed")
    total_duration_ms: float | None = Field(
        None, description="Total execution duration in milliseconds"
    )
    inspections: list[dict[str, Any]] | None = Field(
        None,
        description="Node I/O inspection snapshots (when inspection enabled)",
    )


class NodeTypeMetadata(BaseModel):
    """Metadata describing an available node type for UI palette."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "load_files",
                "category": "data",
                "name": "Load Files",
                "description": "Load diffraction files from directory",
                "icon": "fas fa-file",
                "inputs": [],
                "outputs": [{"name": "files", "type": "DiffractionData[]"}],
                "config_schema": {
                    "type": "object",
                    "properties": {
                        "directory": {"type": "string", "default": "."},
                        "pattern": {"type": "string", "default": "*.chi"},
                    },
                },
            }
        }
    )

    type: str = Field(..., description="Node type identifier")
    category: str = Field(
        ..., description="Category: data, analysis, transform, output, control"
    )
    name: str = Field(..., description="Display name for UI")
    description: str = Field(..., description="Node description")
    icon: str | None = Field(None, description="Icon class (e.g., 'fas fa-file')")
    inputs: list[dict[str, str]] = Field(
        default_factory=list, description="Input port definitions"
    )
    outputs: list[dict[str, str]] = Field(
        default_factory=list, description="Output port definitions"
    )
    config_schema: dict[str, Any] = Field(
        default_factory=dict, description="JSON schema for node configuration"
    )
