
## [Unreleased] - 2025-12-03

### Fixed - CRITICAL GSAS-II Data Format Issue

**Issue**: GSAS-II refinement failing with "Invalid cell metric tensor" and Rwp=0.0%

**Root Cause**: Manual Q→2θ conversion before sending data to GSAS-II service caused double-conversion and refinement failure.

**Resolution**: Send Q-space values directly labeled as "two_theta" in the API. The instrument parameter file (PDF_1m.instprm) handles coordinate conversion internally.

**Changes**:
- Fixed dashboard callback to send Q values without conversion
- Fixed test script to use correct data format
- Added extensive documentation in all GSAS-II-related files
- Created reference integration test
- Updated Copilot instructions with data format requirements

**Validation**:
- Before: Rwp=0.0%, negative cell values, refinement failed
- After: Rwp=7.69%, Cell a=4.157193 Å, refinement succeeds ✓

**Reference**: See `docs/GSASII-DATA-FORMAT-REFERENCE.md` for complete documentation

