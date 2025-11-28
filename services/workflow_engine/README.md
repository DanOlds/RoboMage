# Workflow Engine Service

FastAPI microservice for visual workflow orchestration in RoboMage.

## Overview

The Workflow Engine enables users to create, manage, and execute multi-step powder diffraction analysis pipelines through a drag-and-drop visual interface. Workflows are defined as directed acyclic graphs (DAGs) where nodes represent analysis operations and edges represent data flow.

## Features

- **Visual Workflow Builder**: Create workflows through drag-and-drop interface
- **DAG Execution**: Topologically sorted execution with dependency management
- **8 Node Types**: Data loading, filtering, normalization, peak analysis, statistics, and export
- **REST API**: Complete CRUD operations for workflow management
- **Async Execution**: Non-blocking workflow execution with progress tracking
- **Error Handling**: Graceful failure with partial results and detailed error messages

## Quick Start

### Start the Service

```bash
# From services/workflow_engine directory
python main.py --port 8002

# Or with auto-reload for development
python main.py --port 8002 --reload
```

### Test the Service

```bash
# Health check
curl http://localhost:8002/health

# Get available node types
curl http://localhost:8002/node-types

# View API documentation
open http://localhost:8002/docs
```

## API Endpoints

### Workflow Management

- `POST /workflows` - Create new workflow
- `GET /workflows` - List all workflows
- `GET /workflows/{id}` - Get specific workflow
- `PUT /workflows/{id}` - Update workflow
- `DELETE /workflows/{id}` - Delete workflow

### Execution

- `POST /workflows/{id}/execute` - Execute workflow
- `GET /executions/{id}` - Get execution status and results

### Metadata

- `GET /node-types` - Get available node types for UI palette
- `GET /health` - Service health check
- `GET /` - Service information

## Available Node Types

### Data Input Nodes

**load_files**: Load diffraction files from directory
- Config: `directory`, `pattern`, `wavelength` (optional)
- Outputs: `DiffractionData[]`

### Transform Nodes

**filter_q_range**: Filter data by Q-space range
- Config: `q_min`, `q_max`
- Inputs: `DiffractionData[]`
- Outputs: `DiffractionData[]`

**normalize**: Normalize intensity values
- Config: `method` (max, area, zscore)
- Inputs: `DiffractionData[]`
- Outputs: `DiffractionData[]`

### Analysis Nodes

**peak_analysis**: Detect and fit crystallographic peaks
- Config: `profile_type`, `prominence`, `distance`, `service_url`
- Inputs: `DiffractionData[]`
- Outputs: `PeakAnalysisResults[]`

**statistics**: Calculate statistical metrics
- Config: `metrics` (list of metric names)
- Inputs: `DiffractionData[]`
- Outputs: `Statistics[]`

### Output Nodes

**export_csv**: Export results to CSV file
- Config: `output_path`, `format` (peaks, statistics)
- Inputs: `Any`
- Outputs: `ExportInfo`

**export_json**: Export results to JSON file
- Config: `output_path`, `pretty`
- Inputs: `Any`
- Outputs: `ExportInfo`

**save_results**: Save results to execution context
- Config: `key`
- Inputs: `Any`
- Outputs: `Confirmation`

## Example Workflow

```json
{
  "name": "Batch Peak Analysis",
  "description": "Load files, detect peaks, and export results",
  "nodes": [
    {
      "id": "load_1",
      "type": "load_files",
      "label": "Load CHI Files",
      "config": {
        "directory": "/data/experiment",
        "pattern": "*.chi"
      },
      "position": {"x": 100, "y": 100}
    },
    {
      "id": "filter_1",
      "type": "filter_q_range",
      "label": "Filter Q-Range",
      "config": {
        "q_min": 2.0,
        "q_max": 8.0
      },
      "position": {"x": 300, "y": 100}
    },
    {
      "id": "analyze_1",
      "type": "peak_analysis",
      "label": "Detect Peaks",
      "config": {
        "profile_type": "gaussian",
        "prominence": 0.1
      },
      "position": {"x": 500, "y": 100}
    },
    {
      "id": "export_1",
      "type": "export_csv",
      "label": "Export Results",
      "config": {
        "output_path": "results/peaks.csv",
        "format": "peaks"
      },
      "position": {"x": 700, "y": 100}
    }
  ],
  "edges": [
    {"id": "e1", "source": "load_1", "target": "filter_1"},
    {"id": "e2", "source": "filter_1", "target": "analyze_1"},
    {"id": "e3", "source": "analyze_1", "target": "export_1"}
  ]
}
```

## Integration with RoboMage

### Dashboard Integration
The workflow service is accessed by the RoboMage dashboard's Workflow Builder tab, which provides a visual interface for creating and executing workflows.

### Service Dependencies
- **Peak Analysis Service** (port 8001) - Required for `peak_analysis` node
- **RoboMage Core** - Data loaders and models

### Data Flow
1. Dashboard sends workflow definition to workflow service
2. Workflow service validates and stores workflow
3. On execution, orchestrator coordinates node execution
4. Nodes call RoboMage services and data loaders
5. Results flow through workflow graph
6. Final results returned to dashboard

## Architecture

```
Workflow Service (Port 8002)
├── FastAPI Application (main.py)
├── Pydantic Models (models.py)
└── Integration Layer
    ├── WorkflowOrchestrator (src/robomage/orchestrator.py)
    └── Node Handlers (src/robomage/workflow/nodes/)
        ├── data_nodes.py
        ├── analysis_nodes.py
        └── output_nodes.py
```

## Development

### Adding New Node Types

1. **Create Node Handler** in appropriate module:
```python
# src/robomage/workflow/nodes/custom_nodes.py
async def my_custom_handler(config, inputs, context):
    # Implement node logic
    return output
```

2. **Register Handler** in `main.py`:
```python
async def register_node_handlers(orch):
    # ... existing handlers
    orch.register_node_handler("my_custom", custom_nodes.my_custom_handler)
```

3. **Add Metadata** in `get_registered_node_types()`:
```python
NodeTypeMetadata(
    type="my_custom",
    category="custom",
    name="My Custom Node",
    # ... other metadata
)
```

### Testing

```bash
# Run workflow service tests
cd /nsls2/users/dolds/dev/RoboMage
pixi run pytest tests/test_workflow_*.py -v
```

## Troubleshooting

### Service Won't Start
- Check port 8002 is not in use: `lsof -i :8002`
- Verify Python path includes project root
- Check for import errors in node handlers

### Workflow Execution Fails
- Verify all required services are running (peak analysis on 8001)
- Check workflow has no cycles (must be a DAG)
- Review node configuration parameters
- Check execution logs for specific node failures

### Node Handler Errors
- Ensure input data matches expected type
- Verify configuration parameters are valid
- Check file paths are accessible
- Review error messages in execution result

## Future Enhancements

- **Database Storage**: Replace in-memory storage with SQLite/PostgreSQL
- **Parallel Execution**: Execute independent branches in parallel
- **Conditional Logic**: Add if/else branching nodes
- **Loop Support**: Iterate over file lists
- **Sub-workflows**: Reusable workflow components
- **Version Control**: Track workflow changes over time
- **Real-time Progress**: WebSocket updates during execution

## License

Part of the RoboMage project. See main repository for license information.
