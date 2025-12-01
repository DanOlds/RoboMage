"""
High-level API for session persistence.

Provides SessionManager class for creating, managing, and loading analysis sessions.
"""

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from robomage.data.models import DiffractionData
from robomage.persistence.database import get_db_manager
from robomage.persistence.file_store import get_file_store
from robomage.persistence.models import File, Session

if TYPE_CHECKING:
    from robomage.persistence.models import AnalysisResult


class SessionManager:
    """
    High-level API for managing analysis sessions.

    Handles session creation, file management, and data persistence with
    coordinated database and file storage operations.

    Example:
        >>> mgr = SessionManager()
        >>> session_id = mgr.create_session("My Analysis", "SRM 660b data")
        >>> data = load_test_data()
        >>> file_obj = mgr.add_file_to_session(session_id, "sample.chi", 0.1665, data)
        >>> loaded_data = mgr.load_file_data(file_obj.id)
    """

    def __init__(self, db_path: str | Path | None = None) -> None:
        """
        Initialize SessionManager.

        Args:
            db_path: Path to database file. If None, uses default
                (~/.robomage/robomage.db). Use ":memory:" for testing.
        """
        self.db_manager = get_db_manager(db_path)
        self.file_store = get_file_store()

    def create_session(self, name: str, description: str = "") -> int:
        """
        Create a new analysis session.

        Args:
            name: Unique name for the session
            description: Optional description of the session

        Returns:
            Session ID (integer primary key)

        Raises:
            ValueError: If session name already exists

        Example:
            >>> mgr = SessionManager()
            >>> session_id = mgr.create_session("November 2025 Analysis")
        """
        db = self.db_manager.get_session()
        try:
            # Check if name already exists
            existing = db.execute(
                select(Session).where(Session.name == name)
            ).scalar_one_or_none()

            if existing:
                raise ValueError(f"Session with name '{name}' already exists")

            # Create new session
            session = Session(
                name=name,
                description=description,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
            )
            db.add(session)
            db.commit()
            db.refresh(session)

            return session.id

        finally:
            db.close()

    def get_session(self, session_id: int) -> Session | None:
        """
        Get session by ID.

        Args:
            session_id: Session ID to retrieve

        Returns:
            Session object with files eagerly loaded, or None if not found

        Example:
            >>> mgr = SessionManager()
            >>> session = mgr.get_session(1)
            >>> print(session.name)
        """
        db = self.db_manager.get_session()
        try:
            session = db.execute(
                select(Session)
                .options(selectinload(Session.files))
                .where(Session.id == session_id)
            ).scalar_one_or_none()

            if session:
                # Update last accessed time
                session.last_accessed = datetime.now()
                db.commit()
            return session
        finally:
            db.close()

    def list_sessions(self) -> list[Session]:
        """
        List all sessions, ordered by last accessed (most recent first).

        Returns:
            List of Session objects with files eagerly loaded

        Example:
            >>> mgr = SessionManager()
            >>> sessions = mgr.list_sessions()
            >>> for session in sessions:
            ...     print(f"{session.name}: {len(session.files)} files")
        """
        db = self.db_manager.get_session()
        try:
            sessions = (
                db.execute(
                    select(Session)
                    .options(selectinload(Session.files))
                    .order_by(Session.last_accessed.desc())
                )
                .scalars()
                .all()
            )
            return list(sessions)
        finally:
            db.close()

    def delete_session(self, session_id: int) -> None:
        """
        Delete a session and all associated files.

        Removes both database records and physical files from disk.

        Args:
            session_id: Session ID to delete

        Raises:
            ValueError: If session does not exist

        Example:
            >>> mgr = SessionManager()
            >>> mgr.delete_session(1)
        """
        db = self.db_manager.get_session()
        try:
            session = db.get(Session, session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")

            # Delete physical files first
            self.file_store.delete_session_files(session_id)

            # Delete database records (cascade will handle files table)
            db.delete(session)
            db.commit()

        finally:
            db.close()

    def add_file_to_session(
        self,
        session_id: int,
        filename: str,
        wavelength: float,
        data: DiffractionData,
    ) -> File:
        """
        Add a diffraction data file to a session.

        Stores both the physical file and database metadata.

        Args:
            session_id: Session to add file to
            filename: Original filename (e.g., "sample.chi")
            wavelength: X-ray wavelength in Angstroms
            data: DiffractionData object to store

        Returns:
            File object with database record

        Raises:
            ValueError: If session does not exist

        Example:
            >>> mgr = SessionManager()
            >>> data = load_test_data()
            >>> file_obj = mgr.add_file_to_session(1, "sample.chi", 0.1665, data)
            >>> print(file_obj.stored_path)
        """
        db = self.db_manager.get_session()
        try:
            # Verify session exists (use query for consistency)
            session = db.execute(
                select(Session).where(Session.id == session_id)
            ).scalar_one_or_none()

            if not session:
                raise ValueError(f"Session {session_id} not found")

            # Store physical file
            stored_path = self.file_store.store_file(session_id, filename, data)

            # Create database record
            file_record = File(
                session_id=session_id,
                filename=filename,
                stored_path=str(stored_path),
                wavelength=wavelength,
                num_points=len(data.q_values),
                q_min=float(data.q_values.min()),
                q_max=float(data.q_values.max()),
                upload_time=datetime.now(),
            )
            db.add(file_record)

            # Update session last accessed
            session.last_accessed = datetime.now()

            db.commit()
            db.refresh(file_record)

            return file_record

        finally:
            db.close()

    def get_session_files(self, session_id: int) -> list[File]:
        """
        Get all files for a session.

        Args:
            session_id: Session ID to get files for

        Returns:
            List of File objects

        Example:
            >>> mgr = SessionManager()
            >>> files = mgr.get_session_files(1)
            >>> for f in files:
            ...     print(f"{f.filename}: {f.num_points} points")
        """
        db = self.db_manager.get_session()
        try:
            files = (
                db.execute(select(File).where(File.session_id == session_id))
                .scalars()
                .all()
            )
            return list(files)
        finally:
            db.close()

    def load_file_data(self, file_id: int) -> DiffractionData:
        """
        Load diffraction data from a stored file.

        Args:
            file_id: File ID to load

        Returns:
            DiffractionData object

        Raises:
            ValueError: If file does not exist

        Example:
            >>> mgr = SessionManager()
            >>> data = mgr.load_file_data(1)
            >>> print(f"Loaded {data.num_points} points")
        """
        db = self.db_manager.get_session()
        try:
            file_record = db.get(File, file_id)
            if not file_record:
                raise ValueError(f"File {file_id} not found")

            # Load from physical storage
            data = self.file_store.load_file(file_record.stored_path)

            return data

        finally:
            db.close()

    def get_file(self, file_id: int) -> File | None:
        """
        Get file metadata by ID.

        Args:
            file_id: File ID to retrieve

        Returns:
            File object or None if not found

        Example:
            >>> mgr = SessionManager()
            >>> file_obj = mgr.get_file(1)
            >>> print(f"Wavelength: {file_obj.wavelength} Å")
        """
        db = self.db_manager.get_session()
        try:
            return db.get(File, file_id)
        finally:
            db.close()

    # ========================================================================
    # Workflow Persistence Methods
    # ========================================================================

    def save_workflow_to_session(
        self,
        session_id: int,
        workflow_definition: dict,
        workflow_name: str,
        workflow_description: str = "",
    ) -> str:
        """
        Save a workflow definition and link it to a session.

        Args:
            session_id: Target session ID (or None for standalone workflow)
            workflow_definition: WorkflowDefinition as dict (nodes, edges, etc.)
            workflow_name: Unique name for workflow
            workflow_description: Optional description

        Returns:
            Workflow ID (UUID string)

        Raises:
            ValueError: If session_id doesn't exist or workflow_name is duplicate

        Example:
            >>> mgr = SessionManager()
            >>> session_id = mgr.create_session("Peak Analysis Session")
            >>> workflow_def = {
            ...     "nodes": [{"id": "load_1", "type": "load_files"}],
            ...     "edges": [],
            ... }
            >>> workflow_id = mgr.save_workflow_to_session(
            ...     session_id, workflow_def, "My Workflow"
            ... )
        """
        import uuid

        from robomage.persistence.models import Workflow

        workflow_id = str(uuid.uuid4())

        db = self.db_manager.get_session()
        try:
            # Verify session exists if provided
            if session_id is not None:
                session = db.get(Session, session_id)
                if not session:
                    raise ValueError(f"Session {session_id} not found")

            workflow = Workflow(
                id=workflow_id,
                name=workflow_name,
                description=workflow_description,
                definition=workflow_definition,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                session_id=session_id,
            )
            db.add(workflow)
            db.commit()

            return workflow_id

        finally:
            db.close()

    def get_workflows_for_session(self, session_id: int) -> list[dict]:
        """
        Get all workflows linked to a session.

        Args:
            session_id: Session ID

        Returns:
            List of workflow dictionaries with id, name, description, definition

        Raises:
            ValueError: If session doesn't exist

        Example:
            >>> mgr = SessionManager()
            >>> workflows = mgr.get_workflows_for_session(session_id)
            >>> for wf in workflows:
            ...     print(f"Workflow: {wf['name']}")
        """
        db = self.db_manager.get_session()
        try:
            session = (
                db.query(Session)
                .options(selectinload(Session.workflows))
                .filter_by(id=session_id)
                .first()
            )
            if not session:
                raise ValueError(f"Session {session_id} not found")

            return [
                {
                    "id": wf.id,
                    "name": wf.name,
                    "description": wf.description,
                    "definition": wf.definition,
                    "created_at": wf.created_at.isoformat(),
                    "updated_at": wf.updated_at.isoformat(),
                }
                for wf in session.workflows
            ]

        finally:
            db.close()

    def load_workflow(self, workflow_id: str) -> dict:
        """
        Load a workflow definition by ID.

        Args:
            workflow_id: Workflow ID (UUID string)

        Returns:
            Dictionary with workflow details:
                - id, name, description, definition
                - session_id, created_at, updated_at

        Raises:
            ValueError: If workflow not found

        Example:
            >>> mgr = SessionManager()
            >>> workflow = mgr.load_workflow(workflow_id)
            >>> definition = workflow["definition"]
        """
        from robomage.persistence.models import Workflow

        db = self.db_manager.get_session()
        try:
            workflow = db.query(Workflow).filter_by(id=workflow_id).first()
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")

            return {
                "id": workflow.id,
                "name": workflow.name,
                "description": workflow.description,
                "definition": workflow.definition,
                "session_id": workflow.session_id,
                "created_at": workflow.created_at.isoformat(),
                "updated_at": workflow.updated_at.isoformat(),
            }

        finally:
            db.close()

    def delete_workflow(self, workflow_id: str) -> None:
        """
        Delete a workflow by ID.

        Args:
            workflow_id: Workflow ID (UUID string)

        Raises:
            ValueError: If workflow not found

        Example:
            >>> mgr = SessionManager()
            >>> mgr.delete_workflow(workflow_id)
        """
        from robomage.persistence.models import Workflow

        db = self.db_manager.get_session()
        try:
            workflow = db.query(Workflow).filter_by(id=workflow_id).first()
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")

            db.delete(workflow)
            db.commit()

        finally:
            db.close()

    # ========================================================================
    # Analysis Result Persistence Methods
    # ========================================================================

    def save_analysis_result(
        self,
        file_id: int,
        analysis_type: str,
        result_data: dict,
        parameters: dict | None = None,
        quality_metrics: dict | None = None,
        analysis_version: str | None = None,
    ) -> int:
        """
        Save an analysis result to the database.

        Args:
            file_id: Database ID of the file analyzed
            analysis_type: Type identifier ('peak_detection', 'rietveld', etc.)
            result_data: Analysis-specific results (schema varies by type)
            parameters: Analysis parameters used (for reproducibility)
            quality_metrics: Quality/goodness-of-fit metrics (optional)
            analysis_version: Tool version string (optional)

        Returns:
            Database ID of the created AnalysisResult record

        Raises:
            ValueError: If file_id doesn't exist

        Example:
            >>> mgr = SessionManager()
            >>> result_id = mgr.save_analysis_result(
            ...     file_id=42,
            ...     analysis_type="peak_detection",
            ...     result_data={"peaks": [...], "num_peaks_detected": 5},
            ...     parameters={"profile": "gaussian", "min_prominence": 0.01},
            ...     quality_metrics={"overall_r_squared": 0.982},
            ... )
        """
        from robomage.persistence.models import AnalysisResult

        db = self.db_manager.get_session()
        try:
            # Verify file exists
            file_obj = db.get(File, file_id)
            if not file_obj:
                raise ValueError(f"File {file_id} not found")

            # Create analysis result
            result = AnalysisResult(
                file_id=file_id,
                analysis_type=analysis_type,
                result_data=result_data,
                parameters=parameters,
                quality_metrics=quality_metrics,
                analysis_version=analysis_version,
                created_at=datetime.now(),
            )

            db.add(result)
            db.commit()
            db.refresh(result)

            return result.id

        finally:
            db.close()

    def get_analysis_results(
        self, file_id: int, analysis_type: str | None = None
    ) -> list:
        """
        Get all analysis results for a file.

        Args:
            file_id: Database ID of the file
            analysis_type: Optional filter by analysis type

        Returns:
            List of AnalysisResult objects, ordered by created_at descending

        Example:
            >>> # Get all analysis results for a file
            >>> results = mgr.get_analysis_results(file_id=42)
            >>>
            >>> # Get only peak detection results
            >>> peak_results = mgr.get_analysis_results(
            ...     file_id=42, analysis_type="peak_detection"
            ... )
        """
        from robomage.persistence.models import AnalysisResult

        db = self.db_manager.get_session()
        try:
            query = (
                db.query(AnalysisResult)
                .filter(AnalysisResult.file_id == file_id)
                .order_by(AnalysisResult.created_at.desc())
            )

            if analysis_type is not None:
                query = query.filter(AnalysisResult.analysis_type == analysis_type)

            return list(query.all())

        finally:
            db.close()

    def get_latest_analysis(
        self, file_id: int, analysis_type: str
    ) -> "AnalysisResult | None":
        """
        Get the most recent analysis result of a specific type for a file.

        Args:
            file_id: Database ID of the file
            analysis_type: Type identifier to filter by

        Returns:
            Most recent AnalysisResult or None if not found

        Example:
            >>> latest_peak_analysis = mgr.get_latest_analysis(
            ...     file_id=42, analysis_type="peak_detection"
            ... )
            >>> if latest_peak_analysis:
            ...     print(
            ...         f"Found {len(latest_peak_analysis.result_data['peaks'])} peaks"
            ...     )
        """
        from robomage.persistence.models import AnalysisResult

        db = self.db_manager.get_session()
        try:
            result = (
                db.query(AnalysisResult)
                .filter(
                    AnalysisResult.file_id == file_id,
                    AnalysisResult.analysis_type == analysis_type,
                )
                .order_by(AnalysisResult.created_at.desc())
                .first()
            )

            return result

        finally:
            db.close()

    def delete_analysis_result(self, analysis_id: int) -> bool:
        """
        Delete an analysis result by ID.

        Args:
            analysis_id: Database ID of the AnalysisResult

        Returns:
            True if deleted, False if not found

        Example:
            >>> mgr = SessionManager()
            >>> deleted = mgr.delete_analysis_result(123)
            >>> if deleted:
            ...     print("Analysis result removed")
        """
        from robomage.persistence.models import AnalysisResult

        db = self.db_manager.get_session()
        try:
            result = db.get(AnalysisResult, analysis_id)
            if not result:
                return False

            db.delete(result)
            db.commit()
            return True

        finally:
            db.close()

    # -------------------------------------------------------------------------
    # Node Inspection Methods (Tool 1: Node I/O Inspector)
    # -------------------------------------------------------------------------

    def save_inspection(
        self,
        workflow_id: str,
        node_id: str,
        node_type: str,
        input_data: dict | list | str | int | float | None = None,
        output_data: dict | list | str | int | float | None = None,
        input_shape: str | None = None,
        output_shape: str | None = None,
        timestamp_in: datetime | None = None,
        timestamp_out: datetime | None = None,
        duration_ms: float | None = None,
        execution_metadata: dict | None = None,
        session_id: int | None = None,
    ) -> int:
        """
        Save node inspection data to database.

        Stores a snapshot of input/output data for a workflow node execution,
        enabling the Node I/O Inspector tool to visualize data flow and
        debug issues.

        Args:
            workflow_id: Workflow identifier
            node_id: Unique node identifier in workflow
            node_type: Node type (e.g., 'load_files', 'peak_analysis')
            input_data: Serialized input data (JSON-compatible)
            output_data: Serialized output data (JSON-compatible)
            input_shape: Compact shape description (e.g., 'list[3]')
            output_shape: Compact shape description (e.g., 'dict[5]')
            timestamp_in: Node execution start time
            timestamp_out: Node execution end time
            duration_ms: Execution duration in milliseconds
            execution_metadata: Additional context (JSON)
            session_id: Optional link to session for cleanup

        Returns:
            NodeInspection ID (integer primary key)

        Example:
            >>> mgr = SessionManager()
            >>> inspection_id = mgr.save_inspection(
            ...     workflow_id="workflow_123",
            ...     node_id="normalize_1",
            ...     node_type="normalize",
            ...     input_data={"files": [...]},
            ...     output_data={"files": [...]},
            ...     input_shape="dict[1]",
            ...     output_shape="dict[1]",
            ...     duration_ms=125.5,
            ...     session_id=1
            ... )
        """
        from robomage.persistence.models import NodeInspection

        db = self.db_manager.get_session()
        try:
            # Verify session exists if provided
            if session_id is not None:
                session = db.get(Session, session_id)
                if not session:
                    raise ValueError(f"Session {session_id} not found")

            # Create inspection record
            inspection = NodeInspection(
                session_id=session_id,
                workflow_id=workflow_id,
                node_id=node_id,
                node_type=node_type,
                input_data=input_data,
                output_data=output_data,
                input_shape=input_shape,
                output_shape=output_shape,
                timestamp_in=timestamp_in,
                timestamp_out=timestamp_out,
                duration_ms=duration_ms,
                execution_metadata=execution_metadata,
            )

            db.add(inspection)
            db.commit()
            db.refresh(inspection)

            return inspection.id

        finally:
            db.close()

    def get_inspections(
        self,
        workflow_id: str | None = None,
        node_id: str | None = None,
        node_type: str | None = None,
        session_id: int | None = None,
    ) -> list:
        """
        Get node inspection records with optional filtering.

        Args:
            workflow_id: Filter by workflow ID
            node_id: Filter by node ID
            node_type: Filter by node type
            session_id: Filter by session ID

        Returns:
            List of NodeInspection objects, ordered by timestamp_in

        Example:
            >>> # Get all inspections for a workflow
            >>> inspections = mgr.get_inspections(workflow_id="workflow_123")
            >>>
            >>> # Get all peak_analysis node inspections
            >>> peak_inspections = mgr.get_inspections(node_type="peak_analysis")
            >>>
            >>> # Get inspections for specific session
            >>> session_inspections = mgr.get_inspections(session_id=1)
        """
        from robomage.persistence.models import NodeInspection

        db = self.db_manager.get_session()
        try:
            query = db.query(NodeInspection)

            # Apply filters
            if workflow_id is not None:
                query = query.filter(NodeInspection.workflow_id == workflow_id)

            if node_id is not None:
                query = query.filter(NodeInspection.node_id == node_id)

            if node_type is not None:
                query = query.filter(NodeInspection.node_type == node_type)

            if session_id is not None:
                query = query.filter(NodeInspection.session_id == session_id)

            # Order by timestamp
            query = query.order_by(NodeInspection.timestamp_in)

            return list(query.all())

        finally:
            db.close()

    def get_workflow_inspections(self, workflow_id: str) -> list:
        """
        Get all inspection records for a workflow, ordered by execution time.

        Convenience method for retrieving complete workflow execution trace.

        Args:
            workflow_id: Workflow identifier

        Returns:
            List of NodeInspection objects ordered by timestamp_in

        Example:
            >>> mgr = SessionManager()
            >>> inspections = mgr.get_workflow_inspections("workflow_123")
            >>> for inspection in inspections:
            ...     print(f"{inspection.node_id}: {inspection.duration_ms}ms")
        """
        return self.get_inspections(workflow_id=workflow_id)

    def delete_inspection(self, inspection_id: int) -> bool:
        """
        Delete a node inspection record by ID.

        Args:
            inspection_id: Database ID of the NodeInspection

        Returns:
            True if deleted, False if not found

        Example:
            >>> mgr = SessionManager()
            >>> deleted = mgr.delete_inspection(123)
            >>> if deleted:
            ...     print("Inspection record removed")
        """
        from robomage.persistence.models import NodeInspection

        db = self.db_manager.get_session()
        try:
            inspection = db.get(NodeInspection, inspection_id)
            if not inspection:
                return False

            db.delete(inspection)
            db.commit()
            return True

        finally:
            db.close()

    def clear_session_inspections(self, session_id: int) -> int:
        """
        Delete all inspection records for a session.

        Useful for cleaning up inspection data when re-running workflows
        or when inspection data is no longer needed.

        Args:
            session_id: Database ID of the session

        Returns:
            Number of inspection records deleted

        Example:
            >>> mgr = SessionManager()
            >>> count = mgr.clear_session_inspections(session_id=1)
            >>> print(f"Removed {count} inspection records")
        """
        from robomage.persistence.models import NodeInspection

        db = self.db_manager.get_session()
        try:
            # Verify session exists
            session = db.get(Session, session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")

            # Delete all inspections for this session
            count = (
                db.query(NodeInspection)
                .filter(NodeInspection.session_id == session_id)
                .delete()
            )

            db.commit()
            return count

        finally:
            db.close()

    def clear_workflow_inspections(self, workflow_id: str) -> int:
        """
        Delete all inspection records for a workflow.

        Useful for cleaning up inspection data from previous executions
        before running a workflow again.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Number of inspection records deleted

        Example:
            >>> mgr = SessionManager()
            >>> count = mgr.clear_workflow_inspections("workflow_123")
            >>> print(f"Removed {count} inspection records")
        """
        from robomage.persistence.models import NodeInspection

        db = self.db_manager.get_session()
        try:
            count = (
                db.query(NodeInspection)
                .filter(NodeInspection.workflow_id == workflow_id)
                .delete()
            )

            db.commit()
            return count

        finally:
            db.close()
