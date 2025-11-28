# 🔄 Starting a New LLM Chat with RoboMage Context

When starting a fresh conversation with an AI assistant about this project, here's an effective way to provide context:

## 📋 Quick Context Template

```
Hi! I'm working on the RoboMage project - a microservices-based framework for automated powder diffraction analysis with workflow orchestration and session persistence.

Please read these key files to understand the project:
1. README.md - Project overview and comprehensive API documentation
2. .github/copilot-instructions.md - **CRITICAL**: Architecture, pixi usage, current sprint status
3. docs/sprint-7-analysis-persistence-mvp.md - **NEXT SPRINT**: Extensible analysis result storage plan

Key context:
- **Environment**: Uses **Pixi EXCLUSIVELY** (NOT pip/conda) for dependencies and task management
- **Architecture**: Production-ready microservices with FastAPI workflow engine + Dash dashboard
- **Current Status**: Sprint 6 Days 5-6 COMPLETE (Nov 27, 2025) - Workflow-session integration
- **Latest Features**: 
  - Auto-create default session on dashboard load
  - Workflow results save to active session
  - Analysis tab displays peak detection results
  - Session status bar with file counts
  - Load/delete saved workflows
- **Next Sprint**: Sprint 7 - Analysis result persistence (extensible MVP for future GSAS-II)
- **Known Limitation**: Analysis results in-memory only (cleared on page reload) - Sprint 7 will fix
- **Tech Stack**: Python 3.10+, Pixi, Pydantic v2, FastAPI, Dash, SQLAlchemy, pytest (99/99 tests passing)
- **Commands**: Use `pixi install`, `pixi run test`, `pixi run check`, `pixi run start-all` (see copilot-instructions.md)

[Your specific question or task here...]
```

## 🎯 Specific Use Cases

**For Sprint 7 - Analysis Persistence:**
"I'm working on Sprint 7 - adding extensible analysis result persistence to RoboMage. Please review docs/sprint-7-analysis-persistence-mvp.md to understand the schema design and extensibility requirements. This is an MVP pattern for future GSAS-II integration."

**For New Features:**
"I want to add [feature] to RoboMage. Please review the current microservices architecture, workflow engine, and session persistence in the context files and suggest how to implement this while maintaining the extensible design patterns."

**For Dashboard Work:**
"I'm working on the RoboMage dashboard. Please review the current 4-tab structure (Data Import, Visualization, Analysis, Workflow) and session integration patterns to understand the architecture."

**For Workflow System:**
"I'm working on the workflow orchestrator. Please review docs/sprint-6-workflow-orchestrator-mvp.md and the DAG execution patterns in src/robomage/orchestrator.py."

**For Bug Fixes:**
"I'm seeing [error] in RoboMage. Please check the relevant test files and data models to understand the expected behavior. Note: 99/99 tests currently passing."

**For Documentation:**
"Help me improve the documentation for [component]. Please review the existing docstring patterns and the docs/ directory structure."

**For Testing:**
"I need tests for [functionality]. Please look at the existing test patterns in tests/ directory and maintain 100% test pass rate."

## 📁 Optional: Attach These Files Directly

If your LLM interface supports file attachments, these provide the most comprehensive context:

**Essential (attach these):**
- `README.md` - Full project overview
- `.github/copilot-instructions.md` - **CRITICAL**: Architecture patterns and sprint status
- `docs/sprint-7-analysis-persistence-mvp.md` - Next sprint plan
- `docs/sprint-6-days-5-6-COMPLETE.md` - Latest completion summary
- `pixi.toml` - Environment configuration

**For specific work:**
- **Persistence Layer**: `src/robomage/persistence/models.py`, `src/robomage/persistence/api.py`
- **Workflow Engine**: `src/robomage/orchestrator.py`, `services/workflow_engine/models.py`
- **Dashboard**: `src/robomage/dashboard/callbacks/*.py`, `src/robomage/dashboard/layouts/*.py`
- **Data Models**: `src/robomage/data/models.py`
- **Tests**: Relevant files from `tests/` directory (99 tests total)
- **Examples**: `examples/load_data_example.py`

This approach ensures the AI assistant understands:
✅ Project purpose and domain  
✅ Current implementation status (Sprint 6 complete)
✅ Next sprint objectives (Sprint 7 - analysis persistence)
✅ Code architecture and extensibility patterns  
✅ Available APIs and usage examples  
✅ Development workflow and standards
✅ Session persistence and workflow integration