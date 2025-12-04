#!/usr/bin/env python
"""
Integration test for GSAS-II refinement service.

CRITICAL: GSAS-II Data Format Requirements
===========================================
This test serves as the REFERENCE IMPLEMENTATION for sending data to GSAS-II.

KEY PRINCIPLE:
CHI files are in Q-space (Å⁻¹), but GSAS-II expects Q values to be labeled
as "two_theta" in the API. The instrument parameter file handles coordinate
conversion internally.

DO NOT CHANGE THIS TEST WITHOUT UNDERSTANDING THE DATA FORMAT!

Common Mistake (DO NOT DO THIS):
    # ❌ WRONG - Manual Q→2θ conversion causes refinement failure
    wavelength = 0.1665  # Å
    two_theta = 2 * np.degrees(np.arcsin(q_array * wavelength / (4 * np.pi)))
    request = {"diffraction_data": {"two_theta": two_theta.tolist(), ...}}
    # Result: "Invalid cell metric tensor", Rwp=0.0%, refinement fails

Correct Approach (THIS TEST):
    # ✅ CORRECT - Send Q values directly as "two_theta"
    request = {"diffraction_data": {"two_theta": q_values.tolist(), ...}}
    # Result: Rwp ≈ 7.7%, cell a ≈ 4.157 Å, refinement succeeds

Expected Results for LaB6 SRM 660c:
- Rwp: 7-8%
- Cell parameter a: ~4.157 Å (cubic, ±0.00003 Å)
- Multiple refinement cycles complete (5 cycles)
- Chi² and GoF are non-null values
- No "Invalid cell metric tensor" errors

Requirements:
- GSAS-II service running on port 8003
- LaB6 test data file available
- Service configured with PDF_1m.instprm and LaB6_SRM_660c.CIF
"""

import json
from pathlib import Path

import numpy as np
import pytest
import requests


# Test configuration
SERVICE_URL = "http://localhost:8003"
TEST_DATA_FILE = Path("/nsls2/users/dolds/dev/autoxrd/fit_service/notebook_testing/assets/"
                      "xrd_LaB6_660c_std_brac2_20250724-194924_70c707_primary-1_mean_tth.chi")


def load_chi_file(filepath: Path) -> tuple[np.ndarray, np.ndarray]:
    """
    Load CHI file and parse Q and intensity data.
    
    Note: Despite the file extension and header saying "2theta", this file
    contains Q-space data (Å⁻¹) with values in range 0.5-16 Å⁻¹.
    """
    q_values = []
    intensities = []
    
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            parts = line.split()
            if len(parts) >= 2:
                try:
                    q_values.append(float(parts[0]))
                    intensities.append(float(parts[1]))
                except ValueError:
                    continue
    
    return np.array(q_values), np.array(intensities)


@pytest.fixture
def service_available():
    """Check if GSAS-II service is running."""
    try:
        response = requests.get(f"{SERVICE_URL}/health", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


@pytest.mark.integration
def test_gsasii_refinement_lab6(service_available):
    """
    Integration test: LaB6 SRM 660c refinement with correct data format.
    
    This test validates:
    1. Correct Q-space data handling (no manual conversion)
    2. Proper recipe format with GSAS-II directives
    3. Expected refinement quality for LaB6 standard
    
    REFERENCE IMPLEMENTATION - DO NOT MODIFY WITHOUT REVIEW
    """
    if not service_available:
        pytest.skip("GSAS-II service not running on port 8003")
    
    if not TEST_DATA_FILE.exists():
        pytest.skip(f"Test data file not found: {TEST_DATA_FILE}")
    
    # Step 1: Load Q-space data
    q_values, intensities = load_chi_file(TEST_DATA_FILE)
    assert len(q_values) > 0, "No data loaded from CHI file"
    assert 0.5 < q_values.min() < 1.0, "Q range unexpected (should start ~0.5-0.7 Å⁻¹)"
    assert 15.0 < q_values.max() < 17.0, "Q range unexpected (should end ~15-16 Å⁻¹)"
    
    # Step 2: Build request - CRITICAL PART
    # ======================================
    # Send Q values directly as "two_theta" - GSAS-II handles conversion via instrument file
    request_payload = {
        "diffraction_data": {
            "two_theta": q_values.tolist(),  # Q values labeled as "two_theta" (NOT converted!)
            "intensity": intensities.tolist(),
        },
        "recipe": {
            "instrument_file": "PDF_1m.instprm",  # Handles Q ↔ 2θ conversion
            "cif_file": "LaB6_SRM_660c.CIF",
            "phase_name": "LaB6",
            "refinement_dict": {
                "set": {
                    "Limits": {"low": 0.5, "high": 16.0},
                    "Background": {"type": "chebyschev-1", "no. coeffs": 3, "refine": True},
                    "Cell": True,
                    "Sample Parameters": ["Scale"]
                },
                "do": "refinement"
            }
        },
        "sample_name": "LaB6_test",
        "cycles": 5,
    }
    
    # Step 3: Send refinement request
    response = requests.post(
        f"{SERVICE_URL}/refine",
        json=request_payload,
        timeout=300
    )
    
    assert response.status_code == 200, f"Service error: {response.status_code} - {response.text}"
    
    # Step 4: Validate results
    result = response.json()
    
    assert result["success"] is True, "Refinement reported failure"
    
    # Validate fit quality
    rwp = result["fit_quality"]["Rwp"]
    assert rwp > 0, "Rwp is 0.0 - refinement did not run (likely data format error)"
    assert 5.0 < rwp < 10.0, f"Rwp {rwp}% outside expected range 5-10% for LaB6"
    
    # Validate cell parameters
    cell_a = result["cell"]["a"]["value"]
    cell_a_esd = result["cell"]["a"]["esd"]
    
    assert 4.15 < cell_a < 4.17, f"Cell a={cell_a} Å outside expected range 4.15-4.17 Å"
    assert cell_a_esd > 0, "Cell ESD is 0.0 - refinement did not refine parameters"
    assert cell_a_esd < 0.001, f"Cell ESD {cell_a_esd} Å is too large (should be <0.001 Å)"
    
    # Validate cubic symmetry (LaB6 is cubic)
    cell_b = result["cell"]["b"]["value"]
    cell_c = result["cell"]["c"]["value"]
    assert abs(cell_a - cell_b) < 0.0001, "Cell is not cubic (a ≠ b)"
    assert abs(cell_a - cell_c) < 0.0001, "Cell is not cubic (a ≠ c)"
    
    # Print summary for manual verification
    print("\n" + "="*70)
    print("GSAS-II Refinement Integration Test - PASSED")
    print("="*70)
    print(f"Rwp:           {rwp:.2f}%")
    print(f"Cell a:        {cell_a:.6f} ± {cell_a_esd:.6f} Å")
    print(f"Data points:   {len(q_values)}")
    print(f"Q range:       {q_values.min():.3f} - {q_values.max():.3f} Å⁻¹")
    print("="*70)
    
    # Save result for reference
    output_path = Path("/tmp/gsasii_integration_test_result.json")
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"Full result saved to: {output_path}")


@pytest.mark.integration
def test_gsasii_data_format_documentation():
    """
    Meta-test: Verify that critical data format requirements are documented.
    
    This test checks that the GSAS-II data format requirements are documented
    in key locations to prevent future mistakes.
    """
    # Check worker documentation
    worker_file = Path("services/gsasii_refinement/gsasii_worker.py")
    if worker_file.exists():
        content = worker_file.read_text()
        assert "CRITICAL DATA FORMAT REQUIREMENT" in content, \
            "Worker missing critical data format documentation"
        assert "DO NOT convert Q to 2θ" in content, \
            "Worker missing Q→2θ conversion warning"
    
    # Check callback documentation
    callback_file = Path("src/robomage/dashboard/callbacks/gsasii_callbacks.py")
    if callback_file.exists():
        content = callback_file.read_text()
        assert "CRITICAL" in content or "Data Format" in content, \
            "Callback missing critical data format documentation"
    
    # Check test documentation
    test_file = Path("test_gsasii_refinement.py")
    if test_file.exists():
        content = test_file.read_text()
        assert "CRITICAL" in content or "Data Format" in content, \
            "Test script missing critical data format documentation"


if __name__ == "__main__":
    """Run test standalone for quick validation."""
    import sys
    
    # Check service
    try:
        response = requests.get(f"{SERVICE_URL}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ GSAS-II service not healthy: {response.status_code}")
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"❌ GSAS-II service not available: {e}")
        print(f"   Start with: pixi run python services/gsasii_refinement/main.py --port 8003")
        sys.exit(1)
    
    # Check data file
    if not TEST_DATA_FILE.exists():
        print(f"❌ Test data file not found: {TEST_DATA_FILE}")
        sys.exit(1)
    
    # Run test
    print("Running GSAS-II integration test...")
    try:
        test_gsasii_refinement_lab6(service_available=True)
        print("\n✅ All assertions passed!")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
