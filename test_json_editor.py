#!/usr/bin/env python
"""
Quick manual test for JSON editor functionality.

This script starts the dashboard and provides instructions for testing
the new JSON editor feature.

Usage:
    pixi run python test_json_editor.py
"""

import sys
import time


def print_instructions():
    """Print testing instructions."""
    print("\n" + "=" * 70)
    print("🧪 JSON EDITOR MANUAL TESTING GUIDE")
    print("=" * 70)
    print("\n📋 Pre-requisites:")
    print("   1. Workflow service must be running on port 8002")
    print("   2. Peak analysis service on port 8001 (optional)")
    print("\n🚀 Quick Start:")
    print("   pixi run start-all  # Start all services")
    print("\n" + "=" * 70)
    print("\n🎯 Test Procedure:")
    print("\n1️⃣  TOGGLE JSON EDITOR")
    print("   • Navigate to Workflow Builder tab")
    print("   • Look for 'Show JSON' button (gray, bottom of canvas)")
    print("   • Click it - panel should expand with JSON")
    print("   • Button text should change to 'Hide JSON'")
    print("   • Click again - panel should collapse")
    print("\n2️⃣  VERIFY AUTO-SYNC (Canvas → JSON)")
    print("   • Click 'Show JSON' to open editor")
    print("   • Add a node from the palette (e.g., 'Load Files')")
    print("   • JSON should update automatically")
    print("   • Check that new node appears in JSON with correct structure")
    print("\n3️⃣  MANUAL JSON EDIT (JSON → Canvas)")
    print("   • In JSON editor, change a node's label:")
    print('     "label": "Load Data Files" → "label": "My Custom Name"')
    print("   • Click 'Apply JSON' button")
    print("   • Should see green success message")
    print("   • Node on canvas should update with new label")
    print("\n4️⃣  TEST VALIDATION - INVALID JSON SYNTAX")
    print("   • In JSON editor, add invalid syntax:")
    print('     {"nodes": [missing bracket}')
    print("   • Click 'Apply JSON'")
    print("   • Should see red error with JSON syntax message")
    print("   • Canvas should NOT update")
    print("\n5️⃣  TEST VALIDATION - MISSING REQUIRED KEYS")
    print("   • Remove the 'edges' key from JSON")
    print("   • Click 'Apply JSON'")
    print("   • Should see red error: 'missing edges key'")
    print("\n6️⃣  TEST VALIDATION - WORKFLOW CYCLES")
    print("   • Create a cycle in the edges:")
    print('     {"id": "e1", "source": "n1", "target": "n2"}')
    print('     {"id": "e2", "source": "n2", "target": "n1"}')
    print("   • Click 'Apply JSON'")
    print("   • Should see validation error about cycles")
    print("\n7️⃣  TEST LOAD WORKFLOW")
    print("   • Load a saved workflow (if any exist)")
    print("   • JSON editor should update with loaded workflow")
    print("   • Canvas should update too")
    print("\n" + "=" * 70)
    print("\n✅ SUCCESS CRITERIA:")
    print("   • Toggle works smoothly")
    print("   • Canvas changes auto-update JSON")
    print("   • Valid JSON updates canvas")
    print("   • Invalid JSON shows clear errors")
    print("   • Validation prevents bad workflows")
    print("\n" + "=" * 70)
    print("\n🌐 Opening dashboard at http://localhost:8050")
    print("   Press Ctrl+C to stop\n")


def check_services():
    """Check if required services are running."""
    import requests

    services = {
        "Workflow Engine": "http://localhost:8002/health",
        "Peak Analysis": "http://localhost:8001/health",
    }

    print("\n🔍 Checking services...")
    all_up = True
    for name, url in services.items():
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                print(f"   ✅ {name} is running")
            else:
                print(f"   ⚠️  {name} returned {response.status_code}")
                all_up = False
        except Exception:
            print(f"   ❌ {name} is NOT running")
            all_up = False

    if not all_up:
        print("\n⚠️  Some services are not running!")
        print("   Run: pixi run start-all")
        print("   Or start services individually:")
        print("     Terminal 1: pixi run python services/workflow_engine/main.py")
        print("     Terminal 2: pixi run python services/peak_analysis/main.py")
        response = input("\n   Continue anyway? [y/N]: ")
        if response.lower() != "y":
            sys.exit(1)


def start_dashboard():
    """Start the dashboard."""
    from robomage.dashboard.app import create_app

    app = create_app(debug=True)
    print("\n🎉 Dashboard starting...")
    print("=" * 70 + "\n")
    app.run(debug=True, host="0.0.0.0", port=8050)


if __name__ == "__main__":
    print_instructions()
    time.sleep(2)
    check_services()
    time.sleep(1)
    start_dashboard()
