"""
Peak Analysis Service - Advanced Scientific Computing for Crystallography

A high-performance microservice for automated peak detection, fitting, and analysis
of powder diffraction data. This service implements state-of-the-art algorithms
for crystallographic peak analysis and integrates seamlessly with the RoboMage
scientific framework.

Core Capabilities:
    - Automated peak detection using scipy.signal algorithms
    - Multi-profile fitting (Gaussian, Lorentzian, Voigt) with scipy.optimize
    - Statistical analysis with R² goodness-of-fit metrics
    - Background subtraction and data normalization
    - d-spacing calculation and crystallographic analysis

Service Architecture:
    - FastAPI REST API with automatic OpenAPI documentation
    - Pydantic v2 data validation and JSON schema generation
    - Uvicorn ASGI server for production deployment
    - Stateless design for horizontal scalability

Scientific Algorithms:
    This service implements peer-reviewed algorithms from computational
    crystallography, providing publication-quality results for powder
    diffraction analysis with full statistical validation.

Integration:
    - RoboMage framework: Native data model compatibility
    - CLI interface: peak_analyzer.py command-line tool
    - HTTP client: robomage.clients.peak_analysis_client
    - Future GSAS-II integration for Rietveld refinement

Performance:
    - Sub-second analysis times for typical datasets (1000-4000 points)
    - Memory-efficient processing for large datasets
    - Concurrent request handling for high-throughput workflows
    - Optimized numerical algorithms with vectorized operations

Quality Assurance:
    - Comprehensive test suite with real diffraction data
    - Continuous integration with GitHub Actions
    - Type safety with mypy static analysis
    - Code quality with ruff formatting and linting
"""

# Export main components for easy importing
from .engine import PeakAnalysisEngine
from .main import app
from .models import (
    AnalysisConfig,
    DiffractionDataInput,
    PeakAnalysisRequest,
    PeakAnalysisResponse,
    PeakInfo,
    ProfileType,
    ServiceHealth,
)

__version__ = "1.0.0"
__author__ = "RoboMage Development Team"
__license__ = "MIT"

# Service metadata
SERVICE_NAME = "peak-analysis"
API_VERSION = "v1"
SUPPORTED_FORMATS = [".chi", ".dat", ".xy"]

__all__ = [
    "PeakAnalysisEngine",
    "app",
    "AnalysisConfig",
    "DiffractionDataInput",
    "PeakAnalysisRequest",
    "PeakAnalysisResponse",
    "PeakInfo",
    "ProfileType",
    "ServiceHealth",
    "SERVICE_NAME",
    "API_VERSION",
    "SUPPORTED_FORMATS",
]
