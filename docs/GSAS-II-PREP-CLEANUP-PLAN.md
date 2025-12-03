# GSAS-II Integration - Pre-Development Cleanup Plan

**Date:** December 3, 2025  
**Status:** Ready for Execution  
**Estimated Duration:** 3-4 days  
**Current Test Status:** 16 failing, 367 passing, 18 warnings  

---

## 🎯 Executive Summary

Before starting GSAS-II integration work, we need to:
1. **Fix 16 failing tests** - Update tests for new architectural behavior
2. **Clean up technical debt** - Remove unused code, consolidate documentation
3. **Improve code quality** - Fix warnings, organize workspace
4. **Prepare for GSAS-II** - Ensure clean foundation for new service integration

**Success Criteria:**
- ✅ 100% tests passing (383/383)
- ✅ Zero technical debt warnings
- ✅ Documentation consolidated and current
- ✅ Clean workspace ready for GSAS-II development

---

## 📊 Current State Assessment

### Test Suite Status
```
16 failed, 367 passed, 18 warnings in 22.25s
Pass Rate: 95.8% (Target: 100%)
```

**Failing Tests Breakdown:**
- **Inspection Persistence:** 5 tests (investigation needed)
- **Workflow Orchestrator:** 4 tests (disconnected nodes behavior)
- **Workflow Session Serialization:** 2 tests (orchestrator changes)
- **Workflow Session Integration:** 5 tests (save_to_session redesign)

### Code Quality Issues

**Warnings:**
- 18 pytest warnings (mostly ResourceWarnings - unclosed database connections)
- 11 deprecation warnings (down from 449 ✅)

**Technical Debt:**
- 20+ TODO/FIXME comments (mostly in documentation)
- Temporary test files in root directory (4 files)
- Log files in root (3 files: dashboard.log, peak_analysis.log, workflow_engine.log)
- Test data files in root (2 .xy files, 1 .csv file)
- `__pycache__` directories throughout codebase

**Documentation:**
- 79 markdown files in docs/ (consolidation needed)
- Redundant sprint summaries and completion docs
- Outdated migration guides

---

## 🎯 Priority 1: Fix Failing Tests (Day 1-2)

### 1.1 Workflow Orchestrator Tests (4 failures)

**Files:** `tests/test_workflow_orchestrator.py`

**Root Cause:** Tests use workflows with single disconnected nodes (no edges). New orchestrator correctly excludes these.

**Fix Strategy:**
```python
# Option 1: Add edges to connect nodes
workflow = WorkflowDefinition(
    nodes=[
        WorkflowNode(id="input", type="load_files", ...),
        WorkflowNode(id="node1", type="test_node", ...),
    ],
    edges=[Edge(source="input", target="node1")]
)

# Option 2: Test disconnected node exclusion explicitly
def test_disconnected_nodes_excluded():
    workflow = WorkflowDefinition(
        nodes=[WorkflowNode(id="orphan", type="test_node", ...)],
        edges=[]
    )
    result = await orchestrator.execute(workflow)
    assert "Excluding 1 disconnected node(s)" in logs
```

**Tests to Fix:**
- `test_workflow_execution_with_node_failure`
- `test_workflow_with_missing_handler`
- `test_initial_context_passed_to_handlers`
- `test_execution_timing_recorded`

**Time Estimate:** 2-3 hours

---

### 1.2 Workflow Session Integration Tests (5 failures)

**Files:** `tests/test_workflow_session_integration.py`

**Root Cause:** Tests pass data through `inputs` parameter, but `save_to_session_handler` now searches `context.data` instead.

**Fix Strategy:**
```python
# OLD (broken):
inputs = {"files": [test_data]}
result = await save_to_session_handler(config, inputs, context)

# NEW (required):
context = ExecutionContext()
context.set_node_output("load_files", [test_data])  # Put data IN context
inputs = {}  # Empty - handler searches context
result = await save_to_session_handler(config, inputs, context)
```

**Tests to Fix:**
- `test_save_to_session_handler_basic`
- `test_save_to_session_handler_multiple_files`
- `test_save_to_session_handler_auto_create_session`
- `test_save_to_session_handler_current_session`
- `test_save_to_session_with_analysis_results`

**Time Estimate:** 3-4 hours

---

### 1.3 Workflow Session Serialization Tests (2 failures)

**Files:** `tests/test_workflow_session_full_serialization.py`

**Root Cause:** Likely related to orchestrator changes (disconnected nodes).

**Fix Strategy:**
1. Review test workflows - ensure nodes are connected
2. Update assertions to match new orchestrator behavior
3. Verify serialization still works with connected workflows

**Tests to Fix:**
- `test_orchestrator_full_serialization_mode`
- `test_orchestrator_summary_mode_default`

**Time Estimate:** 1-2 hours

---

### 1.4 Inspection Persistence Tests (5 failures) ⚠️

**Files:** `tests/test_inspection_persistence.py`

**Root Cause:** UNKNOWN - Needs investigation

**Investigation Steps:**
1. Run tests individually with verbose output
2. Check if inspection data is created for disconnected nodes
3. Verify inspection snapshot creation logic
4. Determine if related to December 3 changes or pre-existing

**Tests to Fix:**
- `test_get_inspections_no_filters`
- `test_get_inspections_filter_node_type`
- `test_clear_session_inspections`
- `test_orphaned_inspections_preserved`
- `test_node_type_index_performance`

**Time Estimate:** 4-6 hours (includes investigation)

**Rollback Plan:** If inspection tests are unrelated to recent changes, create separate issue and mark as known limitation.

---

### 1.5 Resource Warnings Cleanup

**Issue:** 18 ResourceWarnings for unclosed database connections

**Fix Strategy:**
```python
# Add proper cleanup in tests
@pytest.fixture
async def session_manager():
    sm = SessionManager(storage_path)
    yield sm
    # Cleanup
    sm.close()  # Ensure connections closed

# Use context managers
async with SessionManager(storage_path) as sm:
    # Test code here
    pass
# Automatic cleanup
```

**Files to Review:**
- `tests/test_peak_analysis_integration.py`
- `tests/test_session_persistence_integration.py`
- All tests using `SessionManager` or SQLAlchemy

**Time Estimate:** 2-3 hours

---

## 🧹 Priority 2: Code Quality Cleanup (Day 2-3)

### 2.1 Root Directory Organization

**Current Issues:**
- Test files in root: `test_json_editor.py`, `test_normalize_workflow.py`
- Log files: `dashboard.log`, `peak_analysis.log`, `workflow_engine.log`
- Test data: `detector_5_roi_*.xy`, `workflow_results.csv`
- Utility scripts: `benchmark_services.py`, `start_services.py`

**Cleanup Actions:**

```bash
# Create test_output subdirectories if not exist
mkdir -p test_output/logs
mkdir -p test_output/data

# Move test files to tests/
mv test_json_editor.py tests/manual/
mv test_normalize_workflow.py tests/manual/

# Move log files to test_output/logs/
mv *.log test_output/logs/

# Move test data to test_output/data/
mv detector_5_roi_*.xy test_output/data/
mv workflow_results.csv test_output/data/

# Keep utility scripts but document in README
# benchmark_services.py - Performance testing
# start_services.py - Service startup utility
# peak_analyzer.py - Standalone CLI tool
```

**Update .gitignore:**
```gitignore
# Log files
*.log
test_output/logs/

# Test data
test_output/data/*.xy
test_output/data/*.csv

# Caches
__pycache__/
.pytest_cache/
.mypy_cache/
.ruff_cache/
```

**Time Estimate:** 1 hour

---

### 2.2 Remove `__pycache__` Directories

**Command:**
```bash
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

**Add to pixi.toml:**
```toml
[tasks]
clean = "find . -type d -name '__pycache__' -exec rm -rf {} + && find . -type f -name '*.pyc' -delete"
clean-logs = "rm -f *.log test_output/logs/*.log"
clean-all = { depends_on = ["clean", "clean-logs"] }
```

**Time Estimate:** 30 minutes

---

### 2.3 TODO/FIXME Audit

**Strategy:**
1. Review all TODO comments in source code
2. Convert to GitHub issues or remove if obsolete
3. Keep only actionable TODOs in code
4. Archive documentation TODOs

**Source Code TODOs (Priority):**
```python
# services/service_template/analysis.py.template (Lines 52, 138, 158)
# TODO: Replace placeholder with actual analysis logic
# → This is INTENTIONAL for templates - Keep

# src/robomage/orchestrator.py
# No actionable TODOs - Good ✅
```

**Documentation TODOs (Archive):**
- `docs/sprint-5-day-3-dashboard-integration.md` - Outdated sprint doc
- `docs/sprint-5-mvp-implementation-plan.md` - Outdated planning doc
- Move to `archive/sprint-summaries/`

**Time Estimate:** 2 hours

---

### 2.4 Fix `type: ignore` Comments

**Review Strategy:**
1. Most `type: ignore` are legitimate (numpy, workflow_engine imports)
2. Remove unnecessary ones
3. Add explanatory comments for necessary ones

**Example Cleanup:**
```python
# BEFORE
import numpy as np  # type: ignore[import]

# AFTER (with explanation)
import numpy as np  # type: ignore[import]  # NumPy stubs incomplete in mypy
```

**Files to Review:**
- `src/robomage/orchestrator.py` (9 instances - legitimate)
- `src/robomage/inspection/models.py` (6 instances - Pydantic computed fields)
- `src/robomage/data_io.py` (2 instances - pandas type inference)

**Time Estimate:** 1 hour

---

## 📚 Priority 3: Documentation Consolidation (Day 3)

### 3.1 Archive Completed Sprint Documentation

**Current State:** 79 markdown files in `docs/`

**Archive Strategy:**

```bash
# Create archive structure
mkdir -p archive/sprint-summaries/sprints-1-5/
mkdir -p archive/sprint-summaries/sprints-6-8/
mkdir -p archive/planning-docs/

# Archive completed sprint docs
mv docs/sprint-*-day-*.md archive/sprint-summaries/sprints-1-5/
mv docs/SPRINT-*-COMPLETION.md archive/sprint-summaries/sprints-6-8/
mv docs/WEEK-*-COMPLETION.md archive/sprint-summaries/sprints-6-8/

# Archive outdated planning
mv docs/*-mvp-implementation-plan.md archive/planning-docs/
mv docs/*-development-context.md archive/planning-docs/

# Archive phase completion docs (custom services complete)
mv docs/PHASE-*-COMPLETE.md archive/custom-services/
```

**Keep in docs/ (Active Documentation):**
- ✅ `README_full.md` - Comprehensive project docs
- ✅ `CUSTOM-SERVICES-PLAN.md` - Next major feature plan
- ✅ `CUSTOM-SERVICES-GUIDE.md` - User guide
- ✅ `SERVICE-CREATION-TIPS.md` - Development tips
- ✅ `TROUBLESHOOTING.md` - Problem-solving guide
- ✅ `node-development-guide.md` - Node development
- ✅ `node-quick-reference.md` - Copy-paste templates
- ✅ `dashboard-persistence-guide.md` - Session persistence
- ✅ `persistence-quick-reference.md` - Code examples
- ✅ `visual-workflow-builder-guide.md` - Workflow builder
- ✅ `llm-chat-guide.md` - LLM conversation templates

**Archive (Completed/Outdated):**
- 📦 All `sprint-*-day-*.md` files (day-by-day logs)
- 📦 All `WEEK-*-DAY-*.md` files (daily logs)
- 📦 All `PHASE-*.md` files (custom services complete)
- 📦 `*-mvp-implementation-plan.md` (planning artifacts)
- 📦 `MIGRATION-GUIDE.md` (superseded by current docs)
- 📦 `DUAL-INTERFACE-PROPOSAL.md` (already implemented)
- 📦 `CRITICAL-EVALUATION-Sprint5.md` (outdated)

**Time Estimate:** 2 hours

---

### 3.2 Update Active Documentation

**README.md Updates:**
1. Add "Test Suite Status: 383/383 passing ✅"
2. Update sprint status to reflect December 3 fixes
3. Link to GSAS-II integration roadmap (create in Priority 4)

**CUSTOM-SERVICES-PLAN.md:**
1. Mark as "Ready for Implementation"
2. Add dependencies section (requires clean test suite)

**TROUBLESHOOTING.md:**
1. Add section on test failures
2. Add section on resource warnings
3. Add section on service debugging

**Time Estimate:** 1-2 hours

---

### 3.3 Create Documentation Index

**New File:** `docs/INDEX.md`

```markdown
# RoboMage Documentation Index

**Last Updated:** December 3, 2025

## 📖 Getting Started
- [README](../README.md) - Project overview and quick start
- [TROUBLESHOOTING](TROUBLESHOOTING.md) - Common issues and solutions

## 🔧 Development Guides
- [Node Development Guide](node-development-guide.md) - Comprehensive guide
- [Node Quick Reference](node-quick-reference.md) - Copy-paste templates
- [Custom Services Guide](CUSTOM-SERVICES-GUIDE.md) - Creating analysis services
- [Service Creation Tips](SERVICE-CREATION-TIPS.md) - Best practices

## 💾 Persistence & Sessions
- [Dashboard Persistence Guide](dashboard-persistence-guide.md) - User guide
- [Persistence Quick Reference](persistence-quick-reference.md) - Code examples
- [Session Storage Expansion](session-storage-expansion-guide.md) - Extending storage

## 🎨 UI & Workflows
- [Visual Workflow Builder Guide](visual-workflow-builder-guide.md) - UI guide
- [Inspection Tools Design](inspection-tools-design.md) - Advanced features

## 🚀 Planning & Roadmap
- [Custom Services Plan](CUSTOM-SERVICES-PLAN.md) - Next major feature
- [GSAS-II Integration Roadmap](GSAS-II-INTEGRATION-ROADMAP.md) - Upcoming

## 🤖 AI Assistance
- [LLM Chat Guide](llm-chat-guide.md) - Starting new conversations

## 📦 Archive
- [Sprint Summaries](../archive/sprint-summaries/) - Historical sprint logs
- [Planning Docs](../archive/planning-docs/) - Completed planning artifacts
```

**Time Estimate:** 1 hour

---

## 🚀 Priority 4: GSAS-II Integration Preparation (Day 4)

### 4.1 Create GSAS-II Integration Roadmap

**New File:** `docs/GSAS-II-INTEGRATION-ROADMAP.md`

**Content Outline:**
```markdown
# GSAS-II Integration Roadmap

## Prerequisites ✅
- Clean test suite (383/383 passing)
- Service registry architecture in place
- Custom services template available
- Workflow integration pattern established

## Phase 1: GSAS-II Service Wrapper (Week 1)
- GSAS-II Python API research
- Service scaffold using template
- Basic refinement endpoint
- Health check integration

## Phase 2: Parameter Management (Week 2)
- Refinement parameter schema
- Pydantic models for GSAS-II inputs
- Validation and constraints
- Default parameter sets

## Phase 3: Workflow Integration (Week 3)
- GSAS-II workflow nodes
- Input data conversion (DiffractionData → GSAS-II)
- Output parsing (refinement results)
- Error handling

## Phase 4: Dashboard Integration (Week 4)
- Refinement tab in dashboard
- Parameter configuration UI
- Results visualization
- Export capabilities

## Dependencies
- GSAS-II Python package (external team)
- Clean service architecture (this cleanup)
- Stable workflow engine (current state)
```

**Time Estimate:** 2 hours

---

### 4.2 Service Architecture Review

**Verify Clean Foundation:**
1. ✅ Service registry pattern working
2. ✅ Service template validated
3. ✅ Workflow integration tested
4. ✅ Dashboard monitoring functional

**Create Pre-Flight Checklist:**
```markdown
# GSAS-II Integration Pre-Flight Checklist

## Code Quality
- [ ] All tests passing (383/383)
- [ ] No resource warnings
- [ ] Documentation current
- [ ] Root directory organized

## Service Architecture
- [ ] Service registry functional
- [ ] Service template validated
- [ ] Health check pattern established
- [ ] Workflow node pattern documented

## Dashboard Integration
- [ ] Service inspector tab working
- [ ] Service monitoring functional
- [ ] Workflow canvas stable
- [ ] Session persistence tested

## Technical Debt
- [ ] No blocking TODOs
- [ ] No critical type: ignore issues
- [ ] No hardcoded service URLs
- [ ] Clean git status
```

**Time Estimate:** 1 hour

---

### 4.3 Update Copilot Instructions

**File:** `.github/copilot-instructions.md`

**Updates Needed:**
1. Mark Sprint 8 as "Complete and Merged"
2. Add December 3, 2025 bug fixes to timeline
3. Update test suite status to 383/383
4. Add GSAS-II integration as next major milestone
5. Reference new GSAS-II roadmap document

**Time Estimate:** 30 minutes

---

## 📅 Execution Timeline

### Day 1: Critical Test Fixes (8 hours)
- **Morning:** Workflow orchestrator tests (2-3 hours)
- **Afternoon:** Workflow session integration tests (3-4 hours)
- **Evening:** Workflow serialization tests (1-2 hours)

### Day 2: Investigation & Quality (8 hours)
- **Morning:** Inspection persistence investigation (4-6 hours)
- **Afternoon:** Resource warnings cleanup (2-3 hours)
- **Evening:** Root directory organization (1 hour)

### Day 3: Documentation & Cleanup (6 hours)
- **Morning:** Archive sprint documentation (2 hours)
- **Afternoon:** Update active documentation (1-2 hours)
- **Evening:** TODO audit & type: ignore review (2-3 hours)

### Day 4: GSAS-II Prep (4 hours)
- **Morning:** Create GSAS-II roadmap (2 hours)
- **Afternoon:** Service architecture review (1 hour)
- **Evening:** Update copilot instructions (30 min)

**Total Estimated Time:** 26-30 hours (3.5-4 days)

---

## ✅ Success Criteria

### Must Have (Blockers)
1. ✅ **100% test pass rate** (383/383 tests passing)
2. ✅ **Zero resource warnings** (all connections properly closed)
3. ✅ **Clean git status** (no uncommitted changes, clean working tree)
4. ✅ **Documentation current** (all active docs reflect current state)

### Should Have (Quality)
1. ✅ **Root directory organized** (test files, logs, data moved)
2. ✅ **Technical debt addressed** (TODOs converted to issues or removed)
3. ✅ **Documentation consolidated** (sprint logs archived)
4. ✅ **Type annotations clean** (justified type: ignore comments)

### Nice to Have (Polish)
1. ✅ **Documentation index** (easy navigation for new developers)
2. ✅ **GSAS-II roadmap** (clear path forward)
3. ✅ **Clean pixi tasks** (clean, clean-logs, clean-all commands)
4. ✅ **Updated .gitignore** (prevent future clutter)

---

## 🚨 Risk Assessment

### High Risk
**Inspection Persistence Tests (5 failures)**
- **Risk:** Unknown root cause - could be deep architectural issue
- **Mitigation:** Time-box investigation to 6 hours
- **Fallback:** Create GitHub issue, mark as known limitation, proceed with GSAS-II

### Medium Risk
**Resource Warnings**
- **Risk:** May require refactoring session management
- **Mitigation:** Use context managers and fixtures
- **Fallback:** Suppress warnings if tests pass functionally

### Low Risk
**Documentation Cleanup**
- **Risk:** Breaking links or losing important content
- **Mitigation:** Review archive contents before moving
- **Fallback:** Git revert if needed (everything in version control)

---

## 📝 Notes for Execution

### Testing Strategy
```bash
# Run specific test categories
pixi run pytest tests/test_workflow_orchestrator.py -v
pixi run pytest tests/test_workflow_session_integration.py -v
pixi run pytest tests/test_inspection_persistence.py -v

# Run with warnings
pixi run pytest -W error::ResourceWarning

# Full suite validation
pixi run test

# Code quality checks
pixi run check  # format + lint + typecheck + test
```

### Git Workflow
```bash
# Create cleanup branch
git checkout -b cleanup/gsas-ii-prep

# Commit incrementally
git commit -m "fix: update workflow orchestrator tests for disconnected nodes"
git commit -m "fix: update save_to_session tests for context-based searching"
git commit -m "fix: resolve resource warnings in test suite"
git commit -m "chore: organize root directory and archive sprint docs"

# Final validation before merge
pixi run check
git push origin cleanup/gsas-ii-prep
# Create PR, review, merge to main
```

### Documentation Review Checklist
Before archiving, verify each document:
- [ ] Content not referenced in active code
- [ ] No critical information missing from current docs
- [ ] File moved to appropriate archive subdirectory
- [ ] Git history preserved (using `git mv` where possible)

---

## 🎯 Post-Cleanup Validation

**Final Checks:**
```bash
# 1. Test suite
pixi run test
# Expected: 383 passed, 0 failed, 0 warnings

# 2. Code quality
pixi run check
# Expected: All checks pass

# 3. Documentation links
cd docs && grep -r "](.*\.md)" *.md | grep -v archive
# Expected: All links valid

# 4. Git status
git status
# Expected: Clean working tree (after commit)

# 5. Root directory
ls -lh *.py *.log *.csv *.xy 2>/dev/null
# Expected: Only utility scripts (no test files/logs)
```

**Success Message:**
```
🎉 Cleanup Complete!

Test Suite: 383/383 passing (100%)
Warnings: 0
Documentation: Consolidated (12 active, 67 archived)
Root Directory: Organized
Git Status: Clean

✅ Ready for GSAS-II integration development
```

---

## 📚 References

- [Test Failures Analysis](DEC-3-2025-TEST-FAILURES.md) - Detailed failure breakdown
- [Disconnected Nodes Fix](DISCONNECTED-NODES-FIX.md) - Orchestrator changes
- [save_to_session Fix](SAVE-TO-SESSION-FIX.md) - Context-based searching
- [Service Inspector Fix](SERVICE-INSPECTOR-DEBUG-SESSION.md) - Callback fixes
- [Custom Services Plan](CUSTOM-SERVICES-PLAN.md) - Next feature roadmap

---

**Document Status:** Ready for Execution  
**Last Updated:** December 3, 2025  
**Next Review:** After Day 2 (inspection tests investigation)
