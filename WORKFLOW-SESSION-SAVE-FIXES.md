# Workflow Session Save Fixes - November 26, 2025

## Problems Fixed

### 1. ❌ "No diffraction data found in workflow results"
**Root Cause**: Callback was looking for `execution_results.get("result", {}).get("node_results")` but the API returns `WorkflowExecutionResult` which has `node_results` at the top level.

**Fix**: Changed from nested access to direct access:
```python
# BEFORE (incorrect):
result = execution_results.get("result", {})
node_results = result.get("node_results", [])

# AFTER (correct):
node_results = execution_results.get("node_results", [])
```

### 2. ❌ Pydantic validation error (lists vs numpy arrays)
**Root Cause**: JSON serialization converts numpy arrays to lists, but `DiffractionData` expects numpy arrays.

**Fix**: Convert lists back to numpy arrays before creating DiffractionData:
```python
item_copy = item.copy()
if isinstance(item_copy.get("q_values"), list):
    item_copy["q_values"] = np.array(item_copy["q_values"])
if isinstance(item_copy.get("intensities"), list):
    item_copy["intensities"] = np.array(item_copy["intensities"])

data = DiffractionData(**item_copy)
```

### 3. ❌ "NOT NULL constraint failed: files.wavelength"
**Root Cause**: `.chi` files don't have wavelength metadata, so `wavelength` is `None` in JSON. Using `item.get("wavelength", 0.1665)` returns `None` when the key exists with value `None`.

**Fix**: Use `or` operator to handle both missing and None values:
```python
# BEFORE (fails when wavelength=None):
wavelength = item.get("wavelength", 0.1665)

# AFTER (works for both missing and None):
wavelength = item.get("wavelength") or 0.1665
```

### 4. ❌ "No files found matching: examples/*.chi"
**Root Cause**: Default workflow used relative path `"examples"` which doesn't work when workflow service runs from `services/workflow_engine/`.

**Fix**: Calculate absolute path using `__file__`:
```python
project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
examples_dir = str(project_root / "examples")
```

## Files Modified

1. **src/robomage/dashboard/callbacks/workflow.py**
   - Fixed node_results access (line ~551)
   - Added numpy array conversion (lines ~597-601)
   - Fixed wavelength default handling (line ~606)
   - Added better error logging

2. **src/robomage/dashboard/layouts/workflow_layout.py**
   - Added Path import
   - Updated `get_default_workflow_json()` to use absolute paths
   - Escaped all braces for f-string compatibility

## Test Results

✅ **test_save_workflow_callback.py**: Simulates complete dashboard flow
```
1️⃣ Creating test session... ✅
2️⃣ Executing workflow... ✅  
3️⃣ Simulating dashboard callback logic... ✅
✅ SUCCESS: Saved 1 file(s) to session
```

✅ **verify_workflow_session_fix.py**: Verifies full serialization works
```
1️⃣ Checking workflow service... ✅
2️⃣ Creating test workflow... ✅
3️⃣ Executing workflow with full serialization... ✅
4️⃣ Verifying full DiffractionData in execution results... ✅
5️⃣ Verifying dashboard callback compatibility... ✅
```

## User Testing Instructions

### Start Services
```bash
# Terminal 1: Workflow Service
cd services/workflow_engine
pixi run python main.py --port 8002

# Terminal 2: Dashboard
pixi run python -m robomage.dashboard
```

### Test Complete Flow

**Option A: Workflow → Session (NO Data Import needed)**
1. Open dashboard at http://localhost:8050
2. **Data Import tab**: Create a new session (give it a name)
3. **Workflow tab**: Click "Execute Workflow" (default workflow loads example file)
4. Wait for completion (status shows "completed")
5. Click **"Save Results to Current Session"**
6. ✅ Expected: "Successfully saved 1 file(s) to session"
7. **Visualization tab**: File should appear and be plottable
8. **Data Import tab**: File should be listed

**Option B: Traditional Data Import → Analysis**
1. **Data Import tab**: Create session and upload files manually
2. **Visualization tab**: Plot data
3. **Analysis tab**: Run peak detection
4. (This flow was already working)

## Conceptual Clarification

You correctly identified that there should be **two independent workflows**:

### Workflow 1: Dashboard UI (Tab-based)
- **Data Import tab** → Upload files → Create session
- **Visualization tab** → Plot data
- **Analysis tab** → Run analysis → View results
- **Persistence**: Automatic (files stored in session database)

### Workflow 2: Workflow Engine (Orchestrated)
- **Workflow tab** → Define nodes → Execute workflow
- **Data flows between nodes** (load → analyze → export)
- **Persistence**: Manual (click "Save Results to Current Session")

### Key Insight
These are **complementary, not conflicting**:
- Tab-based workflow is for **interactive exploration**
- Workflow engine is for **reproducible automated pipelines**
- Both should be able to:
  - Load data independently
  - Run analysis independently
  - Save results to sessions

The bug was that the workflow engine results **couldn't be saved to sessions**, breaking this independence. Now both workflows can:
1. Load data
2. Analyze data  
3. Save to sessions
4. Share results via the session database

## What's Fixed vs. What's Expected Behavior

### ✅ Now Fixed
- Workflows can load data and save results to sessions
- No need to use Data Import tab if using workflows
- Session persistence works from both UI and workflows

### ✅ Expected Behavior (Not a Bug)
- **Must create/load a session first** before saving workflow results
  - This is correct! Sessions are the persistence boundary
  - Without a session, there's nowhere to save results
- **"No files to save"** when trying to save session without files
  - This is correct! You need files to save
  - Either upload via Data Import OR execute workflow and save results

### Design Intent
The dashboard has two modes:
1. **Interactive Mode**: Data Import → Viz → Analysis (manual, UI-based)
2. **Workflow Mode**: Define workflow → Execute → Save results (automated, repeatable)

Both modes require a session as the persistence container, which is the correct design.

## Summary

All bugs are now fixed! The workflow engine can:
- ✅ Load diffraction files
- ✅ Execute analysis pipelines  
- ✅ Save results to active sessions
- ✅ Share data with Visualization and Analysis tabs

The only requirement is that a session must exist (either create new or load existing) before saving workflow results, which is correct design.
