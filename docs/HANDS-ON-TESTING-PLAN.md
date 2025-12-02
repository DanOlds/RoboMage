# Hands-On Testing Plan: Custom Services Architecture

**Purpose:** Verify the complete custom services system works end-to-end in real-world usage

**Status:** Ready for testing  
**Date:** December 2, 2025

---

## Testing Overview

We have 59 passing automated tests, but we need to verify:
- ✅ Service generator actually creates working services
- ✅ Generated services start and respond to requests
- ✅ Registry discovers and manages services correctly
- ✅ Dashboard integration works with real services
- ✅ Workflow integration executes service-backed nodes
- ✅ Pixi tasks work as expected
- ✅ All documentation is accurate

---

## Test Session 1: Service Generator (15 minutes)

### Goal
Create a brand new service from scratch using the generator and verify it works.

### Steps

**1. Create a simple test service:**
```bash
cd /nsls2/users/dolds/dev/RoboMage/services
python create_service.py

# Inputs:
# Service name: simple_stats
# Display name: Simple Statistics
# Description: Calculate basic statistics on diffraction data
# Port: 8005
# Node type: 1 (analysis)
# Confirm: y
```

**Expected Output:**
- Service directory created: `services/simple_stats/`
- All 7 files generated (main.py, models.py, analysis.py, etc.)
- No errors or warnings

**2. Verify generated files:**
```bash
cd services/simple_stats
ls -la

# Check no placeholders remain
grep -r "{{" .
# Should return nothing (or only in README examples)
```

**Expected Result:**
- All files present
- No `{{PLACEHOLDER}}` strings in code files
- Valid Python syntax

**3. Test the service manually:**
```bash
# Install dependencies (should be minimal - already in pixi)
# No pip install needed if using pixi environment

# Start service
python main.py --port 8005

# In another terminal, test health endpoint:
curl http://localhost:8005/health

# Expected: {"status": "healthy", "service": "simple_stats", "version": "1.0.0"}

# Test API docs
curl http://localhost:8005/

# Expected: Service info with endpoints

# Stop service (Ctrl+C)
```

**4. Test with sample data:**
```bash
# Test analyze endpoint
curl -X POST http://localhost:8005/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "data_points": [
        {"x": 1.0, "y": 100.0},
        {"x": 2.0, "y": 150.0},
        {"x": 3.0, "y": 125.0}
      ]
    }
  }'

# Expected: JSON response with results (mean_x, mean_y, max_y)
```

**Success Criteria:**
- ✅ Service generates without errors
- ✅ Service starts on correct port
- ✅ Health endpoint responds
- ✅ Analyze endpoint processes data
- ✅ Returns valid JSON

**Cleanup:**
```bash
# Stop service (Ctrl+C)
# Optionally remove test service
rm -rf services/simple_stats
```

---

## Test Session 2: Service Registry (10 minutes)

### Goal
Verify service discovery, registration, and pixi tasks work correctly.

### Steps

**1. Test service listing:**
```bash
cd /nsls2/users/dolds/dev/RoboMage

# List services
pixi run list-services

# Expected output:
# Registered Services:
#   - Peak Analysis Service (peak_analysis) on port 8001
#   - Workflow Engine Service (workflow_engine) on port 8002
#   - Simple Statistics (simple_stats) on port 8005  [if not cleaned up]
```

**2. Test service health checking:**
```bash
# Start services first
pixi run start-all &

# Wait 5 seconds for startup
sleep 5

# Check health
pixi run check-services

# Expected output:
# Service Health:
#   ✅ Peak Analysis Service (http://127.0.0.1:8001)
#   ✅ Workflow Engine Service (http://127.0.0.1:8002)
```

**3. Test manual registry interaction:**
```bash
pixi run python -c "
from robomage.service_registry import get_registry

registry = get_registry()
print(f'Found {len(registry.get_all_services())} services')

for service in registry.get_all_services():
    print(f'  - {service.display_name} ({service.name}) on port {service.port}')
    print(f'    Workflow: {service.workflow_integration.enabled}')
    print(f'    Dashboard: {service.dashboard_integration.enabled}')
"
```

**4. Test service tests:**
```bash
pixi run test-services

# Expected: 37/37 tests passing
```

**Success Criteria:**
- ✅ `list-services` shows all registered services
- ✅ `check-services` correctly reports health status
- ✅ Manual registry API works
- ✅ Service tests pass

**Cleanup:**
```bash
# Stop services
pixi run kill-all
```

---

## Test Session 3: Dashboard Integration (15 minutes)

### Goal
Verify services integrate with dashboard and analysis works.

### Steps

**1. Start all services:**
```bash
cd /nsls2/users/dolds/dev/RoboMage
pixi run start-all

# Expected output:
# 🚀 Starting RoboMage Workflow System...
# 📋 Found 2 auto-start services
# 🔧 Starting Peak Analysis Service (port 8001)...
# 🔧 Starting Workflow Engine Service (port 8002)...
# 🌐 Starting Dashboard (port 8050)...
```

**2. Open dashboard:**
```bash
# Open browser to: http://localhost:8050
# Or if on remote server, use port forwarding
```

**3. Test Data Import tab:**
- Click "Data Import" tab
- Upload a .chi or .xy file (or use test data if available)
- Verify file appears in file list
- Check wavelength is set (default 0.1665 Å)

**4. Test Visualization tab:**
- Click "Visualization" tab
- Select uploaded file
- Choose plot type (Line)
- Click "Create Plot"
- Verify plot appears with data

**5. Test Analysis tab:**
- Click "Analysis" tab
- Verify service status indicator shows:
  - ✅ Peak Analysis Service (healthy)
- Select file to analyze
- Adjust peak detection parameters
- Click "Run Analysis"
- Verify:
  - Results appear in table
  - Peaks shown on plot with annotations
  - Statistics displayed

**6. Check service monitor:**
- Look for service status badges in UI
- Verify they show green/healthy for running services

**Success Criteria:**
- ✅ Dashboard loads without errors
- ✅ Services show as healthy in UI
- ✅ Peak analysis runs successfully
- ✅ Results displayed correctly
- ✅ No console errors

**Cleanup:**
```bash
# Stop all services
pixi run kill-all

# Or Ctrl+C in start-all terminal
```

---

## Test Session 4: Workflow Integration (20 minutes)

### Goal
Verify service-backed workflow nodes work correctly.

### Steps

**1. Start services:**
```bash
pixi run start-all &
sleep 5  # Wait for startup
```

**2. Test workflow node discovery:**
```bash
pixi run python -c "
from robomage.workflow.nodes.registry import NodeRegistry

registry = NodeRegistry()
registry.discover_and_register_all()

node_types = registry.get_node_types()
print(f'Registered {len(node_types)} node types:')
for node_type in sorted(node_types):
    print(f'  - {node_type}')
"

# Expected: Should see peak_detection, peak_analysis, and other nodes
```

**3. Create and execute a workflow:**
```bash
# Create test workflow file
cat > /tmp/test_workflow.json <<'EOF'
{
  "nodes": [
    {
      "id": "load_1",
      "type": "load_files",
      "config": {
        "file_paths": ["detector_5_roi_175-181_18-218_frames_17847-17978.xy"]
      }
    },
    {
      "id": "peak_1",
      "type": "peak_detection",
      "config": {
        "prominence": 100,
        "profile_type": "gaussian"
      },
      "dependencies": ["load_1"]
    }
  ]
}
EOF

# Execute workflow
pixi run python -c "
import asyncio
import json
from robomage.orchestrator import WorkflowOrchestrator

with open('/tmp/test_workflow.json') as f:
    workflow = json.load(f)

orchestrator = WorkflowOrchestrator()
results = asyncio.run(orchestrator.execute_workflow(workflow))

print(f'Workflow executed: {len(results)} nodes')
for node_id, result in results.items():
    print(f'  {node_id}: {result.status}')
"
```

**4. Test from Workflow Builder tab (if available):**
- Open dashboard
- Navigate to Workflow Builder tab
- Create workflow visually
- Add service node (peak_detection)
- Configure parameters
- Execute workflow
- Verify results appear

**Success Criteria:**
- ✅ Service nodes discovered
- ✅ Workflow executes successfully
- ✅ Service-backed nodes process data
- ✅ Results returned correctly
- ✅ No errors in workflow execution

**Cleanup:**
```bash
pixi run kill-all
rm /tmp/test_workflow.json
```

---

## Test Session 5: Migration Scenario (15 minutes)

### Goal
Verify migration guide is accurate by following it for an existing service.

### Steps

**1. Review existing service (peak_analysis):**
```bash
cd /nsls2/users/dolds/dev/RoboMage/services/peak_analysis

# Check service.json exists
cat service.json | head -20

# Verify it has all required fields
```

**2. Verify health endpoint:**
```bash
# Start service
python main.py --port 8001 &

# Test health
curl http://localhost:8001/health

# Stop service
pkill -f "peak_analysis/main.py"
```

**3. Test registry-based startup:**
```bash
cd /nsls2/users/dolds/dev/RoboMage

# Should start service automatically
pixi run start-all &

sleep 5

# Verify service is running
curl http://localhost:8001/health

pixi run kill-all
```

**4. Verify migration guide matches reality:**
```bash
# Open migration guide
cat docs/MIGRATION-GUIDE.md | less

# Spot-check:
# - Are field names in service.json correct?
# - Are endpoint patterns correct?
# - Are pixi commands correct?
# - Are code examples accurate?
```

**Success Criteria:**
- ✅ Existing services follow migration guide patterns
- ✅ Migration guide examples are accurate
- ✅ No discrepancies between docs and code

---

## Test Session 6: End-to-End User Workflow (20 minutes)

### Goal
Complete a realistic user workflow from service creation to data analysis.

### Scenario
Create a custom "normalize" service that normalizes diffraction intensities.

### Steps

**1. Generate service:**
```bash
cd /nsls2/users/dolds/dev/RoboMage/services
python create_service.py

# Inputs:
# Service name: normalize_intensities
# Display name: Intensity Normalizer
# Description: Normalize diffraction intensities to max value
# Port: 8006
# Node type: 2 (transform)
# Confirm: y
```

**2. Implement analysis logic:**
```bash
cd normalize_intensities

# Edit analysis.py - replace perform_analysis with:
# (User would do this manually - for testing, we can use template as-is)
```

**3. Test service standalone:**
```bash
python main.py --port 8006 &

curl -X POST http://localhost:8006/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "data_points": [
        {"x": 1.0, "y": 100.0},
        {"x": 2.0, "y": 200.0},
        {"x": 3.0, "y": 150.0}
      ]
    }
  }'

pkill -f "normalize_intensities/main.py"
```

**4. Verify registry discovery:**
```bash
cd /nsls2/users/dolds/dev/RoboMage
pixi run list-services

# Should now show 3 services (peak, workflow, normalize)
```

**5. Use in workflow:**
```bash
# Create workflow with normalize node
cat > /tmp/normalize_workflow.json <<'EOF'
{
  "nodes": [
    {
      "id": "load_1",
      "type": "load_files",
      "config": {"file_paths": ["detector_5_roi_175-181_18-218_frames_17847-17978.xy"]}
    },
    {
      "id": "normalize_1",
      "type": "normalize_intensities",
      "config": {},
      "dependencies": ["load_1"]
    }
  ]
}
EOF

# Execute (would need normalize service running)
# This demonstrates the full integration
```

**6. Use from dashboard:**
```bash
pixi run start-all

# Open http://localhost:8050
# Import data
# Run analysis
# Workflow builder includes normalize node
```

**Success Criteria:**
- ✅ Service created in <5 minutes
- ✅ Service works standalone
- ✅ Registry discovers service
- ✅ Workflow integration works
- ✅ Dashboard shows service
- ✅ End-to-end data flow works

**Cleanup:**
```bash
pixi run kill-all
rm -rf services/normalize_intensities
rm /tmp/normalize_workflow.json
```

---

## Test Session 7: Error Handling & Edge Cases (10 minutes)

### Goal
Verify system handles errors gracefully.

### Steps

**1. Test invalid service.json:**
```bash
# Create service with invalid JSON
mkdir -p /tmp/bad_service
echo '{ "invalid json' > /tmp/bad_service/service.json

# Try to discover
pixi run python -c "
from robomage.service_registry import get_registry
registry = get_registry()
# Should handle error gracefully
"
```

**2. Test port conflict:**
```bash
# Create service with duplicate port
cd services
python create_service.py
# Try to use port 8001 (peak_analysis port)
# Expected: Warning about conflict, prompt to choose different port
```

**3. Test service not running:**
```bash
# Check health of stopped service
pixi run check-services
# Expected: Should show ❌ for stopped services
```

**4. Test malformed analyze request:**
```bash
# Start a service
pixi run start-all &
sleep 5

# Send bad request
curl -X POST http://localhost:8001/analyze \
  -H "Content-Type: application/json" \
  -d '{"bad": "data"}'

# Expected: 400 error with helpful message

pixi run kill-all
```

**Success Criteria:**
- ✅ Invalid JSON handled gracefully
- ✅ Port conflicts detected
- ✅ Health checks show accurate status
- ✅ Bad requests return proper errors
- ✅ No crashes or hangs

---

## Testing Checklist

Use this to track testing progress:

### Generator & Templates
- [ ] Service generator runs without errors
- [ ] All template files generated
- [ ] No placeholders in generated code
- [ ] Generated service has valid Python syntax
- [ ] Generated service.json is valid JSON

### Service Functionality
- [ ] Generated service starts successfully
- [ ] Health endpoint responds correctly
- [ ] Analyze endpoint processes data
- [ ] Service handles errors gracefully
- [ ] Service can be stopped cleanly

### Registry System
- [ ] Service auto-discovered by registry
- [ ] `pixi run list-services` works
- [ ] `pixi run check-services` works
- [ ] `pixi run test-services` passes
- [ ] `get_registry()` singleton works

### Dashboard Integration
- [ ] Dashboard starts with services
- [ ] Service status indicators work
- [ ] Analysis tab uses service
- [ ] Results display correctly
- [ ] No JavaScript console errors

### Workflow Integration
- [ ] Service nodes discovered
- [ ] Workflow with service node executes
- [ ] Results returned correctly
- [ ] Workflow Builder shows service nodes

### Documentation Accuracy
- [ ] Migration guide examples work
- [ ] Custom services guide accurate
- [ ] README links work
- [ ] Code examples run as shown

### Performance
- [ ] Service startup time acceptable (<5 seconds)
- [ ] Registry load time fast (<10 ms)
- [ ] Service lookups fast (<1 ms)
- [ ] No memory leaks

### Error Handling
- [ ] Invalid JSON handled
- [ ] Port conflicts detected
- [ ] Network errors handled
- [ ] Bad requests return errors

---

## When to Test

**Recommended Schedule:**

1. **Now (Immediate)**: Quick smoke test
   - Run Test Session 1 (Service Generator)
   - Verify basic functionality works

2. **Before Deployment**: Full test suite
   - Run all 7 test sessions
   - Complete testing checklist
   - Document any issues found

3. **After Bug Fixes**: Regression testing
   - Re-run failed tests
   - Verify fixes work

4. **Regular**: Periodic validation
   - Monthly: Quick smoke tests
   - Quarterly: Full test suite

---

## Quick Smoke Test (5 minutes)

If time is limited, run this minimal test:

```bash
# 1. Create test service
cd /nsls2/users/dolds/dev/RoboMage/services
echo -e "test_smoke\nTest Smoke\nSmoke test service\n8099\n1\ny" | python create_service.py

# 2. Start it
cd test_smoke
python main.py --port 8099 &
sleep 2

# 3. Test health
curl http://localhost:8099/health

# 4. Test analyze
curl -X POST http://localhost:8099/analyze \
  -H "Content-Type: application/json" \
  -d '{"data": {"data_points": [{"x": 1, "y": 10}]}}'

# 5. Cleanup
pkill -f "test_smoke/main.py"
cd ..
rm -rf test_smoke

# If all worked: ✅ Basic system is functional
```

---

## Reporting Issues

If you find issues during testing:

1. **Document the issue:**
   - What you were doing
   - What you expected
   - What actually happened
   - Error messages

2. **Check if it's known:**
   - Review docs/TROUBLESHOOTING.md
   - Check existing tests

3. **Create bug report:**
   - Include steps to reproduce
   - Include system info (Python version, OS, etc.)
   - Attach logs if available

4. **Fix and verify:**
   - Make fix
   - Add test to prevent regression
   - Re-run affected test sessions

---

## Success Criteria for Overall Testing

Testing is complete when:

- ✅ All 7 test sessions passed
- ✅ Testing checklist 100% complete
- ✅ No critical bugs found
- ✅ Documentation verified accurate
- ✅ Performance acceptable
- ✅ Error handling works

**Ready to start testing?** I recommend beginning with **Test Session 1** (Service Generator) to verify the core functionality works. We can then proceed through the other sessions systematically.

Would you like to start testing now? I can guide you through each step.
