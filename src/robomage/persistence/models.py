"""
SQLAlchemy ORM models for persistence layer.

Defines database schema for sessions and files.
"""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
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

    def __repr__(self) -> str:
        """String representation of File."""
        return (
            f"<File(id={self.id}, filename='{self.filename}', "
            f"session_id={self.session_id})>"
        )
