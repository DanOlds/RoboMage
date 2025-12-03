"""GSAS-II Refinement Service - FastAPI Application

REST API for Rietveld refinement using GSAS-II.
"""

import logging
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Add parent directory to path for imports
service_dir = Path(__file__).parent
sys.path.insert(0, str(service_dir))

from models import (
    HealthResponse,
    RefinementRequest,
    RefinementResult,
    RecipeListResponse,
    RecipeValidationResponse,
)

# ============================================================================
# Logging Setup
# ============================================================================

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("gsasii_service")


# ============================================================================
# Startup/Shutdown
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    logger.info("GSAS-II Refinement Service starting up...")

    # Check GSAS-II availability at startup
    try:
        from GSASII import GSASIIscriptable as G2  # noqa: F401

        logger.info("✓ GSAS-II successfully imported")
    except ImportError as e:
        logger.warning(f"✗ GSAS-II import failed: {e}")
        logger.warning(
            "Service will run in degraded mode (health checks will report unavailable)"
        )

    yield  # Application runs here

    logger.info("GSAS-II Refinement Service shutting down...")


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="GSAS-II Refinement Service",
    description=(
        "Rietveld refinement microservice for RoboMage powder diffraction analysis. "
        "Wraps GSAS-II functionality in a REST API with structured JSON input/output."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for dashboard integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Endpoints
# ============================================================================


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """
    Health check endpoint

    Checks if the service is running and if GSAS-II is available.
    Returns status, GSAS-II availability, and service version.
    """
    gsasii_available = False

    try:
        from GSASII import GSASIIscriptable as G2  # noqa: F401

        gsasii_available = True
        status = "healthy"
    except ImportError:
        status = "degraded"

    return HealthResponse(
        status=status, gsasii_available=gsasii_available, version="1.0.0"
    )


@app.post("/refine", response_model=RefinementResult)
def refine(request: RefinementRequest) -> RefinementResult:
    """
    Execute GSAS-II Rietveld refinement

    **Input:**
    - `diffraction_data`: Q and intensity arrays with metadata
    - `recipe`: Refinement configuration (instrument, CIF, parameters)
    - `sample_name`: Sample identifier for output labeling
    - `cycles`: Number of refinement cycles (0 = calculate only, no refinement)
    - `options`: Optional settings (save GPX, generate plot, working directory)

    **Output:**
    - `parameters`: All refined parameters (cell, background, etc.)
    - `cell`: Refined unit cell parameters with ESDs
    - `fit_quality`: Rwp, chi², goodness of fit
    - `fit_profile`: Complete profile (obs, calc, diff, background)
    - `plot_image`: Base64-encoded PNG (optional)
    - `gpx_path`: Path to saved .gpx file (optional)
    - `warnings`: Any warnings from refinement
    - `execution_time_s`: Total execution time

    **Example:**
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
    """
    start_time = time.time()

    try:
        # Import here to provide better error message if GSAS-II unavailable
        from GSASII import GSASIIscriptable as G2  # noqa: F401
    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail=f"GSAS-II not available: {str(e)}. Ensure GSAS-II is installed.",
        )

    try:
        # Import wrapper function
        from gsasii_wrapper import run_gsasii_refinement

        # Prepare input data
        chi_data = (
            request.diffraction_data.q,
            request.diffraction_data.intensity,
        )

        recipe_dict = request.recipe.model_dump()

        # Run refinement
        logger.info(
            f"Starting refinement: sample={request.sample_name}, "
            f"cycles={request.cycles}"
        )

        result = run_gsasii_refinement(
            chi_data=chi_data,
            recipe=recipe_dict,
            sample_name=request.sample_name,
            cycles=request.cycles,
            temp_dir=None,  # Will create temp dir
            save_gpx=request.options.save_gpx,
            generate_plot=request.options.generate_plot,
        )

        # Add execution metadata
        execution_time = time.time() - start_time
        result["execution_time_s"] = execution_time
        result["success"] = True

        logger.info(
            f"Refinement completed: Rwp={result['fit_quality']['Rwp']:.3f}%, "
            f"time={execution_time:.2f}s"
        )

        return RefinementResult(**result)

    except Exception as e:
        logger.error(f"Refinement failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Refinement failed: {str(e)}"
        ) from e


@app.get("/recipes", response_model=RecipeListResponse)
def list_recipes() -> RecipeListResponse:
    """
    List available recipe templates

    Returns bundled recipe templates that can be used as starting points
    for refinements.

    **TODO:** Implement loading from assets/recipes/ directory
    """
    # Placeholder - will be implemented when we add recipe assets
    return RecipeListResponse(recipes=[])


@app.post("/validate_recipe", response_model=RecipeValidationResponse)
def validate_recipe(recipe: Dict[str, Any]) -> RecipeValidationResponse:
    """
    Validate refinement recipe schema

    Checks if a recipe has required keys and valid structure.
    Returns validation errors and warnings.

    **TODO:** Implement recipe validation logic
    """
    # Placeholder - will be implemented with validation logic
    errors = []
    warnings = []

    # Basic check for required keys
    required_keys = ["instrument_file", "cif_file", "phase_name", "refinement_dict"]
    for key in required_keys:
        if key not in recipe:
            errors.append(f"Missing required key: {key}")

    valid = len(errors) == 0

    return RecipeValidationResponse(valid=valid, errors=errors, warnings=warnings)


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    logger.info("Starting GSAS-II Refinement Service on http://0.0.0.0:8002")
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")
