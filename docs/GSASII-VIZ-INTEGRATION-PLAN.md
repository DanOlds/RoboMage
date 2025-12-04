# GSAS-II ↔ Visualization Tab Integration Plan

**Created**: December 3, 2025  
**Purpose**: Enable GSAS-II refinement results (calculated patterns, fits, residuals) to be visualized in the main Visualization tab  
**Estimated Effort**: 4-6 hours  
**Complexity**: Medium

---

## Overview

Currently, GSAS-II refinements are performed in the "⚛️ GSAS-II Refinement" tab with results displayed in that tab only. This plan enables users to:

1. **Send GSAS-II results to Visualization tab** for better comparison with raw data
2. **Overlay calculated patterns** on observed data
3. **Plot fit residuals** to assess refinement quality
4. **Compare multiple refinements** side-by-side
5. **Export refined data** for publication

---

## Architecture

### Current State

**GSAS-II Tab**:
- Stores results in `gsasii-refinement-result` dcc.Store (local to GSAS-II tab)
- Displays static plot image from GSAS-II (PNG base64)
- Shows cell parameters and fit quality in cards

**Visualization Tab**:
- Reads from `file-data-store` (raw uploaded files)
- Reads from `analysis-results-store` (peak analysis from Analysis tab)
- Uses `plotting.py` callbacks to generate interactive plots

**Gap**: No communication between GSAS-II tab and Visualization tab

### Proposed Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GSAS-II Tab                              │
│                                                             │
│  User performs refinement                                   │
│         ↓                                                   │
│  Results stored in gsasii-refinement-result                 │
│         ↓                                                   │
│  [Send to Viz] button clicked                              │
│         ↓                                                   │
│  Callback extracts fit_profile + metadata                  │
│         ↓                                                   │
│  Updates gsasii-viz-data-store (NEW)                       │
└─────────────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│              gsasii-viz-data-store (NEW)                    │
│                                                             │
│  Structure:                                                 │
│  {                                                          │
│    "sample_name": "LaB6_test",                             │
│    "calculated": {                                          │
│      "two_theta": [...],  # or Q                           │
│      "intensity": [...]   # Calculated pattern             │
│    },                                                       │
│    "observed": {                                            │
│      "two_theta": [...],                                   │
│      "intensity": [...]   # Input data                     │
│    },                                                       │
│    "difference": {                                          │
│      "two_theta": [...],                                   │
│      "intensity": [...]   # Observed - Calculated          │
│    },                                                       │
│    "metadata": {                                            │
│      "Rwp": 7.69,                                          │
│      "cell_a": 4.157,                                      │
│      "refinement_date": "2025-12-03T17:36:00",            │
│      "phase_name": "LaB6",                                 │
│      "wavelength": 0.1665                                  │
│    }                                                        │
│  }                                                          │
└─────────────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│                 Visualization Tab                           │
│                                                             │
│  Updated plotting callback reads gsasii-viz-data-store     │
│         ↓                                                   │
│  Adds traces for:                                          │
│    • Calculated pattern (solid line)                       │
│    • Observed data (scatter/line)                          │
│    • Difference curve (bottom panel or offset)             │
│         ↓                                                   │
│  User can:                                                  │
│    • Toggle GSAS-II data on/off                            │
│    • Compare with other files                              │
│    • Export combined plot                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Data Bridge (2 hours)

**Files to Create/Modify:**

1. **Add dcc.Store to main_layout.py** (~5 lines)
   ```python
   dcc.Store(id="gsasii-viz-data-store"),  # GSAS-II results for visualization
   ```

2. **Add "Send to Visualization" button in gsasii_tab.py** (~20 lines)
   ```python
   dbc.Button(
       "📊 Send to Visualization",
       id="gsasii-send-to-viz-button",
       color="primary",
       outline=True,
       disabled=True,  # Enabled when results available
   )
   ```

3. **Create callback in gsasii_callbacks.py** (~60 lines)
   ```python
   @callback(
       Output("gsasii-viz-data-store", "data"),
       Output("gsasii-send-to-viz-button", "disabled"),
       Input("gsasii-send-to-viz-button", "n_clicks"),
       State("gsasii-refinement-result", "data"),
       State("gsasii-chi-data-store", "data"),
       prevent_initial_call=True
   )
   def send_gsasii_to_viz(n_clicks, refinement_result, chi_data):
       """
       Extract fit profile from GSAS-II results and format for visualization.
       
       Transforms:
       - refinement_result["fit_profile"] → calculated pattern
       - chi_data → observed pattern
       - Calculate difference curve
       """
       if not refinement_result or not chi_data:
           return no_update, True
       
       # Extract data
       fit_profile = refinement_result["fit_profile"]
       fit_quality = refinement_result["fit_quality"]
       cell = refinement_result["cell"]
       
       # Build viz data structure
       viz_data = {
           "sample_name": chi_data.get("filename", "GSAS-II Refinement"),
           "calculated": {
               "two_theta": fit_profile["two_theta"],
               "intensity": fit_profile["calculated"]
           },
           "observed": {
               "two_theta": fit_profile["two_theta"],
               "intensity": fit_profile["observed"]
           },
           "difference": {
               "two_theta": fit_profile["two_theta"],
               "intensity": [obs - calc for obs, calc in zip(
                   fit_profile["observed"],
                   fit_profile["calculated"]
               )]
           },
           "metadata": {
               "Rwp": fit_quality["Rwp"],
               "cell_a": cell["a"]["value"],
               "cell_a_esd": cell["a"]["esd"],
               "timestamp": datetime.now().isoformat(),
               "phase_name": refinement_result.get("phase_name", "Unknown")
           }
       }
       
       return viz_data, False  # Enable button
   ```

4. **Enable button when results exist** (~15 lines)
   Update `run_refinement` callback to return button state:
   ```python
   # At end of run_refinement callback
   return (results_display, result, False, False, "", 
           request_payload, response_data, False)  # button_disabled=False
   ```

### Phase 2: Visualization Integration (2 hours)

**Files to Modify:**

1. **Update plotting.py callback** (~80 lines)
   
   Modify `register_main_plot_callback()` to:
   - Add `Input("gsasii-viz-data-store", "data")` to inputs
   - Add checkbox to enable/disable GSAS-II overlay
   - Add traces for calculated, observed, and difference curves
   
   ```python
   @app.callback(
       Output("main-plot", "figure"),
       [
           Input("file-data-store", "data"),
           Input("wavelength-store", "data"),
           Input("x-axis-selector", "value"),
           Input("y-axis-selector", "value"),
           Input("plot-type-selector", "value"),
           Input("analysis-results-store", "data"),
           Input("gsasii-viz-data-store", "data"),  # NEW
           Input("show-gsasii-overlay", "value"),   # NEW checkbox
       ],
   )
   def update_main_plot(file_data, wavelength_data, x_axis, y_axis, 
                        plot_type, analysis_results, gsasii_data, show_gsasii):
       """
       Update plot with optional GSAS-II refinement overlay.
       """
       fig = go.Figure()
       
       # Plot regular files (existing code)
       # ... existing code ...
       
       # Add GSAS-II overlay if enabled and data exists
       if show_gsasii and gsasii_data:
           # Calculated pattern (solid line)
           fig.add_trace(go.Scatter(
               x=gsasii_data["calculated"]["two_theta"],
               y=gsasii_data["calculated"]["intensity"],
               mode="lines",
               name=f"{gsasii_data['sample_name']} (Calculated)",
               line=dict(color="red", width=2, dash="solid"),
               hovertemplate="<b>Calculated</b><br>2θ: %{x:.3f}<br>I: %{y:.0f}<extra></extra>"
           ))
           
           # Observed pattern (markers)
           fig.add_trace(go.Scatter(
               x=gsasii_data["observed"]["two_theta"],
               y=gsasii_data["observed"]["intensity"],
               mode="markers",
               name=f"{gsasii_data['sample_name']} (Observed)",
               marker=dict(color="blue", size=3, opacity=0.6),
               hovertemplate="<b>Observed</b><br>2θ: %{x:.3f}<br>I: %{y:.0f}<extra></extra>"
           ))
           
           # Difference curve (offset below)
           y_min = min(gsasii_data["difference"]["intensity"])
           offset = abs(y_min) * 1.2  # Offset to bottom
           fig.add_trace(go.Scatter(
               x=gsasii_data["difference"]["two_theta"],
               y=[y - offset for y in gsasii_data["difference"]["intensity"]],
               mode="lines",
               name="Difference (Obs - Calc)",
               line=dict(color="green", width=1),
               hovertemplate="<b>Difference</b><br>2θ: %{x:.3f}<br>ΔI: %{y:.0f}<extra></extra>"
           ))
           
           # Add metadata annotation
           fig.add_annotation(
               text=f"Rwp: {gsasii_data['metadata']['Rwp']:.2f}%<br>"
                    f"Cell a: {gsasii_data['metadata']['cell_a']:.4f} Å",
               xref="paper", yref="paper",
               x=0.98, y=0.98,
               showarrow=False,
               bgcolor="rgba(255,255,255,0.8)",
               bordercolor="red",
               borderwidth=1
           )
       
       return fig
   ```

2. **Add UI controls to visualization tab** (~30 lines)
   
   In `main_layout.py` Visualization tab section:
   ```python
   # Add checkbox for GSAS-II overlay
   dbc.Row([
       dbc.Col([
           dbc.Checklist(
               options=[
                   {"label": "Show GSAS-II Refinement Overlay", "value": "show"}
               ],
               value=[],
               id="show-gsasii-overlay",
               switch=True
           )
       ])
   ])
   
   # Add GSAS-II metadata display
   html.Div(id="gsasii-overlay-info")
   ```

3. **Create metadata display callback** (~40 lines)
   ```python
   @callback(
       Output("gsasii-overlay-info", "children"),
       Input("gsasii-viz-data-store", "data")
   )
   def update_gsasii_info(gsasii_data):
       """Display GSAS-II refinement metadata in viz tab."""
       if not gsasii_data:
           return html.Div()
       
       metadata = gsasii_data["metadata"]
       return dbc.Card([
           dbc.CardHeader("GSAS-II Refinement Info"),
           dbc.CardBody([
               html.P([
                   html.Strong("Sample: "),
                   gsasii_data["sample_name"]
               ]),
               html.P([
                   html.Strong("Rwp: "),
                   f"{metadata['Rwp']:.2f}%"
               ]),
               html.P([
                   html.Strong("Cell a: "),
                   f"{metadata['cell_a']:.6f} ± {metadata['cell_a_esd']:.6f} Å"
               ]),
               html.P([
                   html.Strong("Phase: "),
                   metadata['phase_name']
               ])
           ])
       ], className="mt-2")
   ```

### Phase 3: Enhanced Features (2 hours)

**Optional enhancements:**

1. **Multiple refinement comparison** (~45 min)
   - Store list of refinements instead of single result
   - Allow user to select which refinement to display
   - Color-code different refinements

2. **Export functionality** (~30 min)
   - Add "Export GSAS-II Data" button
   - Download CSV with observed, calculated, difference columns
   - Include metadata in header

3. **Residual plot panel** (~45 min)
   - Create subplot layout with main plot + residual panel
   - Automatic scaling of residual panel
   - Zoom synchronization between panels

---

## Data Flow Diagram

```
User performs refinement
        ↓
GSAS-II service returns:
  • fit_profile: {two_theta, observed, calculated, background}
  • fit_quality: {Rwp, chi2, GoF}
  • cell: {a, b, c, alpha, beta, gamma, volume}
        ↓
gsasii-refinement-result store updated
        ↓
User clicks "Send to Visualization"
        ↓
Callback extracts and transforms:
  • calculated pattern from fit_profile
  • observed pattern from fit_profile or chi_data
  • difference = observed - calculated
  • metadata (Rwp, cell params, timestamp)
        ↓
gsasii-viz-data-store updated
        ↓
Visualization tab callback triggered
        ↓
If show-gsasii-overlay enabled:
  • Add calculated trace (red solid line)
  • Add observed trace (blue markers)
  • Add difference trace (green line, offset)
  • Add metadata annotation
        ↓
User sees:
  • Raw data from files
  • GSAS-II calculated pattern overlay
  • Difference curve
  • Fit quality metrics
```

---

## Benefits

1. **Better Quality Assessment**
   - Visual comparison of fit quality
   - Residuals show systematic errors
   - Easy to spot bad refinements

2. **Publication-Ready Figures**
   - Interactive Plotly plots can be exported
   - Professional appearance with annotations
   - Customizable styling

3. **Workflow Efficiency**
   - No need to switch between tabs
   - Compare multiple refinements
   - Quick iteration on refinement parameters

4. **Data Reusability**
   - GSAS-II results stored in session
   - Can be re-plotted without re-running refinement
   - Export for external analysis

---

## Testing Strategy

### Unit Tests

1. **Data transformation test**
   ```python
   def test_gsasii_to_viz_transformation():
       """Test GSAS-II result → viz data transformation."""
       mock_result = {...}  # Sample GSAS-II result
       viz_data = transform_gsasii_for_viz(mock_result)
       assert "calculated" in viz_data
       assert "observed" in viz_data
       assert "difference" in viz_data
       assert len(viz_data["difference"]["intensity"]) == len(
           viz_data["observed"]["intensity"]
       )
   ```

2. **Difference calculation test**
   ```python
   def test_difference_curve():
       """Test residual calculation."""
       observed = [100, 200, 150]
       calculated = [95, 205, 148]
       expected_diff = [5, -5, 2]
       
       diff = calculate_difference(observed, calculated)
       assert diff == expected_diff
   ```

### Integration Tests

1. **End-to-end workflow**
   - Perform refinement
   - Click "Send to Visualization"
   - Verify data appears in viz tab
   - Check plot has correct traces

2. **Multi-refinement scenario**
   - Run refinement twice with different parameters
   - Verify both results can be displayed
   - Check color coding and labels

### Manual Testing Checklist

- [ ] GSAS-II refinement completes successfully
- [ ] "Send to Visualization" button enables after refinement
- [ ] Clicking button updates viz tab store
- [ ] Switching to Visualization tab shows overlay checkbox
- [ ] Enabling checkbox displays GSAS-II traces
- [ ] Calculated pattern matches GSAS-II plot image
- [ ] Difference curve is reasonable (near zero for good fit)
- [ ] Metadata annotation shows correct values
- [ ] Hover tooltips work on all traces
- [ ] Can toggle overlay on/off smoothly
- [ ] Export functionality works (if implemented)

---

## File Checklist

### Files to Create
- [ ] None (all modifications to existing files)

### Files to Modify

1. **Layout Files**
   - [ ] `src/robomage/dashboard/layouts/main_layout.py`
     - Add `gsasii-viz-data-store`
     - Add GSAS-II overlay controls to Visualization tab
   
   - [ ] `src/robomage/dashboard/layouts/gsasii_tab.py`
     - Add "Send to Visualization" button
     - Add button placement in results section

2. **Callback Files**
   - [ ] `src/robomage/dashboard/callbacks/gsasii_callbacks.py`
     - Add `send_gsasii_to_viz` callback
     - Update `run_refinement` to control button state
   
   - [ ] `src/robomage/dashboard/callbacks/plotting.py`
     - Update `register_main_plot_callback` to handle GSAS-II data
     - Add GSAS-II trace rendering logic
     - Add difference curve logic

3. **Documentation**
   - [ ] Update `README.md` with GSAS-II viz integration
   - [ ] Update `docs/GSASII-TAB-SUMMARY.md` with new feature

---

## Alternative Approaches Considered

### Approach 1: Auto-send to Viz (Rejected)
**Idea**: Automatically send every refinement result to viz tab

**Pros**: No button click needed, immediate feedback

**Cons**: 
- Unexpected behavior (plot changes when not looking)
- Can't control which refinements to visualize
- Clutters viz tab

**Decision**: Manual button gives user control

### Approach 2: Separate GSAS-II Viz Tab (Rejected)
**Idea**: Create dedicated tab for GSAS-II visualization

**Pros**: Clean separation, specialized features

**Cons**:
- Duplicate plotting code
- Can't compare GSAS-II with other data
- Extra complexity

**Decision**: Integrate into existing Visualization tab

### Approach 3: Workflow-based Integration (Considered for Phase 4)
**Idea**: Use workflow nodes to pass GSAS-II results to viz

**Pros**: Fits existing workflow architecture

**Cons**:
- Overkill for simple viz needs
- More complex for users

**Decision**: Implement simple button first, workflow integration later

---

## Future Enhancements

1. **Multi-pattern Fitting**
   - Sequential refinements visualization
   - Animation of parameter evolution
   - Convergence plots

2. **Advanced Residual Analysis**
   - Autocorrelation of residuals
   - Statistical tests (runs test, Durbin-Watson)
   - Residual distribution histogram

3. **Peak Marker Integration**
   - Show Miller indices on calculated pattern
   - Color-code peaks by phase (if multi-phase)
   - Click peak to see hkl info

4. **Rietveld Plot Templates**
   - Match GSAS-II publication style
   - Customizable tick marks
   - Background subtraction view

5. **Session Integration**
   - Save GSAS-II viz data with session
   - Load previous refinements on session restore
   - Compare refinements across sessions

---

## Success Criteria

The integration is successful when:

1. ✅ User can perform GSAS-II refinement
2. ✅ User can send results to Visualization tab with one click
3. ✅ Visualization tab displays:
   - Calculated pattern (red line)
   - Observed data (blue markers)
   - Difference curve (green line)
   - Fit quality metrics (annotation)
4. ✅ Overlay can be toggled on/off
5. ✅ Plot is interactive (zoom, pan, hover)
6. ✅ No performance degradation with overlay enabled
7. ✅ All existing visualization features still work
8. ✅ Documentation is updated

---

## Resources Required

- **Developer Time**: 4-6 hours (Phase 1+2), 8-10 hours (with Phase 3)
- **Testing Time**: 1-2 hours
- **Documentation**: 30 minutes
- **Dependencies**: None (uses existing libraries)

---

## Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Data format mismatch | High | Low | Use GSAS-II output format exactly as returned |
| Performance with large data | Medium | Medium | Decimate data for plotting if >10k points |
| UI cluttering | Low | Medium | Collapsible overlay controls |
| Store size limits | Low | Low | Store only current refinement, not history |

---

## Timeline

**Phase 1**: 2 hours
- Day 1 Morning: Add store, button, basic callback

**Phase 2**: 2 hours  
- Day 1 Afternoon: Update plotting, add UI controls

**Phase 3** (optional): 2 hours
- Day 2: Enhanced features

**Testing & Documentation**: 1.5 hours
- Day 2: Comprehensive testing, update docs

**Total**: 5.5-7.5 hours over 1-2 days

---

## Conclusion

This integration provides significant value with moderate implementation effort. The architecture is clean, maintainable, and extensible. By reusing existing stores and callbacks, we minimize code duplication while providing powerful new visualization capabilities.

The phased approach allows for incremental delivery:
- Phase 1 provides basic functionality
- Phase 2 makes it user-friendly
- Phase 3 adds polish

**Recommendation**: Proceed with Phases 1+2 immediately (4 hours), evaluate Phase 3 based on user feedback.
