#!/usr/bin/env python
"""
Test script for GSAS-II refinement with LaB6 SRM 660c data.

CRITICAL: GSAS-II Data Format Requirements
===========================================
This test demonstrates the CORRECT way to send diffraction data to GSAS-II:

1. CHI files from synchrotron sources contain Q-space data (Å⁻¹)
2. GSAS-II expects Q values to be labeled as "two_theta" in the API
3. The instrument parameter file handles Q ↔ 2θ conversion internally
4. DO NOT manually convert Q to 2θ before sending to the service

WHY THIS MATTERS:
- Manual Q→2θ conversion causes refinement failure
- Symptoms: "Invalid cell metric tensor", Rwp=0.0%, negative cell values
- Root cause: GSAS-II gets doubly-converted data and produces garbage results

WORKFLOW:
1. Load CHI file (Q-space data: 0.647-15.867 Å⁻¹)
2. Send Q values directly labeled as "two_theta" in diffraction_data
3. GSAS-II uses instrument file (PDF_1m.instprm) for coordinate conversion
4. Result: Rwp ≈ 7.7%, cell a ≈ 4.157 Å ✓

Expected Results for LaB6 SRM 660c:
- Rwp: ~7-8%
- Cell parameter a: ~4.157 Å (cubic)
- ESDs: Non-zero (e.g., ±0.00003 Å)
- Multiple refinement cycles complete successfully

Usage:
    python test_gsasii_refinement.py
"""

import json
import numpy as np
import requests

# Configuration
SERVICE_URL = "http://localhost:8003"
TEST_FILE = "/nsls2/users/dolds/dev/autoxrd/fit_service/notebook_testing/assets/xrd_LaB6_660c_std_brac2_20250724-194924_70c707_primary-1_mean_tth.chi"

def load_chi_file(filepath):
    """Load CHI file and parse Q and intensity data."""
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

def convert_q_to_two_theta(q_values, wavelength=0.1665):
    """Convert Q (Å⁻¹) to 2θ (degrees) for given wavelength."""
    # 2θ = 2 * arcsin(Q * λ / (4π))
    two_theta = 2 * np.degrees(np.arcsin(q_values * wavelength / (4 * np.pi)))
    return two_theta

def main():
    print("=" * 70)
    print("GSAS-II Refinement Test - LaB6 SRM 660c")
    print("=" * 70)
    
    # Step 1: Check service health
    print("\n1. Checking GSAS-II service health...")
    try:
        response = requests.get(f"{SERVICE_URL}/health", timeout=5)
        response.raise_for_status()
        health = response.json()
        print(f"   ✅ Service status: {health['status']}")
        print(f"   ✅ GSAS-II available: {health['gsasii_available']}")
    except Exception as e:
        print(f"   ❌ Service not available: {e}")
        print("\n   Start service with:")
        print("   pixi run python services/gsasii_refinement/main.py --port 8003")
        return
    
    # Step 2: Load data file
    print(f"\n2. Loading data from:")
    print(f"   {TEST_FILE}")
    try:
        q_values, intensities = load_chi_file(TEST_FILE)
        print(f"   ✅ Loaded {len(q_values)} data points")
        print(f"   ✅ Q range: {q_values.min():.3f} - {q_values.max():.3f} Å⁻¹")
        print(f"   ✅ Intensity range: {intensities.min():.1f} - {intensities.max():.1f}")
    except Exception as e:
        print(f"   ❌ Failed to load file: {e}")
        return
    
    # Step 3: CRITICAL - Send Q values directly as "two_theta"
    # =========================================================
    # DO NOT convert Q to 2θ! GSAS-II expects Q values labeled as "two_theta"
    # The instrument parameter file (PDF_1m.instprm) handles the conversion
    #
    # ✅ CORRECT: two_theta = q_values (send Q directly)
    # ❌ WRONG:   two_theta = 2 * np.degrees(np.arcsin(q * λ / (4π)))
    #
    # If you convert Q→2θ yourself, refinement will fail with:
    #   - "Invalid cell metric tensor" error
    #   - Negative cell values (e.g., -22248 Å)  
    #   - Rwp = 0.0% (calculation-only, no actual refinement)
    print("\n3. Preparing diffraction data (Q-space)...")
    print(f"   ⚠️  CRITICAL: Sending Q values labeled as 'two_theta'")
    print(f"   ⚠️  GSAS-II will use PDF_1m.instprm to interpret coordinate system")
    two_theta = q_values  # Send Q values directly - no conversion!
    print(f"   ✅ Data range: {two_theta.min():.3f} - {two_theta.max():.3f} Å⁻¹")
    
    # Step 4: Build refinement request
    print("\n4. Building refinement request...")
    request_payload = {
        "diffraction_data": {
            "two_theta": two_theta.tolist(),  # Q values labeled as "two_theta"
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
                    "Cell": True,  # Refine unit cell
                    "Sample Parameters": ["Scale"]  # Refine scale factor
                },
                "do": "refinement"  # GSAS-II action directive
            }
        },
        "sample_name": "LaB6_test",
        "cycles": 5,
    }
    
    print(f"   ✅ Sample: {request_payload['sample_name']}")
    print(f"   ✅ Cycles: {request_payload['cycles']}")
    print(f"   ✅ CIF: {request_payload['recipe']['cif_file']}")
    print(f"   ✅ Instrument: {request_payload['recipe']['instrument_file']}")
    print(f"   ✅ Data points: {len(intensities)}")
    
    # Step 5: Send refinement request
    print("\n5. Sending refinement request to service...")
    print("   (This may take 4-10 seconds...)")
    try:
        response = requests.post(
            f"{SERVICE_URL}/refine",
            json=request_payload,
            timeout=300  # 5 minutes max
        )
        response.raise_for_status()
        result = response.json()
        print("   ✅ Refinement completed successfully!")
    except requests.exceptions.HTTPError as e:
        print(f"   ❌ HTTP Error: {e}")
        if e.response is not None:
            try:
                error_data = e.response.json()
                print(f"\n   Error details:")
                print(json.dumps(error_data, indent=2))
            except:
                print(f"   Response text: {e.response.text}")
        return
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
        return
    
    # Debug: Save response to file
    with open('/tmp/gsasii_test_response.json', 'w') as f:
        json.dump(result, f, indent=2)
    print(f"   📝 Full response saved to: /tmp/gsasii_test_response.json")
    
    # Step 6: Display results
    print("\n" + "=" * 70)
    print("REFINEMENT RESULTS")
    print("=" * 70)
    
    # Success status
    print(f"\nSuccess: {result.get('success', False)}")
    
    # Fit quality
    if 'fit_quality' in result:
        fit_quality = result['fit_quality']
        print("\nFit Quality:")
        rwp = fit_quality.get('Rwp')
        chi2 = fit_quality.get('chi2')
        gof = fit_quality.get('GoF')
        print(f"  Rwp:   {rwp:.2f}%" if rwp is not None else "  Rwp:   N/A")
        print(f"  χ²:    {chi2:.3f}" if chi2 is not None else "  χ²:    N/A")
        print(f"  GoF:   {gof:.2f}" if gof is not None else "  GoF:   N/A")
    
    # Cell parameters
    if 'cell' in result:
        cell = result['cell']
        print("\nCell Parameters:")
        for param in ['a', 'b', 'c']:
            if param in cell:
                val = cell[param]['value']
                esd = cell[param]['esd']
                print(f"  {param}:     {val:.6f} ± {esd:.6f} Å")
        for param in ['alpha', 'beta', 'gamma']:
            if param in cell:
                val = cell[param]['value']
                esd = cell[param]['esd']
                print(f"  {param}: {val:.3f} ± {esd:.3f}°")
    
    # Execution time
    exec_time = result.get('execution_time_s', 0)
    print(f"\nExecution Time: {exec_time:.2f} seconds")
    
    # Warnings
    warnings = result.get('warnings', [])
    if warnings:
        print(f"\nWarnings ({len(warnings)}):")
        for i, warning in enumerate(warnings, 1):
            print(f"  {i}. {warning}")
    else:
        print("\nWarnings: None")
    
    # Validation
    print("\n" + "=" * 70)
    print("VALIDATION")
    print("=" * 70)
    
    if 'fit_quality' in result and 'cell' in result:
        fit_quality = result['fit_quality']
        cell = result['cell']
        
        # Expected values for LaB6 SRM 660c
        expected_rwp = 7.7
        expected_cell_a = 4.157
        
        actual_rwp = fit_quality.get('Rwp', 0)
        actual_cell_a = cell.get('a', {}).get('value', 0)
        
        rwp_ok = abs(actual_rwp - expected_rwp) < 2.0  # Within 2%
        cell_ok = abs(actual_cell_a - expected_cell_a) < 0.01  # Within 0.01 Å
        
        print(f"\nRwp:  {actual_rwp:.2f}% (expected ~{expected_rwp}%)  {'✅' if rwp_ok else '⚠️'}")
        print(f"Cell a: {actual_cell_a:.6f} Å (expected ~{expected_cell_a} Å)  {'✅' if cell_ok else '⚠️'}")
        
        if rwp_ok and cell_ok:
            print("\n🎉 SUCCESS! Results match expected values for LaB6 SRM 660c")
        else:
            print("\n⚠️  Results differ from expected values - check refinement settings")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
