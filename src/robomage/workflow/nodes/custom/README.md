# Custom Workflow Nodes

**Add your custom analysis nodes here - they'll automatically appear in the dashboard!**

## Quick Start

1. **Create your node file** in this directory (e.g., `my_analysis.py`)
2. **Use the decorator** to register your handler function
3. **Restart the workflow service** and your node appears in the palette

That's it! No need to modify `main.py` or any service code.

**✨ Automatic Integration**: Your custom node will:
- ✅ Appear in the dashboard workflow builder palette
- ✅ Be recognized by the workflow validator (no "unknown type" errors)
- ✅ Show up in the `/node-types` API endpoint
- ✅ Generate configuration forms from your JSON schema

---

## Simple Example

Create `my_simple_node.py`:

```python
from robomage.workflow.nodes.registry import register_node
from robomage.orchestrator import ExecutionContext
from robomage.data.models import DiffractionData

@register_node(
    type="my_simple_node",
    category="custom",
    name="My Simple Node",
    description="Example custom analysis",
    icon="fas fa-star"
)
async def my_simple_handler(config, inputs, context):
    """Do something with diffraction data."""
    files = inputs.get("input", [])
    
    # Your custom logic here
    results = []
    for file in files:
        result = {"filename": file.filename, "status": "processed"}
        results.append(result)
    
    return results
```

Save the file, restart the workflow service, and "My Simple Node" will appear in the dashboard under the "Custom" category!

---

## Complete Example with Configuration

Create `advanced_analysis.py`:

```python
import logging
from typing import Any

from robomage.workflow.nodes.registry import register_node
from robomage.orchestrator import ExecutionContext
from robomage.data.models import DiffractionData

logger = logging.getLogger(__name__)


@register_node(
    type="advanced_analysis",
    category="custom",
    name="Advanced Analysis",
    description="Advanced diffraction analysis with configurable parameters",
    icon="fas fa-brain",
    inputs=[{"name": "input", "type": "DiffractionData[]"}],
    outputs=[{"name": "output", "type": "AnalysisResults[]"}],
    config_schema={
        "type": "object",
        "properties": {
            "method": {
                "type": "string",
                "enum": ["method_a", "method_b", "method_c"],
                "default": "method_a",
            },
            "threshold": {
                "type": "number",
                "default": 0.5,
                "minimum": 0,
                "maximum": 1,
            },
            "iterations": {
                "type": "integer",
                "default": 100,
                "minimum": 1,
            },
        },
    },
)
async def advanced_analysis_handler(
    config: dict[str, Any],
    inputs: dict[str, Any],
    context: ExecutionContext,
) -> list[dict[str, Any]]:
    """
    Perform advanced analysis on diffraction data.
    
    Config Parameters:
        - method: str (analysis method: "method_a", "method_b", "method_c")
        - threshold: float (threshold value, default: 0.5)
        - iterations: int (number of iterations, default: 100)
    
    Inputs:
        - input: List[DiffractionData] (diffraction patterns)
    
    Outputs:
        List of analysis result dictionaries
    """
    # Extract configuration
    method = config.get("method", "method_a")
    threshold = config.get("threshold", 0.5)
    iterations = config.get("iterations", 100)
    
    logger.info(f"Advanced analysis: method={method}, threshold={threshold}")
    
    # Get input data
    files = inputs.get("input", [])
    if not files:
        raise ValueError("No input files provided")
    
    # Process each file
    results = []
    for file in files:
        # Your custom analysis logic here
        result = {
            "filename": file.filename,
            "method": method,
            "threshold": threshold,
            "iterations": iterations,
            "value": perform_analysis(file, method, threshold, iterations),
        }
        results.append(result)
    
    logger.info(f"Completed analysis: {len(results)} results")
    
    return results


def perform_analysis(file, method, threshold, iterations):
    """Your custom analysis implementation."""
    # Placeholder - implement your algorithm here
    return 42.0
```

---

## Registry Decorator Reference

### `@register_node()` Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `type` | `str` | ✅ Yes | Unique identifier (e.g., `"my_node"`) |
| `category` | `str` | ✅ Yes | Category: `"data"`, `"analysis"`, `"transform"`, `"output"`, `"custom"` |
| `name` | `str` | ✅ Yes | Display name shown in UI palette |
| `description` | `str` | ✅ Yes | Brief description for users |
| `icon` | `str` | No | Font Awesome icon class (default: `"fas fa-cube"`) |
| `inputs` | `list[dict]` | No | Input specifications (see below) |
| `outputs` | `list[dict]` | No | Output specifications (see below) |
| `config_schema` | `dict` | No | JSON Schema for configuration panel |

### Input/Output Specifications

```python
inputs=[
    {"name": "input", "type": "DiffractionData[]"},
    {"name": "secondary", "type": "AnalysisResults[]"}
]

outputs=[
    {"name": "output", "type": "ProcessedData[]"}
]
```

### Configuration Schema

Use JSON Schema to define configuration parameters. The dashboard will automatically generate a configuration form:

```python
config_schema={
    "type": "object",
    "properties": {
        "param_name": {
            "type": "number",       # number, string, integer, boolean, array
            "default": 0.5,         # Default value
            "minimum": 0,           # Optional: min value (for numbers)
            "maximum": 1,           # Optional: max value (for numbers)
        },
        "method": {
            "type": "string",
            "enum": ["opt1", "opt2"],  # Dropdown menu
            "default": "opt1"
        },
        "enabled": {
            "type": "boolean",
            "default": true
        }
    }
}
```

---

## Handler Function Requirements

Your handler function **must**:

1. Be an `async` function
2. Accept three parameters: `config`, `inputs`, `context`
3. Return JSON-serializable data (or `DiffractionData` objects)

```python
async def my_handler(
    config: dict[str, Any],      # Node configuration from workflow
    inputs: dict[str, Any],       # Outputs from upstream nodes
    context: ExecutionContext     # Execution context and metadata
) -> Any:                         # Return data for downstream nodes
    """Your implementation here."""
    pass
```

---

## File Organization

```
src/robomage/workflow/nodes/custom/
├── __init__.py                    # Auto-loaded by registry
├── README.md                      # This file
├── my_analysis.py                 # Your custom node
├── background_subtraction.py      # Another custom node
└── experimental_fitting.py        # More custom nodes
```

Each `.py` file can contain one or multiple node handlers. All will be auto-discovered.

---

## Best Practices

### ✅ Do:
- Use descriptive `type` identifiers: `"chebyshev_background"` not `"cb"`
- Provide helpful `description` text for users
- Use appropriate `category` for organization
- Validate inputs at the start of your handler
- Use logging for progress and debugging
- Return structured, consistent data
- Document your config parameters in docstrings

### ❌ Don't:
- Use `type` names that conflict with built-in nodes
- Return NumPy arrays directly (convert to lists or use DiffractionData)
- Modify global state (keep handlers stateless)
- Forget to handle empty inputs
- Skip error handling

---

## Testing Your Node

### Method 1: Via Dashboard (Recommended)
1. Start workflow service: `pixi run python services/workflow_engine/main.py --port 8002`
2. Start dashboard: `pixi run python -m robomage --dashboard`
3. Go to Workflow Builder tab
4. Your node appears in the palette under its category
5. Drag it onto the canvas and configure it

### Method 2: Direct Python Testing

```python
import asyncio
from robomage.orchestrator import ExecutionContext
from my_analysis import my_handler

async def test_my_node():
    config = {"param": "value"}
    inputs = {"input": [test_data]}
    context = ExecutionContext()
    
    result = await my_handler(config, inputs, context)
    print(result)

asyncio.run(test_my_node())
```

### Method 3: Unit Tests

```python
import pytest
from robomage.orchestrator import ExecutionContext
from my_analysis import my_handler

@pytest.mark.asyncio
async def test_my_node_basic():
    """Test basic functionality."""
    config = {}
    inputs = {"input": [mock_data]}
    context = ExecutionContext()
    
    result = await my_handler(config, inputs, context)
    
    assert len(result) == 1
    assert "status" in result[0]
```

---

## Troubleshooting

### Node doesn't appear in dashboard palette

1. **Check the logs** when starting workflow service - look for "Registered node: your_node_type"
2. **Verify syntax** - Python errors prevent module import
3. **Restart service** - Changes require restart to take effect
4. **Check decorator** - Ensure `@register_node()` is above your handler

### "Unknown type" validation error in dashboard

**This should NOT happen with properly registered nodes!** If you see this:

1. **Verify node is registered** - Check workflow service logs for "✅ Registered X node types"
2. **Restart dashboard** - Dashboard fetches node types from service at startup
3. **Check both services running** - Dashboard needs workflow service (port 8002) running
4. **Clear browser cache** - Force refresh dashboard (Ctrl+Shift+R)

The plugin system automatically updates the validator with your custom node types.

### Configuration form not showing

1. **Verify config_schema** - Must be valid JSON Schema
2. **Check type field** - Use "object" as the top-level type
3. **Provide defaults** - Each property should have a default value

### Node execution fails

1. **Check input validation** - Ensure you handle empty/missing inputs
2. **Review logs** - Look for error messages in workflow service logs
3. **Test independently** - Use Method 2 testing approach above
4. **Verify return type** - Must be JSON-serializable or DiffractionData

---

## Examples in This Repository

See `examples/custom_nodes/` for reference implementations:
- `template_node.py` - Minimal "Hello World" example
- `background_subtraction_node.py` - Real data processing with configuration
- `peak_width_analysis_node.py` - Advanced scientific analysis

These are examples that live outside the service for reference. Copy them here and add the `@register_node()` decorator to make them active.

---

## Advanced Topics

### Using External Services

```python
@register_node(...)
async def service_client_handler(config, inputs, context):
    """Call external analysis service."""
    import httpx
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            config["service_url"],
            json={"data": inputs["input"]}
        )
        return response.json()
```

### Accessing Session Data

```python
@register_node(...)
async def session_aware_handler(config, inputs, context):
    """Access session metadata."""
    session_id = context.metadata.get("active_session_id")
    
    # Store data in context for other nodes
    context.metadata["my_result"] = result
    
    return result
```

### Progress Reporting

```python
@register_node(...)
async def long_running_handler(config, inputs, context):
    """Report progress via logging."""
    import logging
    logger = logging.getLogger(__name__)
    
    files = inputs["input"]
    for i, file in enumerate(files):
        logger.info(f"Processing {i+1}/{len(files)}: {file.filename}")
        # Process file...
    
    return results
```

---

## Questions or Issues?

- See `docs/node-development-guide.md` for comprehensive documentation
- Check `docs/node-quick-reference.md` for code templates
- Open an issue on GitHub for bugs or feature requests

**Happy node development! 🚀**
