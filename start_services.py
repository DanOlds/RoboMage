#!/usr/bin/env python
"""
Start all RoboMage services for the workflow system.

This script starts all required services in the background and
provides a single Ctrl+C handler to stop everything cleanly.
"""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

# Change to project root
project_root = Path(__file__).parent
os.chdir(project_root)

# Track service processes
processes = []


def cleanup(signum=None, frame=None):
    """Kill all background services."""
    print("\n\n🛑 Stopping all services...")
    for proc in processes:
        try:
            proc.terminate()
            proc.wait(timeout=3)
        except Exception:
            proc.kill()
    print("✅ All services stopped")
    sys.exit(0)


# Register signal handler
signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)


def main():
    print("🚀 Starting RoboMage Workflow System...")
    print()

    # Use the current Python executable (should be from pixi when run via 'pixi run start-all')
    python_exe = sys.executable

    # Start Peak Analysis Service
    print("📊 Starting Peak Analysis Service (port 8001)...")
    peak_proc = subprocess.Popen(
        [python_exe, "services/peak_analysis/main.py", "--port", "8001"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    processes.append(peak_proc)
    print(f"   ✓ Peak Analysis PID: {peak_proc.pid}")
    time.sleep(2)

    # Start Workflow Service
    print()
    print("⚙️  Starting Workflow Service (port 8002)...")
    workflow_proc = subprocess.Popen(
        [python_exe, "services/workflow_engine/main.py", "--port", "8002"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    processes.append(workflow_proc)
    print(f"   ✓ Workflow Service PID: {workflow_proc.pid}")
    time.sleep(2)

    # Start Dashboard in foreground
    print()
    print("🌐 Starting Dashboard (port 8050)...")
    print("   Access at: http://localhost:8050")
    print("   Press Ctrl+C to stop all services")
    print()

    try:
        # Run dashboard in foreground (blocking)
        dashboard_proc = subprocess.run(
            [python_exe, "-m", "robomage.dashboard"],
            check=False,
        )
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()


if __name__ == "__main__":
    main()
