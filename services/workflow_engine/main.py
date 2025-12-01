"""
FastAPI Workflow Service

REST API microservice for workflow management and execution in RoboMage.
Provides endpoints for creating, storing, and executing visual workflow definitions.

Architecture:
    - FastAPI framework with automatic OpenAPI documentation
    - Pydantic models for request/response validation
    - Integration with WorkflowOrchestrator for execution
    - In-memory storage for MVP (upgrade to database in Phase 2)
    - CORS enabled for dashboard integration

Endpoints:
    GET  /              - Service information
    GET  /health        - Health check
    POST /workflows     - Create new workflow
    GET  /workflows     - List all workflows
    GET  /workflows/{id} - Get specific workflow
    PUT  /workflows/{id} - Update workflow
    DELETE /workflows/{id} - Delete workflow
    POST /workflows/{id}/execute - Execute workflow
    GET  /executions/{id} - Get execution status
    GET  /node-types    - Get available node types

Usage:
    # Start service
    python main.py --port 8002 --host 0.0.0.0

    # Or with uvicorn directly
    uvicorn main:app --host 0.0.0.0 --port 8002 --reload

Integration:
    - Called by dashboard Workflow tab
    - Uses WorkflowOrchestrator from src/robomage/orchestrator.py
    - Registers node handlers from src/robomage/workflow/nodes/
"""

import argparse
import sys
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from services.workflow_engine.models import (
    ExecutionStatus,
    NodeTypeMetadata,
    WorkflowDefinition,
    WorkflowExecutionResult,
)
from src.robomage.orchestrator import WorkflowOrchestrator

# Global state (in-memory for MVP)
workflows: dict[str, WorkflowDefinition] = {}
executions: dict[str, WorkflowExecutionResult] = {}
orchestrator: WorkflowOrchestrator | None = None


async def register_node_handlers(orch: WorkflowOrchestrator) -> None:
    """Register all available node type handlers with the orchestrator."""
    from src.robomage.workflow.nodes import analysis_nodes, data_nodes, output_nodes

    # Data input/transform nodes
    orch.register_node_handler("load_files", data_nodes.load_files_handler)
    orch.register_node_handler("filter_q_range", data_nodes.filter_q_range_handler)
    orch.register_node_handler("normalize", data_nodes.normalize_handler)

    # Analysis nodes
    orch.register_node_handler("peak_analysis", analysis_nodes.peak_analysis_handler)
    orch.register_node_handler("statistics", analysis_nodes.statistics_handler)

    # Output nodes
    orch.register_node_handler("export_csv", output_nodes.export_csv_handler)
    orch.register_node_handler("export_json", output_nodes.export_json_handler)
    orch.register_node_handler("save_results", output_nodes.save_results_handler)
    orch.register_node_handler("save_to_session", output_nodes.save_to_session_handler)

    print(f"✅ Registered {len(orch.node_handlers)} node types")


def get_registered_node_types() -> list[NodeTypeMetadata]:
    """Return metadata for all registered node types for UI palette."""
    return [
        # Data Input Nodes
        NodeTypeMetadata(
            type="load_files",
            category="data",
            name="Load Files",
            description="Load diffraction files from directory",
            icon="fas fa-folder-open",
            inputs=[],
            outputs=[{"name": "output", "type": "DiffractionData[]"}],
            config_schema={
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "default": "."},
                    "pattern": {"type": "string", "default": "*.chi"},
                    "wavelength": {
                        "type": "number",
                        "description": "Optional wavelength override",
                    },
                },
                "required": ["directory", "pattern"],
            },
        ),
        # Transform Nodes
        NodeTypeMetadata(
            type="filter_q_range",
            category="transform",
            name="Filter Q-Range",
            description="Filter data by Q-space range",
            icon="fas fa-filter",
            inputs=[{"name": "input", "type": "DiffractionData[]"}],
            outputs=[{"name": "output", "type": "DiffractionData[]"}],
            config_schema={
                "type": "object",
                "properties": {
                    "q_min": {"type": "number", "default": 0},
                    "q_max": {"type": "number", "default": 20},
                },
            },
        ),
        NodeTypeMetadata(
            type="normalize",
            category="transform",
            name="Normalize",
            description="Normalize intensity values",
            icon="fas fa-balance-scale",
            inputs=[{"name": "input", "type": "DiffractionData[]"}],
            outputs=[{"name": "output", "type": "DiffractionData[]"}],
            config_schema={
                "type": "object",
                "properties": {
                    "method": {
                        "type": "string",
                        "enum": ["max", "area", "zscore"],
                        "default": "max",
                    }
                },
            },
        ),
        # Analysis Nodes
        NodeTypeMetadata(
            type="peak_analysis",
            category="analysis",
            name="Peak Detection",
            description="Detect and fit crystallographic peaks",
            icon="fas fa-mountain",
            inputs=[{"name": "input", "type": "DiffractionData[]"}],
            outputs=[{"name": "output", "type": "PeakAnalysisResults[]"}],
            config_schema={
                "type": "object",
                "properties": {
                    "profile_type": {
                        "type": "string",
                        "enum": ["gaussian", "lorentzian", "voigt"],
                        "default": "gaussian",
                    },
                    "prominence": {"type": "number", "default": 0.1},
                    "distance": {"type": "number", "default": 5},
                    "service_url": {
                        "type": "string",
                        "default": "http://localhost:8001",
                    },
                },
            },
        ),
        NodeTypeMetadata(
            type="statistics",
            category="analysis",
            name="Statistics",
            description="Calculate statistical metrics",
            icon="fas fa-chart-bar",
            inputs=[{"name": "input", "type": "DiffractionData[]"}],
            outputs=[{"name": "output", "type": "Statistics[]"}],
            config_schema={
                "type": "object",
                "properties": {
                    "metrics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "default": ["mean", "std", "range"],
                    }
                },
            },
        ),
        # Output Nodes
        NodeTypeMetadata(
            type="export_csv",
            category="output",
            name="Export CSV",
            description="Export results to CSV file",
            icon="fas fa-file-csv",
            inputs=[{"name": "input", "type": "Any"}],
            outputs=[{"name": "output", "type": "ExportInfo"}],
            config_schema={
                "type": "object",
                "properties": {
                    "output_path": {"type": "string", "default": "results.csv"},
                    "format": {
                        "type": "string",
                        "enum": ["peaks", "statistics"],
                        "default": "peaks",
                    },
                },
                "required": ["output_path"],
            },
        ),
        NodeTypeMetadata(
            type="export_json",
            category="output",
            name="Export JSON",
            description="Export results to JSON file",
            icon="fas fa-file-code",
            inputs=[{"name": "input", "type": "Any"}],
            outputs=[{"name": "output", "type": "ExportInfo"}],
            config_schema={
                "type": "object",
                "properties": {
                    "output_path": {"type": "string", "default": "results.json"},
                    "pretty": {"type": "boolean", "default": True},
                },
                "required": ["output_path"],
            },
        ),
    ]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage service lifecycle - startup and shutdown."""
    global orchestrator

    # Startup
    print("🚀 RoboMage Workflow Service starting...")
    orchestrator = WorkflowOrchestrator()
    await register_node_handlers(orchestrator)
    print("✅ Workflow Service ready on port 8002")

    yield

    # Shutdown
    print("🛑 Workflow Service shutting down...")


# Create FastAPI application
app = FastAPI(
    title="RoboMage Workflow Service",
    description="Visual workflow orchestration for powder diffraction analysis",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for dashboard integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8050",
        "http://127.0.0.1:8050",
        "http://localhost:8051",
        "http://127.0.0.1:8051",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Service information and available endpoints."""
    return {
        "service": "RoboMage Workflow Service",
        "version": "1.0.0",
        "description": "Visual workflow orchestration for diffraction analysis",
        "endpoints": {
            "workflows": "GET/POST /workflows - Manage workflow definitions",
            "execute": "POST /workflows/{id}/execute - Execute workflow",
            "executions": "GET /executions/{id} - Get execution status",
            "node_types": "GET /node-types - Available node types for UI",
            "health": "GET /health - Service health check",
        },
        "status": "healthy",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "workflows_count": len(workflows),
        "executions_count": len(executions),
        "node_types_registered": len(orchestrator.node_handlers) if orchestrator else 0,
    }


@app.post("/workflows", response_model=WorkflowDefinition)
async def create_workflow(workflow: WorkflowDefinition):
    """
    Create a new workflow definition.

    Args:
        workflow: WorkflowDefinition with nodes and edges

    Returns:
        Created workflow with assigned ID and timestamps
    """
    # Assign ID and timestamps
    workflow.id = str(uuid.uuid4())
    workflow.created_at = datetime.now()
    workflow.updated_at = datetime.now()

    # Store workflow
    workflows[workflow.id] = workflow

    print(f"✅ Created workflow: {workflow.name} (ID: {workflow.id})")
    return workflow


@app.get("/workflows", response_model=list[WorkflowDefinition])
async def list_workflows():
    """List all saved workflows."""
    return list(workflows.values())


@app.get("/workflows/{workflow_id}", response_model=WorkflowDefinition)
async def get_workflow(workflow_id: str):
    """Get a specific workflow by ID."""
    if workflow_id not in workflows:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
    return workflows[workflow_id]


@app.put("/workflows/{workflow_id}", response_model=WorkflowDefinition)
async def update_workflow(workflow_id: str, workflow: WorkflowDefinition):
    """Update an existing workflow."""
    if workflow_id not in workflows:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")

    # Preserve ID and created timestamp
    workflow.id = workflow_id
    workflow.created_at = workflows[workflow_id].created_at
    workflow.updated_at = datetime.now()

    workflows[workflow_id] = workflow

    print(f"✅ Updated workflow: {workflow.name} (ID: {workflow_id})")
    return workflow


@app.delete("/workflows/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """Delete a workflow."""
    if workflow_id not in workflows:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")

    deleted = workflows.pop(workflow_id)
    print(f"🗑️  Deleted workflow: {deleted.name} (ID: {workflow_id})")
    return {"status": "deleted", "workflow_id": workflow_id}


@app.post("/workflows/{workflow_id}/execute", response_model=WorkflowExecutionResult)
async def execute_workflow(
    workflow_id: str, context: dict | None = None, enable_inspection: bool = False
):
    """
    Execute a workflow.

    Args:
        workflow_id: ID of workflow to execute
        context: Optional initial context/configuration
        enable_inspection: Enable node I/O inspection for debugging

    Returns:
        WorkflowExecutionResult with status and outputs
    """
    if workflow_id not in workflows:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")

    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    workflow = workflows[workflow_id]

    print(f"🚀 Executing workflow: {workflow.name} (ID: {workflow_id})")
    if enable_inspection:
        print("🔍 Inspection mode enabled - capturing node I/O snapshots")

    try:
        # Execute using orchestrator with full output storage for session persistence
        result = await orchestrator.execute_workflow(
            workflow,
            context,
            store_full_outputs=True,
            enable_inspection=enable_inspection,
        )

        # Store execution result
        executions[result.execution_id] = result

        status_emoji = "✅" if result.status == ExecutionStatus.COMPLETED else "❌"
        print(
            f"{status_emoji} Workflow execution {result.execution_id}: {result.status}"
        )

        # Debug: Check if node_type is in the results
        if result.node_results:
            print(f"🔍 SERVICE: Returning {len(result.node_results)} node results")
            for nr in result.node_results[:2]:  # Check first 2
                print(
                    f"  Node {nr.node_id}: type={getattr(nr, 'node_type', 'MISSING')}"
                )

        # If inspection was enabled, include inspection data in response
        if enable_inspection and hasattr(result, "inspections"):
            print(
                f"🔍 SERVICE: Captured {len(result.inspections)} inspection snapshots"
            )

        return result

    except Exception as e:
        print(f"❌ Workflow execution failed with exception: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"Workflow execution error: {str(e)}"
        )


@app.get("/executions/{execution_id}", response_model=WorkflowExecutionResult)
async def get_execution(execution_id: str):
    """Get execution status and results."""
    if execution_id not in executions:
        raise HTTPException(
            status_code=404, detail=f"Execution {execution_id} not found"
        )
    return executions[execution_id]


@app.get("/node-types", response_model=list[NodeTypeMetadata])
async def get_node_types():
    """Get available node types for UI palette."""
    return get_registered_node_types()


def main():
    """CLI entry point for running the service."""
    parser = argparse.ArgumentParser(description="RoboMage Workflow Service")
    parser.add_argument("--host", default="127.0.0.1", help="Host address")
    parser.add_argument("--port", type=int, default=8002, help="Port number")
    parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload for development"
    )

    args = parser.parse_args()

    print(f"🌐 Starting Workflow Service on http://{args.host}:{args.port}")
    print(f"📚 API docs available at http://{args.host}:{args.port}/docs")
    print()
    print("⚠️  IMPORTANT: Some workflow nodes require additional services:")
    print(
        "   • Peak Analysis: pixi run python services/peak_analysis/main.py --port 8001"
    )
    print("   • Dashboard: pixi run python -m robomage.dashboard")
    print()

    uvicorn.run(
        "main:app" if args.reload else app,
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
