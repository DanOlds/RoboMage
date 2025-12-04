# GSAS-II Service Design Document

**Date Created:** December 3, 2025  
**Branch:** `feature/gsasii-service`  
**Status:** Initial Design Phase

---

## Executive Summary

This document outlines the design for RoboMage's GSAS-II refinement microservice, which will provide Rietveld refinement capabilities following the established pattern of the `peak_analysis` service.

**Key Design Principles:**
1. **REST API First** - FastAPI service with JSON request/response
2. **Recipe-Based Configuration** - YAML recipes adapted from autoxrd's proven approach
3. **Pydantic Validation** - Strong typing at API boundaries
4. **Stateless Service** - No persistent storage, pure computation
5. **Client Library Pattern** - HTTP client in `src/robomage/clients/`

---

## Reference Implementation Analysis

### autoxrd's GSAS-II Integration

**Core Function:** `run_gsas_refinement()` in `fit_service/xrd_pipeline.py`

**Key Insights:**
1. **Input Requirements:**
   - Diffraction data file (.chi format)
   - Recipe YAML (instrument, CIF, phase, refinement parameters)
   - Sample name (for output labeling)

2. **Recipe Structure:**
   ```yaml
   recipe_description: "DRX_fit_sample3_lattice_refinement"
   instrument_file: "PDF_1m.instprm"
   cif_file: "3_LMTAlNbO-10_start.cif"
   phase_name: "LMTAlNbO"
   refinement_dict:
     set:
       Limits: {low: 1, high: 15}
       Background: {type: "chebyschev-1", "no. coeffs": 30, refine: true}
       Cell: true
       Sample Parameters: ["Scale"]
   ```

3. **GSAS-II API Usage:**
   ```python
   from GSASII import GSASIIscriptable as G2
   
   # Create project
   proj = G2.G2Project(newgpx=str(gpx_path))
   
   # Add histogram (data + instrument)
   hist = proj.add_powder_histogram(chi_file, instrument_file)
   
   # Add phase (structure)
   phase = proj.add_phase(cif_file, phasename=phase_name, histograms=[hist])
   
   # Set refinement cycles
   proj.set_Controls('cycles', 5)
   
   # Execute refinement
   proj.do_refinements([refinement_dict])
   
   # Extract results
   cell, cell_esds = phase.get_cell_and_esd()
   rwp = hist.residuals.get("wR")
   ```

4. **Output Structure:**
   - `parameters.csv` - Rwp, cell parameters, ESDs
   - `fit_profile.txt` - 2θ, Q, d-spacing, Yobs, Ycalc, Ydiff, Ybkg, weights
   - `fit_plot.png` - Visual comparison
   - `.gpx` file - GSAS-II project (optional)

---

## Service Architecture

### Directory Structure

```
services/gsasii_refinement/
├── main.py                  # FastAPI application
├── models.py                # Pydantic request/response models
├── gsasii_wrapper.py        # GSAS-II API wrapper (adapted from autoxrd)
├── recipe_validator.py      # Recipe schema validation
├── requirements.txt         # Service dependencies
├── test_service.py          # Integration tests
├── assets/                  # Bundled test recipes and CIFs
│   ├── recipes/
│   │   ├── lattice_only.yaml
│   │   ├── lattice_sizestrain.yaml
│   │   └── instrument_profile.yaml
│   ├── cifs/
│   │   ├── LaB6_SRM_660c.CIF
│   │   └── [common structures]
│   └── instruments/
│       ├── PDF_1m.instprm
│       └── dummy_instr.instprm
└── README.md
```

### API Endpoints

**1. POST /refine**
```python
{
  "diffraction_data": {
    "q": [...],
    "intensity": [...],
    "metadata": {...}
  },
  "recipe": {
    "instrument_file": "PDF_1m.instprm",  # or base64-encoded content
    "cif_file": "LaB6_SRM_660c.CIF",      # or base64-encoded content
    "phase_name": "LaB6",
    "refinement_dict": {...}
  },
  "sample_name": "LaB6_test",
  "cycles": 5,
  "options": {
    "save_gpx": false,
    "generate_plot": true
  }
}
```

**Response:**
```python
{
  "success": true,
  "parameters": {
    "Rwp": 2.34,
    "chi2": 1.23,
    "cell": {
      "a": {"value": 4.156, "esd": 0.001},
      "b": {"value": 4.156, "esd": 0.001},
      "c": {"value": 4.156, "esd": 0.001},
      "alpha": {"value": 90.0, "esd": 0.0},
      "beta": {"value": 90.0, "esd": 0.0},
      "gamma": {"value": 90.0, "esd": 0.0},
      "volume": {"value": 71.7, "esd": 0.02}
    }
  },
  "fit_profile": {
    "two_theta": [...],
    "q_values": [...],
    "d_spacings": [...],
    "y_obs": [...],
    "y_calc": [...],
    "y_diff": [...],
    "y_bkg": [...],
    "y_weights": [...]
  },
  "plot_image": "data:image/png;base64,...",  # Optional
  "warnings": [],
  "execution_time_s": 12.3
}
```

**2. GET /health**
```python
{
  "status": "healthy",
  "gsasii_available": true,
  "version": "1.0.0"
}
```

**3. GET /recipes**
```python
{
  "recipes": [
    {
      "name": "lattice_only",
      "description": "Lattice parameter refinement only",
      "template": {...}
    },
    ...
  ]
}
```

**4. POST /validate_recipe**
```python
# Request
{
  "recipe": {...}
}

# Response
{
  "valid": true,
  "errors": [],
  "warnings": ["Background coefficients not specified, will use defaults"]
}
```

---

## Data Models (Pydantic)

### Request Models

```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class DiffractionData(BaseModel):
    """Diffraction pattern data"""
    q: List[float] = Field(..., description="Q values (Å⁻¹)")
    intensity: List[float] = Field(..., description="Intensity values")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('q', 'intensity')
    def validate_arrays(cls, v):
        if len(v) == 0:
            raise ValueError("Arrays must not be empty")
        return v

class RefinementDict(BaseModel):
    """GSAS-II refinement dictionary (set/do structure)"""
    set: Dict[str, Any] = Field(..., description="Refinement parameters")
    
    class Config:
        extra = "allow"  # Allow additional keys for flexibility

class Recipe(BaseModel):
    """Refinement recipe configuration"""
    instrument_file: str = Field(..., description="Instrument parameter file (path or base64)")
    cif_file: str = Field(..., description="CIF structure file (path or base64)")
    phase_name: str = Field(..., description="Phase name in CIF")
    refinement_dict: RefinementDict
    recipe_description: Optional[str] = None

class RefinementOptions(BaseModel):
    """Optional refinement settings"""
    save_gpx: bool = Field(False, description="Save GSAS-II project file")
    generate_plot: bool = Field(True, description="Generate fit plot")
    working_dir: Optional[str] = Field(None, description="Custom working directory")

class RefinementRequest(BaseModel):
    """Complete refinement request"""
    diffraction_data: DiffractionData
    recipe: Recipe
    sample_name: str
    cycles: int = Field(5, ge=0, le=20, description="Number of refinement cycles")
    options: RefinementOptions = Field(default_factory=RefinementOptions)
```

### Response Models

```python
class CellParameter(BaseModel):
    """Cell parameter with uncertainty"""
    value: float
    esd: float

class CellParameters(BaseModel):
    """Refined unit cell parameters"""
    a: CellParameter
    b: CellParameter
    c: CellParameter
    alpha: CellParameter
    beta: CellParameter
    gamma: CellParameter
    volume: CellParameter

class FitQuality(BaseModel):
    """Fit quality metrics"""
    Rwp: float = Field(..., description="Weighted R-factor (%)")
    chi2: Optional[float] = Field(None, description="Chi-squared")
    GoF: Optional[float] = Field(None, description="Goodness of fit")

class FitProfile(BaseModel):
    """Complete fit profile data"""
    two_theta: List[float]
    q_values: List[float]
    d_spacings: List[float]
    y_obs: List[float]
    y_calc: List[float]
    y_diff: List[float]
    y_bkg: List[float]
    y_weights: List[float]

class RefinementResult(BaseModel):
    """Complete refinement result"""
    success: bool
    parameters: Dict[str, Any] = Field(..., description="All refined parameters")
    cell: CellParameters
    fit_quality: FitQuality
    fit_profile: FitProfile
    plot_image: Optional[str] = Field(None, description="Base64-encoded PNG")
    gpx_path: Optional[str] = Field(None, description="Path to .gpx file if saved")
    warnings: List[str] = Field(default_factory=list)
    execution_time_s: float
```

---

## GSAS-II Wrapper Module

### Design Philosophy

**Adapt, Don't Copy:**
- Reuse autoxrd's GSAS-II interaction patterns
- Simplify for REST API use case (no file watching)
- Add explicit error handling and validation
- Support both file paths and base64-encoded content

### Key Functions

```python
# gsasii_wrapper.py

from pathlib import Path
from typing import Dict, Any, Tuple
import tempfile
import base64

def is_base64_content(s: str) -> bool:
    """Check if string is base64-encoded content vs file path"""
    return s.startswith("data:") or (len(s) > 100 and "=" in s)

def resolve_file(content: str, extension: str, temp_dir: Path) -> Path:
    """Resolve file path or decode base64 content to temp file"""
    if is_base64_content(content):
        # Decode base64 and write to temp file
        if content.startswith("data:"):
            content = content.split(",", 1)[1]
        data = base64.b64decode(content)
        temp_file = temp_dir / f"temp{extension}"
        temp_file.write_bytes(data)
        return temp_file
    else:
        # Treat as file path
        path = Path(content)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {content}")
        return path

def run_gsasii_refinement(
    chi_data: Tuple[list, list],  # (q, intensity) arrays
    recipe: Dict[str, Any],
    sample_name: str,
    cycles: int = 5,
    temp_dir: Optional[Path] = None,
    save_gpx: bool = False,
    generate_plot: bool = True
) -> Dict[str, Any]:
    """
    Run GSAS-II refinement and return structured results.
    
    Adapted from autoxrd's run_gsas_refinement() but modified for:
    - Array input (not file input)
    - Structured dict output (not CSV/TXT files)
    - Temporary file management
    - Base64 support for instrument/CIF files
    """
    from GSASII import GSASIIscriptable as G2
    import numpy as np
    import matplotlib.pyplot as plt
    import io
    
    if temp_dir is None:
        temp_dir = Path(tempfile.mkdtemp(prefix="gsasii_"))
    
    try:
        # 1. Write diffraction data to temp .chi file
        chi_file = temp_dir / f"{sample_name}.chi"
        q_array, intensity_array = chi_data
        write_chi_file(chi_file, q_array, intensity_array)
        
        # 2. Resolve instrument and CIF files (support both paths and base64)
        instrument_file = resolve_file(recipe["instrument_file"], ".instprm", temp_dir)
        cif_file = resolve_file(recipe["cif_file"], ".cif", temp_dir)
        
        # 3. Create GSAS-II project
        gpx_path = temp_dir / f"{sample_name}.gpx"
        proj = G2.G2Project(newgpx=str(gpx_path))
        
        # 4. Add histogram and phase
        hist = proj.add_powder_histogram(str(chi_file), str(instrument_file))
        phase = proj.add_phase(str(cif_file), phasename=recipe["phase_name"], histograms=[hist])
        
        # 5. Set refinement cycles
        proj.set_Controls('cycles', cycles)
        
        # 6. Execute refinement
        proj.do_refinements([recipe["refinement_dict"]])
        
        # 7. Extract results
        cell, cell_esds = phase.get_cell_and_esd()
        
        results = {
            "parameters": extract_all_parameters(phase, hist),
            "cell": {
                "a": {"value": cell.get("length_a"), "esd": cell_esds.get("length_a")},
                "b": {"value": cell.get("length_b"), "esd": cell_esds.get("length_b")},
                "c": {"value": cell.get("length_c"), "esd": cell_esds.get("length_c")},
                "alpha": {"value": cell.get("angle_alpha"), "esd": cell_esds.get("angle_alpha")},
                "beta": {"value": cell.get("angle_beta"), "esd": cell_esds.get("angle_beta")},
                "gamma": {"value": cell.get("angle_gamma"), "esd": cell_esds.get("angle_gamma")},
                "volume": {"value": cell.get("volume"), "esd": cell_esds.get("volume")}
            },
            "fit_quality": {
                "Rwp": hist.residuals.get("wR"),
                "chi2": hist.residuals.get("chi2") if hasattr(hist.residuals, "get") else None
            },
            "fit_profile": {
                "two_theta": hist.getdata(datatype="X").tolist(),
                "q_values": hist.getdata(datatype="Q").tolist(),
                "d_spacings": hist.getdata(datatype="d").tolist(),
                "y_obs": hist.getdata(datatype="Yobs").tolist(),
                "y_calc": hist.getdata(datatype="Ycalc").tolist(),
                "y_diff": hist.getdata(datatype="Residual").tolist(),
                "y_bkg": hist.getdata(datatype="Background").tolist(),
                "y_weights": hist.getdata(datatype="Yweight").tolist()
            },
            "warnings": []
        }
        
        # 8. Generate plot if requested
        if generate_plot:
            fig = create_fit_plot(results["fit_profile"], sample_name, results["fit_quality"]["Rwp"])
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=150)
            plt.close(fig)
            buf.seek(0)
            results["plot_image"] = f"data:image/png;base64,{base64.b64encode(buf.read()).decode()}"
        
        # 9. Handle GPX file
        if save_gpx:
            results["gpx_path"] = str(gpx_path)
        else:
            gpx_path.unlink(missing_ok=True)
        
        return results
        
    finally:
        # Cleanup temp files if we created the temp_dir
        if not save_gpx and temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)

def write_chi_file(path: Path, q: list, intensity: list):
    """Write Q, I data to .chi format"""
    with path.open('w') as f:
        f.write("# Q(A^-1)  Intensity\n")
        for q_val, i_val in zip(q, intensity):
            f.write(f"{q_val:.6f}  {i_val:.6f}\n")

def create_fit_plot(fit_profile: dict, sample_name: str, rwp: float):
    """Create fit comparison plot (obs vs calc vs diff)"""
    # Similar to autoxrd's plotting code
    fig, ax = plt.subplots(figsize=(8, 5))
    
    tt = fit_profile["two_theta"]
    y_obs = fit_profile["y_obs"]
    y_calc = fit_profile["y_calc"]
    y_diff = fit_profile["y_diff"]
    
    ax.scatter(tt, y_obs, marker="o", edgecolor="black", facecolor="None", label="Observed", s=5)
    ax.plot(tt, y_calc, label="Calculated", color="red", alpha=0.9)
    ax.plot(tt, y_diff, label="Difference", color="gray", alpha=0.7)
    ax.set_xlabel(r"2θ (°)")
    ax.set_ylabel("Intensity (counts)")
    ax.set_title(f"{sample_name} (Rwp={rwp:.3f}%)")
    ax.legend()
    fig.tight_layout()
    
    return fig
```

---

## FastAPI Service Implementation

```python
# main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import time
from typing import Dict, Any

from .models import RefinementRequest, RefinementResult
from .gsasii_wrapper import run_gsasii_refinement

app = FastAPI(
    title="GSAS-II Refinement Service",
    description="Rietveld refinement microservice for RoboMage",
    version="1.0.0"
)

# CORS for dashboard integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check() -> Dict[str, Any]:
    """Health check endpoint"""
    try:
        from GSASII import GSASIIscriptable as G2
        gsasii_available = True
    except ImportError:
        gsasii_available = False
    
    return {
        "status": "healthy" if gsasii_available else "degraded",
        "gsasii_available": gsasii_available,
        "version": "1.0.0"
    }

@app.post("/refine", response_model=RefinementResult)
def refine(request: RefinementRequest) -> RefinementResult:
    """
    Execute GSAS-II Rietveld refinement
    
    **Input:**
    - Diffraction data (Q, intensity arrays)
    - Recipe (instrument, CIF, refinement parameters)
    - Sample name and options
    
    **Output:**
    - Refined parameters (cell, Rwp, etc.)
    - Fit profile (obs, calc, diff curves)
    - Optional plot image
    """
    start_time = time.time()
    
    try:
        # Prepare input data
        chi_data = (
            request.diffraction_data.q,
            request.diffraction_data.intensity
        )
        recipe_dict = request.recipe.model_dump()
        
        # Run refinement
        result = run_gsasii_refinement(
            chi_data=chi_data,
            recipe=recipe_dict,
            sample_name=request.sample_name,
            cycles=request.cycles,
            save_gpx=request.options.save_gpx,
            generate_plot=request.options.generate_plot
        )
        
        # Add execution time
        result["execution_time_s"] = time.time() - start_time
        result["success"] = True
        
        return RefinementResult(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Refinement failed: {str(e)}"
        )

@app.get("/recipes")
def list_recipes() -> Dict[str, Any]:
    """List available recipe templates"""
    # Load bundled recipe templates from assets/recipes/
    # Return as dict with descriptions
    pass

@app.post("/validate_recipe")
def validate_recipe(recipe: Dict[str, Any]) -> Dict[str, Any]:
    """Validate recipe schema"""
    # Check required keys, warn about defaults, etc.
    pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
```

---

## Testing Strategy

### Unit Tests

```python
# test_service.py

import pytest
from fastapi.testclient import TestClient
from .main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert "gsasii_available" in response.json()

def test_refine_with_lab6():
    """Test refinement with LaB6 standard"""
    # Load test data from autoxrd DRX Demo
    # Send refinement request
    # Verify Rwp < 5% (LaB6 is a good standard)
    pass

def test_invalid_recipe():
    """Test error handling for invalid recipe"""
    pass

def test_base64_cif():
    """Test base64-encoded CIF file"""
    pass
```

### Integration Tests

```python
def test_drx_demo_workflow():
    """
    Full workflow test using DRX Demo data:
    1. Load LaB6 .chi file
    2. Use IPF_fit_recipe.yaml
    3. Verify results match autoxrd's output
    """
    pass
```

---

## Client Library Design

```python
# src/robomage/clients/gsasii_client.py

from typing import Dict, Any
import requests
from robomage.data.models import DiffractionData

class GSASIIClient:
    """Client for GSAS-II refinement service"""
    
    def __init__(self, base_url: str = "http://localhost:8002"):
        self.base_url = base_url
    
    def health(self) -> Dict[str, Any]:
        """Check service health"""
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def refine(
        self,
        data: DiffractionData,
        recipe: Dict[str, Any],
        sample_name: str,
        cycles: int = 5,
        **options
    ) -> Dict[str, Any]:
        """Execute refinement"""
        payload = {
            "diffraction_data": {
                "q": data.q.tolist(),
                "intensity": data.intensity.tolist(),
                "metadata": data.metadata
            },
            "recipe": recipe,
            "sample_name": sample_name,
            "cycles": cycles,
            "options": options
        }
        
        response = requests.post(
            f"{self.base_url}/refine",
            json=payload,
            timeout=300  # Refinement can take time
        )
        response.raise_for_status()
        return response.json()
```

---

## Next Steps

### Phase 1a: Service Scaffold (Days 1-2)
- [x] Read implementation plan
- [x] Study autoxrd codebase
- [x] Design service architecture
- [ ] Create service directory structure
- [ ] Set up FastAPI skeleton
- [ ] Add Pydantic models
- [ ] Implement health check endpoint

### Phase 1b: GSAS-II Wrapper (Days 3-4)
- [ ] Extract core refinement logic from autoxrd
- [ ] Implement `gsasii_wrapper.py` with array input
- [ ] Add file resolution (paths + base64)
- [ ] Write unit tests for wrapper

### Phase 1c: Service Integration (Days 5-6)
- [ ] Implement `/refine` endpoint
- [ ] Add bundled recipe assets
- [ ] Test with DRX Demo data
- [ ] Verify results match autoxrd

---

## Open Questions

1. **GSAS-II Installation:**
   - How to handle GSAS-II dependency in pixi.toml?
   - Conda package vs manual install?

2. **Recipe Storage:**
   - Bundle common recipes with service?
   - Allow user uploads?
   - Store in database for session management?

3. **Performance:**
   - Expected refinement time for typical patterns?
   - Need async/background task support?
   - Queue management for multiple requests?

4. **Error Handling:**
   - How to detect refinement convergence failures?
   - What to do with non-converged results?
   - Return partial results or fail completely?

---

## Success Metrics

**Service MVP Complete When:**
- [ ] LaB6 IPF fit reproduces autoxrd's Rwp
- [ ] DRX lattice refinement works correctly
- [ ] Service passes all integration tests
- [ ] Client library successfully calls service
- [ ] Documentation complete

**Timeline:** 6-8 days for service MVP
