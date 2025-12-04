# New Chat Prompt: GSAS-II Visualization Integration

**Copy the text below to start a new chat session for implementing GSAS-II→Visualization integration**

---

## Initial Prompt

```
I need to implement GSAS-II refinement visualization integration for the RoboMage dashboard. 

CONTEXT:
- Project: RoboMage powder diffraction analysis framework with Dash dashboard
- Current state: GSAS-II refinement tab exists and works correctly (port 8003)
- Refinements produce correct results: Rwp ~7.7%, Cell a ~4.157 Å
- Results are displayed ONLY in GSAS-II tab (isolated)
- Goal: Enable GSAS-II refinement data to be visualized in the main Visualization tab

WHAT EXISTS:
1. GSAS-II Refinement tab (src/robomage/dashboard/layouts/gsasii_tab.py)
   - Stores results in gsasii-refinement-result (local dcc.Store)
   - Shows static PNG plot, cell parameters, fit quality metrics
   
2. Visualization tab (main plot in plotting.py)
   - Uses file-data-store (raw uploaded files)
   - Uses analysis-results-store (peak analysis overlays)
   - Interactive Plotly plots with configurable axes

3. GSAS-II response structure:
   ```json
   {
     "success": true,
     "fit_profile": {
       "two_theta": [...],      // Q-space data labeled as two_theta
       "intensity_obs": [...],   // Observed intensities
       "intensity_calc": [...],  // Calculated from refinement
       "residual": [...]         // Obs - Calc
     },
     "cell": {"a": {"value": 4.157, "esd": 0.000027}, ...},
     "fit_quality": {"Rwp": 7.69, "chi2": null, "GoF": null}
   }
   ```

IMPLEMENTATION PLAN:
Please read and follow: docs/GSASII-VIZ-INTEGRATION-PLAN.md

The plan defines:
- New gsasii-viz-data-store for cross-tab data sharing
- "Send to Visualization" button in GSAS-II tab
- Callback to transform GSAS-II results → viz format
- Updated plotting callback to render 3 traces:
  * Calculated pattern (red line)
  * Observed data (blue markers)  
  * Difference curve (green line, offset)
- Toggle control in Visualization tab
- Metadata annotation on plot

CRITICAL REQUIREMENTS:
1. GSAS-II data format: CHI files are Q-space, sent as "two_theta" to service
   - DO NOT manually convert Q→2θ (instrument file handles this)
   - See: services/gsasii_refinement/gsasii_worker.py header for explanation
   
2. State management: Use dcc.Store pattern (NOT session persistence yet)
   - gsasii-viz-data-store is in-memory only
   - Session integration is future work
   
3. Code locations:
   - Layouts: src/robomage/dashboard/layouts/
   - Callbacks: src/robomage/dashboard/callbacks/
   - Main layout: src/robomage/dashboard/layouts/main_layout.py
   
4. Testing approach:
   - Use test_gsasii_refinement.py for end-to-end validation
   - Test data: test_data/LaB6_SRM660c.chi (Q-space)
   - Expected: Rwp ~7.7%, Cell a ~4.157 Å

PHASE 1 TASKS (2 hours - implement this first):
1. Add gsasii-viz-data-store to main_layout.py
2. Add "Send to Visualization" button to gsasii_tab.py
3. Create send_gsasii_to_viz callback in gsasii_callbacks.py
4. Update run_refinement callback to enable button when results exist

PHASE 2 TASKS (2 hours - after Phase 1 works):
1. Update register_main_plot_callback in plotting.py
2. Add Input("gsasii-viz-data-store", "data")
3. Add checkbox "Show GSAS-II Overlay" to Visualization tab
4. Render 3 traces when overlay enabled
5. Add metadata annotation with Rwp and cell parameters

VALIDATION:
After implementation:
1. Start services: pixi run start-all
2. Navigate to GSAS-II tab
3. Upload LaB6_SRM660c.chi
4. Run refinement (should get Rwp ~7.7%)
5. Click "Send to Visualization"
6. Switch to Visualization tab
7. Enable "Show GSAS-II Overlay" checkbox
8. Verify 3 traces appear: calculated, observed, difference
9. Check metadata annotation shows correct Rwp and cell values

FILES TO READ FIRST:
1. docs/GSASII-VIZ-INTEGRATION-PLAN.md (the complete plan)
2. src/robomage/dashboard/layouts/gsasii_tab.py (current tab)
3. src/robomage/dashboard/callbacks/gsasii_callbacks.py (current callbacks)
4. src/robomage/dashboard/callbacks/plotting.py (visualization callbacks)
5. src/robomage/dashboard/layouts/main_layout.py (stores and tabs)

REFERENCES:
- GSAS-II service docs: docs/GSASII-PHASE-3-SUBPROCESS-COMPLETE.md
- Data format requirements: services/gsasii_refinement/gsasii_worker.py (header)
- Test integration: tests/test_gsasii_refinement_integration.py
- Standalone test: test_gsasii_refinement.py

Let's start with Phase 1: adding the data bridge. Please confirm you've read the plan document, then we'll implement the store and button.
```

---

## Follow-up Prompts (Use as needed during implementation)

### If stuck on data transformation:
```
The GSAS-II response has fit_profile with fields: two_theta, intensity_obs, intensity_calc, residual.
I need to transform this into the viz_data structure defined in GSASII-VIZ-INTEGRATION-PLAN.md section "Proposed Architecture".

Can you show me the exact code for the send_gsasii_to_viz callback that:
1. Extracts fit_profile from refinement_result
2. Builds calculated, observed, and difference dictionaries
3. Includes metadata (Rwp, cell_a, timestamp)
4. Returns viz_data and button state
```

### If plotting isn't working:
```
I've added the gsasii-viz-data-store input to the plotting callback, but the traces aren't appearing.

Current state:
- gsasii-viz-data-store contains data (I can see it in browser DevTools)
- show-gsasii-overlay checkbox is enabled
- The callback fires but no GSAS-II traces appear

Can you review the plotting.py code and help debug why traces aren't being added to the figure?
```

### If coordinate system is wrong:
```
CRITICAL: The GSAS-II data is in Q-space (Å⁻¹) but labeled as "two_theta" in the API.

The visualization tab x-axis selector has options: q, two_theta, d_spacing.

How should I handle coordinate system matching when overlaying GSAS-II data?
- Should I convert based on x-axis-selector value?
- Should I always use the GSAS-II coordinate system as-is?
- What happens if user switches x-axis while GSAS-II overlay is active?

Reference: services/gsasii_refinement/gsasii_worker.py header explains the Q vs 2θ issue.
```

### For testing:
```
I've implemented Phase 1+2. Can you help me create a manual testing checklist and validation script?

I need:
1. Step-by-step testing procedure
2. Expected outcomes at each step
3. How to verify data is flowing correctly through stores
4. How to check if traces are rendering properly
5. Common failure modes and how to diagnose them
```

---

## Quick Reference

### Key Files to Modify (in order)

**Phase 1:**
1. `src/robomage/dashboard/layouts/main_layout.py` - Add store
2. `src/robomage/dashboard/layouts/gsasii_tab.py` - Add button
3. `src/robomage/dashboard/callbacks/gsasii_callbacks.py` - Add callback

**Phase 2:**
1. `src/robomage/dashboard/layouts/main_layout.py` - Add checkbox to Viz tab
2. `src/robomage/dashboard/callbacks/plotting.py` - Update plot callback

### Commands

```bash
# Start all services
pixi run start-all

# Run dashboard only
python -m robomage.dashboard

# Test GSAS-II integration
python test_gsasii_refinement.py

# Run full test suite
pixi run test

# Check for errors
pixi run lint
```

### Test Data Location
- **LaB6 CHI file**: `test_data/LaB6_SRM660c.chi`
- **CIF file**: `test_data/LaB6.cif`
- **Instrument params**: `test_data/PDF_1m.instprm`

### Expected Results
- **Rwp**: ~7.7%
- **Cell a**: ~4.157 Å (±0.000027)
- **Execution time**: 3-5 seconds
- **Data points**: 4096 (Q range 0.647-15.867 Å⁻¹)

---

## Success Criteria Checklist

After implementation, verify:

- [ ] gsasii-viz-data-store exists in main_layout.py
- [ ] "Send to Visualization" button appears in GSAS-II tab
- [ ] Button is disabled until refinement completes
- [ ] Button enables when refinement succeeds
- [ ] Clicking button populates gsasii-viz-data-store
- [ ] Visualization tab has "Show GSAS-II Overlay" checkbox
- [ ] Enabling checkbox displays 3 traces
- [ ] Calculated pattern is red solid line
- [ ] Observed data is blue markers
- [ ] Difference curve is green line (offset below)
- [ ] Metadata annotation shows Rwp and cell_a
- [ ] Hover tooltips work on all traces
- [ ] Toggle checkbox on/off works smoothly
- [ ] No errors in browser console
- [ ] No errors in terminal logs
- [ ] test_gsasii_refinement.py still passes

---

## Estimated Timeline

- **Phase 1 Implementation**: 1.5-2 hours
- **Phase 1 Testing**: 30 minutes
- **Phase 2 Implementation**: 1.5-2 hours  
- **Phase 2 Testing**: 30 minutes
- **Documentation**: 15 minutes

**Total**: 4-6 hours

---

## Notes

- This is **NOT** about creating the GSAS-II tab (already exists)
- This is **NOT** about fixing the GSAS-II service (already working)
- This **IS** about connecting existing GSAS-II results to existing Visualization tab
- Focus on clean, maintainable code following existing patterns
- Use existing dcc.Store pattern (like analysis-results-store)
- Don't break existing visualization features
- Test incrementally (Phase 1, then Phase 2)
