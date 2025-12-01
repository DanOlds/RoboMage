# Node Development Quick Reference

**Copy-paste templates and common patterns for rapid node development.**

---

## Basic Handler Template

```python
import logging
from typing import Any

from robomage.orchestrator import ExecutionContext

logger = logging.getLogger(__name__)


async def my_node_handler(
    config: dict[str, Any],
    inputs: dict[str, Any],
    context: ExecutionContext
) -> Any:
    """
    [Brief description of what this node does]
    
    Config Parameters:
        - param1: str (description, required)
        - param2: float (description, default: 0.1)
        - param3: bool (description, default: False)
    
    Inputs:
        - input: [Type] (description of expected input)
    
    Outputs:
        [Type and description of output]
    
    Example:
        config = {
            "param1": "value",
            "param2": 0.5
        }
    """
    # Extract configuration
    param1 = config["param1"]  # Required
    param2 = config.get("param2", 0.1)  # Optional with default
    param3 = config.get("param3", False)  # Boolean flag
    
    logger.info(f"Starting [operation] with param1={param1}")
    
    # Validate inputs
    input_data = inputs.get("input", [])
    if not input_data:
        raise ValueError("No input data provided")
    
    # Process data
    results = []
    for i, item in enumerate(input_data):
        try:
            # TODO: Implement your logic here
            result = process_item(item, param1, param2)
            results.append(result)
            logger.debug(f"Processed item {i+1}/{len(input_data)}")
            
        except Exception as e:
            logger.warning(f"Failed to process item {i+1}: {e}")
            # Decide: continue or raise
    
    if not results:
        raise ValueError("No items processed successfully")
    
    logger.info(f"Completed [operation]: {len(results)} results")
    
    return results
```

---

## Common Imports Checklist

```python
# Standard library
import logging
from pathlib import Path
from typing import Any

# RoboMage core
from robomage.orchestrator import ExecutionContext
from robomage.data.models import DiffractionData

# Optional: For scientific computing
import numpy as np

# Optional: For external service calls
import httpx  # or: from robomage.clients.peak_analysis_client import PeakAnalysisClient

# Optional: For analysis
from scipy import signal, optimize

logger = logging.getLogger(__name__)
```

---

## Common Patterns

### Pattern 1: Data Transformation Node

Process DiffractionData objects and return modified versions:

```python
async def transform_handler(config, inputs, context):
    """Transform diffraction data."""
    method = config.get("method", "default")
    
    files = inputs.get("input", [])
    if not files:
        raise ValueError("No input files provided")
    
    transformed = []
    for file in files:
        # Create new DiffractionData with modified values
        new_data = DiffractionData(
            q_values=file.q_values,
            intensities=transform_intensities(file.intensities, method),
            filename=file.filename,
            sample_name=file.sample_name
        )
        transformed.append(new_data)
    
    return transformed
```

### Pattern 2: Analysis Node

Analyze data and return structured results:

```python
async def analysis_handler(config, inputs, context):
    """Analyze diffraction data."""
    threshold = config.get("threshold", 0.1)
    
    files = inputs.get("input", [])
    if not files:
        raise ValueError("No input files provided")
    
    results = []
    for file in files:
        # Perform analysis
        features = detect_features(file, threshold)
        
        # Return structured result
        result = {
            "filename": file.filename,
            "num_features": len(features),
            "feature_list": [
                {
                    "position": f.position,
                    "intensity": f.intensity,
                    "quality": f.quality
                }
                for f in features
            ],
            "metadata": {
                "threshold_used": threshold,
                "q_range": [file.q_values.min(), file.q_values.max()]
            }
        }
        results.append(result)
    
    return results
```

### Pattern 3: Export Node

Save results to files:

```python
async def export_handler(config, inputs, context):
    """Export results to file."""
    import csv
    
    output_path = config["output_path"]
    
    results = inputs.get("input", [])
    if not results:
        raise ValueError("No input data to export")
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Write CSV
    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["filename", "value1", "value2"])
        
        for result in results:
            writer.writerow([
                result["filename"],
                result["value1"],
                result["value2"]
            ])
    
    logger.info(f"Exported {len(results)} results to {output_file}")
    
    return {
        "output_file": str(output_file),
        "records_exported": len(results)
    }
```

### Pattern 4: Service Client Node

Call external microservice:

```python
async def service_client_handler(config, inputs, context):
    """Call external analysis service."""
    import httpx
    
    service_url = config.get("service_url", "http://localhost:8001")
    
    files = inputs.get("input", [])
    if not files:
        raise ValueError("No input files provided")
    
    results = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        for file in files:
            try:
                # Prepare request
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
                logger.error(f"Service call failed for {file.filename}: {e}")
                raise ValueError(
                    f"Cannot connect to service at {service_url}.\n"
                    f"Start service with: pixi run start-service"
                )
    
    return results
```

---

## Configuration Patterns

### Simple Config with Defaults

```python
# Required parameter (no default)
method = config["method"]

# Optional with default value
threshold = config.get("threshold", 0.1)

# Optional with type conversion
max_iterations = int(config.get("max_iterations", 100))

# Boolean flags
verbose = config.get("verbose", False)
use_cache = config.get("use_cache", True)

# List parameters
methods = config.get("methods", ["method1", "method2"])

# Nested configuration
detection_config = config.get("detection", {})
min_prominence = detection_config.get("min_prominence", 0.1)
```

### Validating Configuration

```python
# Check required parameters
required_params = ["method", "threshold"]
missing = [p for p in required_params if p not in config]
if missing:
    raise ValueError(f"Missing required parameters: {', '.join(missing)}")

# Validate parameter values
method = config["method"]
if method not in ["gaussian", "lorentzian", "voigt"]:
    raise ValueError(f"Invalid method: {method}. Must be one of: gaussian, lorentzian, voigt")

# Validate ranges
threshold = config.get("threshold", 0.1)
if not (0.0 <= threshold <= 1.0):
    raise ValueError(f"Threshold must be between 0 and 1, got {threshold}")
```

---

## Input Validation Patterns

### Check for Empty/Missing Input

```python
input_data = inputs.get("input")
if input_data is None:
    raise ValueError("No input data provided")

if not input_data:  # Empty list/dict
    raise ValueError("Input data is empty")
```

### Validate Input Types

```python
from robomage.data.models import DiffractionData

files = inputs.get("input", [])

# Check type
if not isinstance(files, list):
    raise ValueError(f"Expected list input, got {type(files).__name__}")

# Validate each item
for i, file in enumerate(files):
    if not isinstance(file, DiffractionData):
        raise ValueError(f"Item {i} is not DiffractionData, got {type(file).__name__}")
```

### Handle Multiple Input Types

```python
# Accept either list of files or single file
input_data = inputs.get("input")

if isinstance(input_data, list):
    files = input_data
elif isinstance(input_data, DiffractionData):
    files = [input_data]  # Wrap in list
else:
    raise ValueError(f"Expected DiffractionData or list, got {type(input_data)}")
```

---

## Error Handling Patterns

### Lenient (Best Effort)

```python
results = []
errors = []

for i, item in enumerate(items):
    try:
        result = process(item)
        results.append(result)
    except Exception as e:
        logger.warning(f"Failed to process item {i}: {e}")
        errors.append(f"Item {i}: {str(e)}")

if not results:
    error_msg = "No items processed successfully:\n  " + "\n  ".join(errors)
    raise ValueError(error_msg)

return results
```

### Strict (Fail Fast)

```python
results = []

for item in items:
    # Let exceptions propagate
    result = process(item)
    results.append(result)

return results
```

### With Helpful Error Messages

```python
try:
    result = risky_operation()
except ConnectionError as e:
    raise ValueError(
        f"Cannot connect to service.\n"
        f"Troubleshooting:\n"
        f"  1. Start service: pixi run start-service\n"
        f"  2. Check URL: {service_url}\n"
        f"  3. View logs: tail -f service.log\n"
        f"Error: {e}"
    )
```

---

## Output Formatting

### Structured Dictionary

```python
return {
    "filename": file.filename,
    "results": [
        {"position": 3.5, "height": 1000, "width": 0.2},
        {"position": 5.2, "height": 800, "width": 0.15}
    ],
    "metadata": {
        "num_results": 2,
        "processing_time": 0.42,
        "algorithm": "gaussian_fit"
    }
}
```

### List of Dictionaries

```python
return [
    {
        "filename": "file1.chi",
        "value": 123.45
    },
    {
        "filename": "file2.chi",
        "value": 678.90
    }
]
```

### DiffractionData Objects

```python
from robomage.data.models import DiffractionData

processed_files = []
for file in files:
    new_data = DiffractionData(
        q_values=file.q_values,
        intensities=processed_intensities,
        filename=file.filename,
        sample_name=file.sample_name
    )
    processed_files.append(new_data)

return processed_files
```

---

## Serialization Helpers

### NumPy to JSON

```python
import numpy as np

# Convert arrays to lists
data = {
    "q_values": q_array.tolist(),
    "intensities": intensity_array.tolist()
}

# Convert scalars
data = {
    "mean": float(np.mean(array)),
    "std": float(np.std(array))
}
```

### DiffractionData Serialization

```python
# DiffractionData objects auto-serialize via Pydantic
files = [data1, data2, data3]
return files  # Works automatically

# Or explicitly
return [file.model_dump() for file in files]
```

---

## Testing Template

```python
import pytest
import numpy as np
from robomage.orchestrator import ExecutionContext
from robomage.data.models import DiffractionData
from my_nodes import my_handler


@pytest.fixture
def sample_diffraction():
    """Create sample DiffractionData for testing."""
    return DiffractionData(
        q_values=np.linspace(2.0, 8.0, 100),
        intensities=np.random.rand(100) * 1000,
        filename="test.chi",
        sample_name="Test Sample"
    )


@pytest.mark.asyncio
async def test_basic_functionality(sample_diffraction):
    """Test basic node functionality."""
    config = {"param": "value"}
    inputs = {"input": [sample_diffraction]}
    context = ExecutionContext()
    
    result = await my_handler(config, inputs, context)
    
    assert len(result) == 1
    assert "filename" in result[0]


@pytest.mark.asyncio
async def test_missing_input():
    """Test error handling for missing input."""
    config = {}
    inputs = {}
    context = ExecutionContext()
    
    with pytest.raises(ValueError, match="No input data"):
        await my_handler(config, inputs, context)


@pytest.mark.asyncio
async def test_config_defaults(sample_diffraction):
    """Test configuration defaults."""
    config = {}  # No params
    inputs = {"input": [sample_diffraction]}
    context = ExecutionContext()
    
    result = await my_handler(config, inputs, context)
    
    # Should use defaults
    assert result is not None
```

---

## Registration Code

### In Workflow Service

```python
# services/workflow_engine/main.py

from robomage.orchestrator import WorkflowOrchestrator
from robomage.workflow.nodes.data_nodes import load_files_handler
from robomage.workflow.nodes.analysis_nodes import peak_analysis_handler
from my_custom_nodes import my_new_handler

# Create orchestrator
orchestrator = WorkflowOrchestrator()

# Register handlers
orchestrator.register_node_handler("load_files", load_files_handler)
orchestrator.register_node_handler("peak_analysis", peak_analysis_handler)
orchestrator.register_node_handler("my_new_node", my_new_handler)
```

### In Custom Script

```python
# custom_workflow.py

import asyncio
from robomage.orchestrator import WorkflowOrchestrator
from my_nodes import my_handler

async def main():
    orch = WorkflowOrchestrator()
    orch.register_node_handler("my_node", my_handler)
    
    workflow = {
        "nodes": [
            {"id": "node1", "type": "my_node", "config": {"param": "value"}}
        ],
        "edges": []
    }
    
    result = await orch.execute_workflow(workflow)
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Workflow JSON Examples

### Simple Linear Workflow

```json
{
  "nodes": [
    {
      "id": "load_1",
      "type": "load_files",
      "config": {
        "directory": "data/",
        "pattern": "*.chi"
      }
    },
    {
      "id": "process_1",
      "type": "my_node",
      "config": {
        "param": "value"
      }
    }
  ],
  "edges": [
    {
      "source": "load_1",
      "target": "process_1"
    }
  ]
}
```

### Parallel Branches

```json
{
  "nodes": [
    {"id": "load_1", "type": "load_files", "config": {...}},
    {"id": "analyze_1", "type": "peak_analysis", "config": {...}},
    {"id": "stats_1", "type": "statistics", "config": {...}},
    {"id": "export_1", "type": "export_csv", "config": {...}}
  ],
  "edges": [
    {"source": "load_1", "target": "analyze_1"},
    {"source": "load_1", "target": "stats_1"},
    {"source": "analyze_1", "target": "export_1"}
  ]
}
```

---

## See Also

- **[Node Development Guide](node-development-guide.md)** - Complete documentation
- **[Examples](../examples/custom_nodes/)** - Working example nodes
- **[Existing Nodes](../src/robomage/workflow/nodes/)** - Production reference code

---

**Quick Start**: Copy the basic handler template, implement your logic in the `# TODO` section, test with the testing template, and register your node. That's it!
