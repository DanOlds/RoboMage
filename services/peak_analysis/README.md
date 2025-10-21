# Peak Analysis Service

A standalone microservice for automated peak detection and fitting in powder diffraction data, designed as part of the RoboMage framework.

## Overview

This service provides comprehensive peak analysis capabilities for crystallographic data through a REST API interface. It implements scientific algorithms for peak detection, fitting with multiple profile types (Gaussian, Lorentzian, Voigt), and statistical analysis of diffraction patterns.

## Features

### Core Capabilities
- **Peak Detection**: Automated identification of diffraction peaks using scipy algorithms
- **Multi-Profile Fitting**: Support for Gaussian, Lorentzian, and Voigt peak profiles
- **Background Subtraction**: Automated background removal and normalization
- **Statistical Analysis**: R² goodness-of-fit metrics and quality assessment
- **d-spacing Calculation**: Automatic conversion from Q-space to d-spacing

### Analysis Configuration
- Configurable peak detection sensitivity
- Adjustable fitting quality thresholds
- Background subtraction options
- Peak width and intensity filtering

## Architecture

### Technology Stack
- **FastAPI 0.104.0+**: Modern REST API framework with automatic OpenAPI documentation
- **SciPy 1.10.0+**: Scientific computing library for peak detection (`find_peaks`) and fitting
- **Pydantic v2**: Data validation, serialization, and JSON schema generation
- **NumPy**: Numerical computing foundation
- **uvicorn**: High-performance ASGI server

### Service Design
- **Stateless**: Each analysis request is independent
- **Type-safe**: Full Pydantic validation for all inputs/outputs
- **Error handling**: Comprehensive error responses with detailed messages
- **Performance**: Optimized algorithms with sub-second analysis times

## API Reference

### Endpoints

#### `POST /analyze`
Performs peak analysis on diffraction data.

**Request Body:**
```json
{
  "q_values": [1.0, 1.1, 1.2, ...],
  "intensities": [100, 150, 200, ...],
  "config": {
    "peak_detection": {
      "height_threshold": 0.1,
      "prominence": 0.05,
      "distance": 5
    },
    "fitting": {
      "profile_type": "gaussian",
      "r_squared_threshold": 0.95
    }
  }
}
```

**Response:**
```json
{
  "peaks_detected": 15,
  "peaks_fitted": 8,
  "processing_time_ms": 85.2,
  "overall_r_squared": 0.892,
  "peak_list": [
    {
      "peak_id": 0,
      "position": 1.51,
      "d_spacing": 4.16,
      "height": 5556,
      "width": 0.070,
      "r_squared": 0.981,
      "profile_type": "gaussian"
    }
  ]
}
```

#### `GET /health`
Service health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "peak-analysis",
  "version": "1.0.0",
  "timestamp": "2025-10-21T12:00:00Z"
}
```

#### `GET /schema`
Returns JSON schema for API request/response validation.

## Usage Examples

### Direct Service Usage
```bash
# Start the service
cd services/peak_analysis
python main.py --port 8001 --host 0.0.0.0

# Test health endpoint
curl http://localhost:8001/health

# Analyze data
curl -X POST http://localhost:8001/analyze \
  -H "Content-Type: application/json" \
  -d @sample_data.json
```

### Integration with RoboMage
```python
from robomage.clients.peak_analysis_client import PeakAnalysisClient

# Initialize client
client = PeakAnalysisClient("http://localhost:8001")

# Analyze diffraction data
response = client.analyze_peaks(q_values, intensities)
print(f"Found {response.peaks_detected} peaks")
```

## File Structure

```
services/peak_analysis/
├── README.md           # This documentation
├── __init__.py         # Package initialization
├── main.py            # FastAPI service entry point
├── engine.py          # Core peak analysis algorithms
└── models.py          # Pydantic data models
```

## Dependencies

### Required Packages
- `fastapi>=0.100.0` - REST API framework
- `uvicorn>=0.20.0` - ASGI server
- `scipy>=1.10.0` - Scientific computing
- `numpy` - Numerical operations
- `pydantic>=2.0` - Data validation

### Development Tools
- `pytest` - Testing framework
- `mypy` - Type checking
- `ruff` - Code formatting and linting

## Configuration

### Environment Variables
- `PEAK_ANALYSIS_PORT`: Service port (default: 8001)
- `PEAK_ANALYSIS_HOST`: Service host (default: 127.0.0.1)
- `PEAK_ANALYSIS_LOG_LEVEL`: Logging level (default: INFO)

### Analysis Parameters
All analysis parameters can be configured via the API request:

```python
config = {
    "peak_detection": {
        "height_threshold": 0.1,    # Minimum peak height (fraction of max)
        "prominence": 0.05,         # Peak prominence requirement
        "distance": 5,              # Minimum distance between peaks
        "width": (1, 50)           # Peak width constraints
    },
    "fitting": {
        "profile_type": "gaussian", # gaussian, lorentzian, voigt
        "r_squared_threshold": 0.95,# Minimum fit quality
        "max_iterations": 1000      # Optimization iterations
    },
    "background": {
        "subtract": true,           # Enable background subtraction
        "method": "polynomial",     # Background fitting method
        "order": 3                  # Polynomial order
    }
}
```

## Performance

### Benchmarks
- **Typical dataset** (4000 points): ~100ms analysis time
- **Peak detection**: ~10ms for 50 peaks
- **Peak fitting**: ~2ms per peak (Gaussian profile)
- **Memory usage**: ~10MB for standard datasets

### Optimization
- Vectorized NumPy operations for numerical efficiency
- Scipy's optimized peak detection algorithms
- Minimal memory footprint with streaming processing
- Concurrent request handling via FastAPI/uvicorn

## Integration Points

### RoboMage Framework
- **Data Pipeline**: Processes `DiffractionData` objects from RoboMage loaders
- **Orchestrator**: Managed as a microservice by RoboMage's orchestrator
- **Client Library**: Accessed via `robomage.clients.peak_analysis_client`
- **CLI Integration**: Available through the `peak_analyzer.py` command-line tool

### External Tools
- **GSAS-II**: Future integration for Rietveld refinement workflows
- **Jupyter Notebooks**: Interactive analysis and visualization
- **REST APIs**: Standard HTTP/JSON interface for any client

## Error Handling

The service provides detailed error responses:

```json
{
  "error": "ValidationError",
  "message": "Invalid Q-values: must be monotonically increasing",
  "details": {
    "field": "q_values",
    "invalid_indices": [45, 46, 47]
  }
}
```

## Development

### Running Tests
```bash
# Run service-specific tests
pytest tests/test_peak_analysis_integration.py -v

# Run with coverage
pytest --cov=services/peak_analysis tests/
```

### Local Development
```bash
# Install dependencies (using pixi)
pixi install

# Start development server
pixi run python services/peak_analysis/main.py --reload

# Check code quality
pixi run check
```

## Future Enhancements

### Planned Features
- **Multi-threading**: Parallel peak fitting for large datasets
- **Advanced Profiles**: Pseudo-Voigt and asymmetric peak shapes
- **Real-time Processing**: WebSocket support for streaming data
- **Machine Learning**: AI-enhanced peak identification

### Integration Roadmap
- **Database Storage**: Peak analysis results persistence
- **Visualization**: Real-time plotting and interactive analysis
- **Batch Processing**: High-throughput analysis workflows
- **Cloud Deployment**: Containerized service deployment