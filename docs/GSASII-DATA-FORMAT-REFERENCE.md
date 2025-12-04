# GSAS-II Data Format Reference

**Created**: December 3, 2025  
**Status**: CRITICAL - Required reading for anyone working with GSAS-II integration

---

## Executive Summary

⚠️ **DO NOT convert Q to 2θ before sending data to GSAS-II!**

Synchrotron CHI files are in **Q-space** (Å⁻¹), but GSAS-II requires them to be labeled as `"two_theta"` in the API. The **instrument parameter file handles coordinate conversion internally**.

---

## The Critical Mistake

### ❌ WRONG Approach (Causes Refinement Failure)
```python
# Reading CHI file (Q-space data: 0.647-15.867 Å⁻¹)
q_values, intensities = load_chi_file("data.chi")

# ❌ WRONG: Manual Q→2θ conversion
wavelength = 0.1665  # Å
two_theta = 2 * np.degrees(np.arcsin(q_values * wavelength / (4 * np.pi)))
# Result: two_theta ≈ 0.98-24.27°

# ❌ Sending converted values
request = {
    "diffraction_data": {
        "two_theta": two_theta.tolist(),  # Wrong! These are doubly-converted
        "intensity": intensities.tolist()
    },
    ...
}
```

**Failure Symptoms:**
- `Invalid cell metric tensor for phase #0`
- Negative cell values (e.g., -22248 Å)
- Rwp = 0.0% (calculation-only mode)
- GSAS-II fails on Cycle 0 with "unable to evaluate objective function"
- Refinement "completes" but restores initial parameters

### ✅ CORRECT Approach
```python
# Reading CHI file (Q-space data: 0.647-15.867 Å⁻¹)
q_values, intensities = load_chi_file("data.chi")

# ✅ CORRECT: Send Q values directly as "two_theta"
request = {
    "diffraction_data": {
        "two_theta": q_values.tolist(),  # Q values labeled as "two_theta"
        "intensity": intensities.tolist()
    },
    "recipe": {
        "instrument_file": "PDF_1m.instprm",  # This handles Q ↔ 2θ conversion!
        ...
    },
    ...
}
```

**Success Indicators:**
- Multiple refinement cycles complete (Cycle 0, 1, 2, 3, 4)
- Rwp ≈ 7-8% for LaB6 standard
- Cell parameter a ≈ 4.157 Å with non-zero ESDs (e.g., ±0.00003 Å)
- Chi² and GoF values are populated (not null)
- No "Invalid metric tensor" errors

---

## Why This Happens

1. **CHI File Format**: Despite headers sometimes saying "2theta", synchrotron CHI files contain Q-space data (Å⁻¹)
2. **GSAS-II API**: Expects diffraction data labeled as `"two_theta"` regardless of actual coordinate system
3. **Instrument File**: The instrument parameter file (e.g., `PDF_1m.instprm`) tells GSAS-II how to interpret the coordinates
4. **Internal Conversion**: GSAS-II reads the instrument file and performs the Q ↔ 2θ conversion internally

**Analogy**: It's like units in physics. You don't convert meters to feet before sending to a function that expects "distance" - you label it as "distance" and let the function handle the units based on its configuration.

---

## Expected Results for LaB6 SRM 660c

**Test File**: `xrd_LaB6_660c_std_brac2_20250724-194924_70c707_primary-1_mean_tth.chi`

**Data Characteristics:**
- Format: Q-space (despite filename saying "tth")
- Q range: 0.647 - 15.867 Å⁻¹
- Data points: 4096
- Wavelength: 0.1665 Å (synchrotron)

**Expected Refinement Results:**
```
Rwp:              7-8%
Cell a:           4.157 ± 0.0001 Å (cubic)
Execution time:   3-5 seconds
Cycles:           5 complete
```

**Recipe Configuration:**
```python
{
    "set": {
        "Limits": {"low": 0.5, "high": 16.0},
        "Background": {"type": "chebyschev-1", "no. coeffs": 3, "refine": True},
        "Cell": True,
        "Sample Parameters": ["Scale"]
    },
    "do": "refinement"
}
```

---

## Reference Implementations

### 1. Integration Test (Authoritative)
**File**: `tests/test_gsasii_refinement_integration.py`

This test is the **reference implementation** for GSAS-II data handling. It includes:
- Correct Q-space data loading
- Proper request formatting
- Comprehensive validation
- Expected result checks

**Run with:**
```bash
pixi run python tests/test_gsasii_refinement_integration.py
```

### 2. Standalone Test Script
**File**: `test_gsasii_refinement.py`

User-friendly test script with detailed output and step-by-step progress.

**Run with:**
```bash
pixi run python test_gsasii_refinement.py
```

### 3. Dashboard Callback
**File**: `src/robomage/dashboard/callbacks/gsasii_callbacks.py`

The dashboard correctly sends Q values as "two_theta". See the `run_refinement` callback for the reference implementation.

### 4. Service Worker
**File**: `services/gsasii_refinement/gsasii_worker.py`

The worker script includes extensive documentation about the data format requirements in its header.

---

## Code Documentation Locations

All critical files include warnings about the data format:

1. ✅ **Service Worker**: `services/gsasii_refinement/gsasii_worker.py` (header)
2. ✅ **Dashboard Callbacks**: `src/robomage/dashboard/callbacks/gsasii_callbacks.py` (header)
3. ✅ **Test Script**: `test_gsasii_refinement.py` (header + inline comments)
4. ✅ **Integration Test**: `tests/test_gsasii_refinement_integration.py` (comprehensive docs)
5. ✅ **Copilot Instructions**: `.github/copilot-instructions.md` (GSAS-II section)

---

## Troubleshooting

### Problem: Rwp = 0.0%, refinement "succeeds" but no actual refinement
**Cause**: You converted Q→2θ before sending to GSAS-II  
**Solution**: Send Q values directly as `"two_theta"`

### Problem: "Invalid cell metric tensor" error
**Cause**: You converted Q→2θ before sending to GSAS-II  
**Solution**: Send Q values directly as `"two_theta"`

### Problem: Negative cell values (e.g., -22248 Å)
**Cause**: You converted Q→2θ before sending to GSAS-II  
**Solution**: Send Q values directly as `"two_theta"`

### Problem: GSAS-II fails on Cycle 0
**Cause**: Data format issue (likely manual Q→2θ conversion)  
**Solution**: Check that you're sending Q values directly

### Problem: How do I know if my CHI file is Q or 2θ?
**Answer**: Look at the range:
- Q-space: 0.5-16 Å⁻¹ (typical synchrotron)
- 2θ-space: 5-120° (typical lab X-ray)

For synchrotron data (λ=0.1665 Å), always assume Q-space.

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│ GSAS-II Data Format - Quick Reference                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ CHI File Type:        Q-space (Å⁻¹)                        │
│ API Label:            "two_theta"                          │
│ Conversion:           DO NOT PERFORM (GSAS-II handles it)  │
│ Instrument File:      PDF_1m.instprm (for synchrotron)     │
│                                                             │
│ ✅ CORRECT CODE:                                           │
│   request = {                                              │
│       "diffraction_data": {                                │
│           "two_theta": q_values.tolist(),  # No conversion!│
│           "intensity": intensities.tolist()                │
│       },                                                   │
│       "recipe": {"instrument_file": "PDF_1m.instprm", ...} │
│   }                                                        │
│                                                             │
│ ❌ WRONG CODE:                                             │
│   two_theta = 2*np.degrees(np.arcsin(q*λ/(4π)))  # Don't! │
│                                                             │
│ Success Indicators:                                        │
│   • Rwp: 7-8% (LaB6)                                       │
│   • Multiple cycles complete                               │
│   • Non-zero ESDs                                          │
│   • No "Invalid metric tensor" errors                     │
│                                                             │
│ Reference Test:                                            │
│   pixi run python tests/test_gsasii_refinement_integration.py│
└─────────────────────────────────────────────────────────────┘
```

---

## Related Documentation

- **Implementation Plan**: `docs/GSAS-II-SERVICE-IMPLEMENTATION-PLAN.md`
- **Phase 3 Completion**: `docs/GSASII-PHASE-3-SUBPROCESS-COMPLETE.md`
- **Service Design**: `docs/GSASII-SERVICE-DESIGN.md`
- **Dashboard Tab**: `docs/GSASII-DASHBOARD-TAB-COMPLETE.md`

---

## Revision History

- **2025-12-03**: Initial creation after discovering data format issue
  - Documented correct Q-space handling
  - Added reference implementations
  - Created integration test
  - Updated all code documentation
  - Updated Copilot instructions
