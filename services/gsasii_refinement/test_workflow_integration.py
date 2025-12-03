"""
GSAS-II Workflow Integration Test

Tests the complete workflow integration:
1. Load diffraction files with load_files node
2. Run GSAS-II refinement with gsasii_refinement node
3. Verify results are properly returned

Prerequisites:
    - GSAS-II service must be running on port 8002
    - Workflow engine service must be running on port 8000
    - DRX Demo data accessible at autoxrd repository

Usage:
    cd /nsls2/users/dolds/dev/GSAS-II/pixi
    pixi run python /nsls2/users/dolds/dev/RoboMage/services/gsasii_refinement/main.py --port 8002 &
    
    cd /nsls2/users/dolds/dev/RoboMage
    pixi run python services/workflow_engine/main.py --port 8000 &
    
    cd /nsls2/users/dolds/dev/GSAS-II/pixi
    pixi run python /nsls2/users/dolds/dev/RoboMage/services/gsasii_refinement/test_workflow_integration.py
"""

import json
import sys
from pathlib import Path

import requests

# Test configuration
WORKFLOW_ENGINE_URL = "http://localhost:8000"
GSASII_SERVICE_URL = "http://localhost:8003"
AUTOXRD_DATA_PATH = Path("/nsls2/users/dolds/dev/autoxrd/on-the-fly/test/user_data_DRX_test")

def check_services():
    """Check if required services are running."""
    print("Checking service availability...")
    
    # Check workflow engine
    try:
        resp = requests.get(f"{WORKFLOW_ENGINE_URL}/health", timeout=5)
        if resp.status_code == 200:
            print(f"✓ Workflow engine: {WORKFLOW_ENGINE_URL}")
        else:
            print(f"✗ Workflow engine unhealthy: {resp.status_code}")
            return False
    except Exception as e:
        print(f"✗ Workflow engine not reachable: {e}")
        print(f"  Start with: pixi run python services/workflow_engine/main.py --port 8000")
        return False
    
    # Check GSAS-II service
    try:
        resp = requests.get(f"{GSASII_SERVICE_URL}/health", timeout=5)
        if resp.status_code == 200:
            health = resp.json()
            print(f"✓ GSAS-II service: {GSASII_SERVICE_URL}")
            print(f"  GSAS-II available: {health.get('gsasii_available', False)}")
        else:
            print(f"✗ GSAS-II service unhealthy: {resp.status_code}")
            return False
    except Exception as e:
        print(f"✗ GSAS-II service not reachable: {e}")
        print(f"  Start with: cd /nsls2/users/dolds/dev/GSAS-II/pixi && "
              f"pixi run python /nsls2/users/dolds/dev/RoboMage/services/gsasii_refinement/main.py --port 8002")
        return False
    
    return True


def create_workflow():
    """Create workflow definition for GSAS-II refinement."""
    # Find LaB6 data file
    chi_files = list(AUTOXRD_DATA_PATH.glob("*_tth.chi"))
    if not chi_files:
        raise FileNotFoundError(f"No _tth.chi files found in {AUTOXRD_DATA_PATH}")
    
    chi_file = chi_files[0]
    print(f"\nUsing data file: {chi_file.name}")
    
    workflow = {
        "nodes": [
            {
                "id": "load_1",
                "type": "load_files",
                "config": {
                    "file_paths": [str(chi_file)],
                    "wavelength": 0.1665  # Å (synchrotron default)
                }
            },
            {
                "id": "refine_1",
                "type": "gsasii_refinement",
                "config": {
                    "instrument_file": "PDF_1m.instprm",
                    "cif_file": "LaB6_SRM_660c.CIF",
                    "phase_name": "LaB6",
                    "refinement_cycles": 5,
                    "refine_background": True,
                    "refine_cell": True,
                    "refine_size_strain": False,
                    "service_url": GSASII_SERVICE_URL
                }
            }
        ],
        "edges": [
            {
                "source": "load_1",
                "target": "refine_1",
                "source_output": "output",
                "target_input": "input"
            }
        ]
    }
    
    return workflow


def execute_workflow(workflow):
    """Execute workflow via workflow engine."""
    print("\nExecuting workflow...")
    
    try:
        resp = requests.post(
            f"{WORKFLOW_ENGINE_URL}/execute",
            json={"workflow": workflow},
            timeout=600  # 10 minutes for refinement
        )
        
        if resp.status_code != 200:
            print(f"✗ Workflow execution failed: {resp.status_code}")
            print(resp.text)
            return None
        
        result = resp.json()
        return result
        
    except Exception as e:
        print(f"✗ Workflow execution error: {e}")
        return None


def validate_results(result):
    """Validate refinement results."""
    print("\nValidating results...")
    
    if not result:
        print("✗ No results returned")
        return False
    
    # Check execution status
    if result.get("status") != "completed":
        print(f"✗ Workflow status: {result.get('status')}")
        print(f"  Error: {result.get('error', 'Unknown error')}")
        return False
    
    print(f"✓ Workflow status: {result.get('status')}")
    
    # Check results
    results = result.get("results", {})
    if "refine_1" not in results:
        print("✗ No refinement results found")
        return False
    
    refine_results = results["refine_1"]
    if not refine_results:
        print("✗ Refinement results empty")
        return False
    
    # Validate first result
    first_result = refine_results[0]
    
    required_fields = ["filename", "phase_name", "cell_parameters", "fit_quality"]
    for field in required_fields:
        if field not in first_result:
            print(f"✗ Missing field: {field}")
            return False
    
    print(f"✓ Results structure valid")
    
    # Print key results
    cell = first_result["cell_parameters"]
    fit = first_result["fit_quality"]
    
    print(f"\nRefinement Results:")
    print(f"  Filename: {first_result['filename']}")
    print(f"  Phase: {first_result['phase_name']}")
    print(f"  Cell a: {cell.get('a', 'N/A'):.6f} ± {cell.get('a_esd', 0.0):.6f} Å")
    print(f"  Cell volume: {cell.get('volume', 'N/A'):.4f} ų")
    print(f"  Rwp: {fit.get('Rwp', 'N/A'):.3f}%")
    print(f"  Convergence: {first_result.get('convergence', 'unknown')}")
    print(f"  Data points: {first_result.get('num_data_points', 'N/A')}")
    
    # Validate LaB6 expected values
    expected_a = 4.156  # Å (LaB6 cubic cell parameter)
    actual_a = cell.get("a", 0.0)
    
    if abs(actual_a - expected_a) > 0.01:
        print(f"\n⚠ Warning: Cell parameter a={actual_a:.6f} differs from expected {expected_a:.3f} Å")
    else:
        print(f"\n✓ Cell parameter matches LaB6 reference value")
    
    # Check fit quality
    rwp = fit.get("Rwp", 100.0)
    if rwp < 10.0:
        print(f"✓ Good fit quality (Rwp < 10%)")
    else:
        print(f"⚠ Warning: Rwp={rwp:.3f}% may indicate poor fit")
    
    return True


def main():
    """Main test execution."""
    print("="*60)
    print("GSAS-II Workflow Integration Test")
    print("="*60)
    
    # Step 1: Check services
    if not check_services():
        print("\n✗ Test failed: Services not available")
        return 1
    
    # Step 2: Create workflow
    try:
        workflow = create_workflow()
        print(f"\n✓ Created workflow with {len(workflow['nodes'])} nodes")
    except Exception as e:
        print(f"\n✗ Failed to create workflow: {e}")
        return 1
    
    # Step 3: Execute workflow
    result = execute_workflow(workflow)
    if not result:
        print("\n✗ Test failed: Workflow execution failed")
        return 1
    
    # Step 4: Validate results
    if not validate_results(result):
        print("\n✗ Test failed: Results validation failed")
        return 1
    
    # Success!
    print("\n" + "="*60)
    print("✓ ALL TESTS PASSED")
    print("="*60)
    print("\nGSAS-II workflow integration is working correctly!")
    print(f"- Files loaded via load_files node")
    print(f"- Refinement completed via gsasii_refinement node")
    print(f"- Results validated successfully")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
