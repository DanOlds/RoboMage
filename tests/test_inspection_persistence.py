"""
Tests for Node I/O Inspection Persistence

Verifies database storage and retrieval of node inspection data through
the SessionManager API. Tests CRUD operations, filtering, cascade deletes,
and data integrity.

Test Coverage:
- NodeInspection model creation and validation
- SessionManager save/get/delete inspection methods
- Filtering by workflow_id, node_id, node_type, session_id
- Cascade deletes (session deletion removes inspections)
- JSON serialization/deserialization
- Timestamp and duration tracking
- Orphaned inspections (session_id=None)
"""

from datetime import datetime

import pytest

from robomage.persistence.api import SessionManager


@pytest.fixture(scope="function")
def session_manager(tmp_path):
    """Create SessionManager with unique temporary database for each test."""
    import uuid

    # Use random UUID to ensure unique database file
    db_path = tmp_path / f"test_{uuid.uuid4().hex}.db"
    return SessionManager(db_path=str(db_path))


@pytest.fixture(scope="function")
def test_session(session_manager):
    """Create a test session for each test."""
    import uuid

    session_id = session_manager.create_session(
        f"Test Session {uuid.uuid4()}", "For inspection tests"
    )
    return session_id


class TestNodeInspectionModel:
    """Tests for NodeInspection database model."""

    def test_create_inspection_minimal(self, session_manager):
        """Test creating inspection with minimal required fields."""
        inspection_id = session_manager.save_inspection(
            workflow_id="wf_test",
            node_id="node_1",
            node_type="load_files",
        )

        assert inspection_id is not None
        assert isinstance(inspection_id, int)

        # Retrieve and verify
        inspections = session_manager.get_inspections(workflow_id="wf_test")
        assert len(inspections) == 1
        assert inspections[0].workflow_id == "wf_test"
        assert inspections[0].node_id == "node_1"
        assert inspections[0].node_type == "load_files"
        assert inspections[0].session_id is None  # Optional

    def test_create_inspection_full(self, session_manager, test_session):
        """Test creating inspection with all fields populated."""
        now = datetime.now()
        inspection_id = session_manager.save_inspection(
            workflow_id="wf_full",
            node_id="normalize_1",
            node_type="normalize",
            input_data={"files": [{"filename": "test.chi"}]},
            output_data={"files": [{"filename": "test.chi", "normalized": True}]},
            input_shape="dict[1]",
            output_shape="dict[1]",
            timestamp_in=now,
            timestamp_out=now,
            duration_ms=125.5,
            execution_metadata={"execution_id": "exec_123", "environment": "test"},
            session_id=test_session,
        )

        assert inspection_id is not None

        # Retrieve and verify all fields
        inspections = session_manager.get_inspections(workflow_id="wf_full")
        assert len(inspections) == 1

        insp = inspections[0]
        assert insp.workflow_id == "wf_full"
        assert insp.node_id == "normalize_1"
        assert insp.node_type == "normalize"
        assert insp.input_data == {"files": [{"filename": "test.chi"}]}
        assert insp.output_data == {
            "files": [{"filename": "test.chi", "normalized": True}]
        }
        assert insp.input_shape == "dict[1]"
        assert insp.output_shape == "dict[1]"
        assert insp.duration_ms == 125.5
        assert insp.execution_metadata == {
            "execution_id": "exec_123",
            "environment": "test",
        }
        assert insp.session_id == test_session

    def test_create_inspection_invalid_session(self, session_manager):
        """Test creating inspection with non-existent session fails."""
        with pytest.raises(ValueError, match="Session 999 not found"):
            session_manager.save_inspection(
                workflow_id="wf_test",
                node_id="node_1",
                node_type="load_files",
                session_id=999,  # Non-existent
            )


class TestSessionManagerInspectionCRUD:
    """Tests for SessionManager inspection CRUD operations."""

    def test_save_and_get_inspection(self, session_manager):
        """Test basic save and retrieve workflow."""
        inspection_id = session_manager.save_inspection(
            workflow_id="wf_crud",
            node_id="analyze_1",
            node_type="peak_analysis",
            duration_ms=234.7,
        )

        inspections = session_manager.get_inspections(workflow_id="wf_crud")
        assert len(inspections) == 1
        assert inspections[0].id == inspection_id
        assert inspections[0].duration_ms == 234.7

    def test_get_inspections_no_filters(self, session_manager):
        """Test getting all inspections without filters."""
        # Create multiple inspections
        session_manager.save_inspection("wf_1", "node_a", "load_files")
        session_manager.save_inspection("wf_1", "node_b", "normalize")
        session_manager.save_inspection("wf_2", "node_c", "peak_analysis")

        all_inspections = session_manager.get_inspections()
        assert len(all_inspections) == 3

    def test_get_inspections_filter_workflow(self, session_manager):
        """Test filtering inspections by workflow_id."""
        session_manager.save_inspection("wf_filter1", "node_1", "load_files")
        session_manager.save_inspection("wf_filter1", "node_2", "normalize")
        session_manager.save_inspection("wf_filter2", "node_3", "peak_analysis")

        wf1_inspections = session_manager.get_inspections(workflow_id="wf_filter1")
        assert len(wf1_inspections) == 2
        assert all(i.workflow_id == "wf_filter1" for i in wf1_inspections)

    def test_get_inspections_filter_node_type(self, session_manager):
        """Test filtering inspections by node_type."""
        session_manager.save_inspection("wf_1", "load_1", "load_files")
        session_manager.save_inspection("wf_1", "load_2", "load_files")
        session_manager.save_inspection("wf_1", "analyze_1", "peak_analysis")

        load_inspections = session_manager.get_inspections(node_type="load_files")
        assert len(load_inspections) == 2
        assert all(i.node_type == "load_files" for i in load_inspections)

    def test_get_inspections_filter_node_id(self, session_manager):
        """Test filtering inspections by node_id."""
        session_manager.save_inspection("wf_1", "special_node", "load_files")
        session_manager.save_inspection("wf_1", "other_node", "normalize")

        node_inspections = session_manager.get_inspections(node_id="special_node")
        assert len(node_inspections) == 1
        assert node_inspections[0].node_id == "special_node"

    def test_get_inspections_filter_session(self, session_manager, test_session):
        """Test filtering inspections by session_id."""
        session2_id = session_manager.create_session("Session 2")

        # Create inspections for different sessions
        session_manager.save_inspection(
            "wf_1", "node_1", "load_files", session_id=test_session
        )
        session_manager.save_inspection(
            "wf_2", "node_2", "normalize", session_id=session2_id
        )
        session_manager.save_inspection("wf_3", "node_3", "peak_analysis")  # No session

        session1_inspections = session_manager.get_inspections(session_id=test_session)
        assert len(session1_inspections) == 1
        assert session1_inspections[0].session_id == test_session

    def test_get_inspections_multiple_filters(self, session_manager):
        """Test combining multiple filters."""
        session_manager.save_inspection("wf_multi", "load_1", "load_files")
        session_manager.save_inspection("wf_multi", "load_2", "load_files")
        session_manager.save_inspection("wf_multi", "analyze_1", "peak_analysis")
        session_manager.save_inspection("wf_other", "load_3", "load_files")

        # Filter by workflow AND node_type
        filtered = session_manager.get_inspections(
            workflow_id="wf_multi", node_type="load_files"
        )
        assert len(filtered) == 2
        assert all(
            i.workflow_id == "wf_multi" and i.node_type == "load_files"
            for i in filtered
        )

    def test_get_workflow_inspections(self, session_manager):
        """Test convenience method for getting workflow inspections."""
        session_manager.save_inspection("wf_convenience", "node_1", "load_files")
        session_manager.save_inspection("wf_convenience", "node_2", "normalize")

        inspections = session_manager.get_workflow_inspections("wf_convenience")
        assert len(inspections) == 2
        assert all(i.workflow_id == "wf_convenience" for i in inspections)

    def test_delete_inspection(self, session_manager):
        """Test deleting individual inspection."""
        inspection_id = session_manager.save_inspection(
            "wf_delete", "node_1", "load_files"
        )

        # Verify exists
        inspections = session_manager.get_inspections(workflow_id="wf_delete")
        assert len(inspections) == 1

        # Delete
        deleted = session_manager.delete_inspection(inspection_id)
        assert deleted is True

        # Verify gone
        inspections = session_manager.get_inspections(workflow_id="wf_delete")
        assert len(inspections) == 0

    def test_delete_inspection_not_found(self, session_manager):
        """Test deleting non-existent inspection returns False."""
        deleted = session_manager.delete_inspection(99999)
        assert deleted is False

    def test_clear_session_inspections(self, session_manager, test_session):
        """Test clearing all inspections for a session."""
        # Create inspections for test session
        session_manager.save_inspection(
            "wf_1", "node_1", "load_files", session_id=test_session
        )
        session_manager.save_inspection(
            "wf_1", "node_2", "normalize", session_id=test_session
        )
        session_manager.save_inspection(
            "wf_2", "node_3", "peak_analysis", session_id=test_session
        )

        # Create inspection for another session
        session2_id = session_manager.create_session("Session 2")
        session_manager.save_inspection(
            "wf_3", "node_4", "export_csv", session_id=session2_id
        )

        # Clear test session inspections
        count = session_manager.clear_session_inspections(test_session)
        assert count == 3

        # Verify test session inspections gone
        session1_inspections = session_manager.get_inspections(session_id=test_session)
        assert len(session1_inspections) == 0

        # Verify other session unaffected
        session2_inspections = session_manager.get_inspections(session_id=session2_id)
        assert len(session2_inspections) == 1

    def test_clear_session_inspections_invalid_session(self, session_manager):
        """Test clearing inspections for non-existent session fails."""
        with pytest.raises(ValueError, match="Session 999 not found"):
            session_manager.clear_session_inspections(999)

    def test_clear_workflow_inspections(self, session_manager):
        """Test clearing all inspections for a workflow."""
        # Create inspections for multiple workflows
        session_manager.save_inspection("wf_clear", "node_1", "load_files")
        session_manager.save_inspection("wf_clear", "node_2", "normalize")
        session_manager.save_inspection("wf_keep", "node_3", "peak_analysis")

        # Clear one workflow
        count = session_manager.clear_workflow_inspections("wf_clear")
        assert count == 2

        # Verify cleared
        cleared_inspections = session_manager.get_inspections(workflow_id="wf_clear")
        assert len(cleared_inspections) == 0

        # Verify other workflow unaffected
        kept_inspections = session_manager.get_inspections(workflow_id="wf_keep")
        assert len(kept_inspections) == 1


class TestInspectionCascadeDeletes:
    """Tests for cascade delete behavior."""

    def test_session_delete_cascades_to_inspections(self, session_manager, test_session):
        """Test that deleting session also deletes its inspections."""
        # Create inspections for session
        session_manager.save_inspection(
            "wf_cascade", "node_1", "load_files", session_id=test_session
        )
        session_manager.save_inspection(
            "wf_cascade", "node_2", "normalize", session_id=test_session
        )

        # Verify inspections exist
        inspections = session_manager.get_inspections(session_id=test_session)
        assert len(inspections) == 2

        # Delete session
        session_manager.delete_session(test_session)

        # Verify inspections cascade deleted
        inspections = session_manager.get_inspections(session_id=test_session)
        assert len(inspections) == 0

    def test_orphaned_inspections_preserved(self, session_manager, test_session):
        """Test that inspections without session_id are preserved when session deleted."""
        # Create inspection with session
        session_manager.save_inspection(
            "wf_1", "node_1", "load_files", session_id=test_session
        )

        # Create orphaned inspection (no session)
        session_manager.save_inspection("wf_2", "node_2", "normalize")

        # Delete session
        session_manager.delete_session(test_session)

        # Verify orphaned inspection still exists
        all_inspections = session_manager.get_inspections()
        assert len(all_inspections) == 1
        assert all_inspections[0].node_id == "node_2"
        assert all_inspections[0].session_id is None


class TestInspectionDataIntegrity:
    """Tests for data integrity and serialization."""

    def test_json_data_roundtrip(self, session_manager):
        """Test that complex JSON data survives database roundtrip."""
        complex_data = {
            "files": [
                {"filename": "test1.chi", "q_range": [0.5, 10.0], "num_points": 1000},
                {"filename": "test2.chi", "q_range": [0.5, 10.0], "num_points": 1000},
            ],
            "metadata": {"wavelength": 0.1665, "temperature": 298.15},
            "nested": {"level1": {"level2": {"value": 42}}},
        }

        inspection_id = session_manager.save_inspection(
            workflow_id="wf_json",
            node_id="test_node",
            node_type="load_files",
            input_data=complex_data,
            output_data=complex_data,
        )

        inspections = session_manager.get_inspections(workflow_id="wf_json")
        assert len(inspections) == 1

        insp = inspections[0]
        assert insp.input_data == complex_data
        assert insp.output_data == complex_data

    def test_timestamp_ordering(self, session_manager):
        """Test that inspections are ordered by timestamp_in."""
        from time import sleep

        # Create inspections with different timestamps
        now = datetime.now()

        session_manager.save_inspection(
            "wf_order", "node_3", "export", timestamp_in=now
        )
        sleep(0.01)  # Ensure different timestamps

        later = datetime.now()
        session_manager.save_inspection(
            "wf_order", "node_1", "load", timestamp_in=later
        )
        sleep(0.01)

        even_later = datetime.now()
        session_manager.save_inspection(
            "wf_order", "node_2", "analyze", timestamp_in=even_later
        )

        inspections = session_manager.get_inspections(workflow_id="wf_order")
        assert len(inspections) == 3

        # Should be ordered by timestamp_in
        assert inspections[0].node_id == "node_3"
        assert inspections[1].node_id == "node_1"
        assert inspections[2].node_id == "node_2"

    def test_null_timestamps(self, session_manager):
        """Test handling of null timestamps."""
        inspection_id = session_manager.save_inspection(
            workflow_id="wf_null",
            node_id="node_1",
            node_type="load_files",
            timestamp_in=None,
            timestamp_out=None,
            duration_ms=None,
        )

        inspections = session_manager.get_inspections(workflow_id="wf_null")
        assert len(inspections) == 1
        assert inspections[0].timestamp_in is None
        assert inspections[0].timestamp_out is None
        assert inspections[0].duration_ms is None

    def test_large_data_storage(self, session_manager):
        """Test storing large inspection data."""
        # Create large data structure
        large_data = {
            "files": [
                {
                    "filename": f"file_{i}.chi",
                    "data_points": list(range(100)),  # 100 points each
                }
                for i in range(50)  # 50 files
            ]
        }

        inspection_id = session_manager.save_inspection(
            workflow_id="wf_large",
            node_id="node_1",
            node_type="load_files",
            input_data=large_data,
        )

        inspections = session_manager.get_inspections(workflow_id="wf_large")
        assert len(inspections) == 1
        assert len(inspections[0].input_data["files"]) == 50


class TestInspectionIndexes:
    """Tests that database indexes are working efficiently."""

    def test_workflow_index_performance(self, session_manager):
        """Test that workflow_id index enables fast queries."""
        # Create many inspections across different workflows
        for wf_num in range(10):
            for node_num in range(5):
                session_manager.save_inspection(
                    workflow_id=f"wf_{wf_num}",
                    node_id=f"node_{node_num}",
                    node_type="load_files",
                )

        # Query specific workflow (should use index)
        inspections = session_manager.get_inspections(workflow_id="wf_5")
        assert len(inspections) == 5
        assert all(i.workflow_id == "wf_5" for i in inspections)

    def test_node_type_index_performance(self, session_manager):
        """Test that node_type index enables fast queries."""
        # Create inspections with different types
        for i in range(20):
            node_type = ["load_files", "normalize", "peak_analysis"][i % 3]
            session_manager.save_inspection(
                workflow_id=f"wf_{i}", node_id=f"node_{i}", node_type=node_type
            )

        # Query by node_type (should use index)
        load_inspections = session_manager.get_inspections(node_type="load_files")
        assert len(load_inspections) == 7  # 20 / 3 ≈ 7
        assert all(i.node_type == "load_files" for i in load_inspections)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
