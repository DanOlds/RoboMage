# RoboMage Service Template

This template provides a starting point for creating custom analysis services
that integrate seamlessly with the RoboMage framework.

## Quick Start

### Using the Template Generator

```bash
# From the RoboMage root directory
python create_service.py

# Follow the prompts:
#   Service name: my_analysis
#   Display name: My Analysis Service
#   Description: Custom analysis for my data
#   Port: 8003
#   Node types: my_node,another_node
```

### Manual Setup

1. **Copy this template directory:**
   ```bash
   cp -r services/service_template services/my_service
   cd services/my_service
   ```

2. **Customize the files:**
   - `service.json` - Update service metadata
   - `main.py` - Implement your analysis logic
   - `models.py` - Define request/response models
   - `requirements.txt` - Add dependencies

3. **Register in the service registry:**
   ```json
   // services/registry.json
   {
       "services": [
           {
               "id": "my_service",
               "path": "services/my_service",
               "enabled": true,
               "auto_start": true
           }
       ]
   }
   ```

4. **Test your service:**
   ```bash
   python main.py --port 8003
   # In another terminal:
   curl http://localhost:8003/health
   ```

## Template Structure

```
service_template/
├── README.md              # This file
├── service.json          # Service metadata (REQUIRED)
├── main.py               # FastAPI service implementation
├── models.py             # Pydantic request/response models
├── requirements.txt      # Python dependencies
├── analysis.py           # Your analysis logic (example)
└── tests/
    └── test_service.py   # Unit tests
```

## Customization Guide

### 1. Service Metadata (`service.json`)

```json
{
    "name": "my_service",
    "display_name": "My Analysis Service",
    "description": "Description of what your service does",
    "version": "1.0.0",
    "service_type": "analysis",
    "port": 8003,
    "host": "127.0.0.1",
    "endpoints": {
        "health": "/health",
        "root": "/",
        "docs": "/docs",
        "analyze": "/analyze"
    },
    "workflow_integration": {
        "enabled": true,
        "node_types": ["my_node"]
    },
    "dashboard_integration": {
        "enabled": true,
        "tab_name": null,
        "status_indicator": true,
        "icon": "fas fa-calculator"
    },
    "client_class": null,
    "startup_command": "python services/my_service/main.py --port {port} --host {host}"
}
```

### 2. Service Implementation (`main.py`)

Key points:
- Use FastAPI for REST API
- Implement `/health` endpoint
- Implement your analysis endpoints
- Use Pydantic models for validation
- Enable CORS for dashboard integration

### 3. Request/Response Models (`models.py`)

Define clear data contracts:
```python
from pydantic import BaseModel

class AnalysisRequest(BaseModel):
    data: dict
    config: dict

class AnalysisResponse(BaseModel):
    results: dict
    status: str
```

### 4. Analysis Logic (`analysis.py`)

Separate your scientific code from the API:
```python
def perform_analysis(data, config):
    # Your analysis implementation
    return results
```

## Integration

Once your service is registered:

1. **Dashboard** - Auto-discovered and monitored
2. **Workflows** - Nodes automatically available
3. **CLI** - Can be called via service clients

## Examples

See the `examples/` directory for complete working examples:
- Background subtraction service
- Unit cell calculator service
- Peak width analysis service

## Testing

```bash
# Unit tests
pytest tests/

# Integration test
python main.py --port 8003 &
curl http://localhost:8003/health
```

## Best Practices

1. **Validation** - Use Pydantic models for all inputs/outputs
2. **Error Handling** - Return clear error messages
3. **Documentation** - Add docstrings and OpenAPI docs
4. **Testing** - Write unit tests for analysis logic
5. **Logging** - Use Python logging for debugging
6. **Performance** - Consider async/await for I/O operations

## Support

See the main documentation:
- `docs/CUSTOM-SERVICES-GUIDE.md` - Complete guide
- `docs/CUSTOM-SERVICES-PLAN.md` - Architecture overview
- `docs/node-development-guide.md` - Workflow node development
