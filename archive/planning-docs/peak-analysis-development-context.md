# Peak Analysis Tool Development Context

I'm implementing **Phase 1** of an independent peak analysis tool as part of the RoboMage project. The tool should be a **standalone scientific software** that can run independently but also integrate seamlessly with RoboMage's service architecture.

## Tool Architecture
The tool will be built as a **FastAPI service** that can run standalone (`peak-analyzer` CLI) or be called by RoboMage's orchestrator via HTTP/JSON. It should follow RoboMage's Pydantic patterns but be completely independent. Key decisions:
- **Service-first approach**: Independent HTTP service over integrated modules
- **JSON communication**: Pydantic models → JSON schema for service interface  
- **No Docker initially**: Simple Python process deployment
- **FastAPI choice**: REST framework for service implementation

## Implementation Requirements
- **Multiple interfaces**: CLI, Python API, REST service, future web GUI
- **Professional quality**: Publication-ready plots, robust error handling, comprehensive testing
- **Scientific capabilities**: Peak detection (scipy), profile fitting (Gaussian/Lorentzian/Voigt), background subtraction
- **File format support**: .chi, .xy, .dat files with JSON/CSV/plot outputs

## RoboMage Integration Context
- **Environment**: Uses Pixi package manager, scipy >=1.16.2 already available
- **Quality standards**: Pydantic v2 models, MyPy type safety, Ruff formatting, 100% test coverage
- **Data patterns**: Follow existing `DiffractionData` model patterns from `src/robomage/data/models.py`
- **Service architecture**: Fits into `services/` directory, integrates with orchestrator framework

## Repository Structure
```
RoboMage/
├── services/           # <- Peak analysis service goes here
├── src/robomage/       # <- Existing: Main package code patterns
├── docs/               # <- Plans and documentation  
├── examples/           # <- Test data (SRM 660b LaB₆ standard)
└── tests/              # <- Test suite patterns to follow
```

## Key Files for Reference
- **Tool vision**: `docs/peak-analysis-tool-plan.md` (complete tool specification)
- **Implementation plan**: `docs/sprint-3-peak-analysis-plan.md` (Sprint 3 roadmap)
- **Project standards**: `.github/copilot-instructions.md` (coding conventions, dependencies, patterns)
- **Data model examples**: `src/robomage/data/models.py` (Pydantic patterns to follow)
- **Config examples**: `src/robomage/config/refinement_schema.py` (validation patterns)
- **Test data**: `examples/pdf_SRM_660b_q.chi` (for validation)

## Success Criteria for Phase 1
```bash
# Standalone CLI usage
peak-analyzer sample.chi --output results/

# Service mode  
peak-analyzer --service --port 8001
curl -X POST http://localhost:8001/analyze -d @request.json

# Python API
import peak_analyzer
results = peak_analyzer.analyze_peaks(data, config)
```

The goal is to create a **valuable standalone scientific tool** that serves the crystallography community while perfectly integrating with RoboMage's automation workflows.