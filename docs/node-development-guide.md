# Node Development Guide

**Date**: December 1, 2025  
**Audience**: Developers extending RoboMage with custom analysis capabilities  
**Prerequisites**: Python 3.11+, basic async/await knowledge, familiarity with RoboMage data models

## Table of Contents

1. [Introduction](#introduction)
2. [Node Architecture](#node-architecture)
3. [Handler Function Interface](#handler-function-interface)
4. [Design Patterns](#design-patterns)
5. [Integration](#integration)
6. [Testing Guidelines](#testing-guidelines)
7. [Common Pitfalls](#common-pitfalls)
8. [Advanced Topics](#advanced-topics)

---

## Introduction

### What Are Workflow Nodes?

Workflow nodes are the building blocks of RoboMage analysis pipelines. Each node represents a discrete operation:

- **Data nodes**: Load, transform, filter diffraction data
- **Analysis nodes**: Detect peaks, calculate statistics, perform refinement
- **Output nodes**: Export results to CSV, JSON, or sessions

Nodes are connected in directed acyclic graphs (DAGs) where data flows from source to sink, enabling complex multi-step workflows through simple composition.

### When to Create a New Node

**Create a new node when:**
- ✅ Implementing a new analysis algorithm
- ✅ Adding integration with external tools (GSAS-II, FullProf, etc.)
- ✅ Supporting new file formats or data sources
- ✅ Encapsulating a reusable analysis pattern

**Modify existing nodes when:**
- ❌ Fixing bugs in current functionality
- ❌ Improving performance of existing algorithms
- ❌ Adding minor options to established nodes

### Node Lifecycle

1. **Registration**: Handler function registered with orchestrator
2. **Validation**: Workflow engine validates node configuration
3. **Execution**: Orchestrator calls handler with inputs and config
4. **Output**: Handler returns data for downstream nodes
5. **Inspection** (optional): I/O data captured for debugging

---

## Node Architecture

### Handler Function Pattern

RoboMage uses **async handler functions** rather than class-based nodes for simplicity and flexibility:

```python
async def my_node_handler(
    config: dict[str, Any],
    inputs: dict[str, Any],
    context: ExecutionContext
) -> Any:
    """
    Execute custom analysis operation.
    
    Args:
        config: Node configuration (from workflow definition)
        inputs: Outputs from upstream nodes (node_id -> data)
        context: Execution context with metadata and shared state
        
    Returns:
        Data to pass to downstream nodes (any serializable type)
    """
    # Extract configuration
    param1 = config.get("param1", "default")
    
    # Get input data
    input_data = inputs.get("input", [])
    
    # Perform operation
    result = process_data(input_data, param1)
    
    # Return output
    return result
```

**Key Points:**
- Functions are **async** for non-blocking execution
- **Config** comes from workflow JSON definition
- **Inputs** are outputs from nodes connected by edges
- **Return value** becomes available to downstream nodes

### Current Node Types

RoboMage includes several built-in node types:

| Node Type | Handler Function | Purpose |
|-----------|-----------------|---------|
| `load_files` | `load_files_handler` | Load diffraction files from directory |
| `normalize` | `normalize_handler` | Normalize intensity values |
| `filter_q_range` | `filter_q_range_handler` | Trim data to Q-range |
| `peak_analysis` | `peak_analysis_handler` | Detect and fit peaks |
| `statistics` | `statistics_handler` | Calculate statistical metrics |
| `export_csv` | `export_csv_handler` | Export results to CSV |
| `export_json` | `export_json_handler` | Export results to JSON |
| `save_to_session` | `save_to_session_handler` | Save to dashboard session |

---

## Handler Function Interface

### Required Signature

All node handlers **must** implement this signature:

```python
async def handler_name(
    config: dict[str, Any],
    inputs: dict[str, Any],
    context: ExecutionContext
) -> Any:
```

### Parameters

#### 1. Config Dictionary

Contains node-specific configuration from workflow JSON:

```json
{
  "nodes": [
    {
      "id": "analyze_1",
      "type": "peak_analysis",
      "config": {
        "profile_type": "gaussian",
        "prominence": 0.1,
        "distance": 5
      }
    }
  ]
}
```

Access in handler:
```python
profile_type = config.get("profile_type", "gaussian")  # With default
prominence = config["prominence"]  # Required parameter
```

#### 2. Inputs Dictionary

Contains outputs from upstream nodes (connected by edges):

```json
{
  "edges": [
    {"source": "load_1", "target": "analyze_1", "sourceHandle": "output"}
  ]
}
```

Access in handler:
```python
# Get all outputs from connected node
files = inputs.get("input", [])

# Or get specific output by handle
files = inputs.get("files", [])
```

**Convention**: Most nodes use `"input"` as the key for primary data flow.

#### 3. ExecutionContext

Provides execution environment and shared state:

```python
# Store metadata for other nodes
context.metadata["processing_time"] = 42.5

# Retrieve shared metadata
session_id = context.metadata.get("active_session_id")

# Access all node outputs (advanced)
all_outputs = context.get_all_outputs()
```

### Return Value

Handler should return **any serializable data** that downstream nodes need:

```python
# Return list (common for data processing)
return [data1, data2, data3]

# Return dictionary (common for analysis results)
return {
    "peaks": peak_list,
    "statistics": stats,
    "metadata": metadata
}

# Return primitive (simple nodes)
return "success"
```

**Serialization Note**: Return values must be JSON-serializable for inspection. See [Serialization Patterns](#serialization-patterns) for NumPy arrays and complex objects.

---

## Design Patterns

### Input Validation

Always validate inputs at the start of your handler:

```python
async def my_handler(config, inputs, context):
    # Validate required config
    if "required_param" not in config:
        raise ValueError("Missing required parameter: required_param")
    
    # Validate input data
    input_data = inputs.get("input")
    if not input_data:
        raise ValueError("No input data provided")
    
    if not isinstance(input_data, list):
        raise ValueError(f"Expected list input, got {type(input_data)}")
    
    # Type-specific validation
    from robomage.data.models import DiffractionData
    for item in input_data:
        if not isinstance(item, DiffractionData):
            raise ValueError(f"Expected DiffractionData, got {type(item)}")
```

### Configuration with Defaults

Provide sensible defaults for optional parameters:

```python
async def my_handler(config, inputs, context):
    # Required parameter (no default)
    method = config["method"]
    
    # Optional with default
    threshold = config.get("threshold", 0.1)
    
    # Optional with type conversion
    max_iterations = int(config.get("max_iterations", 100))
    
    # Boolean flags
    verbose = config.get("verbose", False)
```

### Logging Best Practices

Use structured logging to aid debugging:

```python
import logging

logger = logging.getLogger(__name__)

async def my_handler(config, inputs, context):
    # Log at start
    logger.info(f"Starting analysis with method={config.get('method')}")
    
    files = inputs.get("input", [])
    logger.info(f"Processing {len(files)} files")
    
    # Log progress
    for i, file in enumerate(files):
        logger.debug(f"Processing file {i+1}/{len(files)}: {file.filename}")
        # ... processing ...
    
    # Log completion
    logger.info(f"Analysis complete: {len(results)} results")
    
    return results
```

**Levels**:
- `DEBUG`: Detailed progress (per-file operations)
- `INFO`: High-level progress (start, completion, counts)
- `WARNING`: Recoverable errors (skipped files)
- `ERROR`: Serious problems (analysis failures)

### Error Handling Strategies

#### Strategy 1: Fail Fast (Strict)

Stop execution on first error:

```python
async def strict_handler(config, inputs, context):
    files = inputs.get("input", [])
    
    results = []
    for file in files:
        # Let exceptions propagate
        result = process_file(file)
        results.append(result)
    
    return results
```

**Use when**: Data quality is critical, partial results are useless.

#### Strategy 2: Best Effort (Lenient)

Process as many files as possible, log failures:

```python
async def lenient_handler(config, inputs, context):
    files = inputs.get("input", [])
    
    results = []
    errors = []
    
    for i, file in enumerate(files):
        try:
            result = process_file(file)
            results.append(result)
        except Exception as e:
            logger.warning(f"Failed to process file {i}: {e}")
            errors.append(f"File {i} ({file.filename}): {str(e)}")
    
    if not results:
        # All files failed - raise with details
        error_msg = "No files processed successfully:\n  " + "\n  ".join(errors)
        raise ValueError(error_msg)
    
    return results
```

**Use when**: Some results are better than none, failures are expected.

#### Strategy 3: Detailed Error Context

Provide actionable error messages:

```python
async def helpful_handler(config, inputs, context):
    # Check for service dependency
    service_url = config.get("service_url", "http://localhost:8001")
    
    try:
        # Attempt operation
        response = await call_service(service_url, data)
    except ConnectionError as e:
        # Provide troubleshooting guidance
        raise ValueError(
            f"Cannot connect to service at {service_url}.\n"
            f"Start the service with:\n"
            f"  pixi run python services/my_service/main.py --port 8001\n\n"
            f"Error: {e}"
        )
```

### Output Formatting

Return structured, consistent data:

```python
async def analysis_handler(config, inputs, context):
    files = inputs.get("input", [])
    
    results = []
    for file in files:
        peaks = detect_peaks(file)
        
        # Structured result dictionary
        result = {
            "filename": file.filename,
            "num_peaks": len(peaks),
            "peak_list": [
                {
                    "position": p.position,
                    "height": p.height,
                    "width": p.width,
                    "area": p.area
                }
                for p in peaks
            ],
            "metadata": {
                "processing_time": time.time() - start,
                "q_range": (file.q_values.min(), file.q_values.max())
            }
        }
        results.append(result)
    
    return results
```

**Benefits**:
- Downstream nodes can easily access specific fields
- Inspector displays clean, structured data
- Results are self-documenting

### Working with DiffractionData

DiffractionData objects are Pydantic models with validation:

```python
from robomage.data.models import DiffractionData

async def process_diffraction_handler(config, inputs, context):
    files = inputs.get("input", [])
    
    processed = []
    for data in files:
        # Access validated fields
        q_values = data.q_values  # numpy array
        intensities = data.intensities  # numpy array
        
        # Perform processing
        new_intensities = intensities / intensities.max()
        
        # Create new DiffractionData with modified intensities
        # Preserves metadata (filename, sample_name)
        processed_data = DiffractionData(
            q_values=data.q_values,
            intensities=new_intensities,
            filename=data.filename,
            sample_name=data.sample_name
        )
        processed.append(processed_data)
    
    return processed
```

**Key Points**:
- DiffractionData is **immutable** - create new instances for modifications
- Metadata (filename, sample_name) should be preserved
- Statistics are computed automatically via Pydantic computed fields

---

## Integration

### Registering Your Node (Plugin System)

**NEW**: RoboMage uses an automatic plugin registration system. Simply add the `@register_node()` decorator to your handler function - no need to modify service code!

#### Quick Start: 3 Steps

1. **Create your node file** in `src/robomage/workflow/nodes/custom/`
2. **Add the decorator** to your handler function
3. **Restart the workflow service** - your node appears in the dashboard!

**✨ Automatic Integration**: Your custom node will:
- ✅ Appear in the dashboard workflow builder palette
- ✅ Be recognized by the workflow validator (no "unknown type" errors)
- ✅ Show up in the `/node-types` API endpoint
- ✅ Generate configuration forms from your JSON schema

**No manual registration needed** - the plugin system discovers your node at service startup.

#### Example: Complete Custom Node

```python
# File: src/robomage/workflow/nodes/custom/my_analysis.py

from robomage.workflow.nodes.registry import register_node
from robomage.orchestrator import ExecutionContext
from robomage.data.models import DiffractionData

@register_node(
    type="my_custom_analysis",           # Unique identifier
    category="custom",                     # Category in palette (data/analysis/transform/output/custom)
    name="My Custom Analysis",            # Display name in UI
    description="Custom diffraction analysis algorithm",  # Tooltip text
    icon="fas fa-star",                   # Font Awesome icon
    inputs=[{"name": "input", "type": "DiffractionData[]"}],
    outputs=[{"name": "output", "type": "AnalysisResults[]"}],
    config_schema={                       # JSON Schema for config form
        "type": "object",
        "properties": {
            "threshold": {
                "type": "number",
                "default": 0.5,
                "minimum": 0,
                "maximum": 1
            },
            "method": {
                "type": "string",
                "enum": ["fast", "accurate"],
                "default": "fast"
            }
        }
    }
)
async def my_custom_handler(config, inputs, context):
    """
    Perform custom analysis on diffraction data.
    
    Config Parameters:
        - threshold: float (detection threshold, 0-1)
        - method: str (analysis method: "fast" or "accurate")
    
    Inputs:
        - input: List[DiffractionData]
    
    Outputs:
        List of analysis result dictionaries
    """
    threshold = config.get("threshold", 0.5)
    method = config.get("method", "fast")
    
    files = inputs.get("input", [])
    if not files:
        raise ValueError("No input files provided")
    
    results = []
    for file in files:
        # Your custom analysis logic here
        result = {"filename": file.filename, "value": 42.0}
        results.append(result)
    
    return results
```

That's it! The node automatically appears in the dashboard's Workflow Builder palette under the "Custom" category.

### Decorator Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `type` | `str` | ✅ Yes | Unique node type identifier (e.g., `"my_node"`) |
| `category` | `str` | ✅ Yes | Palette category: `"data"`, `"analysis"`, `"transform"`, `"output"`, `"custom"` |
| `name` | `str` | ✅ Yes | Display name shown in UI |
| `description` | `str` | ✅ Yes | Brief description (shows as tooltip) |
| `icon` | `str` | No | Font Awesome class (default: `"fas fa-cube"`) |
| `inputs` | `list[dict]` | No | Input specifications |
| `outputs` | `list[dict]` | No | Output specifications |
| `config_schema` | `dict` | No | JSON Schema for configuration form |

### Configuration Schema

The `config_schema` defines the configuration form in the dashboard. Use JSON Schema:

```python
config_schema={
    "type": "object",
    "properties": {
        "my_param": {
            "type": "number",          # number, string, integer, boolean, array
            "default": 0.5,            # Default value
            "minimum": 0,              # Optional: min value (numbers)
            "maximum": 1,              # Optional: max value (numbers)
            "description": "Help text" # Optional: field description
        },
        "method": {
            "type": "string",
            "enum": ["opt1", "opt2"],  # Creates dropdown menu
            "default": "opt1"
        },
        "enabled": {
            "type": "boolean",
            "default": true
        }
    }
}
```

The dashboard automatically generates a form from this schema with:
- Number inputs with min/max validation
- Dropdowns for enum fields
- Checkboxes for booleans
- Text inputs for strings
- Help text from descriptions

### Making Nodes Visible in Workflow Builder

Nodes with the `@register_node()` decorator are **automatically discovered** when the workflow service starts. The visual workflow builder fetches the node list from the service's `/node-types` endpoint.

To make your node user-friendly:

1. **Use descriptive names**: `"Chebyshev Background"` not `"CB"`
2. **Provide helpful descriptions**: Tell users what the node does
3. **Choose appropriate icons**: See [Font Awesome](https://fontawesome.com/icons) for available icons
4. **Document config parameters**: Add clear descriptions in the schema
5. **Use appropriate category**: Helps users find your node quickly

### File Organization

```
src/robomage/workflow/nodes/
├── __init__.py                   # Built-in nodes module
├── registry.py                   # Plugin registration system
├── data_nodes.py                 # Built-in data nodes
├── analysis_nodes.py             # Built-in analysis nodes
├── output_nodes.py               # Built-in output nodes
└── custom/                       # 👈 Put your custom nodes here
    ├── __init__.py
    ├── README.md                 # Plugin system documentation
    ├── my_analysis.py            # Your custom node
    ├── background_fitting.py     # Another custom node
    └── ...
```

**Important**: Custom nodes go in the `custom/` directory. They are auto-discovered on service startup.

### Legacy Registration (Not Recommended)

For backward compatibility or special cases, you can still manually register nodes:

```python
from robomage.workflow.nodes.registry import register_node_handler

register_node_handler(
    type="my_node",
    handler=my_handler_function,
    category="custom",
    name="My Node",
    description="Does something",
    # ... other parameters
)
```

But the decorator approach is **strongly recommended** for simplicity and maintainability.

### Inspection Integration

Node I/O inspection is **automatic** when the orchestrator has `enable_inspection=True`:

```python
# Inspection captures inputs and outputs automatically
orchestrator = WorkflowOrchestrator(enable_inspection=True)
```

No additional code needed in your handler - the orchestrator handles serialization and storage.

---

## Testing Guidelines

### Unit Testing Pattern

Test node handlers in isolation with mock data:

```python
import pytest
from robomage.orchestrator import ExecutionContext
from my_nodes import my_handler

@pytest.mark.asyncio
async def test_my_handler_basic():
    """Test basic functionality."""
    # Arrange
    config = {"param": "value"}
    inputs = {"input": [mock_data]}
    context = ExecutionContext()
    
    # Act
    result = await my_handler(config, inputs, context)
    
    # Assert
    assert len(result) == 1
    assert result[0]["status"] == "success"

@pytest.mark.asyncio
async def test_my_handler_validation():
    """Test input validation."""
    config = {}
    inputs = {}
    context = ExecutionContext()
    
    # Should raise ValueError for missing input
    with pytest.raises(ValueError, match="No input data"):
        await my_handler(config, inputs, context)

@pytest.mark.asyncio
async def test_my_handler_config_defaults():
    """Test configuration defaults."""
    config = {}  # No parameters
    inputs = {"input": [mock_data]}
    context = ExecutionContext()
    
    result = await my_handler(config, inputs, context)
    
    # Should use default values
    assert result[0]["threshold"] == 0.1  # Default
```

### Integration Testing

Test nodes in workflow context:

```python
@pytest.mark.asyncio
async def test_full_workflow():
    """Test complete workflow with custom node."""
    from robomage.orchestrator import WorkflowOrchestrator
    
    # Register nodes
    orch = WorkflowOrchestrator()
    orch.register_node_handler("load_files", load_files_handler)
    orch.register_node_handler("my_node", my_handler)
    
    # Define workflow
    workflow = {
        "nodes": [
            {"id": "load_1", "type": "load_files", "config": {"directory": "test_data/"}},
            {"id": "process_1", "type": "my_node", "config": {"param": "value"}}
        ],
        "edges": [
            {"source": "load_1", "target": "process_1"}
        ]
    }
    
    # Execute
    result = await orch.execute_workflow(workflow)
    
    # Verify
    assert result.status == "completed"
    assert "process_1" in result.node_outputs
```

### Mock Data Strategies

#### Strategy 1: Use Built-in Test Data

```python
import robomage

def get_test_data():
    """Load standard reference material."""
    return robomage.load_test_data()  # SRM 660b
```

#### Strategy 2: Create Minimal Mock Data

```python
import numpy as np
from robomage.data.models import DiffractionData

def create_mock_diffraction():
    """Create minimal valid DiffractionData."""
    return DiffractionData(
        q_values=np.linspace(1.0, 10.0, 100),
        intensities=np.random.rand(100) * 1000,
        filename="mock_data.chi",
        sample_name="Test Sample"
    )
```

#### Strategy 3: Fixture-based Mocks

```python
@pytest.fixture
def sample_diffraction_data():
    """Reusable test data fixture."""
    q = np.linspace(2.0, 8.0, 200)
    # Create synthetic peaks
    intensity = (
        1000 * np.exp(-((q - 3.5) ** 2) / 0.1) +  # Peak 1
        800 * np.exp(-((q - 5.2) ** 2) / 0.1) +   # Peak 2
        np.random.rand(200) * 50  # Noise
    )
    
    return DiffractionData(
        q_values=q,
        intensities=intensity,
        filename="synthetic.chi",
        sample_name="Synthetic"
    )

@pytest.mark.asyncio
async def test_with_fixture(sample_diffraction_data):
    """Test using fixture data."""
    result = await my_handler(
        config={},
        inputs={"input": [sample_diffraction_data]},
        context=ExecutionContext()
    )
    assert len(result) > 0
```

### Test Coverage Goals

Aim to test:
- ✅ **Happy path**: Valid inputs produce expected outputs
- ✅ **Validation**: Invalid inputs raise appropriate errors
- ✅ **Edge cases**: Empty data, single point, extreme values
- ✅ **Defaults**: Configuration parameters use correct defaults
- ✅ **Error handling**: Failures are logged/handled gracefully
- ✅ **Integration**: Node works in workflow context

---

## Common Pitfalls

### 1. NumPy Array Serialization

**Problem**: NumPy arrays aren't JSON-serializable, breaking inspection.

```python
# ❌ WRONG - Returns NumPy array directly
async def bad_handler(config, inputs, context):
    data = inputs.get("input")[0]
    return data.intensities  # numpy.ndarray - not serializable!
```

**Solution**: Convert to lists or use structured dictionaries:

```python
# ✅ CORRECT - Convert arrays to lists
async def good_handler(config, inputs, context):
    data = inputs.get("input")[0]
    return {
        "intensities": data.intensities.tolist(),
        "q_values": data.q_values.tolist()
    }
```

**Better**: Return DiffractionData objects (have built-in serialization):

```python
# ✅ BEST - Return Pydantic models
async def best_handler(config, inputs, context):
    files = inputs.get("input", [])
    # Process and return DiffractionData objects
    return processed_files  # DiffractionData.model_dump() handles serialization
```

### 2. File Path Handling

**Problem**: Relative paths break when workflow runs from different directories.

```python
# ❌ WRONG - Relative path
config = {"data_dir": "../data/"}
```

**Solution**: Use absolute paths:

```python
# ✅ CORRECT
from pathlib import Path

async def handler(config, inputs, context):
    data_dir = Path(config["data_dir"]).resolve()  # Convert to absolute
    if not data_dir.exists():
        raise ValueError(f"Directory not found: {data_dir}")
```

### 3. State Management

**Problem**: Node handlers should be **stateless** - no shared state between executions.

```python
# ❌ WRONG - Module-level state
_cached_results = {}

async def stateful_handler(config, inputs, context):
    # Don't use module-level cache
    if "cache_key" in _cached_results:
        return _cached_results["cache_key"]
```

**Solution**: Use ExecutionContext for within-workflow state:

```python
# ✅ CORRECT
async def stateless_handler(config, inputs, context):
    # Store in context (scoped to this workflow execution)
    if "cache_key" in context.metadata:
        return context.metadata["cache_key"]
    
    result = expensive_computation()
    context.metadata["cache_key"] = result
    return result
```

### 4. Async/Await Confusion

**Problem**: Calling async functions without `await`.

```python
# ❌ WRONG
async def handler(config, inputs, context):
    result = async_operation()  # Returns coroutine, doesn't execute!
    return result
```

**Solution**: Always `await` async calls:

```python
# ✅ CORRECT
async def handler(config, inputs, context):
    result = await async_operation()
    return result
```

**Note**: If calling sync functions, just call them normally (no `await`).

### 5. Missing Error Context

**Problem**: Generic errors without guidance.

```python
# ❌ WRONG
async def handler(config, inputs, context):
    if not service_available():
        raise ValueError("Service unavailable")
```

**Solution**: Provide actionable error messages:

```python
# ✅ CORRECT
async def handler(config, inputs, context):
    service_url = config.get("service_url", "http://localhost:8001")
    
    if not service_available(service_url):
        raise ValueError(
            f"Cannot connect to service at {service_url}.\n"
            f"Troubleshooting:\n"
            f"  1. Start service: pixi run start-service\n"
            f"  2. Check URL: {service_url}\n"
            f"  3. View logs: tail -f service.log"
        )
```

### 6. Forgetting to Handle Empty Inputs

**Problem**: Assuming inputs are always present.

```python
# ❌ WRONG
async def handler(config, inputs, context):
    files = inputs["input"]  # KeyError if no input!
    return process(files)
```

**Solution**: Always check for empty/missing inputs:

```python
# ✅ CORRECT
async def handler(config, inputs, context):
    files = inputs.get("input", [])
    
    if not files:
        raise ValueError("No input data provided")
    
    return process(files)
```

### 7. Ignoring Logging

**Problem**: Silent failures with no debugging information.

```python
# ❌ WRONG
async def handler(config, inputs, context):
    for file in files:
        try:
            process(file)
        except:
            pass  # Silent failure!
```

**Solution**: Always log errors:

```python
# ✅ CORRECT
import logging
logger = logging.getLogger(__name__)

async def handler(config, inputs, context):
    for i, file in enumerate(files):
        try:
            process(file)
        except Exception as e:
            logger.error(f"Failed to process file {i}: {e}")
            # Decide: continue or raise
```

---

## Advanced Topics

### Optional Dependencies

If your node requires optional libraries:

```python
async def advanced_handler(config, inputs, context):
    """
    Perform advanced analysis using scipy.
    
    Requires: scipy>=1.11.0 (install with: pixi add scipy)
    """
    try:
        from scipy import optimize, signal
    except ImportError:
        raise ImportError(
            "This node requires scipy. Install with:\n"
            "  pixi add scipy\n"
            "or add to pyproject.toml dependencies"
        )
    
    # Use scipy functions
    result = signal.find_peaks(data)
    return result
```

### Progress Reporting

For long-running operations, log progress:

```python
async def long_running_handler(config, inputs, context):
    files = inputs.get("input", [])
    total = len(files)
    
    results = []
    for i, file in enumerate(files):
        logger.info(f"Processing {i+1}/{total}: {file.filename}")
        result = expensive_operation(file)
        results.append(result)
    
    return results
```

**Note**: RoboMage orchestrator doesn't currently support real-time progress callbacks, but logging provides visibility in service logs.

### External Service Integration

Pattern for calling external services:

```python
async def service_client_handler(config, inputs, context):
    """Integrate with external service."""
    import httpx
    
    service_url = config.get("service_url", "http://localhost:8001")
    timeout = config.get("timeout", 30.0)
    
    files = inputs.get("input", [])
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        results = []
        for file in files:
            try:
                # Serialize data
                payload = {
                    "q_values": file.q_values.tolist(),
                    "intensities": file.intensities.tolist(),
                    "config": config
                }
                
                # Call service
                response = await client.post(
                    f"{service_url}/analyze",
                    json=payload
                )
                response.raise_for_status()
                
                results.append(response.json())
                
            except httpx.HTTPError as e:
                logger.error(f"Service request failed: {e}")
                raise ValueError(f"Service error: {e}")
        
        return results
```

### Handling Large Datasets

For very large arrays, consider truncation for inspection:

```python
async def large_data_handler(config, inputs, context):
    """Process large datasets efficiently."""
    files = inputs.get("input", [])
    
    results = []
    for file in files:
        # Process full data
        processed = expensive_computation(file.intensities)
        
        # Return truncated for inspection
        result = {
            "filename": file.filename,
            "summary_stats": {
                "mean": float(processed.mean()),
                "std": float(processed.std()),
                "min": float(processed.min()),
                "max": float(processed.max())
            },
            # Only include first/last 100 points for inspection
            "data_sample": {
                "first_100": processed[:100].tolist(),
                "last_100": processed[-100:].tolist()
            }
        }
        results.append(result)
    
    return results
```

---

## Quick Reference

See [Node Quick Reference](node-quick-reference.md) for copy-paste templates.

---

## Examples

See the `examples/custom_nodes/` directory for working examples:
- **template_node.py** - Minimal "Hello World" example
- **background_subtraction_node.py** - Real data processing
- **peak_width_analysis_node.py** - Advanced scientific analysis

---

## Additional Resources

- **Existing Nodes**: `src/robomage/workflow/nodes/` - Production reference implementations
- **Orchestrator**: `src/robomage/orchestrator.py` - Execution engine
- **Data Models**: `src/robomage/data/models.py` - DiffractionData and validation
- **Visual Builder Guide**: `docs/visual-workflow-builder-guide.md` - UI integration

---

**Questions?** Open an issue or discussion on the RoboMage GitHub repository.
