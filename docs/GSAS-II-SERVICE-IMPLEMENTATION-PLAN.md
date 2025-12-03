# GSAS-II Service Implementation Plan

**Date Created:** December 3, 2025  
**Status:** Planning Phase  
**Goal:** Develop GSAS-II refinement service for RoboMage with workflow integration

---

## 🎯 Implementation Phases

### **Phase 1: GSAS-II Microservice Development** (Week 1-2)
Create a standalone FastAPI service that wraps GSAS-II functionality, following the pattern established by RoboMage's `peak_analysis` service.

**Deliverables:**
- `services/gsasii_refinement/` - FastAPI service with GSAS-II integration
- REST API endpoints for refinement requests
- Recipe-based configuration system (YAML)
- Structured JSON output (parameters, fit quality, profiles)

### **Phase 2: Workflow Node Integration** (Week 3)
Add RoboMage workflow node for GSAS-II refinements.

**Deliverables:**
- `src/robomage/workflow/nodes/gsasii_refinement.py` - Workflow node
- Client library in `src/robomage/clients/gsasii_client.py`
- Node registration in workflow registry
- Dashboard integration for service monitoring

---

## 📚 Reference Codebase: autoxrd

**Location:** `/nsls2/users/dolds/dev/autoxrd`  
**Repository:** git@github.com:AdamCorrao/autoxrd.git

### **How to Access autoxrd Files in Future Chats**

Since the autoxrd repository is **outside the RoboMage workspace**, use terminal commands to read files:

```bash
# List directory structure
ls -la /nsls2/users/dolds/dev/autoxrd

# Read specific files
cat /nsls2/users/dolds/dev/autoxrd/README.md
cat /nsls2/users/dolds/dev/autoxrd/fit_service/xrd_pipeline.py
cat /nsls2/users/dolds/dev/autoxrd/fit_service/functions.py

# Find files by pattern
find /nsls2/users/dolds/dev/autoxrd -name "*.yaml" -o -name "*.py"

# Read recipe examples
cat /nsls2/users/dolds/dev/autoxrd/swarm/test/assets/lattice_scale_refinement_recipe.yaml

# Explore DRX Demo (our reference example)
ls -la /nsls2/users/dolds/dev/autoxrd/on-the-fly/test/user_data_DRX_test/
```

### **Key autoxrd Components to Study**

1. **GSAS-II Wrapper Code:**
   - `fit_service/xrd_pipeline.py` - Main pipeline (~600+ lines)
   - `fit_service/functions.py` - Helper functions (~400+ lines)
   - `fit_service/generalized_refinement_schema.md` - Schema documentation

2. **Recipe System:**
   - `swarm/test/assets/lattice_scale_refinement_recipe.yaml` - Example recipe
   - `on-the-fly/test/user_data_DRX_test/userScripts/refinements/assets/` - DRX recipes

3. **DRX Demo (Primary Reference Example):**
   ```bash
   # DRX Demo location
   /nsls2/users/dolds/dev/autoxrd/on-the-fly/test/user_data_DRX_test/
   
   # Key directories:
   # - DRX_data_to_be_dropped_in/  # Input data (.chi files + metadata)
   # - userScripts/refinements/    # Refinement scripts and recipes
   # - userScripts/refinements/assets/  # Recipe YAML files
   ```

4. **GSAS-II Installation Guide:**
   - `GSASII_pixi_installation_instructions.md` - Pixi-based setup

---

## 🔬 DRX Demo as Reference Example

**Why DRX Demo:**
- Real-world beamline workflow
- Production-tested recipe configurations
- Multiple refinement strategies (lattice, size/strain)
- Metadata integration patterns

**Demo Location:**
```
/nsls2/users/dolds/dev/autoxrd/on-the-fly/test/user_data_DRX_test/
├── DRX_data_to_be_dropped_in/    # Simulated beamline data
│   ├── xrd_LaB6_660c_std_brac2/  # Example dataset
│   │   ├── integration/          # .chi diffraction files
│   │   └── meta/                 # YAML metadata
│   └── xrd_3_LMT_AlNb_O_10/     # Another example
├── userScripts/
│   └── refinements/
│       ├── assets/               # Recipe files (CRITICAL)
│       │   ├── IPF_fit_recipe.yaml
│       │   ├── recipe_3_lattice.yaml
│       │   └── recipe_3_lattice_sizestrain.yaml
│       └── [refinement scripts]
└── [other demo files]
```

**Key Files to Study:**
```bash
# Read DRX recipe examples
cat /nsls2/users/dolds/dev/autoxrd/on-the-fly/test/user_data_DRX_test/userScripts/refinements/assets/IPF_fit_recipe.yaml
cat /nsls2/users/dolds/dev/autoxrd/on-the-fly/test/user_data_DRX_test/userScripts/refinements/assets/recipe_3_lattice.yaml
cat /nsls2/users/dolds/dev/autoxrd/on-the-fly/test/user_data_DRX_test/userScripts/refinements/assets/recipe_3_lattice_sizestrain.yaml

# Examine metadata format
find /nsls2/users/dolds/dev/autoxrd/on-the-fly/test/user_data_DRX_test/DRX_data_to_be_dropped_in -name "*.yaml" | head -3 | xargs cat

# Check integration data (.chi files)
ls -lh /nsls2/users/dolds/dev/autoxrd/on-the-fly/test/user_data_DRX_test/DRX_data_to_be_dropped_in/xrd_LaB6_660c_std_brac2/integration/
```

---

## 🏗️ Technical Architecture

### **Recipe-Based Configuration**
Following autoxrd's proven YAML recipe format:

```yaml
recipe_description: "Lattice refinement"
instrument_file: "myiprms.instprm"  # Instrument parameters
cif_file: "LaB6_SRM_660c.CIF"       # Crystal structure
phase_name: "LaB6"
refinement_dict:
  set:
    Limits: {low: 1, high: 15}      # Q-range or 2θ range
    Background: {type: "chebyshev-1", "no. coeffs": 4, refine: true}
    Sample Parameters: ["Scale"]
    Cell: true                       # Refine lattice parameters
```

### **Service Design (Mirrors peak_analysis service)**

```
services/gsasii_refinement/
├── main.py                  # FastAPI app
├── models.py                # Pydantic request/response models
├── gsasii_wrapper.py        # GSAS-II Python API wrapper (adapted from autoxrd)
├── requirements.txt         # Dependencies (FastAPI, uvicorn, gsas-ii)
├── test_service.py          # Service tests
└── README.md
```

**API Endpoints (Proposed):**
- `POST /refine` - Submit refinement job
- `GET /health` - Service health check
- `GET /recipes` - List available recipe templates
- `POST /validate_recipe` - Validate recipe YAML

**Request Model:**
```python
class RefinementRequest(BaseModel):
    diffraction_data: DiffractionData  # RoboMage data model
    recipe: dict                        # YAML recipe as dict
    instrument_file: str                # Path or base64
    cif_file: str                       # Path or base64
    cycles: int = 3                     # Refinement cycles
```

**Response Model:**
```python
class RefinementResult(BaseModel):
    success: bool
    parameters: dict                    # Refined parameters
    fit_quality: dict                   # Rwp, chi2, etc.
    fit_profile: FitProfile            # Obs, calc, diff curves
    warnings: list[str]
```

### **Workflow Node Design**

```python
# src/robomage/workflow/nodes/gsasii_refinement.py
@workflow_node(
    name="gsasii_refinement",
    display_name="GSAS-II Refinement",
    category="analysis",
    description="Rietveld refinement using GSAS-II"
)
def gsasii_refinement_handler(
    context: ExecutionContext,
    inputs: dict,
    params: dict
) -> NodeExecutionResult:
    """
    Params:
        recipe_file: str         # Path to recipe YAML
        instrument_file: str     # Path to instrument parameters
        cif_file: str           # Path to CIF structure
        cycles: int = 3         # Number of refinement cycles
        refine_background: bool = True
        refine_cell: bool = True
    """
    # Get diffraction data from context
    # Call GSAS-II service via client
    # Return refinement results
```

---

## 🔧 Implementation Steps

### **Step 1: Study autoxrd Code** (Days 1-2)
- [ ] Read `fit_service/xrd_pipeline.py` in full
- [ ] Study `fit_service/functions.py` helper methods
- [ ] Analyze DRX Demo recipes and understand parameters
- [ ] Document GSAS-II API patterns used in autoxrd
- [ ] Identify reusable code segments

### **Step 2: Extract & Adapt GSAS-II Wrapper** (Days 3-5)
- [ ] Create `gsasii_wrapper.py` based on autoxrd's approach
- [ ] Implement recipe loading and validation
- [ ] Handle instrument file and CIF file resolution
- [ ] Add error handling and logging
- [ ] Write unit tests for wrapper functions

### **Step 3: Build FastAPI Service** (Days 6-8)
- [ ] Create service scaffold (main.py, models.py)
- [ ] Implement `/refine` endpoint
- [ ] Add Pydantic models for request/response
- [ ] Integrate GSAS-II wrapper
- [ ] Add health check and diagnostics
- [ ] Write integration tests

### **Step 4: Service Testing** (Days 9-10)
- [ ] Test with DRX Demo data
- [ ] Validate against known refinement results
- [ ] Performance benchmarking
- [ ] Error case handling

### **Step 5: Workflow Integration** (Days 11-13)
- [ ] Create `gsasii_refinement` workflow node
- [ ] Implement client library
- [ ] Add to node registry
- [ ] Dashboard service monitoring integration
- [ ] Write workflow integration tests

### **Step 6: Documentation & Examples** (Days 14-15)
- [ ] Service API documentation
- [ ] Example recipes for common cases
- [ ] Workflow tutorial with DRX Demo
- [ ] Update RoboMage docs

---

## 📋 Key Decisions to Make

1. **Recipe Storage:**
   - Store recipes in database? (Session-linked)
   - File-based recipe library?
   - User-uploaded recipes?

2. **Instrument/CIF Management:**
   - Bundle common files with service?
   - User provides via upload?
   - Database storage?

3. **Output Storage:**
   - Store .gpx files? (Can be large)
   - CSV + JSON summary only?
   - HDF5 for large results?

4. **Service Deployment:**
   - Standalone service like peak_analysis?
   - Shared infrastructure?
   - Resource requirements (GSAS-II can be intensive)?

---

## 🎓 Learning from autoxrd

**What autoxrd Does Well:**
- ✅ Robust path resolution (absolute/relative recipe paths)
- ✅ Structured output formats (CSV, JSON, profile data)
- ✅ Recipe-based configuration (reproducible)
- ✅ Comprehensive metadata tracking
- ✅ Pixi environment management

**What We'll Adapt for RoboMage:**
- ✅ REST API instead of file-watching
- ✅ Pydantic models instead of dataclasses
- ✅ Session-based storage integration
- ✅ Workflow orchestration
- ✅ Dashboard visualization

**What We'll Add:**
- ✅ Multi-file batch refinements
- ✅ Interactive parameter adjustment
- ✅ Real-time refinement progress
- ✅ Comparison workflows (before/after)
- ✅ Export to common formats

---

## 🔗 Integration with RoboMage Architecture

**Fits Existing Patterns:**
- Microservice architecture (like `peak_analysis`)
- Pydantic data models (`DiffractionData`)
- Client library pattern (`GSASIIClient`)
- Workflow node system
- Session persistence (results stored in database)
- Dashboard integration

**New Patterns:**
- Recipe-based configuration system
- Multi-stage refinement workflows
- Structure file (CIF) management
- Instrument parameter handling

---

## 📊 Success Criteria

**Service MVP:**
- [ ] Successfully refines DRX Demo LaB6 data
- [ ] Returns Rwp, chi2, refined parameters
- [ ] Generates fit profile data
- [ ] Handles errors gracefully
- [ ] 100% test coverage for core functions

**Workflow Integration:**
- [ ] Node appears in dashboard palette
- [ ] Executes refinements from workflow
- [ ] Results display in Analysis tab
- [ ] Results persist to session database
- [ ] Can chain with other nodes (load → refine → export)

**Documentation:**
- [ ] Service API documented
- [ ] Recipe format specification
- [ ] User guide with DRX Demo example
- [ ] Developer guide for extending

---

## 🚀 Getting Started (For Next Chat)

**Initial Commands:**
```bash
# Explore DRX Demo structure
ls -R /nsls2/users/dolds/dev/autoxrd/on-the-fly/test/user_data_DRX_test/

# Read core GSAS-II wrapper
cat /nsls2/users/dolds/dev/autoxrd/fit_service/xrd_pipeline.py | head -200

# Study DRX recipes
cat /nsls2/users/dolds/dev/autoxrd/on-the-fly/test/user_data_DRX_test/userScripts/refinements/assets/recipe_3_lattice.yaml

# Check autoxrd dependencies
cat /nsls2/users/dolds/dev/autoxrd/pixi.toml
```

**Context for AI:**
- RoboMage cleanup COMPLETE (380/380 tests passing)
- Foundation ready for new development
- Follow existing microservice patterns (see `services/peak_analysis/`)
- Use DRX Demo as reference example
- Leverage autoxrd's proven GSAS-II integration code

---

## 📝 Notes

**Why Start with Service First:**
- Can develop/test independently
- Clear API contract before workflow integration
- Easier to validate against autoxrd's known results
- Service can evolve without breaking workflows initially

**Why Use DRX Demo:**
- Real beamline workflow (NSLS-II)
- Multiple refinement strategies
- Production-tested configurations
- Comprehensive test data

**Timeline Estimate:**
- Service MVP: 2 weeks
- Workflow integration: 1 week
- Total: ~3 weeks to working prototype

---

**Next Steps:** Begin with Step 1 - deep dive into autoxrd code, starting with DRX Demo exploration.
