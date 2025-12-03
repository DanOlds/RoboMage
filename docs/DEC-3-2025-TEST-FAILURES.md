# Test Failures After December 3, 2025 Fixes

**Date:** December 3, 2025  
**Status:** 16 tests failing (367 passing)  
**Cause:** Recent architectural changes require test updates

## Summary

Three major fixes were implemented today that require test suite updates:

1. **Disconnected Nodes Fix** - Orchestrator now excludes nodes without edges
2. **save_to_session Redesign** - Node now searches context instead of using inputs
3. **Service Inspector Fixes** - No test impact (dashboard callbacks)

## Failing Tests Breakdown

### Category 1: Workflow Orchestrator Tests (5 failures)

**Root Cause:** Tests use workflows with single disconnected nodes (no edges). These are now correctly excluded from execution.

**Files:**
- `tests/test_workflow_orchestrator.py` (4 failures)
- `tests/test_workflow_session_full_serialization.py` (2 failures)

**Example:**
```python
# Test creates workflow with ONE node, NO edges
workflow = WorkflowDefinition(
    name="Failing Workflow",
    nodes=[WorkflowNode(id="node1", type="failing_node", ...)],
    edges=[]  # ← No edges means node won't execute!
)
```

**Fix Required:**
Add edges to make nodes connected, or test explicitly for disconnected node exclusion.

```python
# Option 1: Add edges to connect nodes
edges=[Edge(source="node0", target="node1")]

# Option 2: Test disconnected node behavior explicitly
assert "Excluding 1 disconnected node(s)" in logs
```

### Category 2: save_to_session Handler Tests (5 failures)

**Root Cause:** Tests pass data through `inputs` parameter, but handler now searches `context.data` instead.

**Files:**
- `tests/test_workflow_session_integration.py` (5 failures)

**Example:**
```python
# Old approach (no longer works)
inputs = {"files": [test_data]}
result = await save_to_session_handler(config, inputs, context)

# New approach (required)
context = ExecutionContext()
context.set_node_output("load_1", [test_data])  # Put data IN context
result = await save_to_session_handler(config, {}, context)
```

**Fix Required:**
Update tests to populate `context.data` with DiffractionData objects instead of passing through `inputs`.

### Category 3: Inspection Persistence Tests (5 failures)

**Root Cause:** These tests may be affected by orchestrator changes or may have pre-existing issues.

**Files:**
- `tests/test_inspection_persistence.py` (5 failures)

**Needs Investigation:**
- Check if inspection data is being created for disconnected nodes
- Verify inspection snapshot creation logic
- May be unrelated to today's changes

## Resolution Strategy

### Immediate Actions

1. **Update orchestrator tests** - Add edges to workflows or test disconnected behavior
2. **Update save_to_session tests** - Use context.data instead of inputs
3. **Investigate inspection tests** - Determine if related to today's changes

### Test Update Priority

**High Priority (blocks functionality):**
- `test_save_to_session_handler_*` - Core workflow-session integration

**Medium Priority (semantic changes):**
- `test_workflow_orchestrator.py` tests - Verify new disconnected node behavior

**Low Priority (needs investigation):**
- `test_inspection_persistence.py` - May be pre-existing issues

## Quick Fix Examples

### Fix 1: Orchestrator Test with Edges

**Before:**
```python
workflow = WorkflowDefinition(
    nodes=[WorkflowNode(id="node1", type="test_node", ...)],
    edges=[]
)
```

**After:**
```python
workflow = WorkflowDefinition(
    nodes=[
        WorkflowNode(id="node0", type="input_node", ...),
        WorkflowNode(id="node1", type="test_node", ...),
    ],
    edges=[Edge(source="node0", target="node1")]
)
```

### Fix 2: save_to_session Test with Context

**Before:**
```python
context = ExecutionContext()
inputs = {"files": [test_data]}
result = await save_to_session_handler(config, inputs, context)
```

**After:**
```python
context = ExecutionContext()
context.set_node_output("load_files", [test_data])
inputs = {}  # Inputs no longer used
result = await save_to_session_handler(config, inputs, context)
```

## Recommendation

**For cleanup chat:** These test failures should be addressed as part of the code cleanup effort. The failures are expected and indicate the tests need updating to match the new (correct) behavior.

**Do not merge:** The current code should not be merged to main until tests are updated and passing.

## Test Run Summary

```
16 failed, 367 passed, 19 warnings in 21.93s

FAILED tests:
- test_inspection_persistence.py (5 tests)
- test_workflow_orchestrator.py (4 tests)
- test_workflow_session_full_serialization.py (2 tests)
- test_workflow_session_integration.py (5 tests)
```

## Notes for Next Chat

The failing tests are **expected** given the architectural improvements:
1. Orchestrator correctly excludes disconnected nodes
2. save_to_session correctly searches full context
3. Tests need updates to reflect new behavior

This is technical debt that should be addressed in the cleanup phase before GSAS-II development.
