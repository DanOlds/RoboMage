# Dual Interface Proposal: Visual Canvas + JSON Editor

**Date**: December 2, 2025  
**Status**: Proposal  
**Effort Estimate**: 1-2 days

## Overview

Add optional JSON editor alongside the visual workflow canvas, allowing users to:
- **Beginners**: Use visual drag-and-drop interface
- **Power users**: Edit JSON directly for complex workflows
- **Hybrid users**: Switch between both as needed

## Current State

The system **already has perfect bidirectional conversion**:

```python
# JSON ↔ Visual conversion exists
renderer = WorkflowCanvasFactory.create("cytoscape")
elements = renderer.workflow_to_elements(workflow_json)  # JSON → Visual
workflow_json = renderer.elements_to_workflow(elements)  # Visual → JSON
```

All workflows are stored as JSON in `current-workflow-data` dcc.Store, so both interfaces would share the same source of truth.

## Proposed Implementation

### Option A: Collapsible JSON Panel (Recommended)

**Why**: 
- Non-intrusive (hidden by default)
- Preserves current UI layout
- Easy to implement
- Best for power users who occasionally need JSON access

**Layout**:
```
┌─────────────┬──────────────────────┬─────────────────┐
│  Node       │   Workflow Canvas    │   Properties    │
│  Palette    │                      │   Panel         │
│             │  [Show/Hide JSON] ←──┤                 │
│             │   ┌──────────────┐  │                 │
│             │   │ Visual Canvas │  │                 │
│             │   └──────────────┘  │                 │
│             │                      │                 │
│             │  ┌──────────────┐   │                 │
│             │  │ JSON Editor   │   │                 │
│             │  │ (collapsible) │   │                 │
│             │  └──────────────┘   │                 │
└─────────────┴──────────────────────┴─────────────────┘
```

**Changes Required**:

1. **Layout Update** (`workflow_layout.py`):
```python
# Add toggle button to canvas controls
dbc.Button(
    [
        html.I(className="fas fa-code me-1"),
        html.Span(id="json-toggle-text", children="Show JSON")
    ],
    id="toggle-json-editor-btn",
    color="secondary",
    size="sm",
    outline=True,
)

# Add collapsible JSON editor below canvas
dbc.Collapse(
    dbc.Card([
        dbc.CardHeader([
            html.H6([
                html.I(className="fas fa-code me-2"),
                "JSON Editor",
                dbc.Badge(
                    "Advanced",
                    color="warning",
                    className="ms-2"
                )
            ])
        ]),
        dbc.CardBody([
            dcc.Textarea(
                id="workflow-json-editor",
                placeholder="Workflow JSON...",
                style={
                    "width": "100%",
                    "height": "400px",
                    "font-family": "Consolas, Monaco, monospace",
                    "font-size": "12px",
                },
            ),
            dbc.Row([
                dbc.Col([
                    html.Div(id="json-validation-feedback")
                ]),
                dbc.Col([
                    dbc.Button(
                        [html.I(className="fas fa-sync me-1"), "Apply JSON"],
                        id="apply-json-btn",
                        color="primary",
                        size="sm",
                        className="float-end"
                    )
                ], width="auto")
            ], className="mt-2")
        ])
    ], className="mt-2"),
    id="json-editor-collapse",
    is_open=False
)
```

2. **New Callbacks** (`workflow.py`):

```python
@app.callback(
    Output("json-editor-collapse", "is_open"),
    Output("json-toggle-text", "children"),
    Input("toggle-json-editor-btn", "n_clicks"),
    State("json-editor-collapse", "is_open"),
    prevent_initial_call=True,
)
def toggle_json_editor(n_clicks, is_open):
    """Toggle JSON editor visibility."""
    new_state = not is_open
    button_text = "Hide JSON" if new_state else "Show JSON"
    return new_state, button_text


@app.callback(
    Output("workflow-json-editor", "value"),
    Input("current-workflow-data", "data"),
    prevent_initial_call=False,
)
def sync_json_from_workflow(workflow_data):
    """Update JSON editor when workflow changes (via canvas)."""
    if not workflow_data:
        return ""
    return json.dumps(workflow_data, indent=2)


@app.callback(
    Output("current-workflow-data", "data", allow_duplicate=True),
    Output("json-validation-feedback", "children"),
    Input("apply-json-btn", "n_clicks"),
    State("workflow-json-editor", "value"),
    prevent_initial_call=True,
)
def apply_json_to_workflow(n_clicks, json_text):
    """Apply manually edited JSON to workflow (updates canvas)."""
    if not json_text:
        return no_update, dbc.Alert("JSON is empty", color="warning")
    
    try:
        # Parse JSON
        workflow = json.loads(json_text)
        
        # Validate structure
        if "nodes" not in workflow or "edges" not in workflow:
            return no_update, dbc.Alert(
                "Invalid workflow: must have 'nodes' and 'edges' keys",
                color="danger"
            )
        
        # Validate using WorkflowValidator
        from robomage.dashboard.components import WorkflowValidator
        validator = WorkflowValidator()
        is_valid, errors = validator.validate(workflow)
        
        if not is_valid:
            error_msg = "\\n".join([f"• {err}" for err in errors])
            return no_update, dbc.Alert(
                [html.Strong("Validation errors:"), html.Br(), error_msg],
                color="danger"
            )
        
        # Success - update workflow (this will auto-sync to canvas)
        return workflow, dbc.Alert(
            [html.I(className="fas fa-check-circle me-2"), "JSON applied successfully"],
            color="success",
            duration=3000
        )
        
    except json.JSONDecodeError as e:
        return no_update, dbc.Alert(
            f"Invalid JSON syntax: {str(e)}",
            color="danger"
        )
```

3. **Tests** (`test_dashboard_workflow.py`):

```python
def test_json_editor_toggle():
    """Test JSON editor show/hide."""
    # ... test toggle button functionality


def test_json_sync_from_canvas():
    """Test JSON editor updates when canvas changes."""
    # ... test that adding node to canvas updates JSON


def test_json_apply_to_canvas():
    """Test canvas updates when JSON is manually edited."""
    # ... test that editing JSON updates canvas
    

def test_json_validation():
    """Test that invalid JSON shows error message."""
    # ... test validation feedback
```

---

### Option B: Tabbed Interface (Alternative)

**Why**:
- Clean separation between visual and text modes
- More screen real estate for JSON editor
- Familiar pattern (many tools use this)

**Layout**:
```
┌─────────────┬──────────────────────┬─────────────────┐
│  Node       │  [Visual] [JSON] ←Tabs│   Properties   │
│  Palette    │                      │   Panel         │
│             │  ┌──────────────┐   │                 │
│             │  │               │   │                 │
│             │  │  Active Tab   │   │                 │
│             │  │  Content      │   │                 │
│             │  │               │   │                 │
│             │  └──────────────┘   │                 │
└─────────────┴──────────────────────┴─────────────────┘
```

**Changes Required**:

```python
# In workflow_layout.py
dbc.Tabs([
    dbc.Tab(
        # Current canvas UI
        label="Visual Canvas",
        tab_id="visual-tab",
        children=[...]
    ),
    dbc.Tab(
        # JSON editor UI
        label="JSON Editor",
        tab_id="json-tab",
        children=[
            dcc.Textarea(id="workflow-json-editor", ...),
            # Apply/Reset buttons
        ]
    )
], id="workflow-interface-tabs", active_tab="visual-tab")
```

---

## Comparison

| Feature | Option A (Collapsible) | Option B (Tabs) |
|---------|----------------------|-----------------|
| **Effort** | 1 day | 1-2 days |
| **UI Disruption** | Minimal | Moderate |
| **Screen Space** | Both visible at once | One at a time |
| **Best For** | Occasional JSON access | Frequent mode switching |
| **Discovery** | Requires button click | More visible |

---

## Recommendation

**Start with Option A (Collapsible JSON Panel)**

**Rationale**:
1. **Lower risk** - Doesn't change core UI flow
2. **Faster** - Simpler implementation
3. **Better UX** - Can see both at once for verification
4. **Progressive enhancement** - Can add Option B later if needed

**Future Enhancement** (Option C - Week 2+):
- Add "Import from JSON" button to load external workflow files
- Add "Export JSON" button to download workflow as `.json` file
- Add JSON schema validation with inline error markers
- Add JSON syntax highlighting (using CodeMirror or Monaco editor)

---

## Implementation Steps

### Day 1: Core Functionality
- [ ] Add toggle button and collapsible panel to layout
- [ ] Implement `sync_json_from_workflow` callback
- [ ] Implement `apply_json_to_workflow` callback with validation
- [ ] Add basic tests

### Day 2: Polish & Testing
- [ ] Add syntax highlighting (optional - CodeMirror integration)
- [ ] Add import/export buttons
- [ ] Comprehensive testing (10+ test cases)
- [ ] Update user documentation

---

## Code Locations

**Files to modify**:
1. `src/robomage/dashboard/layouts/workflow_layout.py` (~50 lines added)
2. `src/robomage/dashboard/callbacks/workflow.py` (~100 lines added)
3. `tests/test_dashboard_workflow.py` (~80 lines added)

**Files to reference** (no changes needed):
- `src/robomage/dashboard/components/workflow_canvas.py` (conversion methods)
- `src/robomage/dashboard/components/cytoscape_renderer.py` (JSON ↔ elements)

---

## Risk Assessment

**Low Risk** ✅

- **No breaking changes** - Adds optional feature
- **Existing sync logic** - Already tested and working
- **Validation in place** - WorkflowValidator prevents bad workflows
- **Rollback easy** - Just hide the new UI elements

---

## Success Criteria

- [ ] User can toggle JSON editor on/off
- [ ] JSON editor shows current workflow in real-time
- [ ] Editing JSON updates canvas immediately (after Apply)
- [ ] Invalid JSON shows clear error messages
- [ ] All existing tests still pass
- [ ] 10+ new tests covering JSON editor functionality
- [ ] Documentation updated with JSON editor usage

---

## Documentation Updates

**Files to update**:
1. `docs/visual-workflow-builder-guide.md` - Add "Advanced: JSON Editing" section
2. `README.md` - Mention dual interface capability
3. `docs/SPRINT-8-COMPLETION.md` - Add post-sprint enhancement note

**New section for guide**:
```markdown
## Advanced: Direct JSON Editing

For power users, RoboMage provides direct access to the workflow JSON:

1. Click **"Show JSON"** button below the canvas
2. Edit the JSON directly (with validation)
3. Click **"Apply JSON"** to update the canvas
4. Invalid JSON will show error messages with hints

### Example JSON Structure
\`\`\`json
{
  "name": "My Workflow",
  "nodes": [...],
  "edges": [...]
}
\`\`\`

### Use Cases
- **Copy/paste** workflows from documentation
- **Bulk operations** - Faster than UI for many nodes
- **Version control** - Save workflows to `.json` files
- **Debugging** - Inspect exact workflow structure
```

---

## Future Enhancements (Post-Implementation)

**Phase 2** (Week 2-3):
- JSON schema validation with inline errors (Monaco Editor)
- Diff view when loading workflows
- JSON templates library

**Phase 3** (Month 2):
- Export workflow as standalone Python script
- Import workflows from external tools (GSAS-II, etc.)
- Workflow version control integration

---

## Questions for Stakeholder

1. **Primary Use Case**: 
   - Who would use JSON editor? (Debugging? Advanced users? Documentation?)
   
2. **Default State**: 
   - Hidden by default? Or visible by default?
   
3. **Syntax Highlighting**: 
   - Basic textarea (1 day) or rich editor like Monaco (2 days)?
   
4. **Import/Export**: 
   - High priority or can wait for Phase 2?

---

## Conclusion

**The visual canvas DOES directly correspond to JSON**, and adding a JSON editor interface would be:
- ✅ **Straightforward** (1-2 days)
- ✅ **Low risk** (non-breaking addition)
- ✅ **High value** (serves both beginners and power users)
- ✅ **Well-architected** (already has bidirectional sync)

The existing abstraction layer makes this trivial - just add UI components and wire up the existing conversion methods!
