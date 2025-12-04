# GSAS-II Refinement Service

Rietveld refinement microservice for RoboMage powder diffraction analysis.

## Overview

This service wraps GSAS-II functionality in a REST API, providing:
- Rietveld refinement via HTTP POST requests
- Structured JSON input/output (no file I/O required)
- Recipe-based configuration (YAML format)
- Support for both file paths and base64-encoded assets

## Quick Start

### Prerequisites

1. **GSAS-II Installation**: This service requires GSAS-II Python API
   - See [autoxrd GSAS-II installation guide](/nsls2/users/dolds/dev/autoxrd/GSASII_pixi_installation_instructions.md)
   - Or install via conda: `conda install -c briantoby gsas2full`

2. **Python Dependencies**: See `requirements.txt`

### Running the Service

```bash
# From RoboMage root with pixi
pixi run python -m services.gsasii_refinement.main

# Or directly with uvicorn
cd services/gsasii_refinement
uvicorn main:app --host 0.0.0.0 --port 8002
```

### Health Check

```bash
curl http://localhost:8002/health
# {"status": "healthy", "gsasii_available": true, "version": "1.0.0"}
```

### API Documentation

Interactive API docs available at:
- Swagger UI: http://localhost:8002/docs
- ReDoc: http://localhost:8002/redoc

## API Endpoints

### `GET /health`
Service health check and GSAS-II availability.

### `POST /refine`
Execute Rietveld refinement.

**Request:**
```json
{
  "diffraction_data": {
    "q": [0.5, 0.6, 0.7, ...],
    "intensity": [100, 120, 95, ...]
  },
  "recipe": {
    "instrument_file": "PDF_1m.instprm",
    "cif_file": "LaB6_SRM_660c.CIF",
    "phase_name": "LaB6",
    "refinement_dict": {
      "set": {
        "Limits": {"low": 1, "high": 15},
        "Background": {"type": "chebyschev-1", "no. coeffs": 4, "refine": true},
        "Cell": true,
        "Sample Parameters": ["Scale"]
      }
    }
  },
  "sample_name": "LaB6_test",
  "cycles": 5
}
```

**Response:**
```json
{
  "success": true,
  "parameters": {...},
  "cell": {
    "a": {"value": 4.156, "esd": 0.001},
    ...
  },
  "fit_quality": {
    "Rwp": 2.34,
    "chi2": 1.23
  },
  "fit_profile": {
    "two_theta": [...],
    "y_obs": [...],
    "y_calc": [...],
    ...
  },
  "execution_time_s": 12.3
}
```

### `GET /recipes`
List available recipe templates.

### `POST /validate_recipe`
Validate recipe schema.

## Recipe Format

Recipes follow the autoxrd YAML format:

```yaml
recipe_description: "Lattice refinement example"
instrument_file: "PDF_1m.instprm"
cif_file: "LaB6_SRM_660c.CIF"
phase_name: "LaB6"
refinement_dict:
  set:
    Limits:
      low: 1
      high: 15
    Background:
      type: "chebyschev-1"
      no. coeffs: 4
      refine: true
    Cell: true
    Sample Parameters:
      - Scale
```

## Development

### Project Structure

```
services/gsasii_refinement/
├── main.py                  # FastAPI application
├── models.py                # Pydantic data models
├── gsasii_wrapper.py        # GSAS-II API wrapper (TODO)
├── requirements.txt         # Python dependencies
├── assets/                  # Bundled test assets
│   ├── recipes/             # Example recipes
│   ├── cifs/                # Common crystal structures
│   └── instruments/         # Instrument parameter files
├── tests/                   # Unit and integration tests (TODO)
└── README.md                # This file
```

### Testing

```bash
# Run service tests
pytest tests/

# Manual test with curl
curl -X POST http://localhost:8002/refine \
  -H "Content-Type: application/json" \
  -d @test_request.json
```

## Reference Implementation

This service is adapted from the autoxrd project:
- Repository: `/nsls2/users/dolds/dev/autoxrd`
- Core GSAS-II wrapper: `fit_service/xrd_pipeline.py`
- Example DRX workflows: `on-the-fly/test/user_data_DRX_test/`

Key changes from autoxrd:
- REST API instead of file watching
- JSON input/output instead of CSV/TXT
- Temporary file management (no persistent storage)
- Base64 support for assets (no file paths required)

## Integration with RoboMage

### Client Library

```python
from robomage.clients.gsasii_client import GSASIIClient

client = GSASIIClient(base_url="http://localhost:8002")

# Check health
health = client.health()

# Run refinement
result = client.refine(
    data=diffraction_data,
    recipe=recipe_dict,
    sample_name="my_sample"
)

print(f"Rwp: {result['fit_quality']['Rwp']:.3f}%")
```

### Workflow Node

```python
# Will be implemented in Phase 2
from robomage.workflow.nodes import gsasii_refinement

# Node available in workflow builder
```

## Status

**Current Phase:** 1a - Service Scaffold (In Progress)

**Completed:**
- [x] Service directory structure
- [x] Pydantic data models
- [x] FastAPI skeleton with health check
- [x] Requirements.txt

**Next Steps:**
- [ ] Copy DRX Demo assets
- [ ] Implement gsasii_wrapper.py
- [ ] Test with LaB6 data
- [ ] Add recipe validation
- [ ] Write integration tests

## License

Same as RoboMage (see project root LICENSE file).
