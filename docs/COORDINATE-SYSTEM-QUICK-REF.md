# Coordinate System Metadata Contract - Quick Reference

## Overview
RoboMage now has a formal coordinate system contract that:
- ✅ Uses Q-space (Å⁻¹) as canonical internal format
- ✅ Automatically converts data when nodes require different coordinate systems
- ✅ Tracks all conversions with complete metadata and history
- ✅ Prevents field naming confusion (like the GSAS-II "two_theta" issue)

## For Node Developers

### Declaring Coordinate Requirements

```python
from robomage.workflow.nodes.registry import register_node

@register_node(
    type="my_analysis",
    category="analysis",
    name="My Analysis",
    description="Does analysis in 2θ space",
    coordinate_requirements={
        "input_coordinates": "two_theta",  # or "Q", "d_spacing", None (any)
        "output_coordinates": "two_theta",  # or None (same as input)
        "requires_wavelength": True  # or False
    }
)
async def my_analysis_handler(config, inputs, context):
    # Data will be automatically converted to 2θ before this runs!
    files = inputs.get("input", [])
    for data in files:
        # data.coordinate_metadata.system == CoordinateSystem.TWO_THETA
        two_theta = data.q_values  # Actually contains 2θ values
        # ... perform analysis
    return results
```

## For Data Analysis

### Basic Conversion

```python
from robomage.coordinate_systems import convert_q_to_two_theta
import numpy as np

q = np.array([2.0, 4.0, 6.0])
wavelength = 0.1665  # Synchrotron

two_theta = convert_q_to_two_theta(q, wavelength)
# [3.04, 6.08, 9.12] degrees
```

### DiffractionData Conversion

```python
from robomage.data import DiffractionData
from robomage.coordinate_systems import CoordinateSystem

# Load Q-space data
data = DiffractionData(
    q_values=np.array([2.0, 4.0, 6.0]),
    intensities=np.array([100, 200, 150]),
    wavelength=0.1665
)

# Convert to 2θ
two_theta_data = data.to_coordinate_system("two_theta")

# Check conversion history
print(two_theta_data.coordinate_metadata.conversion_history)
# ['Q → two_theta']
```

### Create from 2θ Data

```python
# Load 2θ data, automatically converts to Q internally
data = DiffractionData.from_coordinate_system(
    np.array([10.0, 20.0, 30.0]),  # 2θ values
    np.array([100, 200, 150]),  # intensities
    CoordinateSystem.TWO_THETA,
    wavelength=1.54056
)
# data.coordinate_metadata.system == CoordinateSystem.Q
```

## Available Conversions

| From | To | Requires Wavelength? | Function |
|------|-----|---------------------|----------|
| Q | 2θ | ✅ Yes | `convert_q_to_two_theta` |
| 2θ | Q | ✅ Yes | `convert_two_theta_to_q` |
| Q | d-spacing | ❌ No | `convert_q_to_d_spacing` |
| d-spacing | Q | ❌ No | `convert_d_spacing_to_q` |
| 2θ | d-spacing | ✅ Yes | `convert_two_theta_to_d_spacing` |
| d-spacing | 2θ | ✅ Yes | `convert_d_spacing_to_two_theta` |

## Error Handling

### Missing Wavelength
```python
from robomage.coordinate_systems import ConversionError

try:
    convert_q_to_two_theta(q_values, wavelength=None)
except ConversionError as e:
    print(e)
    # "Invalid wavelength: None. Wavelength must be positive..."
```

### Physical Constraints
```python
# Q > 4π/λ raises error
wavelength = 1.54056
q_max = 4 * np.pi / wavelength  # ~8.15 Å⁻¹
q_too_large = np.array([10.0])  # Exceeds physical limit

try:
    convert_q_to_two_theta(q_too_large, wavelength)
except ConversionError as e:
    print(e)
    # "Q values exceed physical maximum 8.15 Å⁻¹..."
```

## Logging

The orchestrator logs all conversions:

```
INFO: Node gsasii_refinement requires input coordinates: Q
INFO:   Converting sample.chi: two_theta → Q  
INFO:     ✓ Conversion successful: 1000 points, range 10.0-60.0° → 1.0-6.0 Å⁻¹
INFO: ✓ Converted 1 data object(s) for node gsasii_refinement
```

## Testing

Run coordinate system tests:
```bash
pixi run python -m pytest tests/test_coordinate_systems.py -v
# 33/33 tests passing ✅
```

## Files Modified/Created

### Core Implementation
- ✅ `src/robomage/coordinate_systems.py` - NEW - Conversion utilities (730 lines)
- ✅ `src/robomage/data/models.py` - Enhanced with coordinate metadata
- ✅ `src/robomage/workflow/nodes/registry.py` - Node metadata contract
- ✅ `src/robomage/orchestrator.py` - Automatic conversion logic

### Node Updates
- ✅ `src/robomage/workflow/nodes/data_nodes.py` - load_files updated
- ✅ `src/robomage/workflow/nodes/analysis_nodes.py` - peak_analysis, gsasii_refinement updated

### Testing & Documentation
- ✅ `tests/test_coordinate_systems.py` - NEW - 33 comprehensive tests
- ✅ `docs/COORDINATE-SYSTEM-CONTRACT-COMPLETE.md` - NEW - Complete documentation
- ✅ `docs/COORDINATE-SYSTEM-QUICK-REF.md` - NEW - This file

## Implementation Summary

**Date**: December 4, 2025  
**Sprint**: 9 - Coordinate System Metadata Contract  
**Status**: ✅ **PRODUCTION READY**

**Key Achievements**:
- Formal coordinate system contract with automatic conversion
- Complete error handling and validation
- Comprehensive test coverage (33/33 tests passing)
- All existing tests still pass (backward compatible)
- Clear logging and provenance tracking

**What This Fixes**:
- GSAS-II field naming confusion ("two_theta" actually contains Q)
- Manual coordinate conversions in node code
- Missing wavelength errors caught early
- Complete conversion history for debugging

**Next Steps**:
- Dashboard integration (show conversions in UI)
- Workflow validation (check compatibility before execution)
- Performance optimization (cache conversions)
