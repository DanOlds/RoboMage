# 🔄 Starting a New LLM Chat with RoboMage Context

When starting a fresh conversation with an AI assistant about this project, here's an effective way to provide context:

## 📋 Quick Context Template

```
Hi! I'm working on the RoboMage project - a microservices-based framework for automated powder diffraction analysis. 

Please read these key files to understand the project:
1. README.md - Project overview and comprehensive API documentation
2. .llm-context.md - Complete technical reference for AI assistants (UPDATED Nov 2025)
3. .github/copilot-instructions.md - **CRITICAL**: Current architecture guide for developers
4. src/robomage/__init__.py - Main package API with dual design
5. services/peak_analysis/main.py - FastAPI microservice architecture

Key context:
- **Architecture**: Production-ready microservices with FastAPI + Dash dashboard
- **Current Status**: Sprint 3 + Sprint 4 Phase 1.5 COMPLETE (merged to main Nov 12, 2025)
- **Features**: Peak analysis service, 3-tab dashboard, .chi/.xy file support
- **Next**: Dashboard Phase 2 - service integration in analysis tab (2-3 days)
- **Tech Stack**: Python 3.10+, Pixi, Pydantic v2, FastAPI, Dash, pytest (37/37 tests passing)

[Your specific question or task here...]
```

## 🎯 Specific Use Cases

**For New Features:**
"I want to add [feature] to RoboMage. Please review the current microservices architecture in the context files and suggest how to implement this while maintaining compatibility with existing services and the dual API design."

**For Dashboard Phase 2 Work:**
"I'm working on Dashboard Phase 2 - integrating the peak analysis service into the dashboard analysis tab. Please review the current dashboard framework and service client architecture to understand the integration patterns."

**For Bug Fixes:**
"I'm seeing [error] in RoboMage. Please check the relevant test files and data models to understand the expected behavior."

**For Documentation:**
"Help me improve the documentation for [component]. Please review the existing docstring patterns in the codebase."

**For Testing:**
"I need tests for [functionality]. Please look at the existing test patterns in tests/ directory."

## 📁 Optional: Attach These Files Directly

If your LLM interface supports file attachments, these provide the most comprehensive context:

**Essential (attach these):**
- `README.md` 
- `.llm-context.md`
- `src/robomage/__init__.py`
- `pyproject.toml`

**For specific work:**
- Data models: `src/robomage/data/models.py`
- CLI: `src/robomage/__main__.py` 
- Tests: Relevant files from `tests/` directory
- Examples: `examples/load_data_example.py`

This approach ensures the AI assistant understands:
✅ Project purpose and domain  
✅ Current implementation status  
✅ Code architecture and patterns  
✅ Available APIs and usage examples  
✅ Development workflow and standards