# GitHub Copilot Instructions for RoboMage

## Project Overview
RoboMage is a powder diffraction analysis framework with a **dual API architecture**: modern Pydantic-based models for new code and legacy pandas DataFrames for backward compatibility. The project uses Pixi for environment management and targets automated Rietveld refinement workflows.

## Architecture Patterns

### Dual API Design
- **Modern API**: `robomage.load_diffraction_file()` → `DiffractionData` (Pydantic models)
- **Legacy API**: `robomage.load_test_data_df()` → `pandas.DataFrame`
- Both APIs are exposed through `src/robomage/__init__.py` with clear naming conventions

### Core Data Flow
1. **Load**: `src/robomage/data/loaders.py` → file format detection and validation
2. **Model**: `src/robomage/data/models.py` → Pydantic `DiffractionData` with computed `DataStatistics`
3. **Process**: Immutable operations (trim, interpolate) return new instances
4. **Export**: Convert to pandas via `.to_dataframe()` for legacy workflows

### Validation Philosophy
- **Pydantic v2**: All data models inherit from `BaseModel` with strict validation
- **Immutable by design**: Data transformations return new instances with preserved metadata
- **Automatic sorting**: Q-values automatically sorted on DiffractionData creation
- **Scientific validation**: Units (Å⁻¹ for Q), NaN/inf detection, proper ranges

## Essential Development Commands

### Pixi Workflow (NOT pip/conda)
```bash
pixi install                    # Setup environment (replaces pip install)
pixi run test                   # Run pytest suite (20 tests)
pixi run check                  # Format + lint + typecheck + test
pixi run format                 # ruff format .
pixi run lint                   # ruff check .
pixi run typecheck              # mypy src
```

### CLI Testing
```bash
pixi run python -m robomage test --plot --info    # Test built-in data
pixi run python -m robomage --help                # CLI options
```

## Code Conventions

### File Organization
- `src/robomage/data/`: Core data structures (models.py, loaders.py)
- `src/robomage/data_io.py`: Legacy pandas-based API
- `src/robomage/__main__.py`: CLI implementation (462 lines)
- `src/robomage/config/`: Placeholder config schemas (not fully implemented)

### Testing Patterns
- Test files mirror source structure: `test_data_models.py`, `test_data_loaders.py`
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

## Integration Points
- **File formats**: Currently .chi files (Q, intensity columns)
- **CLI**: Full argparse implementation with glob pattern support
- **Matplotlib**: Publication-quality plotting integration
- **Future**: GSAS-II refinement engine integration planned

## Key Files for Understanding Context
1. `src/robomage/__init__.py` - Public API definition and dual API exports
2. `src/robomage/data/models.py` - Core DiffractionData and DataStatistics
3. `examples/load_data_example.py` - Comprehensive tutorial showing both APIs
4. `.llm-context.md` - Detailed project context and technical reference

## Related Documentation
- `docs/llm-chat-guide.md` - Templates for starting new AI conversations
- `README.md` - User-facing project overview and API documentation