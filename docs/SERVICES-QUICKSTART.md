# RoboMage Services Quick Start Guide

## 🚀 Quick Start - All Services at Once

**The easiest way to start all services:**

```bash
pixi run start-all
```

This single command will:
1. Start Peak Analysis Service (port 8001) in background
2. Start Workflow Service (port 8002) in background  
3. Start Dashboard (port 8050) in foreground
4. Automatically clean up all services when you press Ctrl+C

**Then open your browser to:** http://localhost:8050

---

## Running the Complete Workflow System

The workflow system requires multiple services to be running. Start them in separate terminal windows:

### 1. Peak Analysis Service (Required for peak_analysis nodes)
```bash
pixi run python services/peak_analysis/main.py --port 8001
```

**What it does:** Processes diffraction data for peak detection and fitting  
**Required for:** `peak_analysis` workflow nodes  
**API Docs:** http://localhost:8001/docs

---

### 2. Workflow Service (Required for workflow execution)
```bash
pixi run python services/workflow_engine/main.py --port 8002
```

**What it does:** Manages and executes workflow definitions  
**Required for:** Dashboard workflow tab, workflow execution  
**API Docs:** http://localhost:8002/docs

---

### 3. Dashboard (Required for visual interface)
```bash
pixi run python -m robomage.dashboard
```

**What it does:** Interactive web UI for data visualization and workflow building  
**Access at:** http://localhost:8050  
**Includes:** Workflow Builder tab (⚙️ Workflow Builder)

---

## Typical Startup Sequence

**Terminal 1: Peak Analysis**
```bash
pixi run python services/peak_analysis/main.py --port 8001 &
```

**Terminal 2: Workflow Service**
```bash
pixi run python services/workflow_engine/main.py --port 8002 &
```

**Terminal 3: Dashboard**
```bash
pixi run python -m robomage.dashboard
```

---

## Service Health Checks

Verify services are running:

```bash
# Peak Analysis Service
curl http://localhost:8001/health

# Workflow Service
curl http://localhost:8002/health
```

---

## Troubleshooting Workflow Errors

### Error: "No files were analyzed successfully"

**Cause:** Peak analysis service is not running

**Solution:**
```bash
pixi run python services/peak_analysis/main.py --port 8001
```

The error message will now provide detailed information:
```
Peak analysis service may not be running.
Start the service with:
  pixi run python services/peak_analysis/main.py --port 8001
```

### Error: "Connection refused" or timeout errors

**Cause:** Required service is not running

**Check which service is needed:**
- `load_files`, `filter_q_range`, `normalize` → No external service needed
- `peak_analysis` → Requires peak analysis service (port 8001)
- `statistics` → No external service needed
- `export_csv`, `export_json`, `save_results` → No external service needed

### Dashboard shows "Workflow service not available"

**Solution:** Start the workflow service on port 8002

---

## Development Mode

Run services with auto-reload:

```bash
# Peak Analysis (with reload)
pixi run uvicorn services.peak_analysis.main:app --reload --port 8001

# Workflow Service (with reload)
pixi run python services/workflow_engine/main.py --reload --port 8002

# Dashboard (debug mode)
pixi run python -m robomage.dashboard --debug
```

---

## Port Summary

| Service | Port | Purpose |
|---------|------|---------|
| Peak Analysis | 8001 | Scientific peak detection/fitting |
| Workflow Engine | 8002 | Workflow management & execution |
| Dashboard | 8050 | Web UI for visualization |

---

## Example: Complete Workflow Setup

```bash
# Terminal 1
pixi run python services/peak_analysis/main.py --port 8001

# Terminal 2
pixi run python services/workflow_engine/main.py --port 8002

# Terminal 3
pixi run python -m robomage.dashboard

# Then open browser to: http://localhost:8050
# Click: ⚙️ Workflow Builder tab
# Click: Execute (on the default workflow)
```

You should see:
- ✅ Workflow service connected (8 node types)
- ✅ Execution completes successfully
- ✅ Results displayed with peak counts

---

## Stopping Services

**Stop individual service:**
```bash
# Find and kill by port
lsof -ti:8001 | xargs kill  # Peak Analysis
lsof -ti:8002 | xargs kill  # Workflow Service
lsof -ti:8050 | xargs kill  # Dashboard
```

**Stop all background jobs:**
```bash
jobs          # List jobs
kill %1 %2 %3 # Kill specific jobs
```
