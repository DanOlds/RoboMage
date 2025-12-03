# Disconnected Nodes Execution Bug Fix

**Date:** December 3, 2025  
**Issue:** Workflow orchestrator executes disconnected nodes (nodes with no edges)  
**Status:** ✅ **FIXED**

## Problem

The workflow orchestrator was executing **ALL nodes**, even those that weren't connected to the workflow graph. This violated the fundamental principle of DAG (Directed Acyclic Graph) execution where edges define dependencies and execution order.

### Example

Given this workflow:
```json
{
  "nodes": [
    {"id": "load_1", "type": "load_files"},
    {"id": "analyze_1", "type": "peak_analysis"},
    {"id": "export_1", "type": "export_csv"},
    {"id": "statistics_3c89320c", "type": "statistics"}  // NOT CONNECTED!
  ],
  "edges": [
    {"source": "load_1", "target": "analyze_1"},
    {"source": "analyze_1", "target": "export_1"}
  ]
}
```

**Expected behavior:** Execute only `load_1 → analyze_1 → export_1`  
**Actual behavior:** Executed `load_1` and `statistics_3c89320c`, then failed

### Root Cause

In `src/robomage/orchestrator.py`, the `_topological_sort()` method used Kahn's algorithm but had a critical bug:

```python
# Old code - BUGGY
for node in workflow.nodes:
    in_degree[node.id] = 0  # All nodes start with 0

# Start queue with ALL nodes that have in_degree=0
queue = deque([node_id for node_id in in_degree if in_degree[node_id] == 0])
```

**Problem:** Disconnected nodes have no incoming edges, so they stay at `in_degree=0` and get added to the execution queue!

## Solution

Modified `_topological_sort()` to track which nodes are **part of the connected graph** and exclude disconnected nodes:

```python
# Track which nodes are part of the graph (have edges)
nodes_in_graph = set()

# Build graph from edges
for edge in workflow.edges:
    graph[edge.source].append(edge.target)
    in_degree[edge.target] += 1
    # Mark both source and target as part of graph
    nodes_in_graph.add(edge.source)
    nodes_in_graph.add(edge.target)

# Filter: only process nodes that are part of the graph
connected_nodes = {
    node_id: degree
    for node_id, degree in in_degree.items()
    if node_id in nodes_in_graph
}

# Only start queue with connected nodes
queue = deque(
    [
        node_id
        for node_id, degree in connected_nodes.items()
        if degree == 0
    ]
)
```

### Key Changes

1. **Track connected nodes:** Build a set of all node IDs that appear in edges
2. **Filter before execution:** Only include nodes from `nodes_in_graph` set
3. **Update cycle detection:** Check `len(sorted_nodes) != len(connected_nodes)` instead of `len(workflow.nodes)`
4. **Log excluded nodes:** Inform user which disconnected nodes were skipped

## Impact

### Before Fix
- ❌ All nodes execute, even disconnected ones
- ❌ Execution order unpredictable
- ❌ Failures occur when disconnected nodes missing inputs
- ❌ Confusing for users - arrows seem meaningless

### After Fix
- ✅ Only connected nodes execute
- ✅ Execution follows DAG topology
- ✅ Disconnected nodes safely ignored
- ✅ Clear logging shows which nodes were excluded

## Examples

### Example 1: Disconnected Node

**Workflow:**
```
load_files → peak_analysis → export_csv
statistics (not connected)
```

**Output:**
```
INFO: Excluding 1 disconnected node(s) from execution: statistics_3c89320c
INFO: Execution order determined: ['load_1', 'analyze_1', 'export_1']
```

### Example 2: Multiple Disconnected Nodes

**Workflow:**
```
load_files → peak_analysis
background_subtraction (not connected)
normalize (not connected)
statistics (not connected)
```

**Output:**
```
INFO: Excluding 3 disconnected node(s) from execution: background_subtraction, normalize, statistics
INFO: Execution order determined: ['load_1', 'analyze_1']
```

### Example 3: All Nodes Connected

**Workflow:**
```
load_files → peak_analysis → save_to_session
```

**Output:**
```
INFO: Execution order determined: ['load_1', 'analyze_1', 'save_to_session_1']
```
(No exclusion message)

## Testing

**Restart workflow service:**
```bash
pkill -f "workflow_engine"
pixi run python services/workflow_engine/main.py --port 8002 --host 127.0.0.1
```

**Test workflow with disconnected node:**
1. Create workflow in dashboard
2. Add nodes: load_files, peak_analysis, export_csv
3. Connect: load_files → peak_analysis → export_csv
4. Add another node (e.g., statistics) WITHOUT connecting it
5. Execute workflow

**Expected result:**
- Only connected nodes execute
- Disconnected node appears in log as excluded
- Workflow completes successfully (if connected portion is valid)

## Design Philosophy

This fix aligns with standard workflow/DAG execution principles:

1. **Edges Define Execution:** Only nodes in the connected graph are considered for execution
2. **Explicit Dependencies:** If a node should run, it must be connected to the graph
3. **Safe Defaults:** Disconnected nodes are warnings, not errors
4. **Clear Feedback:** Users see which nodes were excluded and why

## Future Enhancements

Potential improvements:

1. **Warning in UI:** Highlight disconnected nodes in workflow canvas
2. **Validation:** Warn user when saving workflow with disconnected nodes
3. **Multiple Components:** Support workflows with multiple disconnected subgraphs (execute all components)
4. **Manual Triggers:** Allow marking nodes for "always execute" regardless of connections

## Related Code

- **Fixed file:** `src/robomage/orchestrator.py`
- **Method:** `_topological_sort()` (lines 549-629)
- **Related:** Workflow execution in `execute_workflow()` (line 454)
