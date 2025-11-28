# Pixi Task: Start All Services

**Date:** November 26, 2025  
**Feature:** One-command startup for all workflow services  
**Status:** ✅ COMPLETE

## Usage

Simply run:
```bash
pixi run start-all
```

This single command will:
1. ✅ Start Peak Analysis Service (port 8001) in background
2. ✅ Start Workflow Service (port 8002) in background
3. ✅ Start Dashboard (port 8050) in foreground
4. ✅ Automatically stop all services when you press Ctrl+C

## Implementation

### Files Created

**`start_services.py`** - Cross-platform Python script
- Starts services as background subprocesses
- Tracks PIDs for clean shutdown
- Handles Ctrl+C gracefully (SIGINT/SIGTERM)
- Dashboard runs in foreground (blocking)

### Files Modified

**`pixi.toml`** - Added tasks:
```toml
[tasks]
# Individual services
peak-service = "python services/peak_analysis/main.py --port 8001"
workflow-service = "python services/workflow_engine/main.py --port 8002"

# Start all services
start-all = "python start_services.py"
```

**`docs/SERVICES-QUICKSTART.md`** - Added quick start section at top
**`README.md`** - Updated dashboard section with new command

## Advantages

✅ **One Command** - No need to open 3 terminals  
✅ **Cross-Platform** - Python script works on Windows/Linux/Mac  
✅ **Clean Shutdown** - Ctrl+C stops everything properly  
✅ **Clear Feedback** - Shows PID and startup progress  
✅ **No Manual Cleanup** - Services automatically stopped on exit

## Example Output

```
🚀 Starting RoboMage Workflow System...

📊 Starting Peak Analysis Service (port 8001)...
   ✓ Peak Analysis PID: 12345

⚙️  Starting Workflow Service (port 8002)...
   ✓ Workflow Service PID: 12346

🌐 Starting Dashboard (port 8050)...
   Access at: http://localhost:8050
   Press Ctrl+C to stop all services

🔬 RoboMage Dashboard starting...
📊 Access dashboard at: http://127.0.0.1:8050
...

^C
🛑 Stopping all services...
✅ All services stopped
```

## Alternative Methods

### Individual Services (if you need control)
```bash
# Start peak analysis only
pixi run peak-service

# Start workflow service only
pixi run workflow-service

# Start dashboard only
pixi run dashboard
```

### Manual Background Jobs (Linux/Mac)
```bash
pixi run python services/peak_analysis/main.py --port 8001 &
pixi run python services/workflow_engine/main.py --port 8002 &
pixi run python -m robomage.dashboard
```

## Troubleshooting

### Port Already in Use
If you see "Address already in use" errors:
```bash
# Kill existing services
lsof -ti:8001 | xargs kill  # Peak Analysis
lsof -ti:8002 | xargs kill  # Workflow Service
lsof -ti:8050 | xargs kill  # Dashboard

# Then retry
pixi run start-all
```

### Services Not Stopping
If Ctrl+C doesn't stop services:
```bash
# Find PIDs
ps aux | grep "peak_analysis\|workflow_engine\|robomage.dashboard"

# Kill manually
kill <PID1> <PID2> <PID3>
```

## Integration with Workflow System

This command is specifically designed for the **Sprint 6 Workflow Orchestrator** feature, which requires all three services to be running for full functionality:

- **Peak Analysis Service** - Required for `peak_analysis` workflow nodes
- **Workflow Service** - Manages and executes workflow definitions
- **Dashboard** - Provides the Workflow Builder tab UI

See `docs/sprint-6-workflow-orchestrator-mvp.md` for workflow system details.
