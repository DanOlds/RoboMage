# GSAS-II Dashboard Tab - New Chat Handoff

**Date**: December 3, 2025  
**Context**: Phase 3 (subprocess worker) complete, now adding dedicated GSAS-II refinement tab

---

## What to Tell the New Chat

```
I want to add a dedicated GSAS-II Refinement tab to the RoboMage dashboard for 
testing and development. The tab should provide a standalone interface for running 
GSAS-II Rietveld refinements without using the workflow builder.

PROJECT CONTEXT:
- RoboMage is a powder diffraction analysis framework with a Dash-based dashboard
- GSAS-II service is already running and validated (Phase 3 complete)
- Service URL: http://localhost:8003
- Service auto-starts with `pixi run start-all`

REQUIREMENTS:
1. File Selection:
   - Upload or select CHI/XY diffraction data file
   - Select CIF structure file (dropdown from assets or upload)
   - Select instrument parameter file (dropdown from assets)
   - Input phase name

2. Refinement Configuration:
   - Cycles slider (0-20, default 5)
   - Checkboxes for refinement flags:
     * Refine background
     * Refine cell parameters
     * Refine size/strain
   - Optional: Advanced recipe YAML/JSON editor

3. Results Display:
   - Cell parameters table with ESDs
   - Fit quality metrics (Rwp, chi², GoF)
   - Interactive Plotly plot (observed, calculated, difference)
   - Download buttons (GPX file, plot image, results table)

4. Service Integration:
   - Health check indicator
   - Progress spinner during refinement
   - Error display with helpful messages

REFERENCE IMPLEMENTATION:
- Existing Analysis tab (src/robomage/dashboard/layouts/analysis_tab.py)
  - Has parameter controls, "Run Analysis" button, results table
  - Clone this pattern for GSAS-II
- Data Import tab for file upload patterns
- Visualization tab for plotting patterns

KEY FILES:
- Service client: src/robomage/clients/gsasii_client.GSASIIClient
- Assets directory: services/gsasii_refinement/assets/
  - cifs/LaB6_SRM_660c.CIF (example CIF)
  - instruments/PDF_1m.instprm (example instrument params)
- Service docs: docs/GSASII-PHASE-3-SUBPROCESS-COMPLETE.md
- Test data: /nsls2/users/dolds/dev/autoxrd/fit_service/notebook_testing/assets/*.chi

TECHNICAL DETAILS:
- Dashboard framework: Dash with Bootstrap components
- Tab structure: src/robomage/dashboard/layouts/
- Callbacks: src/robomage/dashboard/callbacks/
- Service: Port 8003, FastAPI with OpenAPI docs at /docs
- Response model: RefinementResult with cell, fit_quality, fit_profile, plot_image

VALIDATION:
- LaB6 test: Rwp ≈ 7.7%, cell a ≈ 4.157 Å, execution time ≈ 4.5s
- Plot format: Base64-encoded PNG returned in response
- Service health: GET http://localhost:8003/health

ESTIMATED EFFORT: 2-3 hours, ~300-400 lines of code

Please implement this tab following the existing dashboard patterns. Start by 
creating the layout, then add callbacks for service interaction and result display.
```

---

## Additional Context (If Needed)

### Service Client Usage

```python
from robomage.clients.gsasii_client import GSASIIClient

client = GSASIIClient("http://localhost:8003")

# Check service health
health = client.ping()

# Run refinement
result = client.refine(
    diffraction_data={
        "two_theta": [...],
        "intensity": [...],
        "filename": "sample.chi"
    },
    recipe={
        "instrument_file": "PDF_1m.instprm",
        "cif_file": "LaB6_SRM_660c.CIF",
        "phase_name": "LaB6",
        "refinement_dict": {
            "set": {
                "Limits": [0.5, 16.0],
                "Background": {"no. coeffs": 6, "refine": True},
                "Cell": True
            },
            "do": "refine"
        }
    },
    sample_name="test",
    cycles=5,
    options={"generate_plot": True}
)

# Access results
cell_a = result["cell"]["a"]["value"]
rwp = result["fit_quality"]["Rwp"]
plot_base64 = result["plot_image"]
```

### Dashboard Tab Structure

```python
# Layout structure (in src/robomage/dashboard/layouts/gsasii_tab.py)
def create_gsasii_tab():
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                # File selection section
                html.H4("Data Files"),
                dcc.Upload(...),
                dcc.Dropdown(id="cif-select", ...),
                dcc.Dropdown(id="inst-select", ...),
            ], width=4),
            dbc.Col([
                # Configuration section
                html.H4("Refinement Settings"),
                dcc.Slider(id="cycles", ...),
                dbc.Checklist(id="refine-flags", ...),
            ], width=4),
            dbc.Col([
                # Service status
                html.H4("Service Status"),
                html.Div(id="service-status"),
            ], width=4),
        ]),
        dbc.Row([
            dbc.Button("Run Refinement", id="run-refine-btn"),
            dbc.Spinner(id="refine-spinner"),
        ]),
        dbc.Row([
            dbc.Col([
                # Results table
                html.H4("Results"),
                html.Div(id="results-table"),
            ], width=6),
            dbc.Col([
                # Plot
                dcc.Graph(id="refine-plot"),
            ], width=6),
        ]),
    ])
```

### Callback Pattern

```python
# In src/robomage/dashboard/callbacks/gsasii_callbacks.py
@callback(
    Output("results-table", "children"),
    Output("refine-plot", "figure"),
    Input("run-refine-btn", "n_clicks"),
    State("chi-file-upload", "contents"),
    State("cif-select", "value"),
    State("inst-select", "value"),
    State("cycles", "value"),
    State("refine-flags", "value"),
)
def run_refinement(n_clicks, chi_data, cif, inst, cycles, flags):
    if not n_clicks:
        raise PreventUpdate
    
    # Call service
    client = GSASIIClient("http://localhost:8003")
    result = client.refine(...)
    
    # Parse results
    table = create_results_table(result)
    fig = create_refinement_plot(result)
    
    return table, fig
```

---

## Success Criteria

✅ Tab appears in dashboard alongside Data Import, Visualization, Analysis, Workflow Builder  
✅ Can upload CHI file or select from examples  
✅ Can select CIF and instrument files from assets  
✅ Can configure refinement parameters (cycles, flags)  
✅ "Run Refinement" button calls GSAS-II service  
✅ Results display cell parameters with ESDs  
✅ Results display fit quality metrics  
✅ Interactive plot shows observed, calculated, difference  
✅ Service health indicator shows status  
✅ Error messages display clearly  

---

## Files to Create

1. `src/robomage/dashboard/layouts/gsasii_tab.py` (~150 lines)
2. `src/robomage/dashboard/callbacks/gsasii_callbacks.py` (~150 lines)
3. Update `src/robomage/dashboard/app.py` to register tab (~10 lines)

---

## Testing Plan

1. Start services: `pixi run start-all`
2. Open dashboard: http://localhost:8050
3. Navigate to GSAS-II tab
4. Upload test file: `xrd_LaB6_660c_std_brac2_20250724-194924_70c707_primary-1_mean_tth.chi`
5. Select: LaB6_SRM_660c.CIF, PDF_1m.instprm
6. Set cycles: 5
7. Enable: Refine background, Refine cell
8. Click "Run Refinement"
9. Verify: Rwp ≈ 7.7%, cell a ≈ 4.157 Å
10. Verify: Plot displays correctly

---

**Ready for New Chat!** 🚀
