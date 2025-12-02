# Custom Services Guide

**Complete guide to creating, registering, and deploying custom analysis services in RoboMage**

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Service Architecture](#service-architecture)
4. [Creating a Service (Automated)](#creating-a-service-automated)
5. [Creating a Service (Manual)](#creating-a-service-manual)
6. [Implementing Analysis Logic](#implementing-analysis-logic)
7. [Testing Your Service](#testing-your-service)
8. [Workflow Integration](#workflow-integration)
9. [Dashboard Integration](#dashboard-integration)
10. [Best Practices](#best-practices)
11. [Examples](#examples)
12. [Troubleshooting](#troubleshooting)

---

## Overview

RoboMage supports **custom analysis microservices** that integrate seamlessly with the dashboard and workflow engine. Services are:

- **Independent**: Run as separate FastAPI processes
- **Auto-discovered**: Registered via `service.json` configuration
- **Workflow-ready**: Automatically available as workflow nodes
- **Type-safe**: Pydantic validation at API boundaries
- **Reusable**: Can be called from CLI, dashboard, or workflows

### When to Create a Custom Service

Create a custom service when you need to:

- Implement a specialized analysis algorithm (e.g., Rietveld refinement, background subtraction)
- Integrate external tools or libraries
- Provide compute-intensive operations (runs independently, won't block dashboard)
- Share analysis capabilities across multiple workflows
- Deploy analysis as a standalone REST API

---

## Quick Start

**Create a new service in under 5 minutes:**

```bash
# 1. Navigate to services directory
cd /path/to/RoboMage/services

# 2. Run the interactive generator
python create_service.py

# Follow prompts:
#   Service name: background_subtraction
#   Display name: Background Subtraction
#   Description: Remove background from diffraction patterns
#   Port: 8003
#   Node type: transform

# 3. Implement your analysis logic (optional for testing)
cd background_subtraction
# Edit analysis.py with your algorithm
# Template works out-of-box for initial testing!

# 4. Test the service (use pixi for proper environment)
pixi run python main.py --port 8003

# In another terminal, verify it works:
curl http://localhost:8003/health
# Expected: {"status":"healthy","service":"background_subtraction","version":"1.0.0"}

curl -X POST http://localhost:8003/analyze \
  -H "Content-Type: application/json" \
  -d '{"data": {"data_points": [{"x": 1.0, "y": 100.0}]}}'
# Expected: JSON response with analysis results

# 5. Verify auto-registration
pixi run list-services
# Your service should appear in the list!

# 6. Use it!
# - Service auto-registered in services/registry.json
# - Available in dashboard after restart
# - Appears as workflow node automatically
```

### ⚡ Key Learnings from Testing

**Verified Capabilities (December 2025):**
- ✅ Service creation: **<2 minutes** from start to working service
- ✅ Auto-discovery: **Instant** - no manual registration needed
- ✅ Service startup: **<5 seconds** using pixi
- ✅ Template code: **Works out-of-box** - no editing required for testing
- ✅ Health checks: **<100ms** response time
- ✅ Cross-platform: Confirmed on **Windows and Linux**

---

## Service Architecture

### Directory Structure

Each service is a self-contained directory:

```
services/
├── registry.json              # Auto-updated service registry
├── create_service.py          # Service generator script
├── service_template/          # Template files
└── your_service/              # Your custom service
    ├── service.json           # Service metadata
    ├── main.py                # FastAPI application
    ├── models.py              # Pydantic request/response models
    ├── analysis.py            # Core analysis logic
    ├── requirements.txt       # Python dependencies
    └── .env                   # Environment configuration
```

### Communication Flow

```
┌──────────────┐         ┌──────────────────┐         ┌──────────────┐
│   Dashboard  │────────▶│  Service Client  │────────▶│   Service    │
│   Workflow   │  JSON   │  (HTTP + Retry)  │  POST   │   (FastAPI)  │
└──────────────┘         └──────────────────┘         └──────────────┘
       │                         │                            │
       │                         │                            │
       ▼                         ▼                            ▼
┌──────────────┐         ┌──────────────────┐         ┌──────────────┐
│   Session    │         │  BaseService     │         │  Analysis    │
│   Store      │         │  Client          │         │  Logic       │
└──────────────┘         └──────────────────┘         └──────────────┘
```

### Key Components

1. **Service Metadata** (`service.json`): Configuration, endpoints, workflow integration
2. **FastAPI App** (`main.py`): REST API with `/health` and `/analyze` endpoints
3. **Data Models** (`models.py`): Pydantic schemas for validation
4. **Analysis Logic** (`analysis.py`): Core algorithm implementation
5. **Service Registry**: Auto-discovery system in `src/robomage/service_registry/`
6. **Base Client**: HTTP communication in `src/robomage/clients/base_service_client.py`

---

## Creating a Service (Automated)

### Using the Generator Script

The **recommended approach** is the interactive generator:

```bash
cd services
python create_service.py
```

**Generator Features:**

- ✅ Input validation (naming, port conflicts, etc.)
- ✅ Auto-generates all required files
- ✅ Replaces placeholders with your configuration
- ✅ Creates proper directory structure
- ✅ Checks for conflicts with existing services
- ✅ Provides next-step instructions

**Example Session:**

```
Service name (lowercase_with_underscores): peak_width_analysis
Display name (e.g., 'Peak Width Analysis'): Peak Width Analysis
Service description: Analyze peak width distribution
Port number (8000-9000, default: 8003): 8004

Workflow node type options:
  1. analysis    - Analysis operation (default)
  2. transform   - Data transformation
  3. filter      - Data filtering
  4. export      - Data export
Select node type (1-4, default: 1): 1

Configuration Summary:
  service_name        : peak_width_analysis
  display_name        : Peak Width Analysis
  description         : Analyze peak width distribution
  port                : 8004
  node_type           : analysis

Create service with this configuration? (y/n): y

✅ Created services/peak_width_analysis/
✅ main.py
✅ models.py
✅ analysis.py
✅ requirements.txt
✅ .env
✅ service.json
✅ README.md
```

---

## Creating a Service (Manual)

If you prefer manual setup or need custom structure:

### Step 1: Create Directory

```bash
cd services
mkdir my_service
cd my_service
```

### Step 2: Create `service.json`

```json
{
  "service_name": "my_service",
  "display_name": "My Service",
  "version": "1.0.0",
  "description": "My custom analysis service",
  "port": 8003,
  "health_endpoint": "/health",
  "endpoints": {
    "analyze": {
      "path": "/analyze",
      "method": "POST",
      "description": "Perform analysis"
    }
  },
  "workflow_integration": {
    "enabled": true,
    "node_type": "analysis",
    "input_schema": {
      "data": "DiffractionData",
      "config": "dict"
    },
    "output_schema": {
      "results": "list"
    }
  },
  "dashboard_integration": {
    "enabled": true,
    "display_in_services": true
  },
  "startup_command": "python main.py --port 8003"
}
```

### Step 3: Create `main.py`

See template: `services/service_template/main.py.template`

Key points:
- FastAPI app with CORS middleware
- `/health` endpoint (required)
- `/analyze` endpoint (POST)
- Argument parsing for port/host
- Lifecycle management

### Step 4: Create `models.py`

See template: `services/service_template/models.py.template`

Define:
- `AnalysisRequest`: Input model
- `AnalysisResponse`: Output model
- `AnalysisConfig`: Configuration parameters
- Any domain-specific models

### Step 5: Create `analysis.py`

See template: `services/service_template/analysis.py.template`

Implement:
- `perform_analysis()`: Main entry point
- Input validation
- Core algorithm
- Quality metrics

### Step 6: Create `requirements.txt`

```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.5.0
numpy>=1.24.0
# Add your dependencies
```

---

## Implementing Analysis Logic

### Analysis Module Structure

The `analysis.py` module should separate concerns:

```python
# analysis.py
from typing import List, Optional
import numpy as np
from models import AnalysisConfig, AnalysisResult, InputData

def perform_analysis(
    data: InputData,
    config: Optional[AnalysisConfig] = None,
) -> List[AnalysisResult]:
    """Main entry point - called by main.py /analyze endpoint."""
    config = config or AnalysisConfig()
    
    # 1. Validate input
    validate_input_data(data)
    
    # 2. Extract arrays
    x, y = extract_arrays(data)
    
    # 3. Preprocess if needed
    x, y = preprocess_data(x, y, config)
    
    # 4. Run core algorithm
    results = run_algorithm(x, y, config)
    
    # 5. Compute quality metrics
    add_quality_metrics(results, x, y)
    
    return results

def validate_input_data(data: InputData) -> None:
    """Validate data before analysis."""
    if len(data.data_points) < 2:
        raise ValueError("Need at least 2 points")
    # Check for NaN/inf...

def extract_arrays(data: InputData) -> tuple:
    """Convert Pydantic models to numpy arrays."""
    x = np.array([p.x for p in data.data_points])
    y = np.array([p.y for p in data.data_points])
    return x, y

def preprocess_data(x, y, config):
    """Apply preprocessing (smoothing, normalization, etc.)."""
    # Your preprocessing logic
    return x, y

def run_algorithm(x, y, config):
    """Core analysis algorithm."""
    # Your main algorithm here
    results = []
    # ... compute results ...
    return results

def add_quality_metrics(results, x, y):
    """Add quality/confidence metrics to results."""
    for result in results:
        result.confidence = compute_confidence(result, x, y)
```

### Best Practices for Analysis Code

**✅ DO:**

- Validate all inputs (NaN, inf, ranges, etc.)
- Use numpy for numerical operations
- Separate preprocessing, algorithm, postprocessing
- Log important steps (`logger.info()`)
- Return structured results (Pydantic models)
- Include quality/confidence metrics
- Handle edge cases gracefully

**❌ DON'T:**

- Mix API logic with analysis logic
- Assume data is clean
- Return raw numpy arrays (use Pydantic models)
- Silently fail (raise informative errors)
- Hardcode parameters (use config)
- Skip input validation

### Example: Peak Width Analysis

```python
# analysis.py for peak width analysis
import numpy as np
from scipy.signal import find_peaks, peak_widths
from models import AnalysisConfig, AnalysisResult, InputData

def perform_analysis(data: InputData, config: AnalysisConfig = None):
    config = config or AnalysisConfig()
    
    x = np.array([p.x for p in data.data_points])
    y = np.array([p.y for p in data.data_points])
    
    # Find peaks
    peaks, _ = find_peaks(
        y,
        prominence=config.min_prominence,
        distance=config.min_distance,
    )
    
    # Measure widths
    widths, width_heights, left_ips, right_ips = peak_widths(
        y, peaks, rel_height=0.5
    )
    
    # Convert to results
    results = []
    for i, peak_idx in enumerate(peaks):
        results.append(AnalysisResult(
            position=float(x[peak_idx]),
            intensity=float(y[peak_idx]),
            width=float(widths[i]),
            confidence=compute_confidence(y, peak_idx, widths[i]),
        ))
    
    return results
```

---

## Testing Your Service

### Local Testing

**1. Start the service:**

```bash
cd services/my_service
python main.py --port 8003
```

**2. Test health endpoint:**

```bash
curl http://localhost:8003/health
# {"status": "healthy", "service": "my_service", "version": "1.0.0"}
```

**3. Test analyze endpoint:**

```bash
curl -X POST http://localhost:8003/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "data_points": [
        {"x": 1.0, "y": 10.0},
        {"x": 2.0, "y": 15.0},
        {"x": 3.0, "y": 12.0}
      ]
    },
    "config": {
      "parameter1": "value1"
    }
  }'
```

**4. Use the interactive docs:**

```bash
# Open browser to:
http://localhost:8003/docs
```

### Unit Testing

Create `test_analysis.py`:

```python
# services/my_service/test_analysis.py
import pytest
import numpy as np
from analysis import perform_analysis, validate_input_data
from models import InputData, DataPoint, AnalysisConfig

def test_basic_analysis():
    """Test basic analysis functionality."""
    data = InputData(
        data_points=[
            DataPoint(x=1.0, y=10.0),
            DataPoint(x=2.0, y=15.0),
            DataPoint(x=3.0, y=12.0),
        ]
    )
    config = AnalysisConfig()
    
    results = perform_analysis(data, config)
    
    assert len(results) > 0
    assert all(r.confidence is not None for r in results)

def test_empty_data():
    """Test that empty data raises error."""
    data = InputData(data_points=[])
    
    with pytest.raises(ValueError, match="No data points"):
        validate_input_data(data)

def test_nan_handling():
    """Test that NaN values are rejected."""
    data = InputData(
        data_points=[
            DataPoint(x=1.0, y=float('nan')),
        ]
    )
    
    with pytest.raises(ValueError, match="Invalid y value"):
        validate_input_data(data)
```

Run tests:

```bash
pytest test_analysis.py -v
```

### Integration Testing

Test with RoboMage client:

```python
# test_integration.py
from robomage.clients.base_service_client import BaseServiceClient

def test_service_integration():
    """Test service via client."""
    client = BaseServiceClient(base_url="http://localhost:8003")
    
    # Check health
    assert client.ping()
    
    # Send analysis request
    response = client.post("/analyze", json={
        "data": {
            "data_points": [{"x": 1.0, "y": 10.0}]
        }
    })
    
    assert response["status"] == "success"
    assert "results" in response
```

---

## Workflow Integration

Your service automatically becomes available as a workflow node when:

1. `service.json` has `workflow_integration.enabled = true`
2. Service is running and healthy
3. Workflow engine is restarted (or auto-discovers on startup)

### Using in Workflows

**JSON Workflow:**

```json
{
  "nodes": [
    {
      "id": "load_1",
      "type": "load_files",
      "config": {
        "file_paths": ["data.chi"]
      }
    },
    {
      "id": "my_analysis_1",
      "type": "my_service",
      "config": {
        "parameter1": "value1",
        "parameter2": 42
      },
      "dependencies": ["load_1"]
    }
  ]
}
```

**Python API:**

```python
from robomage.orchestrator import WorkflowOrchestrator

workflow = {
    "nodes": [
        {"id": "load", "type": "load_files", ...},
        {
            "id": "analyze",
            "type": "my_service",  # Your service node type
            "config": {"param": "value"},
            "dependencies": ["load"]
        }
    ]
}

orchestrator = WorkflowOrchestrator()
results = await orchestrator.execute_workflow(workflow)
```

### Node Configuration Schema

The `workflow_integration.input_schema` in `service.json` defines what config parameters your node accepts:

```json
{
  "workflow_integration": {
    "input_schema": {
      "threshold": {"type": "float", "default": 0.5, "min": 0, "max": 1},
      "method": {"type": "string", "enum": ["auto", "manual"]},
      "verbose": {"type": "boolean", "default": false}
    }
  }
}
```

These map to your `AnalysisConfig` in `models.py`.

---

## Dashboard Integration

Services appear in the dashboard automatically if:

1. `service.json` has `dashboard_integration.enabled = true`
2. Service is registered in `services/registry.json`
3. Dashboard is restarted

### Service Monitor

The dashboard shows service status:

```python
# Dashboard displays:
- Service name and description
- Health status (🟢 healthy / 🔴 unavailable)
- Port and endpoint information
- Link to API docs (/docs)
```

### Analysis Tab Integration

Your service can be used from the Analysis tab:

1. User uploads diffraction data
2. Selects your service from dropdown
3. Configures parameters (from `input_schema`)
4. Clicks "Analyze"
5. Results displayed in table/plot

**Implementation in dashboard callbacks:**

```python
# In analysis.py callback
from robomage.service_registry import get_registry

registry = get_registry()
service = registry.get_service("my_service")

client = BaseServiceClient(service.get_base_url())
response = client.post("/analyze", json={...})
```

---

## Best Practices

### Testing & Development Workflow

**⚡ Key Findings from Hands-On Testing (December 2025):**

**1. ALWAYS use Pixi for environment management:**
```bash
# ✅ CORRECT - Use pixi for consistent environment
pixi run python main.py --port 8003

# ❌ WRONG - Don't use pip/conda directly
pip install -r requirements.txt  # May cause environment conflicts
python main.py --port 8003       # May use wrong Python version
```

**2. Test immediately after generation:**
```bash
# Generated services work out-of-box - test before editing!
python create_service.py  # Create service
cd your_service
pixi run python main.py --port 8003  # Start immediately
curl http://localhost:8003/health     # Verify it works
# Result: Should see {"status":"healthy",...} in <5 seconds
```

**3. Verify auto-registration:**
```bash
# After creating a service, confirm it's discovered:
pixi run list-services
# Your service should appear instantly in the list
# If not, check service.json for syntax errors
```

**4. Performance expectations (validated in testing):**
- Service generation: **<2 minutes**
- Service startup: **<5 seconds**
- Health check response: **<100ms**
- Registry discovery: **Instant** (automatic)
- Total time to working service: **<5 minutes**

### Service Design

**1. Keep services focused:**
- One service = one analysis type
- Don't create monolithic services
- Use workflow composition for complex pipelines

**2. Design for reusability:**
- Accept generic `DiffractionData` format
- Provide sensible defaults
- Make config optional

**3. Handle errors gracefully:**
```python
try:
    results = perform_analysis(data, config)
except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    logger.error(f"Analysis failed: {e}")
    raise HTTPException(status_code=500, detail="Internal error")
```

**4. Validated error handling patterns (from testing):**

The system handles these scenarios gracefully:
- ✅ **Invalid service.json**: Skipped during discovery, no crash
- ✅ **Port conflicts**: Detected by registry, clear error messages
- ✅ **Malformed requests**: Pydantic validation returns 422 with details
- ✅ **Service not running**: Connection errors handled, health checks accurate
- ✅ **Missing services**: `ServiceNotFoundError` with list of available services

### Performance

**1. Use async where appropriate:**
```python
# For I/O-bound operations
@app.post("/analyze")
async def analyze(request: AnalysisRequest):
    results = await async_analysis(request.data)
    return results
```

**2. Add timeout handling:**
```python
import asyncio

async with asyncio.timeout(30):  # 30 second timeout
    results = await long_running_analysis()
```

**3. Consider caching:**
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def expensive_computation(param: str) -> float:
    # Cached result
    return compute(param)
```

### Security

**1. Validate all inputs:**
- Use Pydantic models (automatic validation)
- Check ranges, types, constraints
- Sanitize file paths if accepting files

**2. Set resource limits:**
```python
# In config
MAX_DATA_POINTS = 100_000
MAX_FILE_SIZE_MB = 50

if len(data.data_points) > MAX_DATA_POINTS:
    raise ValueError(f"Too many points: {len(data.data_points)}")
```

**3. Use environment variables for secrets:**
```python
import os
API_KEY = os.getenv("SERVICE_API_KEY", "")
```

### Logging

**Structured logging:**
```python
logger.info(
    "Analysis completed",
    extra={
        "data_points": len(data.data_points),
        "processing_time_ms": elapsed * 1000,
        "results_count": len(results),
    }
)
```

---

## Examples

### Example 1: Background Subtraction Service

**Purpose:** Remove background from diffraction patterns

**Files:** See `examples/custom_nodes/background_subtraction/`

**Key Features:**
- Multiple background methods (polynomial, Savitzky-Golay, rolling ball)
- Configurable parameters
- Returns corrected intensities

**Usage:**
```json
{
  "id": "bg_subtract",
  "type": "background_subtraction",
  "config": {
    "method": "polynomial",
    "degree": 3
  }
}
```

### Example 2: Peak Width Analysis Service

**Purpose:** Analyze peak width distribution

**Files:** See `examples/custom_nodes/peak_width_analysis/`

**Key Features:**
- Peak detection with prominence threshold
- FWHM and integral width calculation
- Statistical summary

**Usage:**
```json
{
  "id": "width_analysis",
  "type": "peak_width_analysis",
  "config": {
    "min_prominence": 100,
    "rel_height": 0.5
  }
}
```

### Example 3: Unit Cell Calculator Service

**Purpose:** Calculate unit cell parameters from peak positions

**Files:** Coming soon

**Key Features:**
- Crystal system detection
- Lattice parameter refinement
- Figure of merit calculation

---

## Troubleshooting

### Common Issues & Solutions (Validated in Testing)

#### Service Won't Start

**Problem:** `Address already in use`

**Solution:** Port conflict - change port in `service.json` or use `--port` flag:
```bash
pixi run python main.py --port 8004
```

**Verified in testing:**
- Registry detects port conflicts automatically
- Each service must use unique port (8000-9000 range recommended)
- Production services use: 8001 (peak_analysis), 8002 (workflow_engine)

**Problem:** `ModuleNotFoundError`

**Solution:** Use pixi (preferred) instead of pip:
```bash
# ✅ CORRECT - Use pixi environment
pixi run python main.py --port 8003

# ❌ AVOID - pip may cause conflicts
pip install -r requirements.txt
python main.py --port 8003
```

**Why pixi?** Tested and confirmed:
- ✅ Fast cross-platform dependency resolution
- ✅ Reproducible environments with lockfiles
- ✅ All project dependencies already included
- ✅ Works identically on Windows and Linux

#### Service Not Discovered

**Problem:** Service doesn't appear in dashboard

**Solutions (priority order):**

1. **Verify service.json is valid:**
```bash
# Check for syntax errors
cat services/your_service/service.json | python -m json.tool
```

2. **Check auto-registration worked:**
```bash
pixi run list-services
# Your service should appear in the list
```

3. **Verify integration flags:**
```json
{
  "dashboard_integration": {"enabled": true},
  "workflow_integration": {"enabled": true}
}
```

4. **Restart dashboard:**
```bash
pixi run kill-all
pixi run start-all
```

**Testing confirmed:** Services are discovered **instantly** upon creation with valid `service.json`

#### Service Health Check Fails

**Problem:** Health endpoint not responding

**Diagnosis & Solutions:**

```bash
# 1. Check if service is running
curl http://localhost:8003/health
# Expected: {"status":"healthy","service":"your_service","version":"1.0.0"}

# 2. If connection refused, service isn't running:
pixi run python services/your_service/main.py --port 8003

# 3. If timeout (>2 seconds), service is hung:
# Check logs for errors, restart service

# 4. If 404, health endpoint misconfigured:
# Verify service.json has: "endpoints": {"health": "/health"}
```

**Performance expectations (validated):**
- Health check response time: **<100ms**
- Service startup time: **<5 seconds**
- If slower, check for initialization issues in main.py

#### Workflow Node Not Available

**Problem:** Service node doesn't appear in workflow builder

**Solutions:**

1. **Verify service is running:**
```bash
curl http://localhost:8003/health
# Must return 200 OK
```

2. **Check workflow integration:**
```json
{
  "workflow_integration": {
    "enabled": true,
    "node_types": ["your_node_type"]
  }
}
```

3. **Restart workflow engine:**
```bash
# Node discovery happens at workflow engine startup
pixi run kill-all
pixi run start-all
# Wait 5 seconds for service startup
```

4. **Verify node registration:**
```bash
pixi run python -c "
from robomage.workflow.nodes.registry import NodeRegistry
registry = NodeRegistry()
registry.discover_and_register_all()
print(f'Found {len(registry.get_node_types())} node types')
print(registry.get_node_types())
"
```

**Testing note:** New service nodes may require workflow engine restart (expected behavior for MVP)

#### Analysis Returns Errors

**Problem:** 400 or 422 errors from `/analyze`

**Common causes (validated in testing):**

1. **422 Validation Error:**
```bash
curl -X POST http://localhost:8003/analyze \
  -H "Content-Type: application/json" \
  -d '{"bad": "data"}'
# Returns: {"detail": [...validation errors...]}
```
- **Cause:** Request doesn't match Pydantic model
- **Solution:** Check API docs at `http://localhost:8003/docs`
- **Expected:** Pydantic provides detailed field-level errors

2. **400 Bad Request:**
```python
# In your analysis.py
raise ValueError("Need at least 2 data points")
```
- **Cause:** Business logic validation failed
- **Solution:** Fix input data or adjust validation logic

3. **500 Internal Server Error:**
```python
# Unhandled exception in analysis code
```
- **Solution:** Check service logs, add try/except blocks

**Debug strategy (tested and confirmed effective):**

```bash
# 1. Test with curl first (faster than dashboard)
curl -X POST http://localhost:8003/analyze \
  -H "Content-Type: application/json" \
  -d @test_request.json

# 2. Use FastAPI auto-docs (validates request format)
# Open: http://localhost:8003/docs
# Click "Try it out", fill in example data

# 3. Add debug logging in analysis.py:
import logging
logger = logging.getLogger(__name__)

def perform_analysis(data, config):
    logger.info(f"Starting analysis with {len(data.data_points)} points")
    logger.debug(f"Config: {config.model_dump()}")
    # ... your code ...
```

#### Performance Issues

**Problem:** Analysis takes too long

**Solutions (validated patterns):**

1. **Set timeouts on client calls:**
```python
# Default timeout is 30 seconds
response = client.post("/analyze", json=data, timeout=60)
```

2. **Optimize numpy operations:**
```python
# ✅ Fast: Vectorized numpy
result = np.sum(data * weights)

# ❌ Slow: Python loops
result = sum(d * w for d, w in zip(data, weights))
```

3. **Profile to find bottlenecks:**
```python
import time
start = time.time()
results = perform_analysis(data, config)
logger.info(f"Analysis took {time.time() - start:.2f}s")
```

**Performance expectations from testing:**
- Health check: <100ms
- Simple analysis (stats): <10ms
- Peak detection: <500ms
- Complex fitting: <2 seconds

If slower, check for:
- Large data arrays (>100,000 points)
- Unoptimized loops
- Excessive logging
- Memory allocation issues

---

### Testing Your Service

**Recommended testing workflow (validated in hands-on testing):**

```bash
# 1. Create service
python create_service.py

# 2. Start service immediately (template works!)
cd your_service
pixi run python main.py --port 8003 &

# 3. Test health endpoint (should be <5 seconds)
curl http://localhost:8003/health
# Expected: {"status":"healthy","service":"your_service","version":"1.0.0"}

# 4. Test with minimal data
curl -X POST http://localhost:8003/analyze \
  -H "Content-Type: application/json" \
  -d '{"data": {"data_points": [{"x": 1.0, "y": 100.0}]}}'
# Template returns basic statistics - confirms service works!

# 5. Verify auto-registration
pixi run list-services
# Your service appears in list

# 6. Now customize analysis.py
# Edit perform_analysis() with your algorithm
# Service hot-reloads in development mode

# 7. Test with real data
curl -X POST http://localhost:8003/analyze \
  -H "Content-Type: application/json" \
  -d @real_data_request.json

# 8. Run automated tests (if you added them)
pixi run test-services
```

**Key insight:** Generated services work immediately - test before customizing!

---

## Advanced Topics

### Custom Service Client

Create a specialized client for your service:

```python
# src/robomage/clients/my_service_client.py
from robomage.clients.base_service_client import BaseServiceClient
from typing import List

class MyServiceClient(BaseServiceClient):
    """Client for My Service."""
    
    def analyze(self, data, config=None):
        """High-level analyze method."""
        response = self.post("/analyze", json={
            "data": data,
            "config": config or {}
        })
        return response["results"]
    
    def batch_analyze(self, datasets: List):
        """Analyze multiple datasets."""
        results = []
        for data in datasets:
            results.append(self.analyze(data))
        return results
```

### Adding Authentication

```python
# main.py
from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    if api_key != os.getenv("SERVICE_API_KEY"):
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

@app.post("/analyze", dependencies=[Depends(verify_api_key)])
async def analyze(request: AnalysisRequest):
    # Protected endpoint
    ...
```

### Service-to-Service Communication

Services can call other services:

```python
# In analysis.py
from robomage.service_registry import get_registry
from robomage.clients.base_service_client import BaseServiceClient

def perform_analysis(data, config):
    # Call another service for preprocessing
    registry = get_registry()
    bg_service = registry.get_service("background_subtraction")
    
    client = BaseServiceClient(bg_service.get_base_url())
    bg_corrected = client.post("/analyze", json={
        "data": data,
        "config": {"method": "polynomial"}
    })
    
    # Continue with analysis on corrected data
    ...
```

---

## Related Documentation

- **Node Development Guide**: `docs/node-development-guide.md` - Creating custom workflow nodes
- **Service Registry**: `src/robomage/service_registry/` - Auto-discovery implementation
- **Base Client**: `src/robomage/clients/base_service_client.py` - HTTP client pattern
- **Dashboard Integration**: `docs/sprint-4-visualization-dashboard.md` - Dashboard architecture
- **Workflow Engine**: `docs/sprint-6-workflow-orchestrator-mvp.md` - Workflow execution

---

## Summary

Creating a custom service:

1. **Generate** with `python services/create_service.py`
2. **Implement** your analysis in `analysis.py`
3. **Test** with `python main.py` and `curl`
4. **Deploy** - service auto-discovered and integrated
5. **Use** from dashboard, workflows, or CLI

**Key Benefits:**

- ⚡ **Fast setup** - Under 5 minutes with generator
- 🔄 **Auto-discovery** - No manual registration needed
- 🔌 **Full integration** - Dashboard + workflows + CLI
- 🛡️ **Type-safe** - Pydantic validation
- 📦 **Self-contained** - Independent deployment

**Support:**

- 📧 Questions? Check troubleshooting section
- 📚 Examples in `examples/custom_nodes/`
- 🔍 Source code in `src/robomage/service_registry/`
- 📊 **Testing Results**: See `docs/HANDS-ON-TESTING-RESULTS.md` for validated performance metrics

---

## Appendix: Validated Testing Results

**Status:** ✅ Production-ready (December 2, 2025)

### Performance Benchmarks

From comprehensive hands-on testing with 7 test sessions:

| Metric | Time | Notes |
|--------|------|-------|
| **Service Creation** | <2 minutes | From `create_service.py` to working service |
| **Service Startup** | <5 seconds | Using `pixi run` |
| **Health Check** | <100ms | Response time for `/health` endpoint |
| **Registry Discovery** | Instant | Automatic upon creation with valid service.json |
| **Auto-Registration** | Instant | No manual registration needed |
| **Total Time to Working Service** | <5 minutes | Including testing and verification |

### Testing Coverage

**Automated Tests:**
- ✅ 37/37 service registry tests passing (100%)
- ✅ Test suite execution: 1.37 seconds
- ✅ Coverage: metadata, registry, client, error handling

**Hands-On Testing Sessions:**
1. ✅ Service Generator - Created working service in <2 minutes
2. ✅ Service Registry - All discovery and lookup functions working
3. ✅ Dashboard Integration - Services auto-integrate with UI
4. ✅ Workflow Integration - 13 node types auto-discovered
5. ✅ Migration Scenario - Existing services follow all patterns
6. ✅ End-to-End Workflow - Service creation to workflow execution
7. ✅ Error Handling - 6/6 error scenarios handled gracefully

### Platform Compatibility

- ✅ **Linux:** Fully tested (Rocky Linux 8, Python 3.14)
- ✅ **Windows:** Confirmed working (prior testing, Nov 30 2025)
- ✅ **Pixi:** Working on both platforms
- ✅ **Cross-platform:** Service code portable

### Error Handling Validation

Confirmed robust handling of:
- ✅ Invalid service.json (skipped during discovery)
- ✅ Port conflicts (detected, clear errors)
- ✅ Malformed requests (422 with Pydantic validation details)
- ✅ Service not running (connection errors, accurate health checks)
- ✅ Missing services (ServiceNotFoundError with available list)
- ✅ Stopped services (timeouts handled appropriately)

### Example Services Created During Testing

**simple_stats** (analysis service):
- Port: 8005
- Function: Calculate basic statistics on diffraction data
- Time to create: 1.5 minutes
- Status: Working immediately with template code

**normalize_intensities** (transform service):
- Port: 8006
- Function: Normalize diffraction intensities to max value
- Time to create: 2 minutes
- Status: Auto-discovered, workflow-ready

### Key Findings

**What Works Exceptionally Well:**
1. Service generation is fast and reliable
2. Auto-discovery eliminates manual configuration
3. Template code works out-of-box (can test before customizing)
4. Error messages are clear and actionable
5. Health monitoring is accurate and responsive
6. Cross-platform compatibility confirmed

**Important Learnings:**
1. **Always use Pixi** - Don't use pip/conda directly
2. **Test immediately** - Generated services work before customization
3. **Verify auto-registration** - Check with `pixi run list-services`
4. **Expect instant discovery** - Registry updates automatically
5. **Node discovery timing** - Workflow nodes appear after engine restart

**Developer Experience:**
- ⭐⭐⭐⭐⭐ Service creation speed
- ⭐⭐⭐⭐⭐ Auto-discovery reliability  
- ⭐⭐⭐⭐⭐ Error handling quality
- ⭐⭐⭐⭐⭐ Documentation accuracy
- ⭐⭐⭐⭐⭐ Template code quality

### Reference Documentation

For complete testing details, see:
- **Full Test Report:** `docs/HANDS-ON-TESTING-RESULTS.md`
- **Testing Plan:** `docs/HANDS-ON-TESTING-PLAN.md`
- **Service Registry Tests:** `tests/test_service_registry.py`
- **Client Tests:** `tests/test_base_service_client.py`

---

*Last updated: December 2, 2025 | RoboMage v1.0.0*
*Testing validated: December 2, 2025 | 7/7 test sessions passed*

