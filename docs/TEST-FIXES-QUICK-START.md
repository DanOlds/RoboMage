# Test Fixes Quick Start Guide

**Date:** December 3, 2025  
**Status:** Ready for Execution  
**Current:** 16 failing, 367 passing (95.8% pass rate)  
**Target:** 383 passing (100% pass rate)  

---

## 🎯 Overview

This guide provides **copy-paste ready** test fixes for the 16 failing tests. Execute in order for fastest resolution.

---

## Category 1: Workflow Session Integration (5 tests) ⚡ START HERE

**Time:** 30-45 minutes  
**File:** `tests/test_workflow_session_integration.py`  
**Root Cause:** Handler now searches `context.data` instead of using `inputs`

### Fix Pattern

**Find this pattern:**
```python
context = ExecutionContext()
inputs = {"files": [test_data]}
result = await save_to_session_handler(config, inputs, context)
```

**Replace with:**
```python
context = ExecutionContext()
context.set_node_output("load_files", [test_data])  # Add this line
inputs = {}  # Empty - handler searches context
result = await save_to_session_handler(config, inputs, context)
```

### Specific Test Fixes

#### Test 1: `test_save_to_session_handler_basic`
**Location:** Line ~50

**OLD:**
```python
async def test_save_to_session_handler_basic(tmp_path: Path) -> None:
    """Test basic save_to_session handler functionality."""
    storage_path = tmp_path / "storage"
    storage_path.mkdir()
    
    test_data = load_test_data()
    test_data.metadata.filename = "test_basic.chi"
    
    config = SaveToSessionConfig()
    context = ExecutionContext()
    context.active_session_id = None  # Will auto-create
    context.storage_path = str(storage_path)
    
    inputs = {"files": [test_data]}
    
    result = await save_to_session_handler(config, inputs, context)
```

**NEW:**
```python
async def test_save_to_session_handler_basic(tmp_path: Path) -> None:
    """Test basic save_to_session handler functionality."""
    storage_path = tmp_path / "storage"
    storage_path.mkdir()
    
    test_data = load_test_data()
    test_data.metadata.filename = "test_basic.chi"
    
    config = SaveToSessionConfig()
    context = ExecutionContext()
    context.active_session_id = None  # Will auto-create
    context.storage_path = str(storage_path)
    
    # NEW: Put data in context instead of inputs
    context.set_node_output("load_files", [test_data])
    inputs = {}
    
    result = await save_to_session_handler(config, inputs, context)
```

#### Test 2: `test_save_to_session_handler_multiple_files`
**Location:** Line ~100

**Find and update the inputs section:**
```python
# OLD
inputs = {"files": [test_data1, test_data2]}

# NEW
context.set_node_output("load_files", [test_data1, test_data2])
inputs = {}
```

#### Test 3: `test_save_to_session_handler_auto_create_session`
**Location:** Line ~150

**Find and update:**
```python
# OLD
inputs = {"files": [test_data]}

# NEW
context.set_node_output("load_files", [test_data])
inputs = {}
```

#### Test 4: `test_save_to_session_handler_current_session`
**Location:** Line ~200

**Find and update:**
```python
# OLD
inputs = {"files": [test_data]}

# NEW
context.set_node_output("load_files", [test_data])
inputs = {}
```

#### Test 5: `test_save_to_session_with_analysis_results`
**Location:** Line ~250

**Find and update:**
```python
# OLD
inputs = {"files": [test_data]}

# NEW
context.set_node_output("load_files", [test_data])
inputs = {}
```

### Run Validation
```bash
pixi run pytest tests/test_workflow_session_integration.py -v
# Expected: 5 tests passing
```

---

## Category 2: Workflow Orchestrator (4 tests) ⚡ MEDIUM PRIORITY

**Time:** 1-2 hours  
**File:** `tests/test_workflow_orchestrator.py`  
**Root Cause:** Tests use single disconnected nodes (no edges)

### Fix Pattern

**OLD (creates disconnected node):**
```python
workflow = WorkflowDefinition(
    name="Test Workflow",
    nodes=[WorkflowNode(id="node1", type="failing_node", ...)],
    edges=[]  # ← No edges = node won't execute!
)
```

**NEW (add input node and edge):**
```python
workflow = WorkflowDefinition(
    name="Test Workflow",
    nodes=[
        WorkflowNode(id="input", type="load_files", config={}, inputs={}),
        WorkflowNode(id="node1", type="failing_node", ...),
    ],
    edges=[Edge(source="input", target="node1")]  # ← Connect nodes
)
```

### Specific Test Fixes

#### Test 1: `test_workflow_execution_with_node_failure`
**Location:** Line ~100

**Strategy:** Add input node and connect to failing node

```python
async def test_workflow_execution_with_node_failure() -> None:
    """Test that workflow execution handles node failures gracefully."""
    
    # Register failing handler
    @register_handler("failing_node")
    async def failing_handler(config, inputs, context):
        raise ValueError("Test failure")
    
    workflow = WorkflowDefinition(
        name="Failing Workflow",
        nodes=[
            # ADD THIS NODE
            WorkflowNode(
                id="input",
                type="load_files",
                config={},
                inputs={}
            ),
            # EXISTING NODE
            WorkflowNode(
                id="fail",
                type="failing_node",
                config={},
                inputs={}
            ),
        ],
        edges=[
            Edge(source="input", target="fail")  # ADD THIS EDGE
        ],
    )
    
    orchestrator = WorkflowOrchestrator()
    
    with pytest.raises(ValueError, match="Test failure"):
        await orchestrator.execute(workflow)
```

#### Test 2: `test_workflow_with_missing_handler`
**Location:** Line ~150

**Strategy:** Add input node connected to missing handler node

```python
async def test_workflow_with_missing_handler() -> None:
    """Test that workflow execution fails with missing handler."""
    
    workflow = WorkflowDefinition(
        name="Missing Handler Workflow",
        nodes=[
            # ADD THIS NODE
            WorkflowNode(
                id="input",
                type="load_files",
                config={},
                inputs={}
            ),
            # EXISTING NODE
            WorkflowNode(
                id="missing",
                type="nonexistent_handler",
                config={},
                inputs={}
            ),
        ],
        edges=[
            Edge(source="input", target="missing")  # ADD THIS EDGE
        ],
    )
    
    orchestrator = WorkflowOrchestrator()
    
    with pytest.raises(ValueError, match="No handler registered"):
        await orchestrator.execute(workflow)
```

#### Test 3: `test_initial_context_passed_to_handlers`
**Location:** Line ~200

**Strategy:** Connect nodes to ensure execution

```python
async def test_initial_context_passed_to_handlers() -> None:
    """Test that initial context data is passed to handlers."""
    
    received_context = None
    
    @register_handler("context_receiver")
    async def context_receiver(config, inputs, context):
        nonlocal received_context
        received_context = context
        return NodeExecutionResult(
            node_id="receiver",
            node_type="context_receiver",
            status="success",
            outputs={}
        )
    
    workflow = WorkflowDefinition(
        name="Context Test Workflow",
        nodes=[
            # ADD INPUT NODE
            WorkflowNode(
                id="input",
                type="load_files",
                config={},
                inputs={}
            ),
            # EXISTING NODE
            WorkflowNode(
                id="receiver",
                type="context_receiver",
                config={},
                inputs={}
            ),
        ],
        edges=[
            Edge(source="input", target="receiver")  # ADD EDGE
        ],
    )
    
    initial_context = ExecutionContext()
    initial_context.set_node_output("init", {"test": "data"})
    
    orchestrator = WorkflowOrchestrator()
    await orchestrator.execute(workflow, initial_context=initial_context)
    
    assert received_context is not None
    assert received_context.get_node_output("init") == {"test": "data"}
```

#### Test 4: `test_execution_timing_recorded`
**Location:** Line ~250

**Strategy:** Connect nodes to ensure execution happens

```python
async def test_execution_timing_recorded() -> None:
    """Test that execution timing is recorded for nodes."""
    
    @register_handler("timed_node")
    async def timed_handler(config, inputs, context):
        import asyncio
        await asyncio.sleep(0.1)  # Simulate work
        return NodeExecutionResult(
            node_id="timed",
            node_type="timed_node",
            status="success",
            outputs={}
        )
    
    workflow = WorkflowDefinition(
        name="Timing Test Workflow",
        nodes=[
            # ADD INPUT NODE
            WorkflowNode(
                id="input",
                type="load_files",
                config={},
                inputs={}
            ),
            # EXISTING NODE
            WorkflowNode(
                id="timed",
                type="timed_node",
                config={},
                inputs={}
            ),
        ],
        edges=[
            Edge(source="input", target="timed")  # ADD EDGE
        ],
    )
    
    orchestrator = WorkflowOrchestrator()
    result = await orchestrator.execute(workflow)
    
    assert "timed" in result.node_results
    assert result.node_results["timed"].execution_time_ms > 0
```

### Run Validation
```bash
pixi run pytest tests/test_workflow_orchestrator.py -v
# Expected: 4 tests passing
```

---

## Category 3: Workflow Serialization (2 tests) ⚡ QUICK FIX

**Time:** 30 minutes  
**File:** `tests/test_workflow_session_full_serialization.py`  
**Root Cause:** Same as orchestrator - needs connected nodes

### Fix Pattern

Same as Category 2 - add input nodes and edges to workflows.

#### Test 1: `test_orchestrator_full_serialization_mode`
**Location:** Line ~50

**Find the workflow definition and add input node:**
```python
workflow = WorkflowDefinition(
    name="Serialization Test",
    nodes=[
        # ADD INPUT NODE
        WorkflowNode(id="input", type="load_files", config={}, inputs={}),
        # EXISTING NODES...
    ],
    edges=[
        # ADD EDGES TO CONNECT INPUT TO OTHER NODES
        Edge(source="input", target="next_node_id")
    ]
)
```

#### Test 2: `test_orchestrator_summary_mode_default`
**Location:** Line ~100

**Same pattern - add input node and edges**

### Run Validation
```bash
pixi run pytest tests/test_workflow_session_full_serialization.py -v
# Expected: 2 tests passing
```

---

## Category 4: Inspection Persistence (5 tests) ⚠️ INVESTIGATION NEEDED

**Time:** 4-6 hours (includes investigation)  
**File:** `tests/test_inspection_persistence.py`  
**Status:** Root cause unknown - needs debugging

### Investigation Steps

#### Step 1: Run with verbose output
```bash
pixi run pytest tests/test_inspection_persistence.py -vv -s
```

#### Step 2: Check if related to disconnected nodes
```python
# Add debug logging to test
import logging
logging.basicConfig(level=logging.DEBUG)

# Run specific test
pixi run pytest tests/test_inspection_persistence.py::TestSessionManagerInspectionCRUD::test_get_inspections_no_filters -vv
```

#### Step 3: Review inspection creation logic
- Check if inspections are created for disconnected nodes
- Verify inspection snapshots are saved correctly
- Look for changes in `src/robomage/orchestrator.py` inspection code

#### Step 4: Temporary workaround (if needed)
```python
# Mark as expected failure temporarily
@pytest.mark.xfail(reason="Under investigation - may be related to orchestrator changes")
def test_get_inspections_no_filters():
    ...
```

### Potential Root Causes

1. **Disconnected Nodes:** Inspections may be created only for executed nodes
2. **Database Schema:** Recent changes may affect inspection queries
3. **Context Changes:** Inspection snapshot creation may need context updates
4. **Pre-existing Issue:** May be unrelated to December 3 changes

### Rollback Plan

If investigation exceeds 6 hours:
1. Create GitHub issue with findings
2. Mark tests as `@pytest.mark.xfail`
3. Document limitation in TROUBLESHOOTING.md
4. Proceed with GSAS-II integration

---

## Category 5: Resource Warnings (18 warnings) 🔧 POLISH

**Time:** 2-3 hours  
**Priority:** Medium (tests pass functionally)  
**Root Cause:** Unclosed database connections in tests

### Fix Pattern

**OLD (connection leak):**
```python
def test_something():
    session_manager = SessionManager(storage_path)
    # Test code...
    # No cleanup - connection leaks!
```

**NEW (with fixture):**
```python
@pytest.fixture
async def session_manager(tmp_path):
    """Provide SessionManager with automatic cleanup."""
    sm = SessionManager(str(tmp_path / "storage"))
    yield sm
    # Cleanup
    await sm.close()  # Close connections
    
async def test_something(session_manager):
    # Test code...
    pass  # Automatic cleanup via fixture
```

### Files to Update

1. **tests/test_peak_analysis_integration.py**
2. **tests/test_session_persistence_integration.py**
3. **All tests using SessionManager**

### Validation
```bash
# Run with warnings as errors
pixi run pytest -W error::ResourceWarning
# Expected: All tests pass, no warnings
```

---

## 🚀 Execution Checklist

### Quick Wins (Do These First) ✅
- [ ] Fix Category 1: Workflow session integration (5 tests, 30-45 min)
- [ ] Fix Category 3: Workflow serialization (2 tests, 30 min)
- [ ] **Run tests:** `pixi run test` (should see 11/16 fixed)

### Medium Priority 🔨
- [ ] Fix Category 2: Workflow orchestrator (4 tests, 1-2 hours)
- [ ] **Run tests:** `pixi run test` (should see 15/16 fixed)

### Investigation Required 🔍
- [ ] Investigate Category 4: Inspection persistence (5 tests, 4-6 hours)
- [ ] Fix or mark as xfail
- [ ] **Run tests:** `pixi run test` (target: 383/383 passing)

### Polish 💅
- [ ] Fix Category 5: Resource warnings (2-3 hours)
- [ ] **Run tests:** `pixi run pytest -W error::ResourceWarning`

---

## ✅ Success Criteria

After fixes:
```bash
pixi run test
# Expected output:
# ==================== 383 passed in X.XXs ====================
# No warnings, 100% pass rate
```

---

## 📚 Reference Documents

- [Detailed Cleanup Plan](GSAS-II-PREP-CLEANUP-PLAN.md) - Full cleanup strategy
- [Test Failures Analysis](DEC-3-2025-TEST-FAILURES.md) - Detailed failure breakdown
- [Disconnected Nodes Fix](DISCONNECTED-NODES-FIX.md) - Orchestrator changes
- [save_to_session Fix](SAVE-TO-SESSION-FIX.md) - Context-based searching

---

**Last Updated:** December 3, 2025  
**Next Review:** After Category 1-3 fixes complete
