# Sprint 3 Plan: Independent Peak Analysis Engine

## Objective
Build an **Independent Peak Analysis Engine** as a JSON-based service to establish scalable, modular architecture patterns for all future RoboMage analysis engines (including GSAS-II).

## Strategic Value
- **Service Architecture**: Establishes microservice patterns for production deployment
- **Language Agnostic**: Engine can be implemented in any language (Python, C++, Rust)
- **True Modularity**: Engine can be developed, tested, and versioned independently
- **Scalability**: Engine can run on different machines/containers for performance
- **Reusability**: Other projects can use the engine without RoboMage dependencies
- **Real Science**: Peak finding/fitting delivers immediate scientific value

## Architecture Overview

```
┌─────────────────┐    JSON      ┌─────────────────┐    JSON      ┌─────────────────┐
│   RoboMage     │   Request    │  Peak Analysis  │  Response    │   RoboMage     │
│   Orchestrator  │─────────────▶│     Service     │─────────────▶│   Storage/Viz   │
└─────────────────┘              └─────────────────┘              └─────────────────┘
                                        │
                                   Independent
                                   Process/Service
```

**Communication Protocol:**
- **Input**: JSON containing diffraction data + analysis configuration
- **Output**: JSON containing peak analysis results + metadata
- **Transport**: HTTP REST API (local) with future support for network deployment
- **Validation**: JSON Schema for all request/response interfaces

## Prerequisites & Dependencies
- ✅ **scipy** already available in pixi.toml (>=1.16.2)
- ✅ **FastAPI** or **Flask** for REST service (to be added)
- ✅ **requests** for HTTP client communication
- ✅ **DiffractionData** models for JSON serialization
- ✅ **Pydantic v2** for automatic JSON schema generation

## Core Components (8 Tasks, ~2 weeks)

### 1. JSON Schema Definition (0.5 days)
**Files:** `src/robomage/schemas/` (new directory)
- Export Pydantic models to JSON Schema for service interface
- `peak_analysis_request.json` - Input data + configuration schema
- `peak_analysis_response.json` - Results + metadata schema
- Validation utilities for JSON data exchange

### 2. Independent Peak Analysis Service (3 days)
**Files:** `services/peak_analysis/` (new directory structure)
```
services/peak_analysis/
├── main.py              # FastAPI service entry point
├── engine.py            # Core scipy-based analysis logic
├── models.py            # Service-specific data models
└── requirements.txt     # Independent service dependencies
```
- Standalone FastAPI service with `/analyze` endpoint
- scipy-based peak detection and fitting algorithms
- Background subtraction and quality assessment
- Comprehensive error handling and validation
- Simple process-based deployment (no containers needed)

### 3. Service Client Library (1 day)
**File:** `src/robomage/clients/peak_analysis_client.py`
- HTTP client for communicating with peak analysis service
- Automatic JSON serialization/deserialization
- Connection management, retries, and error handling
- Service discovery and health checking

### 4. Orchestrator Framework (1.5 days)
**File:** `src/robomage/orchestrator.py` (implement empty file)
- Generic `ServiceOrchestrator` for managing external analysis services
- Service lifecycle management (start/stop/health checks)
- Request/response handling with proper error propagation
- Support for multiple engine types through service registry

### 5. Enhanced Visualization (1 day)
**File:** `src/robomage/visualization.py` (implement empty file)
- Publication-quality plots for service-returned results
- JSON result parsing and matplotlib integration
- Analysis reports with peak tables and statistics
- Same plot styles as existing CLI (150 DPI, consistent formatting)

### 6. CLI Integration (1 day)
**File:** Update `src/robomage/__main__.py`
- Add `analyze` subcommand with service integration
- Automatic service startup/shutdown for local development
- Batch processing with service connection pooling
- Progress reporting for long-running service operations

### 7. Service Management Tools (1 day)
**Files:** `src/robomage/services/` (new directory)
- Service registry and discovery mechanisms
- Development server management (start/stop/restart)
- Health monitoring and diagnostic tools
- Configuration management for service endpoints

### 8. Integration Tests & Documentation (1 day)
**Files:** `tests/test_peak_analysis_service.py`, `tests/test_service_client.py`
- End-to-end service integration tests
- Service startup/shutdown test fixtures
- JSON schema validation tests
- Performance and reliability testing
- Service documentation and API reference

## Success Criteria

### Working Independent Service:
```bash
# Start the peak analysis service
cd services/peak_analysis && python main.py
# Service runs on http://localhost:8001

# Service health check
curl http://localhost:8001/health
# Returns: {"status": "healthy", "version": "1.0.0"}

# Direct service API test
curl -X POST http://localhost:8001/analyze \
  -H "Content-Type: application/json" \
  -d @test_request.json
# Returns: JSON with peak analysis results
```

### Working Python API (with service backend):
```python
import robomage
from robomage.orchestrator import ServiceOrchestrator

# Use existing data loading (already working)
data = robomage.load_test_data()  # Returns DiffractionData object

# Configure analysis using service
orchestrator = ServiceOrchestrator()
results = orchestrator.run_analysis(
    data, 
    config={"min_peak_height": 0.05, "fit_peaks": True},
    service_type="peak_analysis"
)

print(f"Found {results['total_peaks_found']} peaks")
```

### Working CLI with Service Integration:
```bash
# CLI automatically manages service lifecycle
pixi run python -m robomage analyze examples/pdf_SRM_660b_q.chi --peaks --output results/

# Batch processing with service pooling
pixi run python -m robomage analyze --files *.chi --peaks --output batch_results/

# Service status and management
pixi run python -m robomage service status
pixi run python -m robomage service restart peak-analysis
```

## GSAS-II and Future Engine Migration Path

This service architecture directly enables future analysis engines:

### GSAS-II Service (Future Sprint):
```bash
# Same service pattern, different implementation
cd services/gsas2_refinement && python main.py  # Port 8002

# Same orchestrator API
results = orchestrator.run_analysis(data, config, service_type="gsas2_refinement")
```

### Service Registry Pattern:
```python
# src/robomage/services/registry.py
AVAILABLE_SERVICES = {
    "peak_analysis": {"port": 8001, "endpoint": "/analyze"},
    "gsas2_refinement": {"port": 8002, "endpoint": "/refine"},  # Future
    "background_subtraction": {"port": 8003, "endpoint": "/subtract"}  # Future
}
```

## Implementation Notes & Dependencies

### New Dependencies to Add to pixi.toml:
```toml
fastapi = "*"          # Service framework
uvicorn = "*"          # ASGI server
requests = "*"         # HTTP client
httpx = "*"            # Async HTTP client (optional)
```

### New Directory Structure:
```
services/                          # Independent services
├── peak_analysis/                 # Peak analysis service
│   ├── main.py                   # FastAPI app
│   ├── engine.py                 # Core analysis logic
│   ├── models.py                 # Service models
│   └── requirements.txt          # Service dependencies
├── shared/                       # Shared service utilities
│   ├── schemas/                  # JSON schemas
│   └── utils.py                  # Common utilities
└── README.md                     # Service architecture docs

src/robomage/
├── clients/                      # Service client libraries
├── services/                     # Service management tools
├── schemas/                      # JSON schema definitions
└── orchestrator.py              # Service orchestration
```

## Deliverables
- **Service Architecture**: Complete independent peak analysis service with REST API
- **JSON Interface**: Validated JSON schemas for all service communication
- **Service Management**: Tools for service lifecycle, health monitoring, and discovery
- **Client Library**: Python client for seamless service integration
- **CLI Integration**: Transparent service usage through existing CLI patterns
- **Testing**: Comprehensive service integration and reliability tests
- **Documentation**: Service API reference and deployment guides

## Validation Checklist
- [ ] Peak analysis service runs independently with FastAPI
- [ ] JSON schemas validate all request/response data
- [ ] Service client handles errors, retries, and timeouts gracefully
- [ ] CLI transparently manages service lifecycle for users
- [ ] Integration tests cover service startup, analysis, and shutdown
- [ ] Service can be deployed independently as a Python process
- [ ] Performance is acceptable for typical diffraction datasets
- [ ] Service architecture patterns are documented for future engines

## Benefits of Independent Service Approach

### Immediate Benefits:
- **True Modularity**: Peak analysis can be developed and tested in isolation
- **Performance**: Service can be optimized independently (C++ core, Python API)
- **Simple Deployment**: Just `python main.py` - no container complexity
- **Reliability**: Service failures don't crash main RoboMage application

### Future Benefits:
- **Language Freedom**: GSAS-II service could use optimal language/bindings
- **Distributed Computing**: Services can run on different machines
- **Version Management**: Services can be updated independently
- **Ecosystem Growth**: Other projects can use RoboMage analysis services
- **Containerization Option**: Can add Docker later if deployment needs require it

## Timeline: 2 weeks
More ambitious scope than integrated approach, but establishes production-ready architecture patterns that will benefit all future RoboMage development.
