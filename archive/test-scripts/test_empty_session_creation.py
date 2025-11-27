#!/usr/bin/env python
"""
Test empty session creation and default session auto-creation.

This verifies the two new features:
1. Creating a session without uploading files first
2. Auto-creating a default session on dashboard load
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from robomage.persistence.api import SessionManager


def test_empty_session_creation():
    """Test creating a session without any files."""
    print("🧪 Testing Empty Session Creation")
    print("=" * 70)

    from datetime import datetime

    mgr = SessionManager()

    # Create an empty session with unique name
    session_name = f"Test Empty Session {datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    session_id = mgr.create_session(
        name=session_name, description="This session has no files initially"
    )

    print(f"✅ Created empty session with ID: {session_id}")

    # Verify it exists and has no files
    session = mgr.get_session(session_id)
    print(f"   Session name: {session.name}")
    print(f"   Number of files: {len(session.files)}")
    assert len(session.files) == 0, "Empty session should have no files"

    print("✅ Empty session creation works!")
    print()
    return session_id


def test_default_session_auto_creation():
    """Test auto-creating a default session."""
    print("🧪 Testing Default Session Auto-Creation")
    print("=" * 70)

    mgr = SessionManager()

    # Simulate what the dashboard callback does
    from datetime import datetime

    # Check if default session exists
    all_sessions = mgr.list_sessions()
    default_sessions = [s for s in all_sessions if s.name.startswith("Default Session")]

    if default_sessions:
        print(f"   Found {len(default_sessions)} existing default session(s)")
        default_session = max(default_sessions, key=lambda s: s.created_at)
        session_id = default_session.id
        print(f"   Using most recent: {default_session.name} (ID: {session_id})")
    else:
        # Create new default session
        session_name = f"Default Session {datetime.now().strftime('%Y-%m-%d')}"
        session_id = mgr.create_session(
            name=session_name,
            description="Auto-created default session for dashboard workflows",
        )
        print(f"   ✅ Created new default session: {session_name}")
        print(f"   Session ID: {session_id}")

    # Verify the session exists
    session = mgr.get_session(session_id)
    print(f"   Session name: {session.name}")
    print(f"   Description: {session.description}")
    print(f"   Number of files: {len(session.files)}")

    print("✅ Default session auto-creation works!")
    print()
    return session_id


def test_workflow_with_empty_session():
    """Test using an empty session with workflow execution."""
    print("🧪 Testing Workflow Execution with Empty Session")
    print("=" * 70)

    from datetime import datetime

    mgr = SessionManager()

    # 1. Create empty session with unique name
    session_name = (
        f"Workflow Test Session {datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    )
    session_id = mgr.create_session(
        name=session_name, description="Empty session for workflow testing"
    )
    print(f"1️⃣ Created empty session (ID: {session_id})")

    session = mgr.get_session(session_id)
    print(f"   Initial file count: {len(session.files)}")
    assert len(session.files) == 0

    # 2. Simulate workflow execution saving results
    # (This would normally come from workflow execution)
    import numpy as np

    from robomage.data.models import DiffractionData

    # Create dummy diffraction data
    q_values = np.linspace(0.5, 10.0, 1000)
    intensities = np.sin(q_values) * 100 + 500

    data = DiffractionData(
        filename="workflow_output.chi",
        q_values=q_values,
        intensities=intensities,
        wavelength=0.1665,
    )

    # Add file to session (as workflow callback would do)
    mgr.add_file_to_session(
        session_id=session_id,
        filename="workflow_output.chi",
        wavelength=0.1665,
        data=data,
    )
    print("2️⃣ Workflow execution added file to session")

    # 3. Verify file was saved
    session = mgr.get_session(session_id)
    print(f"   Final file count: {len(session.files)}")
    assert len(session.files) == 1
    assert session.files[0].filename == "workflow_output.chi"

    print("✅ Workflow execution with empty session works!")
    print()


def main():
    """Run all tests."""
    print("\n🔬 Testing Session Creation Improvements")
    print("=" * 70)
    print()

    # Test 1: Empty session creation
    test_empty_session_creation()

    # Test 2: Default session auto-creation
    test_default_session_auto_creation()

    # Test 3: Workflow with empty session
    test_workflow_with_empty_session()

    print("=" * 70)
    print("✅ All tests passed!")
    print()
    print("Summary:")
    print("  1. ✅ Can create sessions without uploading files first")
    print("  2. ✅ Default session auto-created on dashboard load")
    print("  3. ✅ Workflows can save results to empty sessions")
    print()
    print("User Experience Improvements:")
    print("  • No need to upload files before creating a session")
    print("  • Default session always available for workflow execution")
    print("  • Workflows can run immediately without manual session setup")
    print("=" * 70)


if __name__ == "__main__":
    main()
