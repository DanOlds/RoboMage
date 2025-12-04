"""
Coordinate System Metadata Contract - Implementation Summary

This document summarizes the coordinate system metadata contract implementation
for RoboMage powder diffraction analysis framework.

## Overview

RoboMage uses Q-space (Å⁻¹) as the canonical internal coordinate system, but
external services often require data in different coordinate systems (2θ, d-spacing).
This implementation provides automatic conversion with clear metadata tracking.

## Core Principles

1. **Internal Canonical Form**: Always Q-space in storage
2. **Explicit Node Contracts**: Nodes declare coordinate requirements in metadata
3. **Automatic Conversion with Logging**: Framework converts but makes it visible
4. **Metadata Propagation**: Every data object carries coordinate system info

## Implementation Components

### 1. Coordinate System Utilities (`src/robomage/coordinate_systems.py`)

**Enums and Models**:
- `CoordinateSystem`: Enum for Q, TWO_THETA, D_SPACING
- `CoordinateMetadata`: Pydantic model tracking system, units, wavelength, history
- `ConversionError`: Custom exception for conversion failures

**Conversion Functions**:
- `convert_q_to_two_theta(q, wavelength)`: Q → 2θ
- `convert_two_theta_to_q(two_theta, wavelength)`: 2θ → Q
- `convert_q_to_d_spacing(q)`: Q → d-spacing
- `convert_d_spacing_to_q(d)`: d-spacing → Q
- `convert_two_theta_to_d_spacing(two_theta, wavelength)`: 2θ → d-spacing
- `convert_d_spacing_to_two_theta(d, wavelength)`: d-spacing → 2θ
- `convert_coordinate_system(x, from_sys, to_sys, wavelength)`: Generic converter
- `validate_round_trip_conversion(...)`: Precision validation

**Key Features**:
- Comprehensive error handling (missing wavelength, invalid values)
- Physical constraint validation (Q ≤ 4π/λ, 0 ≤ 2θ ≤ 180°)
- Informative logging for all conversions
- Round-trip precision validation

### 2. Data Model Enhancements (`src/robomage/data/models.py`)

**DiffractionData Updates**:
- New field: `coordinate_metadata: CoordinateMetadata`
- Wavelength synced to metadata in `model_post_init`
- `to_coordinate_system(target_system)`: Convert data to different coordinate system
- `from_coordinate_system(x, intensities, system, wavelength)`: Create from any system

**Example Usage**:
```python
from robomage.data import DiffractionData
from robomage.coordinate_systems import CoordinateSystem
import numpy as np

# Create Q-space data
data = DiffractionData(
    q_values=np.array([2.0, 4.0, 6.0]),
    intensities=np.array([100, 200, 150]),
    wavelength=0.1665
)

# Convert to 2θ
two_theta_data = data.to_coordinate_system(CoordinateSystem.TWO_THETA)
print(two_theta_data.q_values)  # Now contains 2θ values!
print(two_theta_data.coordinate_metadata.system)  # TWO_THETA

# Create from 2θ data
data_from_2theta = DiffractionData.from_coordinate_system(
    np.array([10.0, 20.0, 30.0]),
    np.array([100, 200, 150]),
    CoordinateSystem.TWO_THETA,
    wavelength=1.54056
)
print(data_from_2theta.coordinate_metadata.system)  # Q (converted automatically)
```

### 3. Node Metadata Contract (`src/robomage/workflow/nodes/registry.py`)

**NodeTypeMetadata Enhancement**:
- New field: `coordinate_requirements` dict with:
  - `input_coordinates`: Required input system (None = any)
  - `output_coordinates`: Output system (None = same as input)
  - `requires_wavelength`: Boolean flag

**Node Registration Pattern**:
```python
@register_node(
    type="my_node",
    category="analysis",
    name="My Analysis",
    description="Does analysis",
    coordinate_requirements={
        "input_coordinates": "Q",
        "output_coordinates": "Q",
        "requires_wavelength": False
    }
)
async def my_node_handler(config, inputs, context):
    # Implementation
    pass
```

### 4. Orchestrator Auto-Conversion (`src/robomage/orchestrator.py`)

**Workflow Integration**:
- `_convert_inputs_for_node(...)`: Check requirements and convert if needed
- `_convert_single_data(...)`: Convert individual DiffractionData objects
- Informative logging for all conversions
- Clear error messages for missing wavelength

**Conversion Flow**:
1. Node declares coordinate requirements in metadata
2. Orchestrator checks input data coordinate systems
3. If mismatch detected: Log warning and convert automatically
4. Execute node with converted data
5. All conversions logged for transparency

**Example Log Output**:
```
INFO: Node gsasii_refinement_1 requires input coordinates: Q
INFO:   Converting file1.chi: two_theta → Q
INFO:     ✓ Conversion successful: 1000 points, range 10.0-60.0 → 1.0-6.0
INFO: ✓ Converted 1 data object(s) for node gsasii_refinement_1
```

### 5. Node Updates

**load_files** (`src/robomage/workflow/nodes/data_nodes.py`):
```python
coordinate_requirements={
    "input_coordinates": None,  # No inputs
    "output_coordinates": "Q",  # Always outputs Q-space
    "requires_wavelength": False,  # Optional
}
```

**peak_analysis** (`src/robomage/workflow/nodes/analysis_nodes.py`):
```python
coordinate_requirements={
    "input_coordinates": "Q",  # Requires Q-space
    "output_coordinates": "Q",  # Outputs Q-space results
    "requires_wavelength": False,  # Doesn't need wavelength
}
```

**gsasii_refinement** (`src/robomage/workflow/nodes/analysis_nodes.py`):
```python
coordinate_requirements={
    "input_coordinates": "Q",  # Actually requires Q (not 2θ)!
    # CRITICAL: GSAS-II service expects Q values labeled as "two_theta"
    # The instrument parameter file handles Q ↔ 2θ conversion internally
    "output_coordinates": None,  # Outputs refinement results
    "requires_wavelength": True,  # Wavelength needed
}
```

**IMPORTANT NOTE**: GSAS-II has special data format requirements. See 
`docs/GSASII-DATA-FORMAT-REFERENCE.md` for details on why Q values are
labeled as "two_theta" in the API.

## Testing

### Test Coverage (`tests/test_coordinate_systems.py`)

**Test Classes**:
- `TestBasicConversions`: Verify conversion accuracy
- `TestRoundTripConversions`: Verify precision preservation
- `TestErrorHandling`: Verify error messages and validation
- `TestConvertCoordinateSystem`: Test generic converter
- `TestCoordinateMetadata`: Test metadata model
- `TestEdgeCases`: Numerical stability and edge cases
- `TestDiffractionDataIntegration`: Integration with data model

**Test Results**:
- 33/33 tests passing ✅
- Coverage: Basic conversions, round-trips, errors, edge cases
- Integration: DiffractionData model, wavelength sync, history tracking

## Usage Examples

### Example 1: Basic Conversion

```python
from robomage.coordinate_systems import convert_q_to_two_theta
import numpy as np

q_values = np.array([2.0, 4.0, 6.0])  # Å⁻¹
wavelength = 0.1665  # Synchrotron wavelength

two_theta = convert_q_to_two_theta(q_values, wavelength)
print(two_theta)  # [3.04, 6.08, 9.12] degrees
```

### Example 2: DiffractionData Conversion

```python
from robomage.data import DiffractionData
from robomage.coordinate_systems import CoordinateSystem
import numpy as np

# Load Q-space data
data = DiffractionData(
    q_values=np.array([2.0, 4.0, 6.0]),
    intensities=np.array([100, 200, 150]),
    wavelength=0.1665,
    filename="sample.chi"
)

# Convert to 2θ for analysis
two_theta_data = data.to_coordinate_system("two_theta")

# Check conversion history
print(two_theta_data.coordinate_metadata.conversion_history)
# ['Q → two_theta']

# Intensities unchanged
np.testing.assert_array_equal(
    data.intensities, 
    two_theta_data.intensities
)
```

### Example 3: Workflow with Automatic Conversion

```python
# Node declares it needs Q-space
@register_node(
    type="custom_analysis",
    coordinate_requirements={
        "input_coordinates": "Q",
        "requires_wavelength": False
    }
)
async def custom_analysis_handler(config, inputs, context):
    files = inputs.get("input", [])
    
    # Data will be automatically converted to Q if needed
    for data in files:
        assert data.coordinate_metadata.system == CoordinateSystem.Q
        # Perform analysis in Q-space
        peaks = find_peaks(data.q_values, data.intensities)
    
    return results
```

## Error Handling

### Missing Wavelength

```python
# Attempting Q → 2θ without wavelength raises clear error
try:
    convert_q_to_two_theta(q_values, wavelength=None)
except ConversionError as e:
    print(e)
    # "Invalid wavelength: None. Wavelength must be positive 
    #  (typically 0.1-2.0 Å for X-rays)."
```

### Invalid Q Range

```python
# Q values exceeding physical limit
wavelength = 1.54056
q_max_physical = 4 * np.pi / wavelength
q_too_large = np.array([q_max_physical + 1.0])

try:
    convert_q_to_two_theta(q_too_large, wavelength)
except ConversionError as e:
    print(e)
    # "Q values exceed physical maximum 8.15 Å⁻¹ for wavelength 
    #  1.5406 Å. Check wavelength or Q values for errors."
```

### Node Conversion Failure

```python
# Orchestrator provides clear error if conversion fails
# Error message includes:
# - Which node required the conversion
# - Which file failed
# - What went wrong (e.g., missing wavelength)

# Example:
# "Cannot convert to 2θ for node gsasii_refinement_1: 
#  File sample.chi is missing wavelength. 
#  Please provide wavelength in the file or node configuration."
```

## Design Decisions

### Why Q-Space as Canonical?

1. **Scientific Standard**: Q is the fundamental reciprocal space coordinate
2. **Wavelength Independent**: Q doesn't require wavelength for many operations
3. **Synchrotron Compatibility**: Most modern facilities provide Q-space data
4. **Analysis Clarity**: Peak positions in Q are wavelength-independent

### Why Automatic Conversion?

1. **User Experience**: Removes burden from workflow authors
2. **Error Prevention**: Catches coordinate mismatches early
3. **Transparency**: All conversions logged, nothing hidden
4. **Flexibility**: Nodes can work in natural coordinate systems

### Why Metadata Tracking?

1. **Provenance**: Complete history of data transformations
2. **Debugging**: Easy to diagnose coordinate system issues
3. **Reproducibility**: Know exactly what conversions were applied
4. **Validation**: Can verify conversion accuracy

## Future Enhancements

1. **Dashboard Visualization**: Show coordinate system conversions in UI
2. **Conversion Warnings**: Alert on precision loss (e.g., round-trip errors)
3. **Alternative Conventions**: Support for different 2θ definitions
4. **Performance**: Cache conversions to avoid redundant calculations
5. **Validation**: Pre-execution workflow validation of coordinate compatibility

## References

- `src/robomage/coordinate_systems.py`: Core conversion utilities
- `src/robomage/data/models.py`: DiffractionData enhancements
- `src/robomage/workflow/nodes/registry.py`: Node metadata contract
- `src/robomage/orchestrator.py`: Automatic conversion logic
- `tests/test_coordinate_systems.py`: Comprehensive test suite
- `docs/GSASII-DATA-FORMAT-REFERENCE.md`: GSAS-II special requirements

## Sprint 9 Summary

**Implementation Date**: December 4, 2025

**Status**: ✅ **COMPLETE**

**Deliverables**:
- ✅ Coordinate system conversion utilities with full error handling
- ✅ DiffractionData model enhancements with conversion methods
- ✅ NodeTypeMetadata contract with coordinate requirements
- ✅ Orchestrator automatic conversion logic with informative logging
- ✅ Updated nodes (load_files, peak_analysis, gsasii_refinement)
- ✅ Comprehensive test suite (33/33 tests passing)
- ✅ Complete documentation and examples

**Key Achievement**: Production-ready coordinate system metadata contract
that prevents field naming confusion and provides clear provenance tracking!

---

**Next Steps**: 
- Integrate with dashboard (show conversions in UI)
- Add workflow validation (check compatibility before execution)
- Document best practices for custom node development
