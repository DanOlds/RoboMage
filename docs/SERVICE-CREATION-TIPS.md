# Service Creation Tips & Critical Learnings

**Based on hands-on testing - December 2, 2025**

This document captures the most important learnings from comprehensive testing of the custom services architecture. Read this before creating your first service!

---

## ⚡ Quick Reference

### The 5-Minute Service Creation Recipe

```bash
# 1. Create (30 seconds)
cd services
python create_service.py  # Follow prompts

# 2. Test immediately (30 seconds)
cd your_service
pixi run python main.py --port 8003 &
sleep 3

# 3. Verify (30 seconds)
curl http://localhost:8003/health
curl -X POST http://localhost:8003/analyze \
  -H "Content-Type: application/json" \
  -d '{"data": {"data_points": [{"x": 1.0, "y": 100.0}]}}'

# 4. Confirm registration (10 seconds)
pixi run list-services

# 5. Customize (as needed)
# Edit analysis.py with your algorithm
# Service works out-of-box - customize when ready!
```

**Total time:** <5 minutes to working, tested, registered service

---

## 🎯 Critical Dos and Don'ts

### ✅ ALWAYS DO

**1. Use Pixi (Not pip/conda/venv)**
```bash
# ✅ CORRECT
pixi run python main.py --port 8003
pixi run list-services
pixi run start-all

# ❌ WRONG - May cause environment conflicts
pip install -r requirements.txt
python main.py --port 8003
```
**Why?** Pixi ensures consistent environment across Windows/Linux, faster dependency resolution, and all project dependencies already included.

**2. Test Generated Service Before Customizing**
```bash
# Service works immediately with template code!
python create_service.py      # Create
cd your_service
pixi run python main.py &      # Start
curl http://localhost:8003/health  # Test
# See it work BEFORE editing anything!
```
**Why?** Confirms template is working, isolates any issues to your code changes.

**3. Verify Auto-Registration**
```bash
pixi run list-services
# Your service should appear immediately
```
**Why?** If service doesn't appear, there's likely a service.json syntax error.

**4. Use Unique Ports**
```bash
# Reserved ports:
# 8001 - Peak Analysis Service
# 8002 - Workflow Engine Service
# 8050 - Dashboard

# Your services: Use 8003-8009, 8100-8199, etc.
```
**Why?** Port conflicts prevent service startup. Registry detects conflicts but can't auto-fix them.

**5. Check Health Endpoint First**
```bash
# Before testing analysis, confirm service is running:
curl http://localhost:8003/health
# Expected: {"status":"healthy",...} in <100ms

# If this fails, don't bother testing /analyze yet
```
**Why?** Health check confirms service is reachable. If this fails, everything else will fail.

### ❌ NEVER DO

**1. Don't Use pip/conda Directly**
```bash
# ❌ WRONG - Bypasses project environment
pip install -r requirements.txt
conda install package

# ✅ CORRECT - Use pixi
pixi run python ...
# Dependencies already available in pixi environment
```

**2. Don't Edit service.json Manually (Unless Needed)**
```bash
# ❌ RISKY - Easy to introduce JSON syntax errors
vim services/your_service/service.json

# ✅ BETTER - Use generator, it creates valid JSON
python create_service.py

# Only edit service.json if you need to:
# - Change port
# - Update description
# - Modify integration settings
```

**3. Don't Forget to Test Health Endpoint**
```bash
# ❌ WRONG - Jump straight to complex testing
curl -X POST http://localhost:8003/analyze -d @complex_data.json

# ✅ CORRECT - Test health first
curl http://localhost:8003/health
# Then test analyze endpoint
```

**4. Don't Create Monolithic Services**
```bash
# ❌ WRONG - One service doing everything
my_analysis_service:
  - peak detection
  - background subtraction  
  - peak fitting
  - phase identification
  - unit cell calculation

# ✅ CORRECT - Focused services composed via workflows
peak_detection_service: Just detect peaks
background_subtraction_service: Just subtract background
peak_fitting_service: Just fit profiles
# Compose them in workflows!
```

**5. Don't Ignore Error Messages**
```bash
# ❌ WRONG - Ignore 422 validation errors
curl -X POST .../analyze -d '{"bad": "data"}'
# Returns 422 with details
# "Oh well, I'll try something else..."

# ✅ CORRECT - Read the error details
# Pydantic tells you exactly what's wrong:
# {"detail": [{"loc": ["data", "data_points"], "msg": "field required"}]}
# Fix your request to match the schema
```

---

## 🔍 Common Pitfalls & Solutions

### Pitfall 1: "Service won't start"

**Symptom:**
```bash
pixi run python main.py --port 8003
# Hangs or shows error
```

**Common Causes:**

1. **Port already in use:**
```bash
# Check what's on that port:
lsof -i :8003
# Solution: Use different port or kill the process
pkill -f "main.py --port 8003"
```

2. **Invalid service.json:**
```bash
# Validate JSON syntax:
cat service.json | python -m json.tool
# If this errors, fix the JSON syntax
```

3. **Module import errors:**
```bash
# Make sure you're using pixi:
pixi run python main.py --port 8003
# NOT: python main.py --port 8003
```

### Pitfall 2: "Service not discovered"

**Symptom:**
```bash
pixi run list-services
# Your service is missing!
```

**Solutions (in order):**

1. **Check service.json exists:**
```bash
ls services/your_service/service.json
```

2. **Validate JSON syntax:**
```bash
cat services/your_service/service.json | python -m json.tool
```

3. **Check required fields:**
```json
{
  "name": "your_service",          // Required
  "display_name": "Your Service",  // Required
  "port": 8003,                    // Required
  "workflow_integration": {        // Required
    "enabled": true
  },
  "dashboard_integration": {       // Required
    "enabled": true
  }
}
```

4. **Restart registry scan:**
```bash
pixi run python -c "from robomage.service_registry import get_registry; get_registry(force_reload=True)"
```

### Pitfall 3: "Workflow node missing"

**Symptom:**
```
Workflow builder doesn't show my service as a node
```

**Solutions:**

1. **Check service is running:**
```bash
curl http://localhost:8003/health
# Must return 200 OK
```

2. **Restart workflow engine:**
```bash
pixi run kill-all
pixi run start-all
# Workflow engine discovers nodes at startup
```

3. **Verify workflow integration enabled:**
```json
{
  "workflow_integration": {
    "enabled": true,
    "node_types": ["your_node_type"]
  }
}
```

**Expected behavior:** Node discovery may require workflow engine restart (MVP limitation).

### Pitfall 4: "Analysis returns 422 error"

**Symptom:**
```bash
curl -X POST http://localhost:8003/analyze ...
# {"detail": [{"type": "missing", "loc": [...], ...}]}
```

**Solution:** Use FastAPI auto-docs to see exact schema:
```bash
# Open in browser:
http://localhost:8003/docs

# Click on POST /analyze
# Click "Try it out"
# See example request format
# Match your request to this format
```

**Common mistakes:**
- Missing required fields
- Wrong field names (data_points vs datapoints)
- Wrong types (string instead of number)
- Missing nested objects

### Pitfall 5: "Service slow or timeout"

**Symptom:**
```bash
curl -X POST http://localhost:8003/analyze ...
# Takes >30 seconds or times out
```

**Quick diagnostics:**
```python
# Add timing to your analysis.py:
import time
import logging
logger = logging.getLogger(__name__)

def perform_analysis(data, config):
    start = time.time()
    
    # Your algorithm here
    results = ...
    
    elapsed = time.time() - start
    logger.info(f"Analysis took {elapsed:.2f}s for {len(data.data_points)} points")
    return results
```

**Common causes:**
- Inefficient loops (use numpy vectorization)
- Large data arrays (>100,000 points)
- Excessive logging in tight loops
- Memory allocation issues

**Performance expectations:**
- Health check: <100ms
- Simple stats: <10ms  
- Peak detection: <500ms
- Complex fitting: <2 seconds

---

## 📊 Performance Expectations

**From validated testing (December 2025):**

| Operation | Expected Time | Threshold |
|-----------|---------------|-----------|
| Service creation | <2 minutes | If >5 min, check network/disk |
| Service startup | <5 seconds | If >10s, check imports/init |
| Health check | <100ms | If >1s, service has issues |
| Registry discovery | Instant | If delayed, check service.json |
| Simple analysis | <10ms | If >100ms, optimize algorithm |
| Peak detection | <500ms | If >2s, reduce data or optimize |
| Complex fitting | <2 seconds | If >10s, consider batching |

**If performance is outside these ranges, investigate!**

---

## 🧪 Testing Workflow (Validated Pattern)

This is the **exact workflow** validated in hands-on testing:

### Step 1: Create Service (1 minute)
```bash
cd services
python create_service.py
# Fill in prompts - takes <1 minute
```

### Step 2: Immediate Testing (1 minute)
```bash
cd your_service

# Start service
pixi run python main.py --port 8003 &
sleep 3

# Test health (should be <100ms)
time curl http://localhost:8003/health
# Expected: {"status":"healthy","service":"your_service","version":"1.0.0"}
# Time: real 0m0.05s

# Test analyze with minimal data
curl -X POST http://localhost:8003/analyze \
  -H "Content-Type: application/json" \
  -d '{"data": {"data_points": [{"x": 1.0, "y": 100.0}]}}'
# Expected: JSON response with results (template returns basic stats)
```

**Key insight:** Template code works! You should see valid results before editing anything.

### Step 3: Verify Registration (30 seconds)
```bash
pixi run list-services
# Should show your service in the list

# Check service details
pixi run python -c "
from robomage.service_registry import get_registry
service = get_registry().get_service('your_service')
print(f'Found: {service.display_name}')
print(f'Port: {service.port}')
print(f'Workflow: {service.workflow_integration.enabled}')
"
```

### Step 4: Test with Real Data (2 minutes)
```bash
# Create test request file
cat > test_request.json <<EOF
{
  "data": {
    "data_points": [
      {"x": 1.0, "y": 100.0},
      {"x": 2.0, "y": 150.0},
      {"x": 3.0, "y": 125.0}
    ]
  },
  "config": {
    "parameter1": "test_value"
  }
}
EOF

# Test with file
curl -X POST http://localhost:8003/analyze \
  -H "Content-Type: application/json" \
  -d @test_request.json

# Check response is valid JSON and has expected fields
```

### Step 5: Customize & Iterate (as needed)
```bash
# Now edit analysis.py with your algorithm
vim analysis.py

# Service auto-reloads in dev mode (if using --reload)
# Or restart:
pkill -f "main.py --port 8003"
pixi run python main.py --port 8003 &

# Test again
curl -X POST http://localhost:8003/analyze -d @test_request.json
```

### Step 6: Integration Testing (2 minutes)
```bash
# Start full system
pixi run start-all

# Open dashboard
# http://localhost:8050

# Test in dashboard:
# 1. Data Import tab - upload file
# 2. Analysis tab - your service should appear
# 3. Run analysis - results should display

# Test in workflow:
# 1. Workflow Builder tab
# 2. Your service node should be available
# 3. Create workflow using your node
# 4. Execute and verify results
```

**Total testing time:** <10 minutes from creation to full integration

---

## 💡 Pro Tips

### Tip 1: Use FastAPI Docs for Development

```bash
# Start your service
pixi run python main.py --port 8003

# Open browser to:
http://localhost:8003/docs

# You get:
# - Interactive API testing (Try it out button)
# - Request/response schemas
# - Example data
# - Live testing without curl

# This is faster than command-line testing!
```

### Tip 2: Add Debug Logging Early

```python
# In analysis.py, add early:
import logging
logger = logging.getLogger(__name__)

def perform_analysis(data, config):
    logger.info(f"Analysis started with {len(data.data_points)} points")
    logger.debug(f"Config: {config.model_dump()}")
    
    # Your code here
    
    logger.info(f"Analysis complete, found {len(results)} results")
    return results
```

**Benefits:**
- Easier debugging when things go wrong
- Performance monitoring
- Audit trail for analysis runs

### Tip 3: Test Health Check Separately

```bash
# Create a simple health check script
cat > check_health.sh <<'EOF'
#!/bin/bash
SERVICE_PORT=${1:-8003}
RESPONSE=$(curl -s -w "\n%{http_code}" http://localhost:$SERVICE_PORT/health)
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" -eq 200 ]; then
    echo "✅ Service healthy on port $SERVICE_PORT"
    echo "$BODY" | python -m json.tool
else
    echo "❌ Service unhealthy on port $SERVICE_PORT (HTTP $HTTP_CODE)"
fi
EOF

chmod +x check_health.sh

# Use it:
./check_health.sh 8003
```

### Tip 4: Create Sample Data Files

```bash
# Keep test data files in service directory
mkdir test_data

# Minimal test
cat > test_data/minimal.json <<EOF
{
  "data": {"data_points": [{"x": 1.0, "y": 100.0}]}
}
EOF

# Typical test
cat > test_data/typical.json <<EOF
{
  "data": {
    "data_points": [
      {"x": 1.0, "y": 100.0},
      {"x": 2.0, "y": 150.0},
      {"x": 3.0, "y": 125.0}
    ]
  },
  "config": {"prominence": 50}
}
EOF

# Edge case tests
# test_data/empty.json
# test_data/large.json
# test_data/invalid.json

# Test quickly:
curl -X POST http://localhost:8003/analyze -d @test_data/typical.json
```

### Tip 5: Monitor Service Logs

```bash
# Start service with visible logs
pixi run python main.py --port 8003

# Or redirect to file
pixi run python main.py --port 8003 > service.log 2>&1 &

# Monitor in real-time
tail -f service.log

# Filter for errors
tail -f service.log | grep ERROR

# Filter for your analysis logs
tail -f service.log | grep "perform_analysis"
```

---

## 🎓 Key Learnings Summary

**From 7 test sessions with 100% pass rate:**

1. **Service creation is fast** - <2 minutes from start to working service
2. **Template code works out-of-box** - Test before customizing!
3. **Auto-discovery is instant** - No manual registration needed
4. **Always use Pixi** - Not pip/conda/venv
5. **Health checks are critical** - Test this first, always
6. **Error messages are helpful** - Read them carefully
7. **Performance is excellent** - <5s startup, <100ms health checks
8. **Cross-platform works** - Windows and Linux confirmed
9. **Documentation is accurate** - Examples run as shown
10. **Developer experience is smooth** - Minimal friction

**Biggest surprise:** How well the template code works immediately. You can test a new service in <5 minutes without writing any custom code!

---

## 📚 Related Documentation

- **Full Guide:** `docs/CUSTOM-SERVICES-GUIDE.md`
- **Testing Results:** `docs/HANDS-ON-TESTING-RESULTS.md`
- **Migration Guide:** `docs/MIGRATION-GUIDE.md`
- **Troubleshooting:** `docs/TROUBLESHOOTING.md`

---

## 🚀 Next Steps

**After reading this document:**

1. Create your first service following the 5-minute recipe
2. Test immediately using the validated workflow
3. Verify auto-registration with `pixi run list-services`
4. Only then customize the analysis code
5. Re-test after each change
6. Check the full guide for advanced topics

**Remember:** The system is production-ready and well-tested. Trust the process, follow the patterns, and you'll have a working service in minutes!

---

*Last updated: December 2, 2025*  
*Based on comprehensive hands-on testing with 100% pass rate*  
*Validated on Linux (Rocky 8) and Windows platforms*
