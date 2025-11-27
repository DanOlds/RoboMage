"""
Tests for workflow persistence functionality.

Tests the integration of workflow definitions with the session persistence layer.
"""

import pytest

from robomage.persistence.api import SessionManager


@pytest.fixture
def session_manager():
    """Create SessionManager with in-memory database for testing."""
    return SessionManager(db_path=":memory:")


@pytest.fixture
def test_session(session_manager, request):
    """Create a test session with unique name per test."""
    # Use the test function name to create unique session names
    test_name = request.node.name
    session_id = session_manager.create_session(
        name=f"Test Session {test_name}", description="Session for workflow testing"
    )
    return session_id


@pytest.fixture
def sample_workflow_definition():
    """Create a sample workflow definition."""
    return {
        "name": "Test Workflow",
        "description": "A test workflow",
        "nodes": [
            {
                "id": "load_1",
                "type": "load_files",
                "label": "Load Data",
                "config": {"directory": "examples", "pattern": "*.chi"},
            },
            {
                "id": "analyze_1",
                "type": "peak_analysis",
                "label": "Analyze Peaks",
                "config": {"profile_type": "gaussian", "prominence": 0.1},
            },
        ],
        "edges": [{"id": "edge_1", "source": "load_1", "target": "analyze_1"}],
    }


def test_save_workflow_to_session(
    session_manager, test_session, sample_workflow_definition, request
):
    """Test saving workflow definition to session."""
    workflow_id = session_manager.save_workflow_to_session(
        session_id=test_session,
        workflow_definition=sample_workflow_definition,
        workflow_name=f"Test Workflow {request.node.name}",
        workflow_description="Testing workflow persistence",
    )

    assert workflow_id is not None
    assert isinstance(workflow_id, str)

    # Verify workflow was saved
    loaded = session_manager.load_workflow(workflow_id)
    assert loaded["name"] == f"Test Workflow {request.node.name}"
    assert loaded["definition"] == sample_workflow_definition
    assert loaded["session_id"] == test_session


def test_save_workflow_without_session(session_manager, sample_workflow_definition):
    """Test saving workflow without linking to a session."""
    workflow_id = session_manager.save_workflow_to_session(
        session_id=None,
        workflow_definition=sample_workflow_definition,
        workflow_name="Standalone Workflow",
        workflow_description="No session link",
    )

    assert workflow_id is not None

    loaded = session_manager.load_workflow(workflow_id)
    assert loaded["name"] == "Standalone Workflow"
    assert loaded["session_id"] is None


def test_get_workflows_for_session(
    session_manager, test_session, sample_workflow_definition
):
    """Test retrieving all workflows linked to a session."""
    # Save multiple workflows to the session
    wf1_id = session_manager.save_workflow_to_session(
        session_id=test_session,
        workflow_definition=sample_workflow_definition,
        workflow_name="Workflow 1",
    )

    wf2_def = {**sample_workflow_definition, "name": "Workflow 2"}
    wf2_id = session_manager.save_workflow_to_session(
        session_id=test_session,
        workflow_definition=wf2_def,
        workflow_name="Workflow 2",
    )

    # Retrieve workflows for session
    workflows = session_manager.get_workflows_for_session(test_session)

    assert len(workflows) == 2
    assert any(wf["id"] == wf1_id for wf in workflows)
    assert any(wf["id"] == wf2_id for wf in workflows)
    assert all("definition" in wf for wf in workflows)
    assert all("created_at" in wf for wf in workflows)


def test_load_workflow(
    session_manager, test_session, sample_workflow_definition, request
):
    """Test loading a workflow definition by ID."""
    workflow_id = session_manager.save_workflow_to_session(
        session_id=test_session,
        workflow_definition=sample_workflow_definition,
        workflow_name=f"Test Workflow {request.node.name}",
    )

    loaded = session_manager.load_workflow(workflow_id)

    assert loaded["id"] == workflow_id
    assert loaded["name"] == f"Test Workflow {request.node.name}"
    assert loaded["definition"] == sample_workflow_definition
    assert loaded["session_id"] == test_session
    assert "created_at" in loaded
    assert "updated_at" in loaded


def test_load_nonexistent_workflow(session_manager):
    """Test loading a workflow that doesn't exist."""
    with pytest.raises(ValueError, match="Workflow .* not found"):
        session_manager.load_workflow("nonexistent-id")


def test_delete_workflow(
    session_manager, test_session, sample_workflow_definition, request
):
    """Test deleting a workflow."""
    workflow_id = session_manager.save_workflow_to_session(
        session_id=test_session,
        workflow_definition=sample_workflow_definition,
        workflow_name=f"Test Workflow {request.node.name}",
    )

    # Verify it exists
    loaded = session_manager.load_workflow(workflow_id)
    assert loaded is not None

    # Delete it
    session_manager.delete_workflow(workflow_id)

    # Verify it's gone
    with pytest.raises(ValueError, match="Workflow .* not found"):
        session_manager.load_workflow(workflow_id)


def test_delete_nonexistent_workflow(session_manager):
    """Test deleting a workflow that doesn't exist."""
    with pytest.raises(ValueError, match="Workflow .* not found"):
        session_manager.delete_workflow("nonexistent-id")


def test_workflow_cascade_delete_with_session(
    session_manager, test_session, sample_workflow_definition, request
):
    """Test that workflows are deleted when their session is deleted."""
    workflow_id = session_manager.save_workflow_to_session(
        session_id=test_session,
        workflow_definition=sample_workflow_definition,
        workflow_name=f"Test Workflow {request.node.name}",
    )

    # Verify workflow exists
    loaded = session_manager.load_workflow(workflow_id)
    assert loaded is not None

    # Delete the session
    session_manager.delete_session(test_session)

    # Verify workflow is also deleted (cascade)
    with pytest.raises(ValueError, match="Workflow .* not found"):
        session_manager.load_workflow(workflow_id)


def test_duplicate_workflow_name(
    session_manager, test_session, sample_workflow_definition
):
    """Test that duplicate workflow names raise an error."""
    session_manager.save_workflow_to_session(
        session_id=test_session,
        workflow_definition=sample_workflow_definition,
        workflow_name="Duplicate Name",
    )

    # Try to save another workflow with the same name
    with pytest.raises(Exception):  # SQLAlchemy will raise an IntegrityError
        session_manager.save_workflow_to_session(
            session_id=test_session,
            workflow_definition=sample_workflow_definition,
            workflow_name="Duplicate Name",
        )


def test_workflow_json_storage(
    session_manager, test_session, sample_workflow_definition
):
    """Test that complex workflow definitions are properly stored as JSON."""
    # Add more complex structures to the workflow
    complex_definition = {
        **sample_workflow_definition,
        "metadata": {"author": "test", "version": "1.0", "tags": ["test", "demo"]},
        "config": {"timeout": 300, "retry": True, "parameters": {"key": "value"}},
    }

    workflow_id = session_manager.save_workflow_to_session(
        session_id=test_session,
        workflow_definition=complex_definition,
        workflow_name="Complex Workflow",
    )

    loaded = session_manager.load_workflow(workflow_id)
    assert loaded["definition"] == complex_definition
    assert loaded["definition"]["metadata"]["tags"] == ["test", "demo"]


def test_get_workflows_for_nonexistent_session(session_manager):
    """Test getting workflows for a session that doesn't exist."""
    with pytest.raises(ValueError, match="Session .* not found"):
        session_manager.get_workflows_for_session(99999)


def test_save_workflow_to_nonexistent_session(
    session_manager, sample_workflow_definition, request
):
    """Test saving workflow to a session that doesn't exist."""
    with pytest.raises(ValueError, match="Session .* not found"):
        session_manager.save_workflow_to_session(
            session_id=99999,
            workflow_definition=sample_workflow_definition,
            workflow_name=f"Test Workflow {request.node.name}",
        )
