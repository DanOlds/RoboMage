# Peak Analysis Service

A standalone service for scientific peak analysis of powder diffraction data.

## Overview
This service provides comprehensive peak detection, fitting, and analysis capabilities for crystallographic data through a REST API interface.

## Service Architecture
- **FastAPI**: REST API framework
- **scipy**: Scientific computing for peak detection and fitting
- **Pydantic**: Data validation and JSON schema generation
- **uvicorn**: ASGI server for production deployment

## API Endpoints
- `POST /analyze` - Analyze diffraction data for peaks
- `GET /health` - Service health check
- `GET /schema` - JSON schema for requests/responses

## Usage

### Standalone Service
```bash
cd services/peak_analysis
python main.py --port 8001
```

### Integration with RoboMage
The service integrates seamlessly with RoboMage's orchestrator through HTTP/JSON communication.