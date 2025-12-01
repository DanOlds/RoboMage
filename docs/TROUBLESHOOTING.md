# RoboMage Troubleshooting Guide

**Last Updated**: December 1, 2025  
**Version**: Post-Sprint 8

This guide helps you diagnose and fix common issues with RoboMage.

---

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Service Connection Problems](#service-connection-problems)
3. [Dashboard Issues](#dashboard-issues)
4. [Data Loading Problems](#data-loading-problems)
5. [Test Failures](#test-failures)
6. [Session Persistence Issues](#session-persistence-issues)
7. [Workflow Execution Problems](#workflow-execution-problems)
8. [Performance Issues](#performance-issues)

---

## Installation Issues

### Problem: `pixi` command not found

**Symptoms:**
```bash
$ pixi install
bash: pixi: command not found
```

**Solution:**
Install Pixi from [pixi.sh](https://pixi.sh):
```bash
# macOS/Linux
curl -fsSL https://pixi.sh/install.sh | bash

# Windows (PowerShell)
iwr -useb https://pixi.sh/install.ps1 | iex

# Then restart your shell
```

### Problem: Dependencies fail to install

**Symptoms:**
```bash
$ pixi install
Error: Failed to resolve dependencies
```

**Solution:**
1. Clear the Pixi cache:
   ```bash
   rm -rf .pixi
   pixi install
   ```

2. Check your internet connection (Pixi downloads from conda-forge)

3. If behind a proxy, configure Pixi:
   ```bash
   export HTTP_PROXY=http://your-proxy:port
   export HTTPS_PROXY=http://your-proxy:port
   ```

### Problem: Import errors after installation

**Symptoms:**
```python
ImportError: No module named 'robomage'
```

**Solution:**
Make sure you're using the Pixi environment:
```bash
pixi shell  # Activate the environment
python -m robomage --help
```

Or use `pixi run`:
```bash
pixi run python -m robomage --help
```

---

## Service Connection Problems

### Problem: "Connection refused" or "Service unavailable"

**Symptoms:**
```
PeakAnalysisServiceError: ConnectionError: Request failed after 4 attempts
```

**Diagnosis:**
1. Check if services are running:
   ```bash
   # Check peak analysis service (port 8001)
   curl http://localhost:8001/health
   
   # Check workflow engine (port 8002)
   curl http://localhost:8002/health
   ```

2. If no response, the service isn't running.

**Solution:**
Start the required services:
```bash
# Option 1: Start all services at once
pixi run start-all

# Option 2: Start individually
pixi run python services/peak_analysis/main.py --port 8001 &
pixi run python services/workflow_engine/main.py --port 8002 &
python -m robomage.dashboard
```

### Problem: Port already in use

**Symptoms:**
```
OSError: [Errno 48] Address already in use
```

**Solution:**
1. Find and kill the process using the port:
   ```bash
   # Linux/macOS
   lsof -ti:8001 | xargs kill -9
   lsof -ti:8002 | xargs kill -9
   lsof -ti:8050 | xargs kill -9
   ```

2. Or use different ports:
   ```bash
   python services/peak_analysis/main.py --port 8011
   python services/workflow_engine/main.py --port 8012
   python -m robomage.dashboard --port 8060
   ```

### Problem: Service health check shows "unhealthy"

**Symptoms:**
Dashboard shows red "Service unavailable" badge

**Solution:**
1. Check service logs:
   ```bash
   pixi run python services/peak_analysis/main.py --port 8001
   # Look for errors in the output
   ```

2. Check dependencies:
   ```bash
   pixi run python -c "import numpy, scipy, pydantic; print('OK')"
   ```

3. Restart the service with verbose logging:
   ```bash
   pixi run python services/peak_analysis/main.py --port 8001 --log-level DEBUG
   ```

---

## Dashboard Issues

### Problem: Dashboard won't start

**Symptoms:**
```bash
$ python -m robomage.dashboard
ModuleNotFoundError: No module named 'dash'
```

**Solution:**
Install dashboard dependencies:
```bash
pixi install  # Installs all dependencies including dash
```

### Problem: Files won't upload to dashboard

**Symptoms:**
- No error message, but file doesn't appear in list
- "Invalid file format" error

**Solution:**
1. Check file format - must be `.chi` or `.xy`
2. Verify file structure:
   ```
   # .chi files: Two columns (Q, intensity)
   1.0 100.5
   1.01 102.3
   ...
   
   # .xy files: Same format
   ```

3. Check file size - very large files (>100MB) may time out
4. Try loading with CLI first to see detailed errors:
   ```bash
   pixi run python -m robomage sample.chi --info
   ```

### Problem: Dashboard shows blank page

**Symptoms:**
Browser shows "This site can't be reached"

**Solution:**
1. Check dashboard is running:
   ```bash
   ps aux | grep "robomage.dashboard"
   ```

2. Check the correct port (default 8050):
   ```bash
   http://localhost:8050
   ```

3. Check browser console (F12) for JavaScript errors

4. Try a different browser (Chrome, Firefox, Safari)

### Problem: Session not auto-created on dashboard load

**Symptoms:**
Session status shows "No active session"

**Solution:**
This is expected if you have existing sessions. The auto-create only happens on first launch. To create a new session:
1. Click "Save Session" button
2. Enter a session name
3. Click Save

---

## Data Loading Problems

### Problem: "Invalid file format" error

**Symptoms:**
```python
ValueError: Invalid file format: Expected 2 columns, got 3
```

**Solution:**
1. Check file format:
   ```bash
   head -20 your_file.chi
   ```

2. File should have exactly 2 columns (Q, intensity)
3. Remove any header rows or comments
4. Ensure numeric values only (no NaN, inf)

### Problem: Q-values not sorted

**Symptoms:**
```
ValidationError: Q values must be sorted in ascending order
```

**Solution:**
RoboMage requires sorted Q-values. Fix with:
```python
import numpy as np
import pandas as pd

# Load unsorted data
df = pd.read_csv("data.chi", sep=r'\s+', header=None, names=['Q', 'intensity'])

# Sort by Q
df = df.sort_values('Q').reset_index(drop=True)

# Save
df.to_csv("data_sorted.chi", sep=' ', header=False, index=False)
```

### Problem: NaN or infinite values in data

**Symptoms:**
```
ValidationError: Data contains NaN or infinite values
```

**Solution:**
Clean the data:
```python
import pandas as pd
import numpy as np

df = pd.read_csv("data.chi", sep=r'\s+', header=None, names=['Q', 'intensity'])

# Remove NaN
df = df.dropna()

# Remove infinite values
df = df[np.isfinite(df['intensity'])]

# Save cleaned data
df.to_csv("data_clean.chi", sep=' ', header=False, index=False)
```

---

## Test Failures

### Problem: Tests fail with "fixture not found"

**Symptoms:**
```
E       fixture 'sample_data' not found
```

**Solution:**
1. Check if running tests from project root:
   ```bash
   cd /path/to/RoboMage
   pixi run test
   ```

2. If creating new tests, define fixtures in `conftest.py` or the test file

### Problem: Service integration tests fail

**Symptoms:**
```
FAILED tests/test_peak_analysis_integration.py::TestPeakAnalysisService::test_service_health
```

**Solution:**
1. Ensure no services are running on test ports:
   ```bash
   lsof -ti:8001 | xargs kill -9
   ```

2. Run tests with verbose output:
   ```bash
   pixi run pytest tests/test_peak_analysis_integration.py -v
   ```

3. Check if port is hardcoded - should be 8001 for peak analysis, 8002 for workflow engine

### Problem: "async def functions are not natively supported"

**Symptoms:**
```
FAILED test.py::test_async_function - Failed: async def functions are not natively supported
```

**Solution:**
Add pytest marker to async tests:
```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_call()
    assert result is not None
```

---

## Session Persistence Issues

### Problem: Session won't save

**Symptoms:**
- "Failed to save session" error in dashboard
- No error but session doesn't appear in list

**Solution:**
1. Check storage directory exists and is writable:
   ```bash
   ls -la ~/.robomage/
   # Should show: sessions.db and data/
   ```

2. Check for database lock:
   ```bash
   lsof ~/.robomage/sessions.db
   ```

3. If locked, close other RoboMage instances

4. Try custom storage location:
   ```python
   from robomage.persistence import SessionManager
   
   mgr = SessionManager(db_path="/tmp/robomage_test/sessions.db")
   session_id = mgr.create_session("Test", "Testing custom location")
   ```

### Problem: Session files corrupted

**Symptoms:**
```
sqlite3.DatabaseError: database disk image is malformed
```

**Solution:**
1. Backup existing data:
   ```bash
   cp -r ~/.robomage ~/.robomage.backup
   ```

2. Try to recover:
   ```bash
   sqlite3 ~/.robomage/sessions.db ".recover" | sqlite3 recovered.db
   ```

3. If recovery fails, start fresh:
   ```bash
   rm -rf ~/.robomage
   # RoboMage will create new database on next launch
   ```

### Problem: Wavelength not preserved after session load

**Symptoms:**
File wavelength shows default (0.1665 Å) instead of saved value

**Solution:**
This was fixed in Sprint 5. Update to latest version:
```bash
git pull origin main
pixi install
```

---

## Workflow Execution Problems

### Problem: Workflow won't execute

**Symptoms:**
- "Execution failed" message
- No results displayed

**Solution:**
1. Check workflow service is running:
   ```bash
   curl http://localhost:8002/health
   ```

2. Validate workflow structure:
   - All nodes connected
   - No cycles (DAG requirement)
   - Required parameters configured

3. Check browser console (F12) for errors

4. Enable debug mode to see detailed logs:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

### Problem: "Node type not found" error

**Symptoms:**
```
KeyError: 'my_custom_node'
```

**Solution:**
1. Check node type is registered with workflow orchestrator:
   ```python
   from robomage.orchestrator import WorkflowOrchestrator
   
   orchestrator = WorkflowOrchestrator()
   print(orchestrator.list_node_types())  # See available types
   ```

2. Valid node types:
   - `load_files`
   - `filter_q_range`
   - `normalize`
   - `peak_analysis`
   - `statistics`
   - `export_csv`
   - `export_json`

### Problem: Normalize node fails with AttributeError

**Symptoms:**
```
AttributeError: 'DiffractionData' object has no attribute 'intensity_values'
```

**Solution:**
This was fixed in Sprint 8 Bug #10. Update to latest version. The correct attribute is `intensities`, not `intensity_values`.

---

## Performance Issues

### Problem: Peak analysis takes too long

**Symptoms:**
Analysis hangs or takes >30 seconds for small datasets

**Solution:**
1. Reduce prominence threshold (fewer peaks to fit):
   ```python
   config = AnalysisConfig(prominence=50)  # Default is 10
   ```

2. Use simpler peak profile:
   ```python
   config = AnalysisConfig(profile_type="gaussian")  # Faster than voigt
   ```

3. Reduce data points (resample):
   ```python
   data_resampled = data.trim_q_range(2.0, 8.0)  # Smaller Q range
   ```

### Problem: Dashboard slow to load files

**Symptoms:**
File upload takes >5 seconds for small files

**Solution:**
1. Check file size - compress if >10MB
2. Disable debug mode (if enabled)
3. Close unused browser tabs
4. Check system resources:
   ```bash
   top  # or htop on Linux
   # Look for high CPU/memory usage
   ```

### Problem: Workflow execution timeout

**Symptoms:**
```
TimeoutError: Workflow execution exceeded 300 seconds
```

**Solution:**
1. Break large workflow into smaller pieces
2. Reduce data size (fewer files, smaller Q range)
3. Increase timeout in workflow service configuration
4. Check for infinite loops in workflow (cycles)

---

## Getting More Help

### Enable Debug Logging

For detailed diagnostics:
```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Check Service Logs

Start services with verbose output:
```bash
pixi run python services/peak_analysis/main.py --port 8001 --log-level DEBUG
```

### Run Tests with Verbose Output

```bash
pixi run pytest tests/ -v -s  # -s shows print statements
```

### Use Storage Debug Panel

In dashboard:
1. Click "Manage Sessions"
2. Select a session
3. Click "Show Debug Info"
4. Inspect session data structure

### Check GitHub Issues

Search for similar problems:
https://github.com/DanOlds/RoboMage/issues

### Report a Bug

Include:
1. RoboMage version: `git rev-parse HEAD`
2. Python version: `python --version`
3. OS: `uname -a` (Linux/macOS) or Windows version
4. Full error traceback
5. Steps to reproduce
6. Expected vs actual behavior

---

## Quick Reference

### Essential Commands
```bash
# Install/update
pixi install

# Run tests
pixi run test

# Start all services
pixi run start-all

# Start dashboard
python -m robomage.dashboard

# Check service health
curl http://localhost:8001/health  # Peak analysis
curl http://localhost:8002/health  # Workflow engine

# Clean cache
./clear_cache.sh  # or rm -rf **/__pycache__
```

### Common File Locations
- **Source code**: `src/robomage/`
- **Tests**: `tests/`
- **Services**: `services/`
- **Session storage**: `~/.robomage/`
- **Examples**: `examples/`
- **Documentation**: `docs/`

### Key Configuration Files
- **pixi.toml**: Dependencies and tasks
- **pyproject.toml**: Python package config, pytest settings
- **pyproject.toml**: Ruff linting and formatting config
- **~/.robomage/sessions.db**: SQLite database for sessions

---

**Still stuck?** Check the documentation in `docs/` or open an issue on GitHub!
