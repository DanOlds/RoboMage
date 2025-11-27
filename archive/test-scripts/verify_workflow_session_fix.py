#!/usr/bin/env python
"""
Quick verification script for Sprint 6 Days 5-6: Workflow Session Integration

This script verifies that the full serialization fix is working correctly.
Run this after starting the workflow service to confirm the fix.

Usage:
    # Terminal 1: Start workflow service
    cd services/workflow_engine && pixi run python main.py --port 8002

    # Terminal 2: Run verification
    pixi run python verify_workflow_session_fix.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import httpx


async def verify_fix():
    """Verify the workflow session integration fix."""

    print("🔍 Verifying Sprint 6 Days 5-6: Workflow Session Integration Fix")
    print("=" * 70)
    print()

    # Check if workflow service is running
    print("1️⃣ Checking workflow service...")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            health_response = await client.get("http://127.0.0.1:8002/health")
            if health_response.status_code == 200:
                print("   ✅ Workflow service is running on port 8002")
            else:
                print(
                    f"   ⚠️  Service responded with status {health_response.status_code}"
                )
                return
    except Exception as e:
        print("   ❌ Cannot connect to workflow service on port 8002")
        print(f"   Error: {e}")
        print()
        print("   Please start the service with:")
        print("   cd services/workflow_engine && pixi run python main.py --port 8002")
        return

    print()

    # Create test workflow
    print("2️⃣ Creating test workflow...")
    examples_dir = str(project_root / "examples")
    workflow_def = {
        "name": "Verification Workflow",
        "description": "Test full serialization",
        "nodes": [
            {
                "id": "load_1",
                "type": "load_files",
                "label": "Load Files",
                "config": {"directory": examples_dir, "pattern": "*.chi"},
                "position": {"x": 100, "y": 100},
            }
        ],
        "edges": [],
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            create_response = await client.post(
                "http://127.0.0.1:8002/workflows", json=workflow_def
            )
            workflow_id = create_response.json()["id"]
            print(f"   ✅ Created workflow: {workflow_id}")
        except Exception as e:
            print(f"   ❌ Failed to create workflow: {e}")
            return

    print()

    # Execute workflow
    print("3️⃣ Executing workflow with full serialization...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            exec_response = await client.post(
                f"http://127.0.0.1:8002/workflows/{workflow_id}/execute",
                json={"metadata": {}},
            )
            exec_result = exec_response.json()

            if exec_result["status"] != "completed":
                print(
                    f"   ❌ Workflow failed: {exec_result.get('error', 'Unknown error')}"
                )
                return

            print("   ✅ Workflow completed successfully")
        except Exception as e:
            print(f"   ❌ Failed to execute workflow: {e}")
            return

    print()

    # Verify full data in results
    print("4️⃣ Verifying full DiffractionData in execution results...")
    node_results = exec_result.get("node_results", [])

    if not node_results:
        print("   ❌ No node results found")
        return

    first_node = node_results[0]
    output = first_node.get("output")

    # Check output structure
    if not isinstance(output, list):
        print(f"   ❌ Expected list output, got: {type(output).__name__}")
        if isinstance(output, dict) and "summary" in output:
            print("   ⚠️  Got summary instead of full data!")
            print("   This means store_full_outputs=False was used")
        return

    if len(output) == 0:
        print("   ❌ Output list is empty")
        return

    first_item = output[0]

    if not isinstance(first_item, dict):
        print(f"   ❌ Expected dict in output list, got: {type(first_item).__name__}")
        return

    # Verify required fields
    required_fields = ["q_values", "intensities", "filename"]
    missing_fields = [f for f in required_fields if f not in first_item]

    if missing_fields:
        print(f"   ❌ Missing required fields: {missing_fields}")
        print(f"   Available fields: {list(first_item.keys())}")
        return

    # Verify data is complete (not truncated)
    q_values = first_item["q_values"]
    intensities = first_item["intensities"]

    if not isinstance(q_values, list):
        print(f"   ⚠️  q_values is not a list: {type(q_values)}")
        return

    if len(q_values) < 500:
        print(f"   ⚠️  q_values seems short ({len(q_values)} points)")
        print("   This might be truncated data")
        return

    print("   ✅ Full DiffractionData found!")
    print(f"      - Filename: {first_item.get('filename')}")
    print(f"      - Q-values: {len(q_values)} points")
    print(f"      - Intensities: {len(intensities)} points")
    print(f"      - Wavelength: {first_item.get('wavelength')}")

    print()

    # Verify dashboard callback compatibility
    print("5️⃣ Verifying dashboard callback compatibility...")
    try:
        import numpy as np

        from robomage.data.models import DiffractionData

        # Simulate dashboard callback extraction
        item = first_item.copy()
        item["q_values"] = np.array(item["q_values"])
        item["intensities"] = np.array(item["intensities"])

        data = DiffractionData(**item)

        print("   ✅ DiffractionData reconstruction successful!")
        print(f"      - Type: {type(data).__name__}")
        print(f"      - Filename: {data.filename}")
        print(f"      - Data points: {len(data.q_values)}")

    except Exception as e:
        print(f"   ❌ Failed to reconstruct DiffractionData: {e}")
        return

    print()
    print("=" * 70)
    print("✅ ALL CHECKS PASSED!")
    print()
    print("The workflow session integration fix is working correctly.")
    print("You can now:")
    print("  1. Start the dashboard: pixi run python -m robomage.dashboard")
    print("  2. Execute workflows in the Workflow tab")
    print("  3. Click 'Save Results to Current Session'")
    print("  4. See files appear in Data Import and Visualization tabs")
    print("=" * 70)


if __name__ == "__main__":
    try:
        asyncio.run(verify_fix())
    except KeyboardInterrupt:
        print("\n\nVerification cancelled by user")
        sys.exit(1)
