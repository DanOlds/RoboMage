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

### Pixi Workflow (NOT pip/conda)
```bash
pixi install                    # Setup environment (replaces pip install)
pixi run test                   # Run pytest suite (includes integration tests)
pixi run check                  # Format + lint + typecheck + test
pixi run format                 # ruff format .
pixi run lint                   # ruff check .
pixi run typecheck              # mypy src
```

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

### CLI Testing
```bash
pixi run python -m robomage test --plot --info    # Test built-in data
pixi run python -m robomage --help                # CLI options
python peak_analyzer.py --help                    # Peak analysis CLI
```

## Code Conventions

### File Organization
- `src/robomage/data/`: Core data structures (models.py, loaders.py)
- `src/robomage/data_io.py`: Legacy pandas-based API
- `src/robomage/__main__.py`: CLI implementation for data loading/testing
- `src/robomage/clients/`: HTTP clients for microservice communication
- `services/peak_analysis/`: Independent FastAPI microservice
- `peak_analyzer.py`: Standalone CLI tool for peak analysis workflows
- `src/robomage/orchestrator.py`: Service coordination (planned)

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

## Integration Points
- **File formats**: Currently .chi files (Q, intensity columns)
- **CLI**: Full argparse implementation with glob pattern support
- **Matplotlib**: Publication-quality plotting integration
- **Service Communication**: HTTP/JSON between RoboMage framework and analysis engines
- **Future**: GSAS-II refinement engine integration planned

## Key Files for Understanding Context
1. `src/robomage/__init__.py` - Public API definition and dual API exports
2. `src/robomage/data/models.py` - Core DiffractionData and DataStatistics
3. `examples/load_data_example.py` - Comprehensive tutorial showing both APIs
4. `services/peak_analysis/main.py` - FastAPI microservice implementation
5. `peak_analyzer.py` - Multi-mode CLI demonstrating service patterns
6. `src/robomage/clients/peak_analysis_client.py` - Service client with retry logic

## Related Documentation
- `docs/llm-chat-guide.md` - Templates for starting new AI conversations
- `docs/sprint-3-peak-analysis-plan.md` - Service architecture implementation details
- `README.md` - User-facing project overview and API documentation