# Testing GSAS-II Service

## Prerequisites

1. **GSAS-II Installation Required**
   - The service requires GSAS-II Python API
   - See: `/nsls2/users/dolds/dev/autoxrd/GSASII_pixi_installation_instructions.md`

2. **Install Service Dependencies**
   ```bash
   # From RoboMage root
   pip install -r services/gsasii_refinement/requirements.txt
   
   # Or with pixi (recommended)
   pixi install
   ```

## Manual Testing

### Test 1: LaB6 IPF Fit (DRX Demo)

Tests instrument profile function refinement with LaB6 NIST standard.

```bash
cd services/gsasii_refinement
python test_lab6.py
```

**Expected Output:**
- Rwp: ~2-5% (LaB6 is a good standard)
- Cell a ≈ 4.156 Å (cubic LaB6)
- Fit plot saved to `test_output/lab6_fit.png`
- JSON results in `test_output/lab6_result.json`

### Test 2: Service API (via FastAPI)

Start the service and test via HTTP:

```bash
# Terminal 1: Start service
cd services/gsasii_refinement
python main.py
# Service runs on http://localhost:8002

# Terminal 2: Test endpoints
# Health check
curl http://localhost:8002/health

# API docs
open http://localhost:8002/docs
```

### Test 3: Client Library (Future)

Once client library is implemented:

```python
from robomage.clients.gsasii_client import GSASIIClient

client = GSASIIClient("http://localhost:8002")
result = client.refine(data, recipe, "sample_name")
```

## Integration Testing (TODO)

```bash
pytest services/gsasii_refinement/tests/
```

Tests to implement:
- [ ] Health check endpoint
- [ ] Refinement with all 3 bundled recipes
- [ ] Base64 CIF upload
- [ ] Error handling (missing files, bad recipe)
- [ ] Large datasets (performance)

## Troubleshooting

### GSAS-II Import Error

```
ImportError: No module named 'GSASII'
```

**Solution:** Install GSAS-II
- Via conda: `conda install -c briantoby gsas2full`
- Via pixi: See autoxrd installation guide
- Manual: Clone and build GSAS-II from source

### File Not Found Errors

```
FileNotFoundError: Could not resolve file: LaB6_SRM_660c.CIF
```

**Solution:** Ensure assets directory exists
```bash
ls services/gsasii_refinement/assets/cifs/
# Should contain LaB6_SRM_660c.CIF
```

### Poor Fit Quality (High Rwp)

```
Rwp > 20% - poor fit quality
```

**Possible Causes:**
- Wrong instrument parameters
- Q-range mismatch
- Background not well refined
- Wrong crystal structure (CIF)

**Solution:** Check recipe parameters match your data

## Known Issues

1. **GSAS-II Not in Pixi Yet**
   - GSAS-II packaging for pixi is in progress
   - Currently requires manual installation
   - See autoxrd docs for latest install method

2. **Wavelength Conversion**
   - Service expects Q-space data
   - GSAS-II uses 2θ internally
   - Conversion requires wavelength from metadata
   - Currently using Q data directly (works if instrument file matches)

## Next Steps

- [ ] Add pytest integration tests
- [ ] Test all 3 bundled recipes
- [ ] Validate against autoxrd results
- [ ] Add error handling tests
- [ ] Performance benchmarking
