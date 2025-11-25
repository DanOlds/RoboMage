"""
Database connection and session management.

Provides DatabaseManager class for SQLite database operations.
"""

from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session as DBSession
from sqlalchemy.orm import sessionmaker

from robomage.persistence.models import Base

# Default database location
DEFAULT_DB_PATH = Path.home() / ".robomage" / "robomage.db"


class DatabaseManager:
    """
    Manages database connection and session creation.

    Handles SQLite-specific optimizations including WAL mode for
    better concurrency and busy timeout configuration.
    """

    def __init__(self, db_path: Path | str | None = None):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file.
                    Defaults to ~/.robomage/robomage.db
                    Use ":memory:" for in-memory testing database
        """
        if db_path is None:
            db_path = DEFAULT_DB_PATH

        # Handle Path type explicitly
        if db_path == ":memory:":
            self.db_path: str | Path = ":memory:"
        else:
            self.db_path = Path(db_path)
            # Create parent directory if needed
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Create engine with SQLite-specific optimizations
        db_url = (
            f"sqlite:///{self.db_path}"
            if self.db_path != ":memory:"
            else "sqlite:///:memory:"
        )
        self.engine = create_engine(
            db_url,
            echo=False,  # Set True for SQL debugging
        )

        # Enable WAL mode and set busy timeout for better concurrency
        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record) -> None:  # type: ignore[no-untyped-def]
            """Set SQLite pragmas for better concurrency and performance."""
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
            cursor.execute("PRAGMA busy_timeout=5000")  # Wait 5 seconds on lock
            cursor.close()

        # Create tables if they don't exist
        Base.metadata.create_all(self.engine)

        # Session factory
        self.SessionLocal = sessionmaker(
            bind=self.engine,
            autoflush=False,  # Manual control over flushing
            expire_on_commit=False,  # Keep objects usable after commit
        )

    def get_session(self) -> DBSession:
        """
        Get a new database session.

        Returns:
            SQLAlchemy Session object

        Example:
            >>> db_mgr = DatabaseManager()
            >>> session = db_mgr.get_session()
            >>> # Use session...
            >>> session.close()
        """
        return self.SessionLocal()

    def close(self) -> None:
        """
        Close database connection and dispose of engine.

        Should be called on application shutdown.
        """
        self.engine.dispose()


# Global database manager instance (singleton pattern)
_db_manager: DatabaseManager | None = None


def get_db_manager(db_path: Path | str | None = None) -> DatabaseManager:
    """
    Get or create the global database manager instance.

    Args:
        db_path: Path to database file (only used on first call)

    Returns:
        DatabaseManager instance

    Example:
        >>> mgr = get_db_manager()
        >>> session = mgr.get_session()
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(db_path)
    return _db_manager


def get_db_session() -> DBSession:
    """
    Get a new database session (convenience function).

    Returns:
        SQLAlchemy Session object

    Example:
        >>> session = get_db_session()
        >>> # Use session...
        >>> session.close()
    """
    return get_db_manager().get_session()
