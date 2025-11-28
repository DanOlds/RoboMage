# Workflow Peak Analysis Integration Fix

**Date:** November 26, 2025  
**Issue:** Workflow execution failing with attribute errors  
**Status:** ✅ RESOLVED

## Problem

When executing the default workflow with peak analysis, the workflow failed with:
```
'PeakAnalysisClient' object has no attribute 'analyze_diffraction_data'
```

## Root Cause

The workflow node handler (`analysis_nodes.py`) was using outdated API method names and response structure that didn't match the current `PeakAnalysisClient` and peak analysis service.

### Mismatches Found:

1. **Method Name:**
   - ❌ Old: `client.analyze_diffraction_data()`
   - ✅ New: `client.analyze_peaks()`

2. **Config Structure:**
   - ❌ Old: `{"peak_detection": {...}, "fitting": {...}}`
   - ✅ New: `{"detection": {...}, "fitting": {...}}`

3. **Config Field Names:**
   - ❌ Old: `prominence`, `distance`
   - ✅ New: `min_prominence`, `min_distance`

4. **Response Structure:**
   - ❌ Old: Expected `response.peaks_detected`, `response.peak_list`
   - ✅ New: `response["metadata"]["num_peaks_detected"]`, `response["peaks"]`

5. **Peak Field Names:**
   - ❌ Old: Expected `peak.position`, `peak.height` as attributes
   - ✅ New: `peak.get("position")`, `peak.get("height")` from dict

## Changes Made

### File: `src/robomage/workflow/nodes/analysis_nodes.py`

**1. Updated method call:**
```python
# Before
response = client.analyze_diffraction_data(data, analysis_config)

# After
response = client.analyze_peaks(data, analysis_config)
```

**2. Fixed config structure:**
```python
# Before
analysis_config = {
    "peak_detection": {"prominence": prominence, "distance": distance},
    "fitting": {"profile_type": profile_type},
}

# After
analysis_config = {
    "detection": {
        "min_prominence": prominence,
        "min_distance": distance,
    },
    "fitting": {
        "profile_type": profile_type,
    },
}
```

**3. Updated response parsing:**
```python
# Before
result = {
    "filename": data.filename,
    "peaks_detected": response.peaks_detected,
    "peaks_fitted": response.peaks_fitted,
    "overall_r_squared": response.overall_r_squared,
    "peak_list": [...]
}

# After
peaks = response.get("peaks", [])
metadata = response.get("metadata", {})

result = {
    "filename": data.filename,
    "peaks_detected": metadata.get("num_peaks_detected", len(peaks)),
    "peaks_fitted": metadata.get("num_peaks_fitted", len(peaks)),
    "overall_r_squared": metadata.get("overall_r_squared", 0.0),
    "peak_list": [
        {
            "position": peak.get("position"),
            "d_spacing": peak.get("d_spacing"),
            "height": peak.get("height"),
            "width": peak.get("width"),
            "area": peak.get("area"),
            "r_squared": peak.get("r_squared", 0.0),
        }
        for peak in peaks
    ],
}
```

## Correct Service Response Structure

The peak analysis service returns:

```json
{
  "request_id": "...",
  "peaks": [
    {
      "peak_id": 1,
      "position": 2.5,
      "height": 150.0,
      "width": 0.1,
      "area": 45.2,
      "d_spacing": 2.513,
      "profile_type": "gaussian",
      "r_squared": 0.95
    }
  ],
  "metadata": {
    "num_peaks_detected": 5,
    "num_peaks_fitted": 5,
    "overall_r_squared": 0.92,
    "processing_time_ms": 45.2,
    "success": true,
    "warnings": []
  },
  "background": {
    "background_type": "linear",
    "parameters": [10.0, -0.5],
    "r_squared": 0.98
  }
}
```

## Testing

Now the workflow should work correctly:

```bash
# Start peak analysis service
pixi run python services/peak_analysis/main.py --port 8001

# Start workflow service
pixi run python services/workflow_engine/main.py --port 8002

# Start dashboard
pixi run python -m robomage.dashboard

# Navigate to http://localhost:8050
# Click ⚙️ Workflow Builder tab
# Click Execute
```

Expected result:
- ✅ Node `load_1` completes successfully
- ✅ Node `analyze_1` completes successfully (with peak count)
- ✅ Node `export_1` completes successfully
- ✅ Results displayed with execution time and peak statistics

## Related Documentation

- `docs/SERVICES-QUICKSTART.md` - Service startup guide
- `services/peak_analysis/models.py` - Complete API models
- `src/robomage/clients/peak_analysis_client.py` - Client API reference

## Files Modified

1. `src/robomage/workflow/nodes/analysis_nodes.py` - Fixed API integration
2. `services/workflow_engine/main.py` - Added service dependency warnings
3. `docs/SERVICES-QUICKSTART.md` - Created service reference guide

---

**✅ The workflow should now execute successfully with the peak analysis service running!**
