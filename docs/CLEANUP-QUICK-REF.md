# 🚀 Cleanup Quick Reference Card

**Date:** December 3, 2025  
**Current:** 367/383 passing (95.8%)  
**Target:** 378-383 passing (98.7-100%)  

---

## ⚡ Quick Commands

```bash
# 1. Run workspace cleanup
./cleanup_prep.sh workspace

# 2. Fix test categories (in order)
pixi run pytest tests/test_workflow_session_integration.py -v       # Cat 1 (5 tests)
pixi run pytest tests/test_workflow_session_full_serialization.py -v # Cat 3 (2 tests)
pixi run pytest tests/test_workflow_orchestrator.py -v              # Cat 2 (4 tests)

# 3. Full test suite
pixi run test

# 4. Full cleanup
./cleanup_prep.sh all

# 5. Code quality check
pixi run check
```

---

## 📋 Test Fix Cheat Sheet

### Category 1: Workflow Session Integration (5 tests - 30 min)
**File:** `tests/test_workflow_session_integration.py`

**Find:**
```python
inputs = {"files": [test_data]}
result = await save_to_session_handler(config, inputs, context)
```

**Replace:**
```python
context.set_node_output("load_files", [test_data])
inputs = {}
result = await save_to_session_handler(config, inputs, context)
```

---

### Category 2: Workflow Orchestrator (4 tests - 1 hour)
**File:** `tests/test_workflow_orchestrator.py`

**Find:**
```python
workflow = WorkflowDefinition(
    nodes=[WorkflowNode(id="node1", type="test", ...)],
    edges=[]
)
```

**Replace:**
```python
workflow = WorkflowDefinition(
    nodes=[
        WorkflowNode(id="input", type="load_files", config={}, inputs={}),
        WorkflowNode(id="node1", type="test", ...),
    ],
    edges=[Edge(source="input", target="node1")]
)
```

---

### Category 3: Workflow Serialization (2 tests - 30 min)
**File:** `tests/test_workflow_session_full_serialization.py`

**Same as Category 2** - Add input nodes and edges

---

## 📊 Progress Tracker

```
Phase 1: Quick Wins (2-3 hours)
├─ [☐] Run cleanup script (5 min)
├─ [☐] Fix Cat 1: Session integration (30 min) → 372/383 passing
└─ [☐] Fix Cat 3: Serialization (30 min) → 374/383 passing

Phase 2: Medium Priority (1-2 hours)
└─ [☐] Fix Cat 2: Orchestrator (1-2 hours) → 378/383 passing

Phase 3: Investigation (4-6 hours)
└─ [☐] Cat 4: Inspection tests (or mark xfail) → 378-383/383 passing

Phase 4: Polish (4-6 hours)
├─ [☐] Docs cleanup (2 hours)
├─ [☐] Resource warnings (2-3 hours)
└─ [☐] Final validation (1 hour)

Phase 5: GSAS-II Prep (2-3 hours)
└─ [☐] Create roadmap (2-3 hours)
```

---

## 🎯 Success Validation

```bash
# After each phase:
pixi run test | tail -1
# Should see: "XXX passed" (increasing)

# Final validation:
pixi run check
# Should see: All checks pass

./cleanup_prep.sh validate
# Should see: Clean workspace report
```

---

## 📁 Key Documents

| Document | Purpose | Use When |
|----------|---------|----------|
| [CLEANUP-SUMMARY.md](CLEANUP-SUMMARY.md) | Overview & plan | Starting cleanup |
| [TEST-FIXES-QUICK-START.md](TEST-FIXES-QUICK-START.md) | Copy-paste fixes | Fixing tests |
| [GSAS-II-PREP-CLEANUP-PLAN.md](GSAS-II-PREP-CLEANUP-PLAN.md) | Detailed plan | Need details |
| [DEC-3-2025-TEST-FAILURES.md](DEC-3-2025-TEST-FAILURES.md) | Failure analysis | Understanding issues |

---

## 🚨 If Stuck

### Tests still failing?
```bash
# Run with verbose output
pixi run pytest tests/test_X.py -vv -s

# Check specific test
pixi run pytest tests/test_X.py::test_name -vv
```

### Inspection tests won't pass?
**Time-box to 6 hours, then:**
1. Mark as `@pytest.mark.xfail`
2. Create GitHub issue
3. Proceed with 378/383 passing (98.7%)

### Resource warnings?
**If fixes take >3 hours:**
1. Document in TROUBLESHOOTING.md
2. Create GitHub issue
3. Proceed (tests pass functionally)

---

## ✅ Daily Checkpoints

**End of Day 1:** 374/383 passing (97.6%)  
**End of Day 2:** 378/383 passing (98.7%)  
**End of Day 3:** Documentation consolidated  
**End of Day 4:** Ready for GSAS-II  

---

**Quick Start:** Run `./cleanup_prep.sh workspace && pixi run test`  
**Full Docs:** See [CLEANUP-SUMMARY.md](CLEANUP-SUMMARY.md)
