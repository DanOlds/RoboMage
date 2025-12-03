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

**✅ Sprint 8 - Visual Workflow Builder: COMPLETE (November 28, 2025)**
**PRODUCTION READY** - Full-featured visual workflow builder with clean architecture

**Completed Deliverables:**
- ✅ **Interactive Workflow Canvas** - Cytoscape-based drag-and-drop interface
- ✅ **Node Palette** - 10+ registered node types with category organization
- ✅ **Dynamic Configuration Forms** - Schema-driven forms for any node type
- ✅ **Real-time Validation** - Cycle detection, connection validation, topological sort
- ✅ **Visual Status Indicators** - Execution progress and error visualization
- ✅ **Clean Abstraction Layer** - Framework-agnostic design (Cytoscape → ReactFlow ready)
- ✅ **Comprehensive Testing** - 56 workflow builder tests (100% passing)
- ✅ **Complete Documentation** - User guide and technical documentation

**December 1, 2025 - Test Suite Cleanup** ✅ **COMPLETE**:
- ✅ **Fixed all failing tests** - 233/233 tests passing (100%)
- ✅ **Cleaned up test structure** - Archived old tests, proper pytest configuration
- ✅ **Resolved deprecation warnings** - Warnings dropped from 449 to 11
- ✅ **Created troubleshooting guide** - Comprehensive problem-solving documentation
- ✅ **Updated all documentation** - README, sprint status, and guides current

**Key Achievement**: Production-ready codebase with 100% passing tests and complete documentation!

**December 3, 2025 - Critical Bug Fixes** ✅ **COMPLETE**:
- ✅ **Service Inspector Tab** - Fixed callback circular dependency and state preservation
- ✅ **save_to_session Workflow Node** - Fixed and unified with button behavior (searches ALL context)
- ✅ **Disconnected Nodes Bug** - Fixed workflow orchestrator executing unconnected nodes
- ⚠️ **Test Suite Status**: 16 tests failing (367 passing) - Need updates for new behavior
- 📋 **Cleanup Plan Ready**: Comprehensive plan for GSAS-II integration preparation

**Key Achievement**: Major architectural improvements with clear path to test fixes!

**✅ Sprint 7 - Analysis Result Persistence: COMPLETE (November 27, 2025)**

**READY TO MERGE** - Production-ready extensible analysis result storage

**Completed Deliverables:**
- ✅ **AnalysisResult Database Table** - Extensible JSON storage for any analysis type
- ✅ **SessionManager API Extensions** - save/get/delete analysis result methods
- ✅ **Dashboard Integration** - Workflow save persists, session load restores analysis
- ✅ **Existing File Support** - Analysis saved for both new and existing session files
- ✅ **Robust Error Handling** - Gracefully handles missing files during session load
- ✅ **Comprehensive Testing** - 38/38 tests passing (22 unit + 5 integration + 11 existing)
- ✅ **Provenance Tracking** - Parameters, versions, quality metrics stored
- ✅ **Multi-Analysis Support** - Multiple results per file with type filtering
- ✅ **Cascade Delete** - Session → File → AnalysisResult cleanup
- ✅ **Manual Validation** - Peak analysis persists across page reloads ✨

**Key Achievement**: Peak detection results now persist in database and survive page reloads!

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

**Previous Limitation (NOW FIXED in Sprint 7):**
- ~~Analysis results not persisted~~ ✅ **NOW PERSISTED IN DATABASE**
- ~~Page reload clears analysis results~~ ✅ **NOW RESTORED FROM DATABASE**
- ~~Must re-run workflow to regenerate analysis~~ ✅ **ANALYSIS SURVIVES RELOAD**

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

**🎯 NEXT PRIORITIES (Post-Sprint 8)**:

**December 1, 2025 - Latest Updates** ✅:
- ✅ **Workflow Canvas Save/Load Buttons** - Fixed non-functional Save/Load buttons
  - Added modal dialogs for saving and loading workflows
  - Fixed modal closing bugs (toggle logic and pattern-matched button rendering)
  - Both modals now work correctly (tested by user)
  - Documentation: `docs/WORKFLOW-CANVAS-BUTTONS-FIX.md`
- ✅ **Week 1 Quick Wins Complete** - 233/233 tests passing (100%)
- ✅ **Test Suite Cleanup** - Archived old tests, resolved deprecation warnings
- ✅ **Comprehensive Troubleshooting Guide** - Problem-solving documentation

**December 3, 2025 - Critical Bug Fixes** ✅:
- ✅ **Service Inspector Tab** - Fixed callback circular dependency and state preservation
  - Removed circular State dependency causing display panel failures
  - Implemented Store pattern for tab, accordion, and response preservation across health refreshes
  - Added OpenAPI schema-based endpoint discovery for test console
  - Documentation: `docs/SERVICE-INSPECTOR-DEBUG-SESSION.md`
- ✅ **save_to_session Workflow Node** - Fixed and unified with button behavior
  - Fixed missing session context (active_session_id not passed to workflow service)
  - Fixed dict serialization (DiffractionData objects serialized to JSON)
  - **Major redesign**: Node now searches ALL execution context (matches "Save results" button)
  - Supports any workflow pattern: automatically finds all DiffractionData regardless of connections
  - Documentation: `docs/SAVE-TO-SESSION-FIX.md`
- ✅ **Disconnected Nodes Bug** - Fixed workflow orchestrator executing unconnected nodes
  - Topological sort now filters to only connected graph nodes
  - Disconnected nodes safely excluded with clear logging
  - Edges now properly control execution order (DAG semantics enforced)
  - Documentation: `docs/DISCONNECTED-NODES-FIX.md`
- ✅ **Test Suite Cleanup Complete** - 380/380 tests passing (100%)
  - Fixed all 16 failing tests from December 3 architectural changes
  - Category 1: Workflow session integration (5 tests)
  - Category 2: Workflow orchestrator (4 tests)
  - Category 3: Workflow serialization (2 tests)
  - Category 4: Inspection persistence (5 tests - singleton pollution fix)
  - See `docs/TEST-FIXES-QUICK-START.md` for implementation details
  - Commits: 3 detailed commits with categorized fixes

**✅ CLEANUP COMPLETION (December 3, 2025)**:
- ✅ **Phase 1: Test Fixes Complete** - 100% pass rate achieved (380/380 passing)
  - All 16 failing tests fixed with copy-paste ready solutions
  - Singleton database manager pollution resolved
  - Context-based execution pattern implemented across all workflow tests
  - 3 commits: Categories 1+3, Category 2, Category 4
- ✅ **Phase 2: Workspace Organization Complete** - Clean project structure
  - Manual test scripts moved to tests/manual/ (excluded from pytest)
  - Log files organized in test_output/logs/
  - __pycache__ directories cleaned
  - Automated with ./cleanup_prep.sh workspace
- ✅ **Phase 3: Documentation Consolidation Complete** - 19 docs archived
  - Custom services phase docs → archive/custom-services/ (5 files)
  - Sprint summaries → archive/sprint-summaries/ (9 files)
  - Planning documents → archive/planning-docs/ (5 files)
  - 65 active docs remaining (down from 84)
  - Automated with ./cleanup_prep.sh docs
- ⏳ **Phase 4: Resource Warnings** - 30 unclosed database warnings remaining
  - Non-blocking technical debt (tests still pass)
  - Can be addressed incrementally as encountered
- 📋 **Phase 5: GSAS-II Roadmap** - To be created when ready for integration
  - Deferred until GSAS-II external development is ready
  - Foundation now clean for rapid integration

**Documents Created**: `docs/CLEANUP-SUMMARY.md`, `docs/TEST-FIXES-QUICK-START.md`, `docs/GSAS-II-PREP-CLEANUP-PLAN.md`, `docs/CLEANUP-QUICK-REF.md`
**Tool Created**: `cleanup_prep.sh` - Automated cleanup script (executable)

**🚀 NEXT MAJOR MILESTONES**:
- ✅ **Pre-GSAS-II Cleanup COMPLETE** (Dec 3, 2025) - Foundation ready! 🎉
  - ✅ 380/380 tests passing (100% pass rate achieved)
  - ✅ Workspace organized (manual tests, logs, cache cleaned)
  - ✅ Documentation consolidated (19 docs archived, 65 active)
  - ⏳ 30 resource warnings remain (non-blocking)
- 🔬 **GSAS-II Integration** (TBD) - Automated Rietveld refinement service
  - Service wrapper for GSAS-II Python API
  - Dashboard integration and workflow nodes
  - Waiting on external GSAS-II development
  - Roadmap: `docs/GSAS-II-INTEGRATION-ROADMAP.md` (to be created)
  - Dashboard integration and workflow nodes
  - See `docs/GSAS-II-INTEGRATION-ROADMAP.md` (to be created)
- 🎯 **Custom Services Architecture** - Generic service registry and template system
  - Replace hardcoded services with discoverable registry
  - Cookiecutter template for creating custom analysis services
  - Dashboard auto-discovers and monitors custom services
  - See `docs/CUSTOM-SERVICES-PLAN.md` for detailed roadmap

**Future Enhancements**:
- 🔄 **Advanced Inspection Tools** - Node I/O Inspector, Analysis Result Viewer, Workflow Debugger
- 🔄 **Workflow Templates** - Pre-built common analysis patterns
- 🔄 **ReactFlow Migration** - Modern drag-and-drop UX
- 🔄 **ML Integration** - AI-enhanced parameter optimization
- 🔄 **Multi-User Support** - PostgreSQL backend, collaboration

**Waiting on External Development**:
- ⏸️ **GSAS-II Integration** - Automated Rietveld refinement (in development by another team)

## Integration Points
- **Environment Management**: **Pixi ONLY** - All dependencies via `pixi.toml`, tasks via `pixi run`
- **File formats**: .chi and .xy files (Q, intensity columns) with auto-detection
- **CLI**: Multiple tools - `python -m robomage` and `peak_analyzer.py` with service modes
- **Dashboard**: Professional 4-tab Dash UI with workflow builder and session integration
- **Session Storage**: SQLite database + HDF5 files in `~/.robomage/` (configurable)
- **Analysis Persistence**: Extensible AnalysisResult table with JSON storage (Sprint 7 ✅)
- **Workflow Engine**: FastAPI service with DAG orchestrator, JSON workflow definitions
- **Microservices**: FastAPI services (peak analysis, workflow execution) with HTTP/JSON communication  
- **Type Safety**: Strategic MyPy configuration - strict for core library, lenient for UI
- **Service Communication**: Robust retry logic and validation at API boundaries
- **Error Handling**: Graceful degradation for missing files during session load

## Key Files for Understanding Context
1. `src/robomage/__init__.py` - Public API definition and dual API exports
2. `src/robomage/data/models.py` - Core DiffractionData and DataStatistics
3. `src/robomage/persistence/models.py` - Database schema (Session, File, AnalysisResult)
4. `src/robomage/persistence/api.py` - SessionManager with analysis result methods
5. `examples/load_data_example.py` - Comprehensive tutorial showing both APIs
6. `examples/custom_nodes/` - Custom node development examples (template, background, peak width)
7. `docs/node-development-guide.md` - Complete guide for creating custom workflow nodes
8. `services/peak_analysis/main.py` - FastAPI microservice implementation
9. `services/workflow_engine/main.py` - Workflow execution service
10. `peak_analyzer.py` - Multi-mode CLI demonstrating service patterns
11. `src/robomage/clients/peak_analysis_client.py` - Service client with retry logic
12. `src/robomage/orchestrator.py` - DAG workflow executor
13. `docs/SPRINT-7-COMPLETION.md` - Sprint 7 completion summary and usage guide

## Related Documentation
- `docs/llm-chat-guide.md` - Templates for starting new AI conversations
- `docs/node-development-guide.md` - Comprehensive guide for creating custom workflow nodes (820 lines)
- `docs/node-quick-reference.md` - Copy-paste templates for rapid node development (530 lines)
- `docs/NODE-DEVELOPMENT-EXAMPLES-COMPLETE.md` - Node development implementation summary
- `examples/custom_nodes/` - Working examples (template, background subtraction, peak width analysis)
- `docs/NEXT-STEPS-WEEK-2.md` - Detailed Week 2 implementation plan (Node I/O Inspector)
- `docs/WEEK-1-COMPLETION.md` - Week 1 quick wins completion summary
- `docs/inspection-tools-design.md` - Complete architecture for 5 inspection tools (4-5 week plan)
- `docs/TROUBLESHOOTING.md` - Comprehensive troubleshooting guide for common issues
- `docs/SPRINT-8-COMPLETION.md` - Sprint 8 complete: Visual workflow builder
- `docs/visual-workflow-builder-guide.md` - User guide for workflow builder
- `docs/SPRINT-7-COMPLETION.md` - Sprint 7 complete: Extensible analysis result persistence
- `docs/sprint-7-analysis-persistence-mvp.md` - Sprint 7 planning document
- `docs/sprint-6-days-5-6-COMPLETE.md` - Workflow-session integration completion summary
- `docs/sprint-5-persistence-architecture.md` - Persistence layer design philosophy
- `docs/sprint-6-workflow-orchestrator-mvp.md` - Workflow engine architecture
- `docs/sprint-4-visualization-dashboard.md` - Dashboard development plan and architecture
- `docs/dashboard-persistence-guide.md` - Complete session persistence user guide
- `docs/persistence-quick-reference.md` - Code examples for persistence API
- `docs/session-storage-expansion-guide.md` - Guide for extending persistence layer
- `docs/WORKFLOW-CANVAS-BUTTONS-FIX.md` - **NEW**: Save/Load buttons fix (Dec 1, 2025)
- `docs/CUSTOM-SERVICES-PLAN.md` - **NEW**: Custom services architecture plan (2-3 weeks)
- `docs/CUSTOM-SERVICES-GUIDE.md` - **UPDATED**: Complete guide with validated testing results (Dec 2, 2025)
- `docs/SERVICE-CREATION-TIPS.md` - **NEW**: Critical learnings, dos/don'ts, validated workflow (Dec 2, 2025)
- `docs/HANDS-ON-TESTING-RESULTS.md` - **NEW**: Comprehensive testing report - 7/7 sessions passed (Dec 2, 2025)
- `docs/HANDS-ON-TESTING-PLAN.md` - Testing plan for custom services (comprehensive validation)
- `docs/KILL-COMMAND-SAFETY.md` - **NEW**: Safety analysis and best practices for kill-all commands (Dec 2, 2025)
- `docs/CLEANUP-SUMMARY.md` - **NEW**: Comprehensive cleanup plan summary (Dec 3, 2025)
- `docs/TEST-FIXES-QUICK-START.md` - **NEW**: Copy-paste ready test fixes (Dec 3, 2025)
- `docs/GSAS-II-PREP-CLEANUP-PLAN.md` - **NEW**: 4-day cleanup execution plan (Dec 3, 2025)
- `docs/CLEANUP-QUICK-REF.md` - **NEW**: Quick reference card for cleanup tasks (Dec 3, 2025)
- `docs/DEC-3-2025-TEST-FAILURES.md` - Test failure analysis and fix strategy
- `docs/DISCONNECTED-NODES-FIX.md` - Orchestrator disconnected nodes fix
- `docs/SAVE-TO-SESSION-FIX.md` - save_to_session context-based searching
- `docs/SERVICE-INSPECTOR-DEBUG-SESSION.md` - Service inspector callback fixes
- `STORAGE-DEBUG-FEATURES.md` - Storage configuration and debug tools documentation
- `README.md` - User-facing project overview and API documentation