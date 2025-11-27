#!/usr/bin/env python
"""
Test the save workflow results callback logic.

This simulates what the dashboard does when you click "Save Results to Current Session".
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import asyncio
import httpx
import numpy as np
from robomage.data.models import DiffractionData
from robomage.persistence.api import SessionManager


async def test_save_workflow_results():
    """Test the complete save workflow results flow."""
    
    print("🧪 Testing Save Workflow Results to Session")
    print("=" * 70)
    
    # 1. Create a session
    print("\n1️⃣ Creating test session...")
    manager = SessionManager()
    
    from datetime import datetime
    session_name = f"Test Workflow Save {datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    session_id = manager.create_session(
        name=session_name,
        description="Testing workflow result saving"
    )
    print(f"   ✅ Created session ID: {session_id}")
    
    # 2. Execute workflow via API
    print("\n2️⃣ Executing workflow...")
    examples_dir = str(project_root / "examples")
    workflow_def = {
        "name": "Test Save Workflow",
        "description": "Test workflow result saving",
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
        # Create workflow
        create_response = await client.post(
            "http://127.0.0.1:8002/workflows", json=workflow_def
        )
        workflow_id = create_response.json()["id"]
        
        # Execute workflow
        exec_response = await client.post(
            f"http://127.0.0.1:8002/workflows/{workflow_id}/execute",
            json={"metadata": {}},
        )
        execution_results = exec_response.json()
    
    print(f"   ✅ Workflow executed: {execution_results['status']}")
    print(f"   Execution ID: {execution_results['execution_id']}")
    
    # 3. Simulate what the callback does
    print("\n3️⃣ Simulating dashboard callback logic...")
    
    # This is what the callback receives
    node_results = execution_results.get("node_results", [])
    print(f"   Found {len(node_results)} node results")
    
    files_saved = 0
    errors = []
    
    for node_result in node_results:
        node_id = node_result.get("node_id")
        output = node_result.get("output")
        status = node_result.get("status")
        
        print(f"\n   Node: {node_id}")
        print(f"   Status: {status}")
        print(f"   Output type: {type(output).__name__}")
        
        if status != "completed":
            print(f"   ⏭️  Skipping (not completed)")
            continue
        
        if isinstance(output, list):
            print(f"   Output has {len(output)} items")
            
            for i, item in enumerate(output):
                if isinstance(item, dict) and "q_values" in item:
                    print(f"\n   Item {i}:")
                    print(f"   - Type: {type(item).__name__}")
                    print(f"   - Has q_values: {'q_values' in item}")
                    print(f"   - Keys: {list(item.keys())}")
                    
                    try:
                        # Convert lists to numpy arrays (as callback does)
                        item_copy = item.copy()
                        if isinstance(item_copy.get("q_values"), list):
                            item_copy["q_values"] = np.array(item_copy["q_values"])
                        if isinstance(item_copy.get("intensities"), list):
                            item_copy["intensities"] = np.array(item_copy["intensities"])
                        
                        # Reconstruct DiffractionData
                        data = DiffractionData(**item_copy)
                        
                        filename = item.get("filename", f"{node_id}_output_{i}.chi")
                        # Use default wavelength if None or missing
                        wavelength = item.get("wavelength") or 0.1665
                        
                        # Save to session
                        manager.add_file_to_session(
                            session_id=session_id,
                            filename=filename,
                            wavelength=wavelength,
                            data=data,
                        )
                        files_saved += 1
                        print(f"   ✅ Saved {filename} to session")
                        
                    except Exception as e:
                        error_msg = f"Failed to save {node_id} output {i}: {str(e)}"
                        print(f"   ❌ {error_msg}")
                        errors.append(error_msg)
                else:
                    print(f"   Item {i}: Not a DiffractionData dict")
        else:
            print(f"   ⚠️  Output is not a list (it's {type(output).__name__})")
    
    # 4. Check results
    print("\n" + "=" * 70)
    if files_saved > 0:
        print(f"✅ SUCCESS: Saved {files_saved} file(s) to session")
        
        # Verify files in session
        session = manager.get_session(session_id)
        print(f"\nSession now has {len(session.files)} file(s):")
        for file in session.files:
            print(f"  - {file.filename} (wavelength: {file.wavelength})")
    else:
        print(f"❌ FAILED: No files saved")
        if errors:
            print(f"\nErrors:")
            for error in errors:
                print(f"  - {error}")
    
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_save_workflow_results())
