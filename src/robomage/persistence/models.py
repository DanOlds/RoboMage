"""
SQLAlchemy ORM models for persistence layer.

Defines database schema for sessions and files.
"""

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class Session(Base):
    """
    Analysis session - top-level organizational unit.

    A session represents a collection of related diffraction data files
    that are analyzed together. Sessions can be saved, loaded, and managed
    through the dashboard interface.

    Attributes:
        id: Primary key
        name: Unique session name
        description: Optional description of the session
        created_at: Timestamp when session was created
        last_accessed: Timestamp when session was last accessed
        files: Relationship to File objects in this session
    """

    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    last_accessed: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # Relationship to files (cascade delete)
    files: Mapped[list["File"]] = relationship(
        "File", back_populates="session", cascade="all, delete-orphan"
    )

    # Relationship to workflows (cascade delete)
    workflows: Mapped[list["Workflow"]] = relationship(
        "Workflow", back_populates="session", cascade="all, delete-orphan"
    )

    # Relationship to node inspections (cascade delete)
    inspections: Mapped[list["NodeInspection"]] = relationship(
        "NodeInspection", back_populates="session", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String representation of Session."""
        file_count = len(self.files) if self.files else 0
        return f"<Session(id={self.id}, name='{self.name}', files={file_count})>"


class File(Base):
    """
    Individual diffraction data file within a session.

    Stores metadata about a diffraction file and links to its stored
    data on disk.

    Attributes:
        id: Primary key
        session_id: Foreign key to parent session
        filename: Original filename
        stored_path: Path to stored file on disk
        wavelength: X-ray wavelength in Angstroms
        upload_time: Timestamp when file was uploaded
        num_points: Number of data points in file
        q_min: Minimum Q value (Å⁻¹)
        q_max: Maximum Q value (Å⁻¹)
        session: Relationship to parent Session
    """

    __tablename__ = "files"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"))

    # File metadata
    filename: Mapped[str] = mapped_column(String)
    stored_path: Mapped[str] = mapped_column(String)
    wavelength: Mapped[float] = mapped_column(Float)
    upload_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # Data statistics (for quick display without loading file)
    num_points: Mapped[int | None] = mapped_column(Integer)
    q_min: Mapped[float | None] = mapped_column(Float)
    q_max: Mapped[float | None] = mapped_column(Float)

    # Relationship to session
    session: Mapped["Session"] = relationship("Session", back_populates="files")

    # Relationship to analysis results (cascade delete)
    analysis_results: Mapped[list["AnalysisResult"]] = relationship(
        "AnalysisResult",
        back_populates="file",
        cascade="all, delete-orphan",
        order_by="desc(AnalysisResult.created_at)",
    )

    def __repr__(self) -> str:
        """String representation of File."""
        return (
            f"<File(id={self.id}, filename='{self.filename}', "
            f"session_id={self.session_id})>"
        )


class Workflow(Base):
    """
    Workflow definition storage.

    Stores workflow definitions and links them to sessions for reproducibility.
    Workflows can be saved, loaded, and re-executed within the context of a session.

    Attributes:
        id: Primary key (UUID string)
        name: Unique workflow name
        description: Optional description
        definition: Workflow definition as JSON (nodes, edges, etc.)
        created_at: Timestamp when workflow was created
        updated_at: Timestamp when workflow was last updated
        session_id: Optional foreign key to parent session
        session: Relationship to parent Session
    """

    __tablename__ = "workflows"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    definition: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # Optional link to session
    session_id: Mapped[int | None] = mapped_column(ForeignKey("sessions.id"))
    session: Mapped["Session"] = relationship("Session", back_populates="workflows")

    def __repr__(self) -> str:
        """String representation of Workflow."""
        return f"<Workflow(id='{self.id}', name='{self.name}', session_id={self.session_id})>"


class AnalysisResult(Base):
    """
    Generic analysis result storage with extensible JSON schema.

    Supports multiple analysis types:
    - peak_detection: Peak positions, fits, quality metrics
    - rietveld: GSAS-II refinement results (future)
    - phase_identification: Phase matching results (future)
    - texture_analysis: Pole figures, ODF (future)

    Each analysis type defines its own result_data schema while
    sharing common metadata fields for provenance and reproducibility.

    Attributes:
        id: Primary key
        file_id: Foreign key to analyzed file
        analysis_type: Type identifier ('peak_detection', 'rietveld', etc.)
        analysis_version: Tool version for reproducibility
        created_at: Timestamp when analysis was performed
        result_data: Analysis-specific results (JSON schema varies by type)
        parameters: Analysis parameters used (for reproducibility)
        quality_metrics: Quality/goodness-of-fit metrics
        file: Relationship to parent File
    """

    __tablename__ = "analysis_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Link to file
    file_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("files.id"), nullable=False
    )
    file: Mapped["File"] = relationship("File", back_populates="analysis_results")

    # Analysis metadata
    analysis_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    analysis_version: Mapped[str | None] = mapped_column(String)

    # Timing
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )

    # Flexible result storage
    result_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    parameters: Mapped[dict | None] = mapped_column(JSON)
    quality_metrics: Mapped[dict | None] = mapped_column(JSON)

    # Index for common queries
    __table_args__ = (Index("idx_file_analysis_type", "file_id", "analysis_type"),)

    def __repr__(self) -> str:
        """String representation of AnalysisResult."""
        return (
            f"<AnalysisResult(id={self.id}, file_id={self.file_id}, "
            f"type='{self.analysis_type}')>"
        )


class NodeInspection(Base):
    """
    Workflow node inspection data for debugging and visualization.

    Stores snapshots of input/output data for individual node executions
    during workflow runs. This enables the Node I/O Inspector tool to
    visualize data flow, diagnose issues, and understand transformations.

    Key Features:
    - Complete I/O snapshots with timing data
    - Compact shape descriptions for quick overview
    - Linked to sessions for easy cleanup
    - Supports filtering by workflow/node/type
    - Indexed for fast queries

    Use Cases:
    - Debugging failed workflows
    - Understanding data transformations
    - Performance profiling
    - Educational demonstrations
    - Quality assurance

    Attributes:
        id: Primary key
        session_id: Optional link to session (for cleanup)
        workflow_id: Workflow identifier
        node_id: Unique node identifier in workflow
        node_type: Node type (e.g., 'load_files', 'peak_analysis')
        input_data: Serialized input data (JSON)
        output_data: Serialized output data (JSON)
        input_shape: Compact shape description (e.g., 'list[3]')
        output_shape: Compact shape description (e.g., 'dict[5]')
        timestamp_in: Node execution start time
        timestamp_out: Node execution end time
        duration_ms: Execution duration in milliseconds
        execution_metadata: Additional context (JSON)
        session: Relationship to parent Session
    """

    __tablename__ = "node_inspections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Optional link to session (for cleanup when session deleted)
    session_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("sessions.id"), nullable=True
    )
    session: Mapped["Session | None"] = relationship(
        "Session", back_populates="inspections"
    )

    # Workflow context
    workflow_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    node_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    node_type: Mapped[str] = mapped_column(String, nullable=False, index=True)

    # I/O data (JSON serialized)
    input_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    output_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Shape summaries (for quick display without parsing JSON)
    input_shape: Mapped[str | None] = mapped_column(String, nullable=True)
    output_shape: Mapped[str | None] = mapped_column(String, nullable=True)

    # Timing information
    timestamp_in: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    timestamp_out: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Additional context (renamed from 'metadata' to avoid SQLAlchemy reserved name)
    execution_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Indexes for common queries
    __table_args__ = (
        Index("idx_workflow_node", "workflow_id", "node_id"),
        Index("idx_session_workflow", "session_id", "workflow_id"),
        Index("idx_node_type", "node_type"),
    )

    def __repr__(self) -> str:
        """String representation of NodeInspection."""
        return (
            f"<NodeInspection(id={self.id}, workflow_id='{self.workflow_id}', "
            f"node_id='{self.node_id}', node_type='{self.node_type}')>"
        )
