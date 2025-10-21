"""
FastAPI service for peak analysis.

This module implements the REST API endpoints for the peak analysis service
using FastAPI. The service can run standalone or be integrated with RoboMage.
"""

import argparse
import importlib.util
import os
import time
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

# Import local modules
try:
    from .engine import PeakAnalysisEngine
    from .models import (
        AnalysisConfig,
        PeakAnalysisRequest,
        PeakAnalysisResponse,
        ServiceError,
        ServiceHealth,
    )
except ImportError:
    # Fall back to direct imports when running as script
    from engine import PeakAnalysisEngine
    from models import (
        AnalysisConfig,
        PeakAnalysisRequest,
        PeakAnalysisResponse,
        ServiceError,
        ServiceHealth,
    )


# Global engine instance
engine = None
start_time = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage service lifecycle."""
    global engine, start_time

    # Startup
    engine = PeakAnalysisEngine()
    start_time = time.time()
    print("Peak Analysis Service started")

    yield

    # Shutdown
    print("Peak Analysis Service stopped")


# Create FastAPI app
app = FastAPI(
    title="Peak Analysis Service",
    description="Scientific peak analysis for powder diffraction data",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Peak Analysis Service",
        "version": "1.0.0",
        "description": "Scientific peak analysis for powder diffraction data",
        "endpoints": {
            "analyze": "POST /analyze - Analyze diffraction data for peaks",
            "health": "GET /health - Service health check",
            "schema": "GET /schema - JSON schema for requests/responses",
        },
    }


@app.get("/health", response_model=ServiceHealth)
async def health_check():
    """Service health check endpoint."""
    global start_time

    uptime = time.time() - start_time if start_time else 0.0

    # Check dependencies
    dependencies_ok = True
    try:
        # Test availability of required modules
        required_modules = ["numpy", "scipy", "pydantic"]
        for module in required_modules:
            if importlib.util.find_spec(module) is None:
                dependencies_ok = False
                break

        # Basic test of engine
        if engine is None:
            dependencies_ok = False
    except Exception:
        dependencies_ok = False

    status = "healthy" if dependencies_ok else "unhealthy"

    return ServiceHealth(
        status=status,
        version="1.0.0",
        uptime_seconds=uptime,
        dependencies_ok=dependencies_ok,
    )


@app.post("/analyze", response_model=PeakAnalysisResponse)
async def analyze_peaks(request: PeakAnalysisRequest):
    """
    Analyze diffraction data for peaks.

    Performs comprehensive peak detection, fitting, and analysis on the
    provided diffraction data using the specified configuration.
    """
    if engine is None:
        raise HTTPException(
            status_code=503, detail="Service not ready - engine not initialized"
        )

    try:
        # Validate input data
        if len(request.data.q_values) < 10:
            raise ValueError("Insufficient data points (minimum 10 required)")

        if len(request.data.q_values) != len(request.data.intensities):
            raise ValueError("Q-values and intensities must have same length")

        # Perform analysis
        result = engine.analyze_peaks(
            data=request.data, config=request.config, request_id=request.request_id
        )

        return result

    except ValueError as e:
        error = ServiceError(
            error_type="ValidationError", message=str(e), request_id=request.request_id
        )
        raise HTTPException(status_code=400, detail=error.model_dump()) from e

    except Exception as e:
        error = ServiceError(
            error_type="InternalError",
            message="Analysis failed due to internal error",
            details=str(e),
            request_id=request.request_id,
        )
        raise HTTPException(status_code=500, detail=error.model_dump()) from e


@app.get("/schema")
async def get_schemas():
    """Get JSON schemas for request and response models."""
    return {
        "request_schema": PeakAnalysisRequest.model_json_schema(),
        "response_schema": PeakAnalysisResponse.model_json_schema(),
        "config_schema": AnalysisConfig.model_json_schema(),
        "error_schema": ServiceError.model_json_schema(),
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    error = ServiceError(
        error_type="UnhandledError",
        message="An unexpected error occurred",
        details=str(exc),
    )
    return JSONResponse(status_code=500, content=error.model_dump())


def main():
    """Main entry point for standalone service."""
    parser = argparse.ArgumentParser(
        description="Peak Analysis Service",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --port 8001
  python main.py --host 0.0.0.0 --port 8080 --workers 4
  python main.py --dev  # Development mode with auto-reload
        """,
    )

    parser.add_argument(
        "--host", default="127.0.0.1", help="Host to bind to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port", type=int, default=8001, help="Port to bind to (default: 8001)"
    )
    parser.add_argument(
        "--workers", type=int, default=1, help="Number of worker processes (default: 1)"
    )
    parser.add_argument(
        "--dev", action="store_true", help="Run in development mode with auto-reload"
    )
    parser.add_argument(
        "--log-level",
        default="info",
        choices=["critical", "error", "warning", "info", "debug", "trace"],
        help="Log level (default: info)",
    )

    args = parser.parse_args()

    print("Starting Peak Analysis Service...")
    print(f"Host: {args.host}")
    print(f"Port: {args.port}")
    print(f"Workers: {args.workers}")
    print(f"Development mode: {args.dev}")
    print(f"Log level: {args.log_level}")
    print()
    print("Available endpoints:")
    print(f"  http://{args.host}:{args.port}/")
    print(f"  http://{args.host}:{args.port}/health")
    print(f"  http://{args.host}:{args.port}/analyze")
    print(f"  http://{args.host}:{args.port}/schema")
    print()

    # Configure uvicorn
    config = {
        "app": "main:app",
        "host": args.host,
        "port": args.port,
        "log_level": args.log_level,
    }

    if args.dev:
        config.update(
            {
                "reload": True,
                "reload_dirs": [os.path.dirname(__file__)],
            }
        )
    else:
        config["workers"] = args.workers

    # Start server
    uvicorn.run(**config)


if __name__ == "__main__":
    main()
