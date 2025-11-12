# 🔄 Starting a New LLM Chat with RoboMage Context

When starting a fresh conversation with an AI assistant about this project, here's an effective way to provide context:

## 📋 Quick Context Template

```
Hi! I'm working on the RoboMage project - a Python framework for automated powder diffraction analysis. 

Please read these key files to understand the project:
1. README.md - Project overview and API documentation
2. .llm-context.md - Complete technical reference for AI assistants  
3. src/robomage/__init__.py - Main package API
4. src/robomage/data/models.py - Core data structures

Note: For GitHub Copilot users, see .github/copilot-instructions.md for development-focused guidance.

Key context:
- Python 3.10+ with Pixi environment management
- Dual API: Modern (Pydantic models) + Legacy (pandas DataFrames)  
- Current status: Week 2 complete with working data pipeline
- Domain: X-ray powder diffraction analysis (Q vs intensity data)

[Your specific question or task here...]
```

## 🎯 Specific Use Cases

**For New Features:**
"I want to add [feature] to RoboMage. Please review the current architecture in the context files and suggest how to implement this while maintaining the dual API design."

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