# GitHub Copilot Instructions for RoboMage

## Project Overview
RoboMage is a powder diffraction analysis framework with a **microservices architecture** supporting both modern Pydantic-based models and legacy pandas DataFrames. The project uses Pixi for environment management and implements independent analysis engines for scientific workflows including peak detection and future Rietveld refinement.

## Architecture Patterns

### Microservices Design
- **Core Framework**: `src/robomage/` - Data models, loaders, and client libraries
- **Independent Services**: `services/peak_analysis/` - FastAPI microservice with JSON API
- **Service Clients**: `src/robomage/clients/` - HTTP clients for service integration
- **CLI Tools**: `peak_analyzer.py` - Standalone CLI with multiple operation modes
- **Orchestrator**: `src/robomage/orchestrator.py` - Service coordination (planned)

### Dual API Design
- **Modern API**: `robomage.load_diffraction_file()` → `DiffractionData` (Pydantic models)
- **Legacy API**: `robomage.load_test_data_df()` → `pandas.DataFrame`
- Both APIs are exposed through `src/robomage/__init__.py` with clear naming conventions

### Service Communication Pattern
1. **Load**: RoboMage loads `DiffractionData` with validation
2. **Serialize**: Client converts to JSON via `PeakAnalysisClient`
3. **Analyze**: Independent FastAPI service processes data
4. **Return**: JSON response with peaks, fits, and statistics
5. **Integrate**: Results stored/visualized in RoboMage framework

### Validation Philosophy
- **Pydantic v2**: All data models inherit from `BaseModel` with strict validation
- **Service Boundaries**: JSON schema validation at API boundaries
- **Immutable by design**: Data transformations return new instances with preserved metadata
- **Scientific validation**: Units (Å⁻¹ for Q), NaN/inf detection, proper ranges

## Essential Development Commands

### ⚠️ CRITICAL: Use Pixi for Environment Management
**This project EXCLUSIVELY uses Pixi (NOT pip/conda/venv)** for dependency and task management. All development commands must use pixi.

### Pixi Workflow
```bash
pixi install                    # Setup environment (replaces pip install/conda create)
pixi run test                   # Run pytest suite (includes integration tests)
pixi run check                  # Format + lint + typecheck + test (recommended before commits)
pixi run format                 # ruff format .
pixi run lint                   # ruff check .
pixi run typecheck              # mypy src
```

**Why Pixi?**
- ✅ Fast cross-platform dependency resolution
- ✅ Reproducible environments with lockfiles
- ✅ Integrated task management (no separate Makefile)
- ✅ conda-forge package ecosystem
- ✅ All dependencies defined in `pixi.toml`

### Service Development
```bash
# Peak Analysis Service (FastAPI)
cd services/peak_analysis
python main.py --port 8001 --host 0.0.0.0    # Start service locally
curl http://localhost:8001/health              # Health check
curl http://localhost:8001/docs                # OpenAPI documentation

# CLI Peak Analysis (Multiple modes)
python peak_analyzer.py direct file.chi        # Direct analysis
python peak_analyzer.py service --port 8001    # Service mode
python peak_analyzer.py client file.chi        # Client mode
```

### Dashboard Development (Sprint 4 + Sprint 5)
```bash
# Dashboard Development
python -m robomage.dashboard                       # Start dashboard (port 8050)
python -m robomage --dashboard --dashboard-port 8051  # Custom port
pixi run python -m pytest tests/test_dashboard*   # Dashboard-specific tests
```

**Dashboard Architecture:**
- **Tab Structure**: 4-tab layout (Data Import, Visualization, Analysis, Workflow Builder)
- **Session Integration**: Auto-create default session on load, save/load workflow results
- **Session Persistence**: Save/load/manage analysis sessions with all files and metadata
- **Storage Configuration**: Configurable storage location (default: ~/.robomage/)
- **Debug Tools**: Built-in debug panel for inspecting session data
- **Wavelength System**: Per-file assignment, 0.1665 Å synchrotron default, accurate Q→2θ conversion
- **File Management**: Upload, validate, remove files with instant visual feedback
- **Plotting**: Line, scatter, filled area, export options, peak overlays with tooltips
- **Analysis Integration**: Real-time peak detection with FastAPI service integration
- **Workflow Builder**: Visual JSON editor, execute workflows, save results to session
- **Interactive Controls**: Profile selection (Gaussian/Lorentzian/Voigt), prominence, distance, sensitivity sliders
- **Results Display**: Professional tables with fit quality metrics, scrollable per-file results
- **Service Monitoring**: Health check indicators with startup instructions
- **State Management**: Inter-tab communication via dcc.Store
- **File Structure**: 
  - `src/robomage/dashboard/layouts/`: Tab-specific layouts
  - `src/robomage/dashboard/callbacks/`: Tab-specific callback functions (file upload, removal, plotting, analysis, persistence, workflow)
  - `src/robomage/dashboard/components/`: Reusable UI components
  - `src/robomage/persistence/`: Complete persistence layer (database, file store, API)

## Code Conventions

### File Organization
- `src/robomage/data/`: Core data structures (models.py, loaders.py)
- `src/robomage/data_io.py`: Legacy pandas-based API
- `src/robomage/__main__.py`: CLI implementation for data loading/testing
- `src/robomage/clients/`: HTTP clients for microservice communication
- `src/robomage/dashboard/`: Dash-based visualization dashboard (Sprint 4-6)
- `src/robomage/persistence/`: Complete persistence layer (Sprint 5)
  - `database.py`: SQLAlchemy ORM and database management
  - `models.py`: Database models (Session, File) - **Sprint 7 will add AnalysisResult**
  - `file_store.py`: HDF5-based file storage
  - `api.py`: SessionManager high-level API
- `src/robomage/workflow/`: Workflow definition and node implementations
  - `nodes/`: Workflow node types (load_files, peak_analysis, export_csv)
- `src/robomage/visualization.py`: Publication-quality plotting utilities (Sprint 4)
- `src/robomage/orchestrator.py`: DAG-based workflow execution engine (Sprint 6)
- `services/peak_analysis/`: Independent FastAPI microservice for peak detection
- `services/workflow_engine/`: FastAPI service for workflow execution
- `peak_analyzer.py`: Standalone CLI tool for peak analysis workflows

### Service Architecture Patterns
- **Independent Services**: FastAPI apps in `services/` with their own requirements.txt
- **Client Libraries**: HTTP clients in `src/robomage/clients/` with retry logic and validation
- **JSON Communication**: Pydantic models for request/response validation at service boundaries
- **Multi-mode CLIs**: Tools support direct, service, and client operation modes

### Testing Patterns
- Test files mirror source structure: `test_data_models.py`, `test_data_loaders.py`
- Integration tests: `test_peak_analysis_integration.py` for service communication
- Use pytest with parametrization for multiple test cases
- Built-in SRM 660b test data available via `load_test_data()`

### Documentation Standards
- Comprehensive docstrings with scientific context and examples
- Domain-specific terminology: Q-space, momentum transfer (Å⁻¹), powder diffraction
- Both modern and legacy API usage examples in docstrings

## Critical Dependencies
- **Pydantic v2**: Data validation and computed fields
- **NumPy/Pandas**: Scientific computing backbone
- **Pixi**: Environment management (NOT conda/pip)
- **Ruff**: Formatting/linting (88-character line limit)
- **MyPy**: Type checking with strict compliance
- **FastAPI**: Microservice framework for independent analysis engines
- **SciPy**: Scientific algorithms for peak detection and fitting
- **Dash**: Interactive web dashboard framework (Sprint 4)
- **Plotly**: Interactive scientific plotting (Sprint 4)
- **Dash Bootstrap Components**: Professional UI components for dashboard
- **SQLAlchemy**: ORM for session persistence (Sprint 5)
- **h5py**: HDF5 file storage for data persistence (Sprint 5)

## Current Sprint Status

**✅ Sprint 6 Days 5-6 - Workflow Session Integration: COMPLETE (November 27, 2025)**

**Completed Deliverables:**
- ✅ **Auto-Session Creation** - Dashboard auto-creates "Default Session YYYY-MM-DD" on load
- ✅ **Session File Loading** - Existing session files load automatically on startup
- ✅ **Workflow Save Integration** - Save workflow results (files, metadata) directly to active session
- ✅ **UI Auto-Refresh** - All tabs update after workflow save (file-data, wavelength, analysis stores)
- ✅ **Session Status Display** - 3-column status bar shows session name and file count
- ✅ **Saved Workflows Management** - Load and delete saved workflows from UI
- ✅ **Node Type Tracking** - `NodeExecutionResult` includes `node_type` field for result processing
- ✅ **Analysis Tab Population** - Peak analysis results display after workflow execution
- ✅ **Store Listener Pattern** - Analysis tab listens to `analysis-results-store` updates
- ✅ **Seamless UX** - No manual session creation needed before running workflows

**Known Limitation:**
- ⚠️ **Analysis results not persisted** - Stored in `analysis-results-store` (in-memory only)
- Page reload clears analysis results (files and metadata persist)
- Must re-run workflow to regenerate analysis
- **Sprint 7 will fix** with extensible database storage

**✅ Sprint 5 - Session Persistence: COMPLETE (November 25, 2025)**
**MERGED TO MAIN** - Production-ready session persistence with dashboard integration

**Completed Deliverables:**
- ✅ **Complete Persistence Layer** - SQLite + HDF5 storage with SQLAlchemy ORM
- ✅ **SessionManager API** - High-level API for session CRUD operations
- ✅ **Dashboard Integration** - Save/Load/Manage UI with 3 modals
- ✅ **Wavelength Preservation** - Per-file wavelength storage and retrieval
- ✅ **Storage Configuration** - Configurable storage location with path validation
- ✅ **Debug Information Panel** - Detailed session inspection and troubleshooting
- ✅ **Data Integrity** - Verified roundtrip with comprehensive testing
- ✅ **Comprehensive Testing** - 99/99 tests passing (85 existing + 14 new)
- ✅ **Complete Documentation** - User guides, API docs, expansion guide

**✅ Sprint 3 + Sprint 4 Phase 2: COMPLETE (November 13, 2025)**
**MERGED TO MAIN** - Full-featured dashboard with integrated peak analysis

**Completed Deliverables:**
- ✅ **Complete Peak Analysis Microservice** - FastAPI REST API with multi-profile fitting
- ✅ **Professional Dashboard Framework** - 4-tab UI with wavelength management (0.1665 Å default)
- ✅ **Analysis Tab Integration** - Real-time peak detection with interactive parameter controls
- ✅ **Peak Visualization** - Automatic peak annotation on diffraction plots with tooltips
- ✅ **Service Health Monitoring** - Connection status indicators and startup guidance
- ✅ **Enhanced Data Loading** - .chi and .xy file support with auto-detection
- ✅ **Type Safety** - Strategic MyPy configuration with dashboard exclusion
- ✅ **Code Quality** - All linting/formatting/type checks passing

**🚀 NEXT: Sprint 7 - Analysis Result Persistence (Extensible MVP)**

**Objective**: Add **extensible analysis result storage** to support peak detection now and future analysis types (GSAS-II Rietveld, phase identification, texture analysis)

**Key Features**:
- ✅ Generic `AnalysisResult` table with JSON storage for flexibility
- ✅ Support multiple analysis types per file
- ✅ Track parameters and quality metrics for reproducibility
- ✅ Analysis versioning for tool compatibility
- ✅ Peak detection results persist across page reloads
- ✅ Foundation pattern for future GSAS-II integration

**See**: `docs/sprint-7-analysis-persistence-mvp.md` for detailed plan

## Integration Points
- **Environment Management**: **Pixi ONLY** - All dependencies via `pixi.toml`, tasks via `pixi run`
- **File formats**: .chi and .xy files (Q, intensity columns) with auto-detection
- **CLI**: Multiple tools - `python -m robomage` and `peak_analyzer.py` with service modes
- **Dashboard**: Professional 4-tab Dash UI with workflow builder and session integration
- **Session Storage**: SQLite database + HDF5 files in `~/.robomage/` (configurable)
- **Workflow Engine**: FastAPI service with DAG orchestrator, JSON workflow definitions
- **Microservices**: FastAPI services (peak analysis, workflow execution) with HTTP/JSON communication  
- **Type Safety**: Strategic MyPy configuration - strict for core library, lenient for UI
- **Service Communication**: Robust retry logic and validation at API boundaries
- **Future**: Analysis result persistence (Sprint 7), GSAS-II refinement engine integration

## Key Files for Understanding Context
1. `src/robomage/__init__.py` - Public API definition and dual API exports
2. `src/robomage/data/models.py` - Core DiffractionData and DataStatistics
3. `examples/load_data_example.py` - Comprehensive tutorial showing both APIs
4. `services/peak_analysis/main.py` - FastAPI microservice implementation
5. `services/workflow_engine/main.py` - Workflow execution service
6. `peak_analyzer.py` - Multi-mode CLI demonstrating service patterns
7. `src/robomage/clients/peak_analysis_client.py` - Service client with retry logic
8. `src/robomage/persistence/api.py` - SessionManager for session persistence
9. `src/robomage/orchestrator.py` - DAG workflow executor
10. `docs/sprint-7-analysis-persistence-mvp.md` - Next sprint plan (extensible analysis storage)

## Related Documentation
- `docs/llm-chat-guide.md` - Templates for starting new AI conversations
- `docs/sprint-6-days-5-6-COMPLETE.md` - Workflow-session integration completion summary
- `docs/sprint-7-analysis-persistence-mvp.md` - **NEXT SPRINT**: Extensible analysis result storage
- `docs/sprint-5-persistence-architecture.md` - Persistence layer design philosophy
- `docs/sprint-6-workflow-orchestrator-mvp.md` - Workflow engine architecture
- `docs/sprint-4-visualization-dashboard.md` - Dashboard development plan and architecture
- `docs/dashboard-persistence-guide.md` - Complete session persistence user guide
- `docs/persistence-quick-reference.md` - Code examples for persistence API
- `docs/session-storage-expansion-guide.md` - Guide for extending persistence layer
- `STORAGE-DEBUG-FEATURES.md` - Storage configuration and debug tools documentation
- `README.md` - User-facing project overview and API documentation