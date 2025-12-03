# GSAS-II Data Format Issue - Resolution Summary

**Date**: December 3, 2025  
**Issue**: Refinement failing with "Invalid cell metric tensor" and Rwp=0.0%  
**Root Cause**: Manual Q→2θ conversion before sending data to GSAS-II  
**Resolution**: Send Q values directly labeled as "two_theta"  
**Status**: ✅ RESOLVED - All tests passing with Rwp ≈ 7.7%

---

## Problem Discovery

During dashboard testing, GSAS-II refinement was consistently failing with:
- Rwp = 0.0% (no actual refinement)
- "Invalid cell metric tensor" errors
- Negative cell values (e.g., -22248 Å)
- Refinement failed on Cycle 0

The issue was traced to incorrect data format handling when sending diffraction data to the GSAS-II service.

---

## Root Cause

**Misconception**: CHI files contain 2θ data, so we should just pass it directly.

**Reality**: 
1. Synchrotron CHI files contain **Q-space data** (Å⁻¹), not 2θ
2. GSAS-II API expects data labeled as `"two_theta"` regardless of coordinate system
3. The **instrument parameter file** (PDF_1m.instprm) tells GSAS-II how to interpret coordinates
4. GSAS-II performs Q ↔ 2θ conversion internally based on the instrument file

**What went wrong**:
- Code was manually converting Q→2θ: `two_theta = 2 * arcsin(q * λ / (4π))`
- This produced values in range ~0.98-24.27° (converted from Q range 0.647-15.867 Å⁻¹)
- GSAS-II received these pre-converted values and tried to convert them AGAIN
- Double conversion resulted in garbage values and refinement failure

---

## Solution

**Send Q values directly labeled as "two_theta":**

```python
# ✅ CORRECT
request = {
    "diffraction_data": {
        "two_theta": q_values.tolist(),  # Q values from CHI file (0.647-15.867 Å⁻¹)
        "intensity": intensities.tolist()
    },
    "recipe": {
        "instrument_file": "PDF_1m.instprm",  # Handles Q ↔ 2θ conversion
        ...
    }
}
```

**Result**: Rwp ≈ 7.7%, cell a ≈ 4.157 Å, refinement succeeds! ✓

---

## Changes Made

### 1. Code Fixes

**Dashboard Callback** (`src/robomage/dashboard/callbacks/gsasii_callbacks.py`):
- ❌ Removed: Manual Q→2θ conversion
- ✅ Added: Send Q values directly as "two_theta"
- ✅ Added: Comprehensive documentation in file header

**Test Script** (`test_gsasii_refinement.py`):
- ❌ Removed: Q→2θ conversion step
- ✅ Added: Extensive comments explaining the correct approach
- ✅ Added: Detailed documentation in file header

### 2. Documentation Added

**New Files:**
1. `docs/GSASII-DATA-FORMAT-REFERENCE.md` - Comprehensive reference guide
2. `tests/test_gsasii_refinement_integration.py` - Authoritative reference test
3. `docs/GSASII-DATA-FORMAT-RESOLUTION.md` - This file

**Updated Files:**
1. `services/gsasii_refinement/gsasii_worker.py` - Added critical data format warning in header
2. `src/robomage/dashboard/callbacks/gsasii_callbacks.py` - Added extensive documentation
3. `test_gsasii_refinement.py` - Added step-by-step explanations
4. `.github/copilot-instructions.md` - Added GSAS-II data format requirements section

### 3. Reference Tests

**Integration Test**: `tests/test_gsasii_refinement_integration.py`
- Serves as authoritative reference implementation
- Includes meta-test to verify documentation exists
- Can run standalone or via pytest
- Expected results: Rwp 7-8%, cell a ≈ 4.157 Å

**Standalone Test**: `test_gsasii_refinement.py`
- User-friendly output with progress indicators
- Detailed step-by-step explanations
- Clear validation results

---

## Validation Results

### Before Fix
```
Rwp:                  0.00% ❌
Cell a:               4.156820 Å (unchanged from CIF)
ESDs:                 0.000000 (no refinement occurred)
Error:                "Invalid cell metric tensor"
Cell values:          -22248 Å (negative!)
Cycles:               Failed on Cycle 0
```

### After Fix
```
Rwp:                  7.69% ✅
Cell a:               4.157193 ± 0.000027 Å ✅
Cycles:               5 complete ✅
Execution time:       3-5 seconds ✅
No errors:            ✅
```

---

## Prevention Measures

To ensure this mistake doesn't happen again:

### 1. Code-Level Safeguards
- ✅ All GSAS-II-related files include prominent warnings
- ✅ Reference test (`test_gsasii_refinement_integration.py`) validates correct behavior
- ✅ Meta-test checks that documentation exists

### 2. Documentation
- ✅ Copilot instructions include GSAS-II data format requirements
- ✅ Quick reference card in `GSASII-DATA-FORMAT-REFERENCE.md`
- ✅ Inline code comments in all critical locations

### 3. Testing
- ✅ Integration test with expected results validation
- ✅ Standalone test script for manual verification
- ✅ Both tests can be run easily: `pixi run python tests/test_gsasii_refinement_integration.py`

### 4. Knowledge Transfer
- ✅ This resolution document captures the full story
- ✅ Future developers will see warnings in multiple places
- ✅ AI assistants (Copilot) will have the requirements in instructions

---

## Key Takeaways

1. **Never assume coordinate system from file extension or headers**
   - CHI files can be Q or 2θ space
   - Check the actual values (Q: 0.5-16 Å⁻¹, 2θ: 5-120°)

2. **GSAS-II API uses "two_theta" as a generic label**
   - "two_theta" doesn't mean the data IS in 2θ space
   - It's just the field name - the instrument file defines interpretation

3. **Instrument parameter files are critical**
   - They tell GSAS-II how to interpret the coordinate system
   - PDF_1m.instprm is for synchrotron Q-space data
   - Don't convert data manually - let GSAS-II use the instrument file

4. **Reference implementations prevent regressions**
   - Always have a working test to compare against
   - Document expected results explicitly
   - Make tests easy to run

---

## Quick Reference

**When sending data to GSAS-II:**

```python
# Read CHI file (Q-space: 0.5-16 Å⁻¹)
q_values, intensities = load_chi_file("data.chi")

# ✅ DO THIS:
request = {"diffraction_data": {"two_theta": q_values.tolist(), ...}}

# ❌ DON'T DO THIS:
two_theta = 2 * np.degrees(np.arcsin(q_values * wavelength / (4 * np.pi)))
request = {"diffraction_data": {"two_theta": two_theta.tolist(), ...}}
```

**Run tests to verify:**
```bash
pixi run python tests/test_gsasii_refinement_integration.py
pixi run python test_gsasii_refinement.py
```

**Expected results for LaB6:**
- Rwp: 7-8%
- Cell a: ~4.157 Å (±0.00003 Å)
- 5 refinement cycles complete
- No "Invalid metric tensor" errors

---

## Related Documentation

- **Data Format Reference**: `docs/GSASII-DATA-FORMAT-REFERENCE.md` (comprehensive guide)
- **Integration Test**: `tests/test_gsasii_refinement_integration.py` (reference implementation)
- **Standalone Test**: `test_gsasii_refinement.py` (user-friendly validation)
- **Service Worker**: `services/gsasii_refinement/gsasii_worker.py` (implementation)
- **Dashboard Callbacks**: `src/robomage/dashboard/callbacks/gsasii_callbacks.py` (UI integration)
- **Copilot Instructions**: `.github/copilot-instructions.md` (AI assistant guidance)

---

## Acknowledgments

This issue was resolved through careful comparison with the working reference implementation in `/tmp/test_refinement.py` from Phase 3 testing, which correctly sent Q values without conversion. The key insight came from recognizing that the working test and the failing test differed only in whether Q→2θ conversion was performed.
