# Sprint 6: Workflow Orchestrator MVP - ReactFlow Integration

**Status**: Planning  
**Date**: November 25, 2025  
**Target Duration**: 7-10 days  
**Priority**: HIGH - Enables advanced automation capabilities  
**Prerequisites**: Sprint 5 Complete ✅ (Session Persistence)

---

## 🎯 MVP Objective

Build a **visual workflow orchestrator** using ReactFlow that enables users to create, save, and execute multi-step powder diffraction analysis pipelines through an intuitive drag-and-drop interface integrated into the existing RoboMage dashboard.

### Success Criteria
- ✅ Users can create workflows visually in a new Dashboard tab
- ✅ Workflows execute peak analysis on multiple files automatically
- ✅ Workflows are saved/loaded using existing persistence layer
- ✅ At least 5 useful node types implemented
- ✅ Clear execution feedback and error handling
- ✅ All existing tests still pass + 15+ new workflow tests

---

## 🏗️ Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                   Dash Dashboard (Enhanced)                      │
│  ├── Data Import Tab          (existing)                        │
│  ├── Visualization Tab        (existing)                        │
│  ├── Analysis Tab             (existing)                        │
│  ├── Manage Sessions Tab      (existing)                        │
│  └── 🆕 Workflow Builder Tab  (NEW)                             │
│      ├── ReactFlow Canvas     (drag-and-drop workflow editor)   │
│      ├── Node Palette         (available analysis steps)        │
│      ├── Properties Panel     (configure selected nodes)        │
│      ├── Execution Controls   (run, pause, stop)                │
│      └── Results Viewer       (execution logs, outputs)         │
└────────────────┬────────────────────────────────────────────────┘
                 │ HTTP/JSON
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│          Workflow Service (FastAPI Microservice)                 │
│  Port: 8002                                                      │
│  ├── POST /workflows          - Create workflow                 │
│  ├── GET  /workflows          - List workflows                  │
│  ├── GET  /workflows/{id}     - Get workflow definition         │
│  ├── PUT  /workflows/{id}     - Update workflow                 │
│  ├── DELETE /workflows/{id}   - Delete workflow                 │
│  ├── POST /workflows/{id}/execute - Execute workflow            │
│  ├── GET  /executions/{id}    - Get execution status            │
│  ├── GET  /node-types         - Available node types            │
│  └── GET  /health             - Service health                  │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│         Workflow Orchestrator (Core Execution Engine)            │
│  Location: src/robomage/orchestrator.py                         │
│  ├── DAG Builder              (parse workflow to execution DAG) │
│  ├── Topological Sorter       (determine execution order)       │
│  ├── Async Executor           (run nodes in parallel where safe)│
│  ├── Context Manager          (pass data between nodes)         │
│  ├── Error Handler            (graceful failure, rollback)      │
│  └── Progress Tracker         (emit status updates)             │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Node Type Registry                              │
│  Location: src/robomage/workflow/nodes/                         │
│  ├── base.py                  (BaseNode abstract class)         │
│  ├── data_nodes.py            (LoadFiles, FilterData)           │
│  ├── analysis_nodes.py        (PeakDetection, Statistics)       │
│  ├── transform_nodes.py       (QRangeTrim, Normalize)           │
│  └── output_nodes.py          (ExportCSV, PlotResults)          │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│              Existing RoboMage Services                          │
│  ├── Peak Analysis Service    (port 8001)                       │
│  ├── Data Loaders             (load_diffraction_file, etc.)     │
│  ├── Persistence Layer        (SQLite + HDF5)                   │
│  └── Visualization            (matplotlib, plotly)               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Data Models

### Core Pydantic Models

```python
# services/workflow_engine/models.py

from pydantic import BaseModel, Field
from typing import Literal, Any
from datetime import datetime

class NodePosition(BaseModel):
    """UI position for ReactFlow rendering."""
    x: float
    y: float

class WorkflowNode(BaseModel):
    """Single node in a workflow graph."""
    id: str = Field(..., description="Unique node identifier")
    type: str = Field(..., description="Node type (e.g., 'load_files', 'peak_analysis')")
    label: str = Field(..., description="User-friendly node label")
    config: dict[str, Any] = Field(default_factory=dict, description="Node-specific configuration")
    position: NodePosition = Field(..., description="Position on canvas")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "node_1",
                "type": "load_files",
                "label": "Load CHI Files",
                "config": {"pattern": "*.chi", "directory": "/data"},
                "position": {"x": 100, "y": 100}
            }
        }

class WorkflowEdge(BaseModel):
    """Connection between two nodes."""
    id: str = Field(..., description="Unique edge identifier")
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    source_handle: str | None = Field(None, description="Source output port")
    target_handle: str | None = Field(None, description="Target input port")

class WorkflowDefinition(BaseModel):
    """Complete workflow specification."""
    id: str | None = Field(None, description="Workflow ID (assigned by system)")
    name: str = Field(..., description="Workflow name")
    description: str = Field(default="", description="Workflow description")
    nodes: list[WorkflowNode] = Field(..., description="Workflow nodes")
    edges: list[WorkflowEdge] = Field(..., description="Node connections")
    created_at: datetime | None = None
    updated_at: datetime | None = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Batch Peak Analysis",
                "description": "Load multiple files and detect peaks",
                "nodes": [
                    {
                        "id": "load_1",
                        "type": "load_files",
                        "label": "Load Data",
                        "config": {"pattern": "*.chi"},
                        "position": {"x": 100, "y": 100}
                    },
                    {
                        "id": "analyze_1",
                        "type": "peak_analysis",
                        "label": "Detect Peaks",
                        "config": {"profile": "gaussian", "prominence": 0.1},
                        "position": {"x": 400, "y": 100}
                    }
                ],
                "edges": [
                    {
                        "id": "edge_1",
                        "source": "load_1",
                        "target": "analyze_1"
                    }
                ]
            }
        }

class ExecutionStatus(str, Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class NodeExecutionResult(BaseModel):
    """Result from executing a single node."""
    node_id: str
    status: ExecutionStatus
    started_at: datetime
    completed_at: datetime | None = None
    output: dict[str, Any] | None = None
    error: str | None = None

class WorkflowExecutionResult(BaseModel):
    """Result from executing a complete workflow."""
    execution_id: str
    workflow_id: str
    status: ExecutionStatus
    started_at: datetime
    completed_at: datetime | None = None
    node_results: list[NodeExecutionResult] = []
    final_output: dict[str, Any] | None = None
    error: str | None = None

class NodeTypeMetadata(BaseModel):
    """Metadata describing an available node type."""
    type: str = Field(..., description="Node type identifier")
    category: str = Field(..., description="Category (data, analysis, transform, output)")
    name: str = Field(..., description="Display name")
    description: str = Field(..., description="Node description")
    icon: str | None = Field(None, description="Icon class (e.g., 'fas fa-file')")
    inputs: list[dict[str, str]] = Field(default_factory=list, description="Input ports")
    outputs: list[dict[str, str]] = Field(default_factory=list, description="Output ports")
    config_schema: dict[str, Any] = Field(..., description="JSON schema for configuration")
```

---

## 🔧 MVP Node Types (Phase 1)

### 1. Data Input Nodes
- **`load_files`**: Load diffraction files from directory/pattern
  - Config: `directory`, `pattern` (glob), `wavelength`
  - Outputs: `files[]` (list of DiffractionData)

- **`load_session`**: Load files from saved session
  - Config: `session_id`
  - Outputs: `files[]`

### 2. Data Transform Nodes
- **`filter_q_range`**: Trim Q-space range
  - Config: `q_min`, `q_max`
  - Inputs: `files[]`
  - Outputs: `files[]`

- **`normalize`**: Normalize intensity values
  - Config: `method` ("max", "area", "zscore")
  - Inputs: `files[]`
  - Outputs: `files[]`

### 3. Analysis Nodes
- **`peak_analysis`**: Detect and fit peaks
  - Config: `profile_type`, `prominence`, `distance`
  - Inputs: `files[]`
  - Outputs: `results[]` (PeakAnalysisResponse per file)

- **`statistics`**: Calculate data statistics
  - Config: `metrics` (list of stat types)
  - Inputs: `files[]`
  - Outputs: `stats[]`

### 4. Control Flow Nodes
- **`merge`**: Combine multiple inputs
  - Inputs: `input_1`, `input_2`, ...
  - Outputs: `combined[]`

- **`split`**: Split based on condition
  - Config: `condition` (e.g., "peak_count > 5")
  - Inputs: `files[]`
  - Outputs: `true_branch[]`, `false_branch[]`

### 5. Output Nodes
- **`export_csv`**: Export results to CSV
  - Config: `output_path`, `format`
  - Inputs: `results[]`
  - Outputs: `file_path`

- **`export_json`**: Export results to JSON
  - Config: `output_path`
  - Inputs: `results[]`
  - Outputs: `file_path`

- **`save_to_session`**: **[NEW - Day 5-6]** Save results to session for visualization
  - Config: `session_id` ("current" or specific ID), `include_files`, `include_results`
  - Inputs: `files[]`, `results[]`
  - Outputs: `session_info` (files_saved count, session_id)
  - **Purpose**: Enables workflow → dashboard visualization integration

- **`plot_results`**: Generate plots
  - Config: `plot_type`, `style`
  - Inputs: `files[]`, `results[]` (optional)
  - Outputs: `image_paths[]`

---

## 📝 Implementation Plan - 7 Day MVP

### **Day 1-2: Core Orchestrator Engine**

#### Task 1.1: Workflow Orchestrator Implementation
**File**: `src/robomage/orchestrator.py`

```python
"""
Workflow Orchestrator - DAG Execution Engine

Executes multi-step diffraction analysis workflows by coordinating
node execution, managing data flow, and handling errors.
"""

import asyncio
from collections import defaultdict, deque
from typing import Any, Callable
from datetime import datetime
import logging

from pydantic import BaseModel

logger = logging.getLogger(__name__)

class ExecutionContext:
    """Manages data flow between workflow nodes."""
    
    def __init__(self):
        self.data: dict[str, Any] = {}  # node_id -> output data
        self.metadata: dict[str, Any] = {}
    
    def set_node_output(self, node_id: str, output: Any) -> None:
        """Store output from a node execution."""
        self.data[node_id] = output
    
    def get_node_output(self, node_id: str) -> Any:
        """Retrieve output from a previous node."""
        return self.data.get(node_id)

class WorkflowOrchestrator:
    """
    Executes workflows as directed acyclic graphs (DAGs).
    
    Features:
    - Topological sorting for correct execution order
    - Parallel execution of independent nodes
    - Error handling with partial rollback
    - Progress tracking and status updates
    """
    
    def __init__(self):
        self.node_handlers: dict[str, Callable] = {}
        self._execution_callbacks: list[Callable] = []
    
    def register_node_handler(self, node_type: str, handler: Callable) -> None:
        """
        Register a handler function for a node type.
        
        Args:
            node_type: Node type identifier (e.g., 'load_files')
            handler: Async function(node_config, context) -> output
        """
        self.node_handlers[node_type] = handler
        logger.info(f"Registered handler for node type: {node_type}")
    
    def on_progress(self, callback: Callable) -> None:
        """Register callback for execution progress updates."""
        self._execution_callbacks.append(callback)
    
    async def execute_workflow(
        self, 
        workflow: "WorkflowDefinition",
        initial_context: dict[str, Any] | None = None
    ) -> "WorkflowExecutionResult":
        """
        Execute a complete workflow.
        
        Args:
            workflow: Workflow definition with nodes and edges
            initial_context: Optional initial data/configuration
        
        Returns:
            WorkflowExecutionResult with status and outputs
        """
        from services.workflow_engine.models import (
            WorkflowExecutionResult,
            NodeExecutionResult,
            ExecutionStatus
        )
        
        execution_id = f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        started_at = datetime.now()
        
        logger.info(f"Starting workflow execution: {execution_id}")
        
        # Initialize context
        context = ExecutionContext()
        if initial_context:
            context.metadata.update(initial_context)
        
        # Build execution graph
        execution_order = self._topological_sort(workflow)
        logger.info(f"Execution order: {[n.id for n in execution_order]}")
        
        # Execute nodes
        node_results = []
        try:
            for node in execution_order:
                node_result = await self._execute_node(node, context, workflow)
                node_results.append(node_result)
                
                if node_result.status == ExecutionStatus.FAILED:
                    raise RuntimeError(f"Node {node.id} failed: {node_result.error}")
                
                # Emit progress
                for callback in self._execution_callbacks:
                    await callback(execution_id, node_result)
            
            # Success
            return WorkflowExecutionResult(
                execution_id=execution_id,
                workflow_id=workflow.id or "unknown",
                status=ExecutionStatus.COMPLETED,
                started_at=started_at,
                completed_at=datetime.now(),
                node_results=node_results,
                final_output=context.data
            )
        
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}", exc_info=True)
            return WorkflowExecutionResult(
                execution_id=execution_id,
                workflow_id=workflow.id or "unknown",
                status=ExecutionStatus.FAILED,
                started_at=started_at,
                completed_at=datetime.now(),
                node_results=node_results,
                error=str(e)
            )
    
    def _topological_sort(self, workflow: "WorkflowDefinition") -> list["WorkflowNode"]:
        """
        Sort nodes in valid execution order using topological sort.
        
        Returns:
            List of nodes in execution order
        
        Raises:
            ValueError: If workflow contains cycles
        """
        # Build adjacency list
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
            
            for neighbor_id in graph[current_id]:
                in_degree[neighbor_id] -= 1
                if in_degree[neighbor_id] == 0:
                    queue.append(neighbor_id)
        
        # Check for cycles
        if len(sorted_nodes) != len(workflow.nodes):
            raise ValueError("Workflow contains cycles - cannot execute")
        
        return sorted_nodes
    
    async def _execute_node(
        self,
        node: "WorkflowNode",
        context: ExecutionContext,
        workflow: "WorkflowDefinition"
    ) -> "NodeExecutionResult":
        """Execute a single node."""
        from services.workflow_engine.models import (
            NodeExecutionResult,
            ExecutionStatus
        )
        
        logger.info(f"Executing node: {node.id} ({node.type})")
        started_at = datetime.now()
        
        try:
            # Get handler for this node type
            handler = self.node_handlers.get(node.type)
            if not handler:
                raise ValueError(f"No handler registered for node type: {node.type}")
            
            # Collect inputs from predecessor nodes
            inputs = self._collect_node_inputs(node, context, workflow)
            
            # Execute handler
            output = await handler(node.config, inputs, context)
            
            # Store output in context
            context.set_node_output(node.id, output)
            
            return NodeExecutionResult(
                node_id=node.id,
                status=ExecutionStatus.COMPLETED,
                started_at=started_at,
                completed_at=datetime.now(),
                output=output
            )
        
        except Exception as e:
            logger.error(f"Node {node.id} failed: {e}", exc_info=True)
            return NodeExecutionResult(
                node_id=node.id,
                status=ExecutionStatus.FAILED,
                started_at=started_at,
                completed_at=datetime.now(),
                error=str(e)
            )
    
    def _collect_node_inputs(
        self,
        node: "WorkflowNode",
        context: ExecutionContext,
        workflow: "WorkflowDefinition"
    ) -> dict[str, Any]:
        """Collect inputs from predecessor nodes."""
        inputs = {}
        
        # Find edges pointing to this node
        for edge in workflow.edges:
            if edge.target == node.id:
                source_output = context.get_node_output(edge.source)
                input_key = edge.target_handle or "input"
                inputs[input_key] = source_output
        
        return inputs
```

#### Task 1.2: Node Base Classes
**File**: `src/robomage/workflow/nodes/base.py`

```python
"""Base classes for workflow nodes."""

from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel

class BaseNode(ABC):
    """Abstract base class for all workflow nodes."""
    
    @property
    @abstractmethod
    def node_type(self) -> str:
        """Unique identifier for this node type."""
        pass
    
    @property
    @abstractmethod
    def category(self) -> str:
        """Node category: data, analysis, transform, output."""
        pass
    
    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable node name."""
        pass
    
    @abstractmethod
    async def execute(
        self,
        config: dict[str, Any],
        inputs: dict[str, Any],
        context: Any
    ) -> Any:
        """
        Execute this node's operation.
        
        Args:
            config: Node configuration from workflow definition
            inputs: Outputs from predecessor nodes
            context: Execution context for shared state
        
        Returns:
            Node output (passed to successor nodes)
        """
        pass
    
    def validate_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """Validate and process node configuration."""
        return config
```

**Deliverables**:
- ✅ Working orchestrator with topological sort
- ✅ Execution context for data flow
- ✅ Base node interface
- ✅ Unit tests for DAG execution

---

### **Day 3-4: Workflow Service & Node Implementations**

#### Task 3.1: FastAPI Workflow Service
**File**: `services/workflow_engine/main.py`

```python
"""
FastAPI Workflow Service

REST API for workflow management and execution.
"""

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime
import uuid

from .models import (
    WorkflowDefinition,
    WorkflowExecutionResult,
    NodeTypeMetadata,
    ExecutionStatus
)
from src.robomage.orchestrator import WorkflowOrchestrator

# Global state
workflows: dict[str, WorkflowDefinition] = {}
executions: dict[str, WorkflowExecutionResult] = {}
orchestrator = WorkflowOrchestrator()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Service lifecycle management."""
    # Startup: Register node handlers
    await register_node_handlers()
    print("Workflow Service started on port 8002")
    
    yield
    
    # Shutdown
    print("Workflow Service stopped")

app = FastAPI(
    title="RoboMage Workflow Service",
    description="Visual workflow orchestration for diffraction analysis",
    version="1.0.0",
    lifespan=lifespan
)

# CORS for dashboard integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8050", "http://127.0.0.1:8050"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "service": "RoboMage Workflow Service",
        "version": "1.0.0",
        "endpoints": {
            "workflows": "GET/POST /workflows",
            "execute": "POST /workflows/{id}/execute",
            "node_types": "GET /node-types"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "workflows_count": len(workflows),
        "executions_count": len(executions)
    }

@app.post("/workflows", response_model=WorkflowDefinition)
async def create_workflow(workflow: WorkflowDefinition):
    """Create a new workflow definition."""
    workflow.id = str(uuid.uuid4())
    workflow.created_at = datetime.now()
    workflow.updated_at = datetime.now()
    
    workflows[workflow.id] = workflow
    return workflow

@app.get("/workflows", response_model=list[WorkflowDefinition])
async def list_workflows():
    """List all saved workflows."""
    return list(workflows.values())

@app.get("/workflows/{workflow_id}", response_model=WorkflowDefinition)
async def get_workflow(workflow_id: str):
    """Get a specific workflow."""
    if workflow_id not in workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflows[workflow_id]

@app.put("/workflows/{workflow_id}", response_model=WorkflowDefinition)
async def update_workflow(workflow_id: str, workflow: WorkflowDefinition):
    """Update an existing workflow."""
    if workflow_id not in workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow.id = workflow_id
    workflow.updated_at = datetime.now()
    workflows[workflow_id] = workflow
    return workflow

@app.delete("/workflows/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """Delete a workflow."""
    if workflow_id not in workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    del workflows[workflow_id]
    return {"status": "deleted"}

@app.post("/workflows/{workflow_id}/execute", response_model=WorkflowExecutionResult)
async def execute_workflow(workflow_id: str, context: dict = None):
    """Execute a workflow."""
    if workflow_id not in workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow = workflows[workflow_id]
    
    # Execute using orchestrator
    result = await orchestrator.execute_workflow(workflow, context)
    
    # Store execution result
    executions[result.execution_id] = result
    
    return result

@app.get("/executions/{execution_id}", response_model=WorkflowExecutionResult)
async def get_execution(execution_id: str):
    """Get execution status and results."""
    if execution_id not in executions:
        raise HTTPException(status_code=404, detail="Execution not found")
    return executions[execution_id]

@app.get("/node-types", response_model=list[NodeTypeMetadata])
async def get_node_types():
    """Get available node types for UI palette."""
    # Will populate this with registered node types
    return get_registered_node_types()

async def register_node_handlers():
    """Register all node type handlers with orchestrator."""
    from src.robomage.workflow.nodes import data_nodes, analysis_nodes, output_nodes
    
    # Data nodes
    orchestrator.register_node_handler("load_files", data_nodes.load_files_handler)
    orchestrator.register_node_handler("filter_q_range", data_nodes.filter_q_range_handler)
    
    # Analysis nodes
    orchestrator.register_node_handler("peak_analysis", analysis_nodes.peak_analysis_handler)
    
    # Output nodes
    orchestrator.register_node_handler("export_csv", output_nodes.export_csv_handler)

def get_registered_node_types() -> list[NodeTypeMetadata]:
    """Return metadata for all registered node types."""
    # Will implement node type registry
    return []

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
```

#### Task 3.2: Implement Core Node Handlers
**File**: `src/robomage/workflow/nodes/data_nodes.py`

```python
"""Data input and transformation nodes."""

import glob
from pathlib import Path
from typing import Any

import robomage

async def load_files_handler(
    config: dict[str, Any],
    inputs: dict[str, Any],
    context: Any
) -> list:
    """
    Load diffraction files from directory.
    
    Config:
        - directory: str (path to directory)
        - pattern: str (glob pattern, e.g., "*.chi")
        - wavelength: float (optional, override file wavelength)
    
    Outputs:
        List of DiffractionData objects
    """
    directory = config.get("directory", ".")
    pattern = config.get("pattern", "*.chi")
    wavelength = config.get("wavelength")
    
    # Find matching files
    search_path = Path(directory) / pattern
    file_paths = glob.glob(str(search_path))
    
    if not file_paths:
        raise ValueError(f"No files found matching: {search_path}")
    
    # Load files
    loaded_files = []
    for file_path in file_paths:
        data = robomage.load_diffraction_file(file_path)
        if wavelength:
            data.wavelength = wavelength
        loaded_files.append(data)
    
    return loaded_files

async def filter_q_range_handler(
    config: dict[str, Any],
    inputs: dict[str, Any],
    context: Any
) -> list:
    """
    Filter data by Q-range.
    
    Config:
        - q_min: float
        - q_max: float
    
    Inputs:
        - input: List of DiffractionData
    
    Outputs:
        Filtered list of DiffractionData
    """
    q_min = config.get("q_min", 0)
    q_max = config.get("q_max", float('inf'))
    
    files = inputs.get("input", [])
    filtered = []
    
    for data in files:
        trimmed = data.trim_q_range(q_min, q_max)
        filtered.append(trimmed)
    
    return filtered
```

**File**: `src/robomage/workflow/nodes/analysis_nodes.py`

```python
"""Analysis nodes."""

from typing import Any
from robomage.clients.peak_analysis_client import PeakAnalysisClient

async def peak_analysis_handler(
    config: dict[str, Any],
    inputs: dict[str, Any],
    context: Any
) -> list:
    """
    Perform peak analysis on diffraction data.
    
    Config:
        - profile_type: str (gaussian, lorentzian, voigt)
        - prominence: float
        - distance: float
        - service_url: str (default: http://localhost:8001)
    
    Inputs:
        - input: List of DiffractionData
    
    Outputs:
        List of PeakAnalysisResponse objects
    """
    service_url = config.get("service_url", "http://localhost:8001")
    client = PeakAnalysisClient(service_url)
    
    # Build analysis config
    analysis_config = {
        "peak_detection": {
            "prominence": config.get("prominence", 0.1),
            "distance": config.get("distance", 5)
        },
        "fitting": {
            "profile_type": config.get("profile_type", "gaussian")
        }
    }
    
    files = inputs.get("input", [])
    results = []
    
    for data in files:
        response = client.analyze_diffraction_data(data, analysis_config)
        results.append(response)
    
    return results
```

**Deliverables**:
- ✅ FastAPI service with CRUD endpoints
- ✅ 3-5 working node handlers
- ✅ Service integration tests
- ✅ OpenAPI documentation

---

### **Day 5-6: Dashboard Integration**

#### Task 5.1: ReactFlow Dash Component
**Options**:
1. Use `dash-extensions` with custom React component
2. Embed ReactFlow in iframe with postMessage communication
3. Use `dash-react-flow` (if available)

**Recommended**: Option 2 (iframe) for MVP simplicity

**File**: `src/robomage/dashboard/layouts/workflow_layout.py`

```python
"""Workflow Builder tab layout."""

import dash_bootstrap_components as dbc
from dash import dcc, html

def create_workflow_tab() -> html.Div:
    """Create the Workflow Builder tab."""
    return html.Div([
        dbc.Row([
            # Left sidebar - Node palette
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-puzzle-piece me-2"),
                            "Node Palette"
                        ])
                    ]),
                    dbc.CardBody([
                        html.Div(id="node-palette", children=[
                            create_node_palette()
                        ])
                    ])
                ], className="h-100")
            ], width=3),
            
            # Center - Workflow canvas
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-project-diagram me-2"),
                            "Workflow Canvas"
                        ]),
                        html.Div([
                            dbc.ButtonGroup([
                                dbc.Button([
                                    html.I(className="fas fa-save me-2"),
                                    "Save"
                                ], id="save-workflow-btn", color="primary", size="sm"),
                                dbc.Button([
                                    html.I(className="fas fa-folder-open me-2"),
                                    "Load"
                                ], id="load-workflow-btn", color="secondary", size="sm"),
                                dbc.Button([
                                    html.I(className="fas fa-file me-2"),
                                    "New"
                                ], id="new-workflow-btn", color="info", size="sm"),
                            ]),
                            dbc.ButtonGroup([
                                dbc.Button([
                                    html.I(className="fas fa-play me-2"),
                                    "Execute"
                                ], id="execute-workflow-btn", color="success", size="sm", className="ms-2"),
                            ])
                        ])
                    ]),
                    dbc.CardBody([
                        # ReactFlow canvas (iframe)
                        html.Iframe(
                            id="workflow-canvas",
                            src="/assets/workflow_editor.html",
                            style={
                                "width": "100%",
                                "height": "600px",
                                "border": "1px solid #ddd",
                                "borderRadius": "4px"
                            }
                        ),
                        # Hidden stores for workflow data
                        dcc.Store(id="current-workflow", data=None),
                        dcc.Store(id="execution-status", data=None),
                    ])
                ])
            ], width=6),
            
            # Right sidebar - Properties & Results
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-cog me-2"),
                            "Properties & Results"
                        ])
                    ]),
                    dbc.CardBody([
                        dbc.Tabs([
                            dbc.Tab(
                                label="Node Properties",
                                children=[
                                    html.Div(
                                        id="node-properties",
                                        children=[
                                            html.P("Select a node to configure", className="text-muted mt-3")
                                        ]
                                    )
                                ]
                            ),
                            dbc.Tab(
                                label="Execution Log",
                                children=[
                                    html.Div(
                                        id="execution-log",
                                        style={"maxHeight": "500px", "overflowY": "auto"}
                                    )
                                ]
                            ),
                        ])
                    ])
                ], className="h-100")
            ], width=3),
        ])
    ])

def create_node_palette():
    """Create draggable node palette."""
    node_categories = [
        {
            "category": "Data Input",
            "nodes": [
                {"type": "load_files", "name": "Load Files", "icon": "fa-file"},
                {"type": "load_session", "name": "Load Session", "icon": "fa-database"},
            ]
        },
        {
            "category": "Transform",
            "nodes": [
                {"type": "filter_q_range", "name": "Filter Q-Range", "icon": "fa-filter"},
                {"type": "normalize", "name": "Normalize", "icon": "fa-balance-scale"},
            ]
        },
        {
            "category": "Analysis",
            "nodes": [
                {"type": "peak_analysis", "name": "Peak Detection", "icon": "fa-mountain"},
                {"type": "statistics", "name": "Statistics", "icon": "fa-chart-bar"},
            ]
        },
        {
            "category": "Output",
            "nodes": [
                {"type": "export_csv", "name": "Export CSV", "icon": "fa-file-csv"},
                {"type": "plot_results", "name": "Plot Results", "icon": "fa-chart-line"},
            ]
        }
    ]
    
    palette_items = []
    for category in node_categories:
        palette_items.append(
            html.Div([
                html.H6(category["category"], className="text-muted mt-3 mb-2"),
                *[
                    dbc.Card([
                        dbc.CardBody([
                            html.I(className=f"fas {node['icon']} me-2"),
                            node["name"]
                        ], className="py-2")
                    ], className="mb-2 cursor-pointer node-palette-item", 
                       **{"data-node-type": node["type"]})
                    for node in category["nodes"]
                ]
            ])
        )
    
    return palette_items
```

#### Task 5.2: Workflow Callbacks
**File**: `src/robomage/dashboard/callbacks/workflow.py`

```python
"""Workflow callbacks for execution and management."""

from dash import Input, Output, State, callback
import requests

WORKFLOW_SERVICE_URL = "http://localhost:8002"

def register_callbacks(app):
    """Register workflow-related callbacks."""
    
    @app.callback(
        Output("current-workflow", "data"),
        Input("save-workflow-btn", "n_clicks"),
        State("workflow-canvas", "src"),  # Will get workflow from iframe
        prevent_initial_call=True
    )
    def save_workflow(n_clicks, workflow_data):
        """Save current workflow to service."""
        if not workflow_data:
            return None
        
        # POST to workflow service
        response = requests.post(
            f"{WORKFLOW_SERVICE_URL}/workflows",
            json=workflow_data
        )
        
        if response.status_code == 200:
            return response.json()
        return None
    
    @app.callback(
        Output("execution-log", "children"),
        Input("execute-workflow-btn", "n_clicks"),
        State("current-workflow", "data"),
        prevent_initial_call=True
    )
    def execute_workflow(n_clicks, workflow):
        """Execute the current workflow."""
        if not workflow or "id" not in workflow:
            return html.P("No workflow to execute", className="text-danger")
        
        # POST to execution endpoint
        response = requests.post(
            f"{WORKFLOW_SERVICE_URL}/workflows/{workflow['id']}/execute"
        )
        
        if response.status_code == 200:
            result = response.json()
            return create_execution_log_ui(result)
        
        return html.P("Execution failed", className="text-danger")

def create_execution_log_ui(result):
    """Create UI for execution results."""
    return html.Div([
        html.H6(f"Execution: {result['execution_id']}"),
        html.P(f"Status: {result['status']}"),
        html.P(f"Started: {result['started_at']}"),
        html.Hr(),
        html.H6("Node Results:"),
        *[
            html.Div([
                html.Strong(f"{nr['node_id']}: "),
                html.Span(nr['status'], className=f"badge bg-{'success' if nr['status'] == 'completed' else 'danger'}")
            ], className="mb-2")
            for nr in result.get('node_results', [])
        ]
    ])
```

**Deliverables**:
- ✅ Working workflow tab in dashboard
- ✅ Node palette with drag-and-drop
- ✅ Save/load workflows
- ✅ Execute workflows with visual feedback

---

### **Day 7: Testing, Documentation & Polish**

#### Task 7.1: Comprehensive Testing
**File**: `tests/test_workflow_orchestrator.py`

```python
"""Tests for workflow orchestrator."""

import pytest
from src.robomage.orchestrator import WorkflowOrchestrator, ExecutionContext
from services.workflow_engine.models import (
    WorkflowDefinition,
    WorkflowNode,
    WorkflowEdge,
    NodePosition,
    ExecutionStatus
)

@pytest.mark.asyncio
async def test_simple_workflow_execution():
    """Test executing a simple two-node workflow."""
    orchestrator = WorkflowOrchestrator()
    
    # Register test handlers
    async def test_handler_1(config, inputs, context):
        return {"value": 42}
    
    async def test_handler_2(config, inputs, context):
        input_val = inputs["input"]["value"]
        return {"result": input_val * 2}
    
    orchestrator.register_node_handler("test_1", test_handler_1)
    orchestrator.register_node_handler("test_2", test_handler_2)
    
    # Create workflow
    workflow = WorkflowDefinition(
        name="Test Workflow",
        nodes=[
            WorkflowNode(
                id="node1",
                type="test_1",
                label="Node 1",
                position=NodePosition(x=0, y=0)
            ),
            WorkflowNode(
                id="node2",
                type="test_2",
                label="Node 2",
                position=NodePosition(x=100, y=0)
            )
        ],
        edges=[
            WorkflowEdge(id="edge1", source="node1", target="node2")
        ]
    )
    
    # Execute
    result = await orchestrator.execute_workflow(workflow)
    
    assert result.status == ExecutionStatus.COMPLETED
    assert len(result.node_results) == 2
    assert result.final_output["node2"]["result"] == 84

@pytest.mark.asyncio
async def test_topological_sort():
    """Test DAG topological sorting."""
    # Test with complex graph
    pass

@pytest.mark.asyncio
async def test_cycle_detection():
    """Test that cycles are detected and rejected."""
    # Test workflow with cycle
    pass
```

#### Task 7.2: Documentation
**File**: `docs/workflow-orchestrator-guide.md`

```markdown
# Workflow Orchestrator User Guide

## Overview
The RoboMage Workflow Orchestrator enables visual creation of multi-step
diffraction analysis pipelines through an intuitive drag-and-drop interface.

## Quick Start

1. **Start Services**:
   ```bash
   # Terminal 1: Peak analysis
   cd services/peak_analysis
   python main.py --port 8001
   
   # Terminal 2: Workflow service
   cd services/workflow_engine
   python main.py --port 8002
   
   # Terminal 3: Dashboard
   pixi run dashboard
   ```

2. **Create Workflow**:
   - Navigate to "Workflow Builder" tab
   - Drag nodes from palette to canvas
   - Connect nodes by dragging from output to input
   - Configure each node by selecting it

3. **Execute Workflow**:
   - Click "Execute" button
   - Monitor progress in Execution Log
   - View results in Results panel

## Example Workflows

### Batch Peak Analysis
...
```

**Deliverables**:
- ✅ 15+ unit tests for orchestrator
- ✅ Integration tests for service
- ✅ User documentation
- ✅ API documentation

---

## 📦 File Structure After MVP

```
RoboMage/
├── src/robomage/
│   ├── orchestrator.py                  # NEW: Core workflow executor
│   ├── workflow/                        # NEW: Workflow components
│   │   ├── __init__.py
│   │   └── nodes/
│   │       ├── __init__.py
│   │       ├── base.py                  # Base node classes
│   │       ├── data_nodes.py            # Data I/O nodes
│   │       ├── analysis_nodes.py        # Analysis nodes
│   │       ├── transform_nodes.py       # Transform nodes
│   │       └── output_nodes.py          # Output nodes
│   └── dashboard/
│       ├── layouts/
│       │   └── workflow_layout.py       # NEW: Workflow tab
│       └── callbacks/
│           └── workflow.py              # NEW: Workflow callbacks
├── services/
│   └── workflow_engine/                 # NEW: Workflow microservice
│       ├── main.py                      # FastAPI app
│       ├── models.py                    # Pydantic models
│       └── README.md                    # Service docs
├── tests/
│   ├── test_workflow_orchestrator.py    # NEW: Orchestrator tests
│   ├── test_workflow_service.py         # NEW: Service tests
│   └── test_workflow_nodes.py           # NEW: Node tests
└── docs/
    ├── sprint-6-workflow-orchestrator-mvp.md  # This file
    └── workflow-orchestrator-guide.md   # NEW: User guide
```

---

## 🎯 MVP Success Metrics

### Functional Requirements
- ✅ Create workflows with 5+ node types
- ✅ Execute workflows with proper DAG ordering
- ✅ Save/load workflows using persistence layer
- ✅ Visual feedback during execution
- ✅ Error handling with clear messages

### Technical Requirements
- ✅ All existing tests pass (99 tests)
- ✅ 15+ new workflow tests
- ✅ Code quality: ruff, mypy passing
- ✅ API documentation complete
- ✅ User guide with examples

### Performance Requirements
- ✅ Workflow execution < 5s for typical analysis
- ✅ UI responsive < 100ms for node operations
- ✅ Handles 20+ node workflows

---

## 🚀 Beyond MVP - Future Enhancements

### Phase 2 Features (Sprint 7)
- **Parallel Execution**: Execute independent branches in parallel
- **Conditional Logic**: If/else branching based on results
- **Loops**: Iterate over file lists
- **Sub-workflows**: Reusable workflow components
- **Templates**: Pre-built workflow library

### Phase 3 Features (Sprint 8)
- **Real-time Collaboration**: Multi-user workflow editing
- **Version Control**: Workflow versioning and history
- **Advanced Nodes**: GSAS-II integration, machine learning
- **Monitoring Dashboard**: Live execution monitoring
- **Workflow Marketplace**: Share workflows with community

### Integration Opportunities
- **Jupyter Notebooks**: Export workflows as notebooks
- **CI/CD**: Automated workflow execution
- **REST API**: Programmatic workflow execution
- **NSLS-II Integration**: Beamline data pipelines

---

## 📋 Dependencies & Requirements

### Python Packages (add to pixi.toml)
```toml
# No new dependencies for MVP!
# Uses existing: pydantic, fastapi, dash
```

### Frontend (optional for enhanced UI)
```json
{
  "reactflow": "^11.0.0",
  "react": "^18.0.0",
  "react-dom": "^18.0.0"
}
```

### Development Tools
- Existing pixi environment
- No additional tools needed

---

## 🔄 Integration with Existing Systems

### Session Persistence
Workflows stored in SQLite database alongside sessions:

```python
# Extend persistence/models.py
class Workflow(Base):
    __tablename__ = "workflows"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    definition = Column(JSON, nullable=False)  # WorkflowDefinition as JSON
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=True)  # Optional link to session
```

### Workflow → Session Integration (Day 5-6 Feature)
Enable seamless workflow results → dashboard visualization:

#### 1. `save_to_session` Node Handler
```python
# src/robomage/workflow/nodes/output_nodes.py

async def save_to_session_handler(
    config: dict[str, Any],
    inputs: dict[str, Any], 
    context: Any
) -> dict:
    """
    Save workflow results into a session for visualization.
    
    Config Parameters:
        - session_id: str (target session ID, or "current" for active session)
        - include_files: bool (save DiffractionData objects, default: True)
        - include_results: bool (save analysis results, default: True)
    
    Inputs:
        - files: List[DiffractionData] (optional)
        - results: List[PeakAnalysisResponse] (optional)
    
    Outputs:
        Dictionary with session info and saved items count
    
    Example:
        config = {
            "session_id": "current",
            "include_files": True,
            "include_results": True
        }
    """
    from robomage.persistence.api import SessionManager
    
    session_id = config.get("session_id", "current")
    include_files = config.get("include_files", True)
    include_results = config.get("include_results", True)
    
    manager = SessionManager()
    saved_count = 0
    
    # Save DiffractionData files
    if include_files:
        files = inputs.get("files", [])
        for data in files:
            manager.add_file_to_session(
                session_id=session_id,
                diffraction_data=data,
                filename=data.filename or f"workflow_output_{saved_count}.chi"
            )
            saved_count += 1
    
    # Save analysis results as metadata
    if include_results:
        results = inputs.get("results", [])
        # Store in session metadata or separate results table
        # (implementation depends on persistence schema)
    
    return {
        "session_id": session_id,
        "files_saved": saved_count,
        "status": "success"
    }
```

#### 2. Dashboard UI Integration
Add "Save to Session" button in workflow tab:

```python
# src/robomage/dashboard/callbacks/workflow.py

@callback(
    Output("save-to-session-status", "children"),
    Input("save-results-to-session-btn", "n_clicks"),
    State("execution-results", "data"),
    State("active-session-id", "data"),
    prevent_initial_call=True
)
def save_workflow_results_to_session(n_clicks, execution_results, session_id):
    """
    Extract DiffractionData from workflow execution and add to active session.
    Enables immediate visualization of workflow results.
    """
    if not execution_results or not session_id:
        return dbc.Alert("No results or active session", color="warning")
    
    from robomage.persistence.api import SessionManager
    manager = SessionManager()
    
    # Extract DiffractionData objects from execution results
    files_saved = 0
    for node_result in execution_results.get("node_results", []):
        output = node_result.get("output")
        
        # Handle different output types
        if isinstance(output, list):
            for item in output:
                if hasattr(item, "q_values"):  # DiffractionData-like object
                    manager.add_file_to_session(
                        session_id=session_id,
                        diffraction_data=item,
                        filename=getattr(item, "filename", f"workflow_{files_saved}.chi")
                    )
                    files_saved += 1
    
    # Trigger refresh of Data Import and Visualization tabs
    return dbc.Alert(
        f"✅ Saved {files_saved} files to session '{session_id}'. "
        "Switch to Visualization tab to view results.",
        color="success"
    )
```

#### 3. Benefits
- **Seamless workflow**: Load → Analyze → Visualize in one interface
- **No manual exports**: Results automatically available for plotting
- **Session continuity**: All analysis saved together
- **Reproducibility**: Workflow + results linked to session

### Service Architecture
Workflow service follows same patterns as peak analysis:
- FastAPI with Pydantic models
- Health check endpoint
- OpenAPI documentation
- HTTP/JSON communication

### Dashboard Integration
New tab follows existing patterns:
- Bootstrap components
- Dash callbacks
- State management with dcc.Store
- Professional UI matching other tabs

---

## 🎓 Learning Resources

### ReactFlow
- [ReactFlow Documentation](https://reactflow.dev/docs)
- [React Flow Examples](https://reactflow.dev/examples)

### DAG Execution
- [Topological Sort Algorithm](https://en.wikipedia.org/wiki/Topological_sorting)
- [Kahn's Algorithm](https://www.geeksforgeeks.org/topological-sorting-indegree-based-solution/)

### Workflow Engines (Reference)
- [Apache Airflow](https://airflow.apache.org/)
- [Prefect](https://www.prefect.io/)
- [Dagster](https://dagster.io/)

---

## ✅ Ready to Start!

This MVP plan provides:
1. **Clear 7-day implementation path**
2. **Incremental deliverables** (test early and often)
3. **Leverages existing architecture** (minimal new dependencies)
4. **Professional quality** (matches current codebase standards)
5. **Extensible design** (easy to add features later)

**Next Steps**:
1. Review and approve this plan
2. Create `sprint-6-workflow-orchestrator` branch
3. Start with Day 1 tasks (orchestrator core)
4. Daily progress updates and testing

**Questions or adjustments?** Let's discuss before implementation!
