# Dashboard Coordinate System Integration

**Status**: ✅ **COMPLETE** (December 4, 2025)  
**Related**: [Coordinate System Contract](COORDINATE-SYSTEM-CONTRACT-COMPLETE.md)

## Overview

The RoboMage dashboard visualization callbacks now use the centralized coordinate system utilities from `robomage.coordinate_systems`, ensuring consistent conversions across the entire framework.

## Changes Made

### 1. **Refactored Dashboard Plotting Callbacks**

**File**: `src/robomage/dashboard/callbacks/plotting.py`

**Before** (inline conversions):
```python
# Q to 2θ conversion (duplicated logic)
sin_theta = q_data * wavelength / (4 * np.pi)
sin_theta = np.clip(sin_theta, -1.0, 1.0)
two_theta = 2 * np.arcsin(sin_theta) * 180 / np.pi

# Q to d-spacing conversion (duplicated logic)
d_spacing = 2 * np.pi / q_data
```

**After** (centralized utilities):
```python
from robomage.coordinate_systems import (
    convert_q_to_two_theta,
    convert_q_to_d_spacing,
)

# Q to 2θ conversion (uses centralized utility)
two_theta = convert_q_to_two_theta(q_data, wavelength)

# Q to d-spacing conversion (uses centralized utility)
d_spacing = convert_q_to_d_spacing(q_data)
```

### 2. **Updated Peak Annotation Logic**

Peak positions in analysis results are now converted using the same centralized utilities:

```python
# Before
sin_theta = np.clip(peak_q * wavelength / (4 * np.pi), -1.0, 1.0)
peak_x = 2 * np.arcsin(sin_theta) * 180 / np.pi

# After
peak_x = float(convert_q_to_two_theta(np.array([peak_q]), wavelength)[0])
```

## Benefits

### 1. **Single Source of Truth**
- All coordinate conversions use the same tested utilities
- No duplicate conversion logic across the codebase
- Easier to maintain and update

### 2. **Automatic Metadata Tracking** (Future)
- Conversions can be logged with provenance
- Conversion history can be tracked
- Round-trip validation available

### 3. **Consistent Error Handling**
- Same validation logic everywhere
- Proper handling of edge cases (small Q, large Q)
- Consistent clipping behavior for arcsin domain

### 4. **Easier Testing**
- Test conversions once in `test_coordinate_systems.py`
- Dashboard tests verify integration, not math
- Reduced test duplication

## Physical Constraints

### Important Note on 2θ Range

The original inline code clipped `sin(θ)` to [-1, 1] to prevent `arcsin` domain errors. However, **negative 2θ values are physically valid**:

- **Negative 2θ**: Reflections measured past the beamstop at 0°
  - Common in synchrotron experiments
  - Example: Measuring down to -5° is not unusual
  
- **2θ > 180°**: Reflections in the backward direction
  - Less common but theoretically valid
  - Unlikely to be measured in practice

The centralized utilities handle this correctly by:
1. Clipping `sin(θ)` to [-1, 1] (mathematical requirement)
2. **NOT** constraining 2θ to [0, 180°] (physical reality)
3. Allowing any 2θ value that results from valid Q data

## Testing

### Integration Tests

Created `tests/test_dashboard_coordinate_integration.py` with 7 comprehensive tests:

1. ✅ **Q→2θ conversion matches utility**: Verifies dashboard uses centralized function
2. ✅ **Q→d-spacing conversion matches utility**: Verifies dashboard uses centralized function
3. ✅ **Q passthrough unchanged**: Q values returned as-is
4. ✅ **Default wavelength handling**: Uses 0.1665 Å when not provided
5. ✅ **Custom wavelength handling**: Uses wavelength from store
6. ✅ **Edge case handling**: Small Q, large Q (near physical limits)
7. ✅ **Unknown axis defaults to Q**: Graceful fallback

**All tests passing** ✅

### Verification

```bash
# Run integration tests
pixi run python tests/test_dashboard_coordinate_integration.py

# Run all coordinate system tests
pixi run pytest tests/test_coordinate_systems.py -v

# Run all dashboard tests
pixi run pytest tests/test_dashboard.py -v
```

## Usage Examples

### Dashboard X-Axis Selector

The dashboard dropdown already provides three coordinate systems:

```python
dcc.Dropdown(
    id="x-axis-selector",
    options=[
        {"label": "Q (Å⁻¹)", "value": "q"},
        {"label": "2θ (degrees)", "value": "two_theta"},
        {"label": "d-spacing (Å)", "value": "d_spacing"},
    ],
    value="q",  # Default to Q-space
    clearable=False,
)
```

### Conversion Flow

1. **User selects coordinate system** in dropdown
2. **Dashboard reads wavelength** from store (or uses default 0.1665 Å)
3. **`get_x_data()` calls centralized utility**:
   - `convert_q_to_two_theta(q, λ)` for 2θ
   - `convert_q_to_d_spacing(q)` for d-spacing
4. **Plot updates** with converted data
5. **Peak annotations converted** using same utilities

### Wavelength Management

The dashboard supports per-file wavelength assignment:

```python
# Default synchrotron wavelength
wavelength_data = {"current_wavelength": 0.1665}  # Å

# Custom wavelength (e.g., Cu Kα)
wavelength_data = {"current_wavelength": 1.5406}  # Å

# Dashboard uses this for Q ↔ 2θ conversions
x_data, x_label = get_x_data(file_data, "two_theta", wavelength_data)
```

## Implementation Details

### Function Signature

```python
def get_x_data(
    data: dict[str, Any],
    x_axis: str,
    wavelength_data: dict[str, Any] | None = None,
) -> tuple[list[float], str]:
    """
    Get X-axis data and label using centralized coordinate system utilities.
    
    Args:
        data: File data dictionary with 'q' and 'intensity' keys
        x_axis: X-axis selection ('q', 'two_theta', 'd_spacing')
        wavelength_data: Wavelength settings from store (optional)
        
    Returns:
        Tuple of (converted_x_data, axis_label)
    """
```

### Coordinate System Mapping

| Dashboard Value | Coordinate System | Utility Function | Wavelength Required |
|----------------|------------------|-----------------|-------------------|
| `"q"` | Q-space (Å⁻¹) | None (passthrough) | No |
| `"two_theta"` | 2θ (degrees) | `convert_q_to_two_theta()` | Yes |
| `"d_spacing"` | d-spacing (Å) | `convert_q_to_d_spacing()` | No |

## Related Files

### Modified Files
- `src/robomage/dashboard/callbacks/plotting.py`: Refactored to use centralized utilities
- `tests/test_dashboard_coordinate_integration.py`: New integration tests

### Reference Files
- `src/robomage/coordinate_systems.py`: Centralized conversion utilities
- `src/robomage/data/models.py`: DiffractionData with coordinate metadata
- `tests/test_coordinate_systems.py`: Core conversion tests (33 tests)

## Future Enhancements

### 1. **Metadata Display**
Show conversion history in dashboard:
```python
# Display in plot subtitle or info panel
"Q → 2θ (λ=0.1665 Å, converted at 2025-12-04 10:30:00)"
```

### 2. **Validation Warnings**
Visual indicators for edge cases:
- Very large Q values (approaching physical limits)
- Missing wavelength preventing conversion
- Precision loss warnings

### 3. **Conversion Provenance**
Track and display conversion chain:
```python
# Example metadata
{
    "original_system": "Q",
    "current_system": "two_theta",
    "wavelength_used": 0.1665,
    "converted_at": "2025-12-04T10:30:00Z"
}
```

### 4. **Performance Optimization**
Cache converted data to avoid re-conversions:
```python
# Cache key: (filename, coordinate_system, wavelength)
cache_key = (filename, x_axis, wavelength)
if cache_key in conversion_cache:
    return conversion_cache[cache_key]
```

## Migration Notes

### For Developers

If you're adding new coordinate system conversions to the dashboard:

1. ✅ **DO**: Import from `robomage.coordinate_systems`
2. ✅ **DO**: Use `convert_q_to_two_theta()`, `convert_q_to_d_spacing()`, etc.
3. ✅ **DO**: Add tests to `test_dashboard_coordinate_integration.py`
4. ❌ **DON'T**: Implement inline conversion logic
5. ❌ **DON'T**: Duplicate the conversion formulas

### Example: Adding a New Coordinate System

```python
# Import the conversion utility
from robomage.coordinate_systems import convert_q_to_energy

# Add to dropdown options
options = [
    {"label": "Q (Å⁻¹)", "value": "q"},
    {"label": "2θ (degrees)", "value": "two_theta"},
    {"label": "d-spacing (Å)", "value": "d_spacing"},
    {"label": "Energy (keV)", "value": "energy"},  # New option
]

# Add conversion case in get_x_data()
elif x_axis == "energy":
    energy = convert_q_to_energy(q_data, wavelength)
    return energy.tolist(), "Energy (keV)"
```

## Conclusion

The dashboard now leverages the centralized coordinate system infrastructure, providing:

- ✅ **Consistent conversions** across UI and workflows
- ✅ **Single source of truth** for conversion logic
- ✅ **Comprehensive testing** (7 integration tests)
- ✅ **Future-ready** for metadata tracking and validation
- ✅ **Backward compatible** (all existing tests pass)

This completes **Phase 1 Integration** of the coordinate system contract into the dashboard visualization layer.
