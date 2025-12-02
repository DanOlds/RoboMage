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
    """
    Register all available node type handlers with the orchestrator.
    
    Uses the NodeRegistry auto-discovery system to find and register all nodes:
    - Built-in nodes from robomage/workflow/nodes/
    - Custom nodes from robomage/workflow/nodes/custom/
    
    No manual registration needed - just add @register_node decorator to your handler!
    """
    from robomage.workflow.nodes.registry import NodeRegistry
    
    # Auto-discover and register all nodes (built-in + custom)
    NodeRegistry.discover_and_register_all()
    
    # Transfer all handlers from registry to orchestrator
    for node_type, handler in NodeRegistry.get_all_handlers().items():
        orch.register_node_handler(node_type, handler)
    
    try:
        print(f"✅ Registered {len(orch.node_handlers)} node types via NodeRegistry")
        print(f"   Node types: {', '.join(sorted(orch.node_handlers.keys()))}")
    except UnicodeEncodeError:
        print(f"Registered {len(orch.node_handlers)} node types via NodeRegistry")
        print(f"   Node types: {', '.join(sorted(orch.node_handlers.keys()))}")


def get_registered_node_types() -> list[NodeTypeMetadata]:
    """
    Return metadata for all registered node types for UI palette.
    
    Retrieves metadata from the NodeRegistry which was populated by
    @register_node decorators on handler functions.
    """
    from robomage.workflow.nodes.registry import NodeRegistry
    
    # Get metadata from registry and convert to API model
    registry_metadata = NodeRegistry.get_all_metadata()
    
    return [
        NodeTypeMetadata(
            type=meta.type,
            category=meta.category,
            name=meta.name,
            description=meta.description,
            icon=meta.icon,
            inputs=meta.inputs,
            outputs=meta.outputs,
            config_schema=meta.config_schema,
        )
        for meta in registry_metadata
    ]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage service lifecycle - startup and shutdown."""
    global orchestrator

    # Startup
    try:
        print("🚀 RoboMage Workflow Service starting...")
    except UnicodeEncodeError:
        print("RoboMage Workflow Service starting...")
    
    orchestrator = WorkflowOrchestrator()
    await register_node_handlers(orchestrator)
    
    try:
        print("✅ Workflow Service ready on port 8002")
    except UnicodeEncodeError:
        print("Workflow Service ready on port 8002")

    yield

    # Shutdown
    try:
        print("🛑 Workflow Service shutting down...")
    except UnicodeEncodeError:
        print("Workflow Service shutting down...")


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

    try:
        print(f"✅ Created workflow: {workflow.name} (ID: {workflow.id})")
    except UnicodeEncodeError:
        print(f"Created workflow: {workflow.name} (ID: {workflow.id})")
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

    try:
        print(f"✅ Updated workflow: {workflow.name} (ID: {workflow_id})")
    except UnicodeEncodeError:
        print(f"Updated workflow: {workflow.name} (ID: {workflow_id})")
    return workflow


@app.delete("/workflows/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """Delete a workflow."""
    if workflow_id not in workflows:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")

    deleted = workflows.pop(workflow_id)
    try:
        print(f"🗑️  Deleted workflow: {deleted.name} (ID: {workflow_id})")
    except UnicodeEncodeError:
        print(f"Deleted workflow: {deleted.name} (ID: {workflow_id})")
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

    try:
        print(f"🚀 Executing workflow: {workflow.name} (ID: {workflow_id})")
        if enable_inspection:
            print("🔍 Inspection mode enabled - capturing node I/O snapshots")
    except UnicodeEncodeError:
        print(f"Executing workflow: {workflow.name} (ID: {workflow_id})")
        if enable_inspection:
            print("Inspection mode enabled - capturing node I/O snapshots")

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

        try:
            status_emoji = "✅" if result.status == ExecutionStatus.COMPLETED else "❌"
            print(
                f"{status_emoji} Workflow execution {result.execution_id}: {result.status}"
            )

            # Debug: Check if node_type is in the results
            if result.node_results:
                print(f"🔍 SERVICE: Returning {len(result.node_results)} node results")
                for nr in result.node_results[:2]:  # Check first 2
                    print(
                        f"   Node {nr.node_id}: type={nr.node_type}, status={nr.status}"
                    )
        except UnicodeEncodeError:
            status_text = "SUCCESS" if result.status == ExecutionStatus.COMPLETED else "FAILED"
            print(
                f"{status_text} Workflow execution {result.execution_id}: {result.status}"
            )

            # Debug: Check if node_type is in the results
            if result.node_results:
                print(f"SERVICE: Returning {len(result.node_results)} node results")
                for nr in result.node_results[:2]:  # Check first 2
                    print(
                    f"  Node {nr.node_id}: type={getattr(nr, 'node_type', 'MISSING')}"
                )

        # If inspection was enabled, save inspection data to database
        if enable_inspection and hasattr(result, "inspections") and result.inspections:
            print(
                f"🔍 SERVICE: Captured {len(result.inspections)} inspection snapshots"
            )
            
            # Save inspection data to database for later viewing in Inspector tab
            try:
                from datetime import datetime

                from robomage.persistence.api import SessionManager
                
                mgr = SessionManager()
                for inspection_dict in result.inspections:
                    # Convert timestamp strings to datetime objects if needed
                    timestamp_in = inspection_dict.get("timestamp_in")
                    timestamp_out = inspection_dict.get("timestamp_out")
                    
                    if isinstance(timestamp_in, str):
                        timestamp_in = datetime.fromisoformat(timestamp_in)
                    if isinstance(timestamp_out, str):
                        timestamp_out = datetime.fromisoformat(timestamp_out)
                    
                    # Extract data from the inspection snapshot
                    mgr.save_inspection(
                        workflow_id=result.workflow_id,
                        node_id=inspection_dict.get("node_id", "unknown"),
                        node_type=inspection_dict.get("node_type", "unknown"),
                        input_data=inspection_dict.get("input_data"),
                        output_data=inspection_dict.get("output_data"),
                        input_shape=inspection_dict.get("input_shape"),
                        output_shape=inspection_dict.get("output_shape"),
                        timestamp_in=timestamp_in,
                        timestamp_out=timestamp_out,
                        duration_ms=inspection_dict.get("duration_ms"),
                        execution_metadata=inspection_dict.get("metadata"),
                        session_id=None,  # Not linked to a session (standalone execution)
                    )
                try:
                    print(f"💾 Saved {len(result.inspections)} inspection records to database")
                except UnicodeEncodeError:
                    print(f"Saved {len(result.inspections)} inspection records to database")
            except Exception as e:
                try:
                    print(f"⚠️ Warning: Failed to save inspection data: {e}")
                except UnicodeEncodeError:
                    print(f"Warning: Failed to save inspection data: {e}")
                import traceback
                traceback.print_exc()
                # Don't fail the request, just log the warning

        return result

    except Exception as e:
        try:
            print(f"❌ Workflow execution failed with exception: {e}")
        except UnicodeEncodeError:
            print(f"Workflow execution failed with exception: {e}")
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

    # Use safe characters for Windows console (avoid emojis that fail on cp1252)
    try:
        print(f"🌐 Starting Workflow Service on http://{args.host}:{args.port}")
        print(f"📚 API docs available at http://{args.host}:{args.port}/docs")
        print()
        print("⚠️  IMPORTANT: Some workflow nodes require additional services:")
        print(
            "   • Peak Analysis: pixi run python services/peak_analysis/main.py --port 8001"
        )
        print("   • Dashboard: pixi run python -m robomage.dashboard")
    except UnicodeEncodeError:
        # Fallback for Windows consoles with limited encoding (cp1252)
        print(f"Starting Workflow Service on http://{args.host}:{args.port}")
        print(f"API docs available at http://{args.host}:{args.port}/docs")
        print()
        print("IMPORTANT: Some workflow nodes require additional services:")
        print(
            "   - Peak Analysis: pixi run python services/peak_analysis/main.py --port 8001"
        )
        print("   - Dashboard: pixi run python -m robomage.dashboard")
    
    print()

    uvicorn.run(
        "main:app" if args.reload else app,
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
