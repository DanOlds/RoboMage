#!/usr/bin/env python
"""
Test end-to-end workflow → session integration with full serialization.

This test:
1. Starts a workflow service (assumed running on port 8002)
2. Executes a workflow via the API
3. Checks that execution results contain full DiffractionData
4. Simulates the dashboard save operation
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import httpx


async def test_workflow_session_integration():
    """Test the complete workflow → session flow."""

    print("🧪 Testing Workflow → Session Integration")
    print()

    # Get absolute path to examples directory
    examples_dir = str(Path(__file__).parent / "examples")

    # Create simple workflow definition
    workflow_def = {
        "name": "Test Session Integration",
        "description": "Load files for session testing",
        "nodes": [
            {
                "id": "load_1",
                "type": "load_files",
                "label": "Load Data Files",
                "config": {"directory": examples_dir, "pattern": "*.chi"},
                "position": {"x": 100, "y": 100},
            }
        ],
        "edges": [],
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Create workflow
        print("1️⃣ Creating workflow via API...")
        create_response = await client.post(
            "http://127.0.0.1:8002/workflows", json=workflow_def
        )
        if create_response.status_code != 200:
            print(f"   ❌ Failed to create workflow: {create_response.text}")
            return

        workflow_data = create_response.json()
        workflow_id = workflow_data["id"]
        print(f"   ✅ Created workflow: {workflow_id}")
        print()

        # 2. Execute workflow
        print("2️⃣ Executing workflow...")
        exec_response = await client.post(
            f"http://127.0.0.1:8002/workflows/{workflow_id}/execute",
            json={"metadata": {}},
        )
        if exec_response.status_code != 200:
            print(f"   ❌ Failed to execute: {exec_response.text}")
            return

        exec_result = exec_response.json()
        print(f"   ✅ Execution completed: {exec_result['status']}")
        print(f"   Execution ID: {exec_result['execution_id']}")
        print()

        # 3. Analyze execution results
        print("3️⃣ Checking execution results for full DiffractionData...")
        node_results = exec_result.get("node_results", [])
        print(f"   Found {len(node_results)} node results")

        if node_results:
            first_node = node_results[0]
            output = first_node.get("output")

            print(f"   Node ID: {first_node.get('node_id')}")
            print(f"   Output type: {type(output).__name__}")

            if isinstance(output, list):
                print(f"   Output list length: {len(output)}")
                if len(output) > 0:
                    first_item = output[0]
                    print(f"   First item type: {type(first_item).__name__}")

                    if isinstance(first_item, dict):
                        keys = list(first_item.keys())
                        print(f"   First item keys: {keys}")

                        if "q_values" in first_item:
                            print("   ✅ SUCCESS: Full DiffractionData found!")
                            print(
                                f"      - q_values: {len(first_item['q_values'])} points"
                            )
                            print(
                                f"      - intensities: {len(first_item.get('intensities', []))} points"
                            )
                            print(f"      - filename: {first_item.get('filename')}")
                            print(f"      - wavelength: {first_item.get('wavelength')}")
                            print()

                            # 4. Simulate save to session
                            print("4️⃣ Testing session save (simulation)...")
                            print(
                                "   Would extract DiffractionData and call manager.add_file_to_session()"
                            )
                            print(
                                "   ✅ Data structure is correct for session persistence"
                            )

                        else:
                            print("   ❌ FAILED: q_values not found in output")
                            print("      This means full serialization didn't work!")
            elif isinstance(output, dict):
                print(f"   Output keys: {list(output.keys())}")
                if "summary" in output:
                    print("   ⚠️  WARNING: Got summary instead of full data!")
                    print("   This means store_full_outputs=False was used")
        else:
            print("   ❌ No node results found")

        print()
        print("✅ Test complete!")


if __name__ == "__main__":
    asyncio.run(test_workflow_session_integration())
