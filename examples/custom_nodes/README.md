# Custom Node Examples

**Complete working examples demonstrating RoboMage workflow node development.**

This directory contains three example nodes with increasing complexity levels, demonstrating best practices for creating custom analysis capabilities in RoboMage.

## Examples Overview

### 1. Template Node (Simple)
**File**: `template_node.py`  
**Complexity**: ⭐ Beginner  
**Purpose**: Minimal "Hello World" example with extensive inline documentation

**What it does**:
- Accepts DiffractionData files
- Applies simple transformation (scale intensities)
- Returns structured results

**Key concepts demonstrated**:
- Basic handler function structure
- Configuration extraction with defaults
- Input validation
- Error handling
- Logging best practices

**Use this when**: Starting a new node from scratch

---

### 2. Background Subtraction Node (Medium)
**File**: `background_subtraction_node.py`  
**Complexity**: ⭐⭐ Intermediate  
**Purpose**: Real-world data processing example

**What it does**:
- Fits backgrounds using linear, constant, or polynomial methods
- Subtracts background from diffraction patterns
- Preserves metadata through transformations
- Returns modified DiffractionData objects

**Key concepts demonstrated**:
- Working with NumPy arrays
- Creating new DiffractionData instances
- Q-range selection and masking
- Quality metrics (R² calculation)
- Metadata preservation

**Use this when**: Building data transformation nodes

---

### 3. Peak Width Analysis Node (Advanced)
**File**: `peak_width_analysis_node.py`  
**Complexity**: ⭐⭐⭐ Advanced  
**Purpose**: Scientific analysis with external libraries

**What it does**:
- Analyzes peak widths (FWHM) from peak detection results
- Fits Gaussian, Lorentzian, or Voigt profiles
- Calculates statistical summaries
- Classifies peaks (narrow/medium/broad)

**Key concepts demonstrated**:
- Integration with scipy
- Processing results from other nodes
- Multiple input sources (files + results)
- Optional dependencies with helpful errors
- Statistical analysis
- Complex output structures

**Use this when**: Building advanced analysis nodes with external dependencies

---

## Quick Start

### 1. Study the Examples

Start with the template node to understand the basic structure:

```python
# Read template_node.py
# Copy the handler function template
# Modify the TODO sections with your logic
```

Progress to background subtraction for data processing patterns, then peak width analysis for advanced techniques.

### 2. Register Your Node

Add your handler to the workflow orchestrator:

```python
# In services/workflow_engine/main.py or custom script

from examples.custom_nodes import template_node_handler

orchestrator = WorkflowOrchestrator()
orchestrator.register_node_handler("template_node", template_node_handler)
```

### 3. Use in Workflows

Reference your node in workflow JSON:

```json
{
  "nodes": [
    {
      "id": "my_node_1",
      "type": "template_node",
      "config": {
        "scale_factor": 2.0,
        "description": "Test scaling"
      }
    }
  ]
}
```

### 4. Test the Inspector

Enable inspection to see I/O data:

```python
orchestrator = WorkflowOrchestrator(enable_inspection=True)
result = await orchestrator.execute_workflow(workflow)

# View captured I/O in dashboard Inspector tab
```

---

## Complete Example Workflow

**File**: `example_workflow.json`

Demonstrates all three custom nodes in a complete analysis pipeline:

```
Load Files → Background Subtract → Peak Analysis → Width Analysis → Export
```

**Run the example**:

```bash
# 1. Start the peak analysis service
pixi run python services/peak_analysis/main.py --port 8001

# 2. Run the example workflow
python -m examples.custom_nodes.run_example_workflow

# 3. View results in test_output/
```

See `example_workflow.json` for the complete workflow definition.

---

## Testing Your Nodes

### Unit Testing

Test handlers in isolation:

```python
import pytest
from robomage.orchestrator import ExecutionContext
from examples.custom_nodes import template_node_handler

@pytest.mark.asyncio
async def test_template_node():
    config = {"scale_factor": 2.0}
    inputs = {"input": [test_data]}
    context = ExecutionContext()
    
    result = await template_node_handler(config, inputs, context)
    
    assert len(result) == 1
    assert result[0]["scale_factor"] == 2.0
```

### Integration Testing

Test in workflow context:

```python
@pytest.mark.asyncio
async def test_workflow_with_custom_nodes():
    orch = WorkflowOrchestrator()
    orch.register_node_handler("template_node", template_node_handler)
    
    workflow = {...}  # Your workflow definition
    result = await orch.execute_workflow(workflow)
    
    assert result.status == "completed"
```

**Run all tests**:

```bash
pixi run python -m pytest examples/custom_nodes/test_custom_nodes.py -v
```

---

## Registration Patterns

### Pattern 1: Direct Registration

Simple registration in your script:

```python
from robomage.orchestrator import WorkflowOrchestrator
from examples.custom_nodes import (
    template_node_handler,
    background_subtraction_handler,
    peak_width_analysis_handler,
)

orch = WorkflowOrchestrator()
orch.register_node_handler("template_node", template_node_handler)
orch.register_node_handler("background_subtraction", background_subtraction_handler)
orch.register_node_handler("peak_width_analysis", peak_width_analysis_handler)
```

### Pattern 2: Batch Registration

Register multiple nodes from a module:

```python
from examples import custom_nodes

NODE_HANDLERS = {
    "template_node": custom_nodes.template_node_handler,
    "background_subtraction": custom_nodes.background_subtraction_handler,
    "peak_width_analysis": custom_nodes.peak_width_analysis_handler,
}

for node_type, handler in NODE_HANDLERS.items():
    orch.register_node_handler(node_type, handler)
```

### Pattern 3: Auto-Discovery

Dynamically discover and register handlers:

```python
import inspect
from examples import custom_nodes

for name, obj in inspect.getmembers(custom_nodes):
    if name.endswith("_handler") and callable(obj):
        # Extract node type from handler name
        node_type = name.replace("_handler", "")
        orch.register_node_handler(node_type, obj)
```

---

## Workflow JSON Structure

### Basic Structure

```json
{
  "nodes": [
    {
      "id": "unique_node_id",
      "type": "node_type",
      "config": {
        "param1": "value1",
        "param2": 123
      }
    }
  ],
  "edges": [
    {
      "source": "source_node_id",
      "target": "target_node_id"
    }
  ]
}
```

### Linear Pipeline

```json
{
  "nodes": [
    {"id": "load", "type": "load_files", "config": {...}},
    {"id": "bg_sub", "type": "background_subtraction", "config": {...}},
    {"id": "analyze", "type": "peak_analysis", "config": {...}}
  ],
  "edges": [
    {"source": "load", "target": "bg_sub"},
    {"source": "bg_sub", "target": "analyze"}
  ]
}
```

### Parallel Branches

```json
{
  "nodes": [
    {"id": "load", "type": "load_files", "config": {...}},
    {"id": "branch1", "type": "peak_analysis", "config": {...}},
    {"id": "branch2", "type": "statistics", "config": {...}},
    {"id": "merge", "type": "export_csv", "config": {...}}
  ],
  "edges": [
    {"source": "load", "target": "branch1"},
    {"source": "load", "target": "branch2"},
    {"source": "branch1", "target": "merge"}
  ]
}
```

---

## Node I/O Inspector Integration

All custom nodes automatically integrate with the Inspector tab when inspection is enabled.

### Enable Inspection

```python
orchestrator = WorkflowOrchestrator(enable_inspection=True)
```

### What Gets Captured

For each node execution:
- **Inputs**: All data passed to the handler (config, inputs, context metadata)
- **Outputs**: Return value from the handler
- **Metadata**: Execution time, node type, success/failure status

### Viewing in Dashboard

1. Run workflow with inspection enabled
2. Open RoboMage dashboard
3. Navigate to "Inspector" tab
4. Select node execution from list
5. View inputs/outputs in formatted panels

**Tip**: Inspector is invaluable for debugging node interactions!

---

## Common Workflows

### Workflow 1: Simple Processing

```
Load Files → Template Node → Export CSV
```

**Use case**: Quick data transformation and export

### Workflow 2: Background-Corrected Analysis

```
Load Files → Background Subtract → Peak Analysis → Export
```

**Use case**: Standard peak detection with background correction

### Workflow 3: Complete Analysis Pipeline

```
Load Files → Background Subtract → Peak Analysis → Width Analysis → Export
```

**Use case**: Comprehensive peak characterization (see `example_workflow.json`)

### Workflow 4: Multi-Method Comparison

```
            ┌─ BG Sub (linear) ─┐
Load Files ─┼─ BG Sub (constant)─┼─ Peak Analysis → Export
            └─ BG Sub (poly) ────┘
```

**Use case**: Compare different background subtraction methods

---

## Best Practices Checklist

### Configuration ✅
- [ ] Use `config.get(key, default)` for optional parameters
- [ ] Validate required parameters exist
- [ ] Validate parameter ranges/types
- [ ] Log configuration at start

### Input Validation ✅
- [ ] Check for empty/missing inputs
- [ ] Validate input types
- [ ] Handle both single items and lists
- [ ] Provide clear error messages

### Processing ✅
- [ ] Log progress (DEBUG for details, INFO for milestones)
- [ ] Use try/except for error handling
- [ ] Decide on fail-fast vs. best-effort strategy
- [ ] Track errors for detailed reporting

### Output ✅
- [ ] Return structured dictionaries or lists
- [ ] Convert NumPy arrays to lists for JSON serialization
- [ ] Include metadata in results
- [ ] Preserve DiffractionData metadata when transforming

### Documentation ✅
- [ ] Comprehensive docstring with parameters, inputs, outputs
- [ ] Example configuration in docstring
- [ ] Inline comments explaining complex logic
- [ ] Describe expected errors and troubleshooting

---

## Troubleshooting

### Problem: Node not found in workflow builder

**Solution**: Ensure node is registered before workflow execution:

```python
orchestrator.register_node_handler("my_node", my_handler)
```

### Problem: JSON serialization error

**Solution**: Convert NumPy arrays to lists:

```python
# ❌ WRONG
return data.intensities

# ✅ CORRECT
return data.intensities.tolist()
```

### Problem: Import errors for optional dependencies

**Solution**: Add helpful error message:

```python
try:
    from scipy import optimize
except ImportError:
    raise ImportError(
        "This node requires scipy. Install with:\n"
        "  pixi add scipy"
    )
```

### Problem: Inspector shows no data

**Solution**: Enable inspection when creating orchestrator:

```python
orch = WorkflowOrchestrator(enable_inspection=True)
```

---

## Next Steps

### For Beginners
1. Read `template_node.py` thoroughly
2. Copy the template and modify one parameter
3. Test with simple workflow
4. View in Inspector tab

### For Intermediate Users
1. Study `background_subtraction_node.py`
2. Implement your own data transformation
3. Test with real diffraction data
4. Compare results with/without processing

### For Advanced Users
1. Study `peak_width_analysis_node.py`
2. Integrate external scientific libraries
3. Build multi-step analysis pipelines
4. Contribute back to RoboMage!

---

## Additional Resources

- **[Node Development Guide](../../docs/node-development-guide.md)** - Comprehensive documentation
- **[Quick Reference](../../docs/node-quick-reference.md)** - Copy-paste templates
- **[Built-in Nodes](../../src/robomage/workflow/nodes/)** - Production reference code
- **[Orchestrator](../../src/robomage/orchestrator.py)** - Workflow execution engine
- **[Data Models](../../src/robomage/data/models.py)** - DiffractionData API

---

## Questions or Issues?

Open an issue on the RoboMage GitHub repository or start a discussion.

**Happy node building! 🚀**
