# Migration Guide: Custom Services Architecture

**Migrating existing services to use the Service Registry pattern**

---

## Overview

This guide helps you migrate existing microservices to the new Service Registry architecture introduced in the Custom Services Plan (Phases 1-5). The registry enables:

- **Auto-discovery**: Services registered via `service.json`
- **Dynamic startup**: `pixi run start-all` starts all registered services
- **Health monitoring**: `pixi run check-services` for status checks
- **Workflow integration**: Automatic node registration
- **Dashboard integration**: Service monitoring UI

---

## What's Changed?

### Before (Hardcoded Services)

**start_services.py:**
```python
# Hardcoded service startup
peak_proc = subprocess.Popen(
    [python_exe, "services/peak_analysis/main.py", "--port", "8001"]
)
workflow_proc = subprocess.Popen(
    [python_exe, "services/workflow_engine/main.py", "--port", "8002"]
)
```

**Dashboard callbacks:**
```python
# Hardcoded URLs
PEAK_SERVICE_URL = "http://localhost:8001"
response = requests.post(f"{PEAK_SERVICE_URL}/analyze", ...)
```

### After (Registry-Driven)

**start_services.py:**
```python
from robomage.service_registry import get_registry

registry = get_registry()
for service in registry.get_auto_start_services():
    cmd = service.format_startup_command()
    proc = subprocess.Popen(cmd.split())
```

**Dashboard callbacks:**
```python
from robomage.service_registry import get_registry
from robomage.clients.base_service_client import BaseServiceClient

registry = get_registry()
service = registry.get_service("peak_analysis")
client = BaseServiceClient(service_metadata=service)
response = client.post("/analyze", json={...})
```

---

## Migration Steps

### Step 1: Create service.json

Every service needs a `service.json` metadata file in its directory.

**Template:**
```json
{
  "name": "your_service",
  "display_name": "Your Service Name",
  "description": "Service description",
  "version": "1.0.0",
  "service_type": "analysis",
  "port": 8001,
  "host": "127.0.0.1",
  "endpoints": {
    "health": "/health",
    "root": "/",
    "docs": "/docs"
  },
  "health_check_interval": 5000,
  "startup_timeout": 30,
  "dependencies": {
    "python": ">=3.10",
    "packages": [
      "fastapi",
      "uvicorn",
      "pydantic>=2.0"
    ]
  },
  "workflow_integration": {
    "enabled": true,
    "node_types": ["your_node_type"]
  },
  "dashboard_integration": {
    "enabled": true,
    "tab_name": null,
    "status_indicator": true,
    "icon": "fas fa-calculator"
  },
  "client_class": null,
  "startup_command": "python services/your_service/main.py --port {port} --host {host}"
}
```

**Field Descriptions:**

- `name`: **Required**. Service identifier (snake_case, unique, lowercase)
- `display_name`: **Required**. Human-readable name
- `description`: **Required**. Brief description of service
- `version`: Service version (semantic versioning)
- `service_type`: Category (analysis/transform/filter/export)
- `port`: **Required**. Port number (8000-9000 range recommended)
- `host`: Host to bind to (127.0.0.1 for local)
- `endpoints`: API endpoint paths
- `health_check_interval`: Milliseconds between health checks
- `startup_timeout`: Seconds to wait for service startup
- `dependencies.python`: Minimum Python version
- `dependencies.packages`: Python package dependencies
- `workflow_integration.enabled`: Enable as workflow node
- `workflow_integration.node_types`: Node type identifiers
- `dashboard_integration.enabled`: Show in dashboard
- `dashboard_integration.tab_name`: Optional dedicated tab
- `client_class`: Optional custom client class path
- `startup_command`: Command to start service (use {port} and {host} placeholders)

### Step 2: Update service main.py

Ensure your service follows the standard pattern:

**Required endpoints:**
```python
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "your_service", "version": "1.0.0"}

@app.get("/")
async def root():
    """Service information."""
    return {
        "service": "Your Service",
        "version": "1.0.0",
        "endpoints": {...}
    }
```

**CORS middleware** (for dashboard integration):
```python
from fastapi.middleware.cors import CORSMiddleware

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
```

**Argument parsing:**
```python
def main():
    parser = argparse.ArgumentParser(description="Your Service")
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--host", type=str, default="127.0.0.1")
    args = parser.parse_args()
    
    uvicorn.run("main:app", host=args.host, port=args.port)
```

### Step 3: Register Service

The service registry auto-discovers services with `service.json` files in `services/` subdirectories.

**Manual registration (optional):**
```python
from robomage.service_registry import get_registry

registry = get_registry()
registry.reload()  # Force re-discovery
registry.save_registry()  # Save to services/registry.json
```

**Verify registration:**
```bash
pixi run list-services
# Should show your service
```

### Step 4: Update Dashboard Integration

**Before (hardcoded):**
```python
# In dashboard callbacks
import requests

PEAK_SERVICE_URL = "http://localhost:8001"

@callback(...)
def analyze(...):
    response = requests.post(f"{PEAK_SERVICE_URL}/analyze", json={...})
    return response.json()
```

**After (registry-driven):**
```python
from robomage.service_registry import get_registry
from robomage.clients.base_service_client import BaseServiceClient

@callback(...)
def analyze(...):
    registry = get_registry()
    service = registry.get_service("peak_analysis")
    
    client = BaseServiceClient(service_metadata=service)
    response = client.post("/analyze", json={...})
    return response
```

**Benefits:**
- ✅ Automatic URL discovery
- ✅ Built-in retry logic
- ✅ Health checking
- ✅ Error handling

### Step 5: Update Workflow Integration

**Service node handler:**

If your service should be available as a workflow node, ensure:

1. `workflow_integration.enabled = true` in `service.json`
2. `node_types` lists the workflow node categories
3. Service implements standard request/response pattern

The workflow engine will automatically discover and register service nodes.

**Verify:**
```python
from robomage.workflow.nodes.registry import NodeRegistry

registry = NodeRegistry()
registry.discover_and_register_all()

# Check if your service node is registered
node_types = registry.get_node_types()
print(node_types)  # Should include your service node types
```

### Step 6: Update startup scripts

**Before:**
```bash
# Manual service startup
python services/peak_analysis/main.py --port 8001 &
python services/workflow_engine/main.py --port 8002 &
python -m robomage --dashboard
```

**After:**
```bash
# Registry-driven startup
pixi run start-all
# Starts all auto-start services + dashboard
```

**Custom startup (if needed):**
```python
from robomage.service_registry import get_registry

registry = get_registry()
service = registry.get_service("your_service")

# Start with custom parameters
import subprocess
cmd = service.format_startup_command()
proc = subprocess.Popen(cmd.split())
```

---

## Example Migration: Peak Analysis Service

### Before Migration

**services/peak_analysis/main.py:**
```python
# No service.json file
# Hardcoded port
# No health endpoint

app = FastAPI()

@app.post("/analyze")
def analyze(...):
    ...

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)
```

**start_services.py:**
```python
peak_proc = subprocess.Popen([
    "python", "services/peak_analysis/main.py"
])
```

### After Migration

**services/peak_analysis/service.json:**
```json
{
  "name": "peak_analysis",
  "display_name": "Peak Analysis Service",
  "description": "Automated peak detection and fitting",
  "version": "1.0.0",
  "service_type": "analysis",
  "port": 8001,
  "host": "127.0.0.1",
  "endpoints": {
    "health": "/health",
    "analyze": "/analyze"
  },
  "workflow_integration": {
    "enabled": true,
    "node_types": ["peak_detection", "peak_analysis"]
  },
  "dashboard_integration": {
    "enabled": true,
    "tab_name": "Analysis"
  },
  "startup_command": "python services/peak_analysis/main.py --port {port}"
}
```

**services/peak_analysis/main.py:**
```python
import argparse
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS for dashboard
app.add_middleware(CORSMiddleware, ...)

@app.get("/health")
def health():
    return {"status": "healthy", "service": "peak_analysis"}

@app.post("/analyze")
def analyze(...):
    ...

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--host", type=str, default="127.0.0.1")
    args = parser.parse_args()
    
    uvicorn.run("main:app", host=args.host, port=args.port)

if __name__ == "__main__":
    main()
```

**start_services.py:**
```python
from robomage.service_registry import get_registry

registry = get_registry()
for service in registry.get_auto_start_services():
    proc = subprocess.Popen(service.format_startup_command().split())
```

---

## Testing Your Migration

### 1. Verify Service Discovery

```bash
pixi run list-services
# Expected output:
# Registered Services:
#   - Peak Analysis Service (peak_analysis) on port 8001
#   - Your Service (your_service) on port XXXX
```

### 2. Test Service Startup

```bash
pixi run start-all
# Should start all services automatically
```

### 3. Check Health Status

```bash
pixi run check-services
# Expected output:
# Service Health:
#   ✅ Peak Analysis Service (http://127.0.0.1:8001)
#   ✅ Your Service (http://127.0.0.1:XXXX)
```

### 4. Test from Dashboard

1. Start dashboard: `pixi run dashboard`
2. Navigate to Analysis tab
3. Verify service appears in UI
4. Test analysis request
5. Check service status indicator

### 5. Test Workflow Integration

```python
from robomage.orchestrator import WorkflowOrchestrator

workflow = {
    "nodes": [
        {"id": "test", "type": "your_service", "config": {...}}
    ]
}

orchestrator = WorkflowOrchestrator()
results = await orchestrator.execute_workflow(workflow)
```

---

## Common Issues & Solutions

### Issue: Service not discovered

**Symptom:** Service doesn't appear in `pixi run list-services`

**Solutions:**
1. Check `service.json` exists in service directory
2. Verify JSON is valid: `python -m json.tool services/your_service/service.json`
3. Ensure service directory is in `services/` (not nested deeper)
4. Force reload: `python -c "from robomage.service_registry import get_registry; get_registry().reload()"`

### Issue: Port conflict

**Symptom:** `ServiceValidationError: Port 8001 already in use`

**Solutions:**
1. Check existing services: `pixi run list-services`
2. Choose different port (8000-9000 range)
3. Update `port` in `service.json`

### Issue: Service won't start

**Symptom:** `pixi run start-all` fails to start service

**Solutions:**
1. Test manually: `python services/your_service/main.py --port XXXX`
2. Check startup_command in `service.json`
3. Verify dependencies installed: `pip install -r services/your_service/requirements.txt`
4. Check logs for errors

### Issue: Dashboard can't connect

**Symptom:** Dashboard shows service as unavailable

**Solutions:**
1. Verify service is running: `pixi run check-services`
2. Test health endpoint: `curl http://localhost:XXXX/health`
3. Check CORS middleware configured
4. Verify `dashboard_integration.enabled = true`

### Issue: Workflow node not found

**Symptom:** Workflow engine can't find service node

**Solutions:**
1. Check `workflow_integration.enabled = true`
2. Verify `node_types` contains correct identifiers
3. Restart workflow engine
4. Check node registration: 
   ```python
   from robomage.workflow.nodes.registry import NodeRegistry
   NodeRegistry().discover_and_register_all()
   ```

---

## Backward Compatibility

The new registry system is **fully backward compatible**:

- Services without `service.json` still work (manual startup required)
- Hardcoded URLs still work (but not recommended)
- Existing client code doesn't break

**Migration is optional but recommended** for:
- Auto-discovery and centralized management
- Health monitoring and service status
- Workflow integration
- Dashboard integration
- Future extensibility

---

## Best Practices

### 1. Service Naming

- Use **snake_case** for `name` field
- Keep names **descriptive** but concise
- Avoid special characters
- Examples: `peak_analysis`, `background_subtraction`, `unit_cell_calculator`

### 2. Port Assignment

- Use ports **8000-9000** range
- Dashboard uses **8050** (avoid)
- Assign sequential ports for related services
- Document port in README

### 3. Health Endpoints

- Always implement `/health`
- Return minimal JSON: `{"status": "healthy"}`
- Include service name and version
- Keep response time <100ms

### 4. Startup Commands

- Use **placeholders**: `{port}`, `{host}`
- Test command manually before adding to config
- Include all required arguments
- Use absolute paths if needed

### 5. Error Handling

- Use FastAPI's `HTTPException` for errors
- Return informative error messages
- Log errors for debugging
- Don't expose sensitive information

### 6. Documentation

- Update service README with registry info
- Document new endpoint patterns
- Link to this migration guide
- Update examples to use registry

---

## Migration Checklist

Use this checklist to track your migration:

- [ ] Create `service.json` with all required fields
- [ ] Add `/health` endpoint to service
- [ ] Configure CORS middleware
- [ ] Add argument parsing (--port, --host)
- [ ] Test service startup manually
- [ ] Verify service discovery: `pixi run list-services`
- [ ] Update dashboard callbacks to use registry
- [ ] Update workflow integration (if applicable)
- [ ] Test with `pixi run start-all`
- [ ] Check health status: `pixi run check-services`
- [ ] Test end-to-end from dashboard
- [ ] Update service documentation
- [ ] Run integration tests
- [ ] Clean up old hardcoded references

---

## Getting Help

**Documentation:**
- **Service Registry**: `src/robomage/service_registry/`
- **Custom Services Guide**: `docs/CUSTOM-SERVICES-GUIDE.md`
- **Phase Completion Docs**: `docs/PHASE-*-COMPLETE.md`

**Testing:**
- **Unit Tests**: `tests/test_service_registry.py`
- **Integration Tests**: `tests/test_custom_services_integration.py`
- **Example Services**: `services/peak_analysis/`, `services/workflow_engine/`

**Commands:**
```bash
pixi run list-services     # List all registered services
pixi run check-services    # Check service health
pixi run test-services     # Run service tests
pixi run start-all         # Start all services
```

---

## Summary

Migrating to the Service Registry:

1. **Add `service.json`** with metadata
2. **Implement `/health`** endpoint
3. **Configure CORS** for dashboard
4. **Update startup** to use registry
5. **Test thoroughly** with pixi commands

**Benefits:**
- ✅ Auto-discovery and centralized management
- ✅ Built-in health monitoring
- ✅ Automatic workflow/dashboard integration
- ✅ Simplified deployment
- ✅ Future-proof extensibility

**Questions?** See `docs/CUSTOM-SERVICES-GUIDE.md` for detailed examples.

---

*Last updated: December 2025 | Custom Services Plan Phase 5*
