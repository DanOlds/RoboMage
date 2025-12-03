# Service Inspector Debug Session Summary
**Date:** December 2, 2025  
**Status:** ✅ **FIXED** - Root cause identified and resolved

## Problem Statement

The Service Inspector tab in the RoboMage dashboard had a bug where clicking on discovered services did not display their details in the service detail panel. The panel continued to show "Select a service from the list to view details" even after clicking on a service.

## Root Cause ✅ IDENTIFIED

**The issue was a circular dependency in the callback definition.**

The `display_service_details` callback had a `State` dependency on `"service-detail-tabs"` `active_tab` property:

```python
@app.callback(
    [Output("service-detail-panel", "children"), ...],
    [Input("selected-service-id", "data"), ...],
    [State("service-detail-tabs", "active_tab")],  # ❌ PROBLEM!
)
```

However, the `service-detail-tabs` component is created **inside** `create_service_detail_panel()`, which is returned by this very callback. This means:

1. On page load, `service-detail-tabs` doesn't exist in the layout
2. Dash cannot resolve the State dependency during callback registration
3. The callback fails silently or doesn't trigger properly
4. The UI never updates

## The Fix ✅

### Part 1: Remove Circular Dependency

**Removed the circular State dependency:**

```python
@app.callback(
    [Output("service-detail-panel", "children"), ...],
    [Input("selected-service-id", "data"), ...],
    # Removed: State("service-detail-tabs", "active_tab")  ❌ Circular!
    [State("service-detail-active-tab", "data")],  # ✅ Use Store instead
)
def display_service_details(selected_id, service_data, active_tab_from_store):
    # Use stored tab value to preserve selection
    active_tab = active_tab_from_store if active_tab_from_store else "overview-tab"
    ...
```

### Part 2: Preserve Tab Selection Across Health Refreshes

**Problem:** Every 5 seconds, the health monitoring interval triggers a refresh of `service-inspector-data`, which causes `display_service_details` to re-fire and reset tabs to "overview-tab".

**Solution:** Add a `dcc.Store` component and callback to track tab changes:

1. **Added Store to layout** (`service_inspector_layout.py`):
   ```python
   dcc.Store(id="service-detail-active-tab", data="overview-tab"),
   ```

2. **Added callback to save tab changes** (`service_inspector.py`):
   ```python
   @app.callback(
       Output("service-detail-active-tab", "data"),
       Input("service-detail-tabs", "active_tab"),
       prevent_initial_call=True,
   )
   def save_active_tab(active_tab):
       """Save the active tab selection to preserve across health refreshes."""
       if active_tab:
           logger.info(f"📑 Tab changed to: {active_tab}")
           return active_tab
       raise PreventUpdate
   ```

3. **Use stored tab in display callback**:
   ```python
   active_tab = active_tab_from_store if active_tab_from_store else "overview-tab"
   ```

### Part 3: Preserve Accordion State Across Health Refreshes

**Problem:** When viewing API Docs tab, expanded accordion items (endpoints) would collapse after the 5-second health refresh, forcing users to re-expand them.

**Solution:** Similar pattern - Store + callback to track accordion state:

1. **Added Store to layout** (`service_inspector_layout.py`):
   ```python
   dcc.Store(id="api-docs-active-items", data=[]),
   ```

2. **Updated accordion component** (`service_detail_panel.py`):
   ```python
   # Give accordion an ID and use active_item prop
   dbc.Accordion(
       accordion_items, 
       id="api-docs-accordion",
       active_item=active_items,  # List of open item IDs
       always_open=True,  # Allow multiple items open
   )
   
   # Assign unique item_id to each AccordionItem
   item_id = f"{method}-{path}"  # e.g., "get-/health"
   dbc.AccordionItem(..., item_id=item_id)
   ```

3. **Added callback to save accordion state** (`service_inspector.py`):
   ```python
   @app.callback(
       Output("api-docs-active-items", "data"),
       Input("api-docs-accordion", "active_item"),
       prevent_initial_call=True,
   )
   def save_accordion_state(active_items):
       """Save active accordion items to preserve across health refreshes."""
       if active_items is not None:
           logger.info(f"📂 Accordion items changed to: {active_items}")
           return active_items if isinstance(active_items, list) else [active_items]
       return []
   ```

4. **Pass stored state to panel creation**:
   ```python
   detail_panel = create_service_detail_panel(
       service_data=metadata,
       health_data=health,
       openapi_schema=openapi_schema,
       active_tab=active_tab,
       active_accordion_items=active_accordion_items,  # ✅ Preserve state
   )
   ```

### Part 4: Preserve Test Console Responses Across Health Refreshes

**Problem:** When sending test requests in the Test Console tab, the response would disappear after the 5-second health refresh, forcing users to re-send requests to see results.

**Solution:** Store the response and restore it on refresh:

1. **Added Store to layout** (`service_inspector_layout.py`):
   ```python
   dcc.Store(id="test-console-response", data=None),
   ```

2. **Updated test console component** (`service_detail_panel.py`):
   ```python
   def create_testing_console_tab(
       service_data: dict[str, Any],
       base_url: str,
       stored_response: dict[str, Any] | None = None,
       openapi_schema: dict[str, Any] | None = None,  # NEW: Use OpenAPI endpoints
   ) -> dbc.Tab:
       # Build endpoint options from OpenAPI schema (comprehensive list)
       if openapi_schema and "paths" in openapi_schema:
           for path, methods in openapi_schema["paths"].items():
               for method in methods.keys():
                   if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                       endpoint_options.append({"label": f"{method.upper()} {path}", "value": path})
       else:
           # Fallback to registered endpoints
           endpoint_options = [...]
       
       # Use stored response or default message
       if stored_response and isinstance(stored_response, dict):
           response_display = stored_response.get("content", default_msg)
       else:
           response_display = default_msg
   ```

3. **Updated send request callback** (`service_inspector.py`):
   ```python
   @app.callback(
       [
           Output("test-response-display", "children"),
           Output("test-console-response", "data"),  # Save to Store
       ],
       Input("test-send-request-btn", "n_clicks"),
       ...
   )
   def send_test_request(...):
       # Build response display
       response_display = html.Div([...])
       
       # Return both the display AND save to Store
       return response_display, {"type": "success", "content": response_display}
   ```

4. **Pass stored response to panel creation**:
   ```python
   detail_panel = create_service_detail_panel(
       service_data=metadata,
       health_data=health,
       openapi_schema=openapi_schema,
       active_tab=active_tab,
       active_accordion_items=active_accordion_items,
       test_console_response=test_console_response,  # ✅ Preserve response
   )
   ```

**Additional Fix:** The endpoint dropdown now uses the OpenAPI schema instead of only the registered endpoints, providing a comprehensive list of all available API endpoints for testing (not just the handful in `service.json`).

**Why this works:**
- `dcc.Store` exists in the layout from page load (no circular dependency)
- When user changes tabs/expands accordions/sends requests, callbacks save the state
- When health refresh triggers, `display_service_details` uses all saved states
- Components are recreated with the user's selections and data still active ✨

## Implementation Details

### Changes Made

**File: `src/robomage/dashboard/callbacks/service_inspector.py`**

1. **Removed State dependency:**
   - Deleted `State("service-detail-tabs", "active_tab")` from callback signature
   - Removed `current_active_tab` parameter from function

2. **Added comprehensive logging:**
   - Log when callback fires
   - Log selected service ID and available services
   - Log health status and OpenAPI fetch results
   - Log successful completion

3. **Simplified tab handling:**
   - Always use `"overview-tab"` as the default
   - Removed conditional logic for preserving tabs (can add back via Store if needed)

### Code Before (BROKEN):
```python
@app.callback(
    [...],
    [Input("selected-service-id", "data"), ...],
    [State("service-detail-tabs", "active_tab")],  # ❌ Component doesn't exist!
)
def display_service_details(selected_id, service_data, current_active_tab):
    active_tab = current_active_tab if current_active_tab else "overview-tab"
    ...
```

### Code After - Version 1 (WORKING but loses tab on refresh):
```python
@app.callback(
    [...],
    [Input("selected-service-id", "data"), ...],
    # No State dependency - component doesn't exist yet!
)
def display_service_details(selected_id, service_data):
    active_tab = "overview-tab"  # Always start with overview
    ...
```

### Code After - Version 2 (FULLY WORKING with tab preservation):
```python
# Added to layout:
dcc.Store(id="service-detail-active-tab", data="overview-tab")

# New callback to save tab changes:
@app.callback(
    Output("service-detail-active-tab", "data"),
    Input("service-detail-tabs", "active_tab"),
    prevent_initial_call=True,
)
def save_active_tab(active_tab):
    if active_tab:
        return active_tab
    raise PreventUpdate

# Updated display callback:
@app.callback(
    [...],
    [Input("selected-service-id", "data"), ...],
    [State("service-detail-active-tab", "data")],  # ✅ Store exists in layout
)
def display_service_details(selected_id, service_data, active_tab_from_store):
    active_tab = active_tab_from_store if active_tab_from_store else "overview-tab"
    ...
```

## Testing Instructions

1. **Start the services:**
   ```bash
   pixi run kill-all
   pixi run python services/peak_analysis/main.py --port 8001 --host 127.0.0.1 &
   pixi run python services/workflow_engine/main.py --port 8002 --host 127.0.0.1 &
   ```

2. **Start the dashboard:**
   ```bash
   pixi run python -m robomage.dashboard
   ```

3. **Test the fix:**
   - Navigate to the Service Inspector tab
   - Wait for services to be discovered
   - Click on a service card (e.g., "Peak Analysis")
   - **Expected:** Detail panel shows service overview with tabs
   - **Expected logs:** See "🔍 display_service_details callback FIRED" messages

4. **Verify logging:**
   ```bash
   # Watch terminal for logs like:
   # ================================================================================
   # 🔍 display_service_details callback FIRED
   #    selected_id: peak_analysis
   #    service_data keys: ['peak_analysis', 'workflow_engine']
   # ================================================================================
   # ✅ Processing service: peak_analysis
   #    Health status: healthy
   #    Fetching OpenAPI schema...
   #    OpenAPI schema fetched: True
   #    Active tab: overview-tab
   #    Creating detail panel...
   #    Title: Service Details: Peak Analysis
   # ✅ display_service_details completed successfully
   ```

## What Was Working ✅

1. **Service Discovery**: Services are being discovered and displayed in the service list
2. **Service Selection Callback**: The `select_service` callback fires correctly when services are clicked
3. **Service ID Storage**: The `selected-service-id` store updates with the correct service ID
4. **Service Health Checks**: The 5-second health monitoring works

## Lessons Learned

### Dash Callback Gotchas

1. **State dependencies must exist in initial layout**
   - Cannot reference components created dynamically by other callbacks
   - Use `dcc.Store` components for state that spans dynamic content

2. **Circular dependencies fail silently**
   - Dash may not throw errors, just won't trigger callbacks
   - Always check that State/Input components exist in the layout tree

3. **Logging is essential**
   - Added comprehensive logging to track callback execution
   - Helps identify when callbacks aren't firing vs. returning wrong data

### Best Practices for Tab Preservation

If tab preservation is needed in the future, use this pattern:

```python
# In layout:
dcc.Store(id="service-detail-active-tab", data="overview-tab")

# In callback:
@app.callback(
    Output("service-detail-active-tab", "data"),
    Input("service-detail-tabs", "active_tab"),
)
def save_active_tab(tab):
    return tab

@app.callback(
    [...],
    [Input("selected-service-id", "data")],
    [State("service-detail-active-tab", "data")],  # ✅ Store exists in layout
)
def display_details(selected_id, active_tab):
    ...
```

## Files Modified

1. ✅ `src/robomage/dashboard/callbacks/service_inspector.py` 
   - Fixed circular dependency
   - Added logging for debugging
   - Added `save_active_tab` callback for tab preservation
   - Added `save_accordion_state` callback for accordion preservation  
   - Updated `send_test_request` to save response to Store

2. ✅ `src/robomage/dashboard/layouts/service_inspector_layout.py`
   - Added `service-detail-active-tab` Store
   - Added `api-docs-active-items` Store
   - Added `test-console-response` Store

3. ✅ `src/robomage/dashboard/components/service_detail_panel.py`
   - Updated `create_service_detail_panel` to accept all preserved state params
   - Updated `create_api_docs_tab` to accept and pass accordion state
   - Updated `create_openapi_paths_display` to use `active_item` and assign unique `item_id` values
   - Updated `create_testing_console_tab` to accept and display stored response
   - Changed accordion from `start_collapsed=True` to `active_item=active_items` + `always_open=True`

4. 📝 `docs/SERVICE-INSPECTOR-DEBUG-SESSION.md` - Complete solution documentation

## Next Steps

- [x] Test the fix with both services running
- [x] Verify logs show callback execution
- [x] Confirm UI updates when clicking services
- [x] Add tab preservation via Store (completed!)
- [x] Test tab preservation across 5-second health refreshes
- [x] Add accordion state preservation (completed!)
- [x] Test accordion preservation across health refreshes
- [x] Add test console response preservation (completed!)
- [x] Test response preservation across health refreshes
- [ ] Remove debug logging once confirmed working (or reduce to DEBUG level)
- [ ] Consider applying this state preservation pattern to other dynamic components in the dashboard

## Key Learnings - The Store Pattern for Dynamic UI State

This debugging session revealed a critical pattern for Dash applications with dynamic content that refreshes:

### The Problem
When Dash recreates components (due to callback triggers like health monitoring), any user interactions or displayed data are lost unless explicitly preserved.

### The Solution Pattern
For ANY dynamic UI state that should survive component recreation:

1. **Add a `dcc.Store` component** in the layout (exists from page load)
2. **Create a callback** to save user interactions to the Store
3. **Add State dependency** on the Store in the display callback
4. **Pass the stored value** to the component creation functions
5. **Use the stored value** when creating the component

### When to Use This Pattern
- ✅ Tab selections in dynamic tab containers
- ✅ Accordion open/closed states
- ✅ Form responses or data displays
- ✅ User input values that should persist
- ✅ Filter/search states
- ✅ Any user interaction that creates visual state

### Code Template
```python
# 1. Add Store to layout
dcc.Store(id="my-ui-state", data=default_value)

# 2. Save user interactions
@app.callback(
    Output("my-ui-state", "data"),
    Input("my-component", "some_property"),
    prevent_initial_call=True,
)
def save_ui_state(value):
    return value

# 3. Use stored state in display
@app.callback(
    Output("my-panel", "children"),
    Input("refresh-trigger", "n_intervals"),
    State("my-ui-state", "data"),
)
def display_panel(n_intervals, stored_state):
    return create_panel(stored_value=stored_state)
```

This pattern ensures a seamless user experience even with frequent data refreshes! 🎉

## Status: ✅ COMPLETELY RESOLVED (All UI State Preservation Issues Fixed)

**Problem 1:** Circular dependency on dynamic component → **FIXED**  
**Problem 2:** Tab selection lost on health refresh → **FIXED**  
**Problem 3:** Accordion items collapse on health refresh → **FIXED**  
**Problem 4:** Test console responses vanish on health refresh → **FIXED**  
**Solution:** Comprehensive state management with `dcc.Store` components + callbacks for all UI interactions  
**Result:** Perfect user experience - all UI state (tabs, accordions, test responses) persists across 5s health refreshes ✨
