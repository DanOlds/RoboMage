#!/usr/bin/env python
"""
Start all RoboMage services for the workflow system.

This script uses the service registry to dynamically discover and start
all auto-start services in the background, providing a single Ctrl+C
handler to stop everything cleanly.
"""

import os
import shlex
import signal
import subprocess
import sys
import time
from pathlib import Path

# Change to project root
project_root = Path(__file__).parent
os.chdir(project_root)

# Add project to path for imports
sys.path.insert(0, str(project_root / "src"))

from robomage.service_registry import get_registry

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

    # Load service registry
    try:
        registry = get_registry()
        auto_start_services = registry.get_auto_start_services()
        print(f"📋 Found {len(auto_start_services)} auto-start services")
        print()
    except Exception as e:
        print(f"❌ Failed to load service registry: {e}")
        print("   Falling back to hardcoded services...")
        auto_start_services = []

    # Use the current Python executable (should be from pixi when run via 'pixi run start-all')
    python_exe = sys.executable

    # Start all auto-start services
    if auto_start_services:
        for service in auto_start_services:
            print(f"🔧 Starting {service.display_name} (port {service.port})...")

            # Parse startup command and replace placeholders
            # Use shlex.split for proper command parsing (handles paths with spaces on Windows)
            cmd_str = service.format_startup_command()
            
            # Replace 'python' with actual Python executable (critical for Windows)
            if cmd_str.startswith("python "):
                cmd_str = f"{python_exe} {cmd_str[7:]}"
            
            cmd_parts = shlex.split(cmd_str)
            
            # Create log file for service output
            log_path = project_root / f"{service.name}.log"
            log_file = open(log_path, "w")

            # Start service
            proc = subprocess.Popen(
                cmd_parts,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                cwd=project_root,
            )
            processes.append(proc)
            print(f"   ✓ {service.display_name} PID: {proc.pid}")
            print(f"   📝 Logs: {log_path}")
            
            # Wait a moment and check if process is still running
            time.sleep(2)
            if proc.poll() is not None:
                print(f"   ⚠️  WARNING: Process exited with code {proc.returncode}")
                print(f"   📄 Check logs: {log_path}")
            print()
    else:
        # Fallback to hardcoded services if registry fails
        print("📊 Starting Peak Analysis Service (port 8001)...")
        peak_proc = subprocess.Popen(
            [python_exe, "services/peak_analysis/main.py", "--port", "8001"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        processes.append(peak_proc)
        print(f"   ✓ Peak Analysis PID: {peak_proc.pid}")
        time.sleep(2)
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
        print()

    # Start Dashboard in foreground
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
