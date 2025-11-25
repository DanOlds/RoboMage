# Sprint 5: Persistence Layer MVP - Implementation Plan

**Goal**: Get basic session save/load working in 3 days  
**Date**: November 25, 2025  
**Approach**: Simplest thing that works, then iterate

---

## 🎯 MVP Scope Definition

### ✅ What's IN the MVP

**Core Functionality:**
1. ✅ **Save current dashboard state** (files, wavelengths) to database
2. ✅ **Load previously saved sessions** back into dashboard
3. ✅ **List all saved sessions** (simple browser UI)
4. ✅ **Delete sessions** (cleanup old work)

**Data Stored:**
- ✅ Session metadata (name, description, created date)
- ✅ File metadata (filename, wavelength, upload time, Q range)
- ✅ File data (copy actual .chi/.xy files to storage)

**User Workflow:**
```
1. User uploads files to dashboard (existing)
2. User clicks "Save Session" button (NEW)
3. User enters session name (NEW)
4. Session saved to database (NEW)
5. User can close browser ✨
6. Later: User clicks "Load Session" button (NEW)
7. User selects from saved sessions list (NEW)
8. Dashboard restores exactly as it was ✨
```

### ❌ What's OUT of MVP (Phase 2)

- ❌ Analysis results caching (too complex, add later)
- ❌ Peak data storage (not needed yet)
- ❌ Auto-save (manual save/load is fine for MVP)
- ❌ Session sharing/export (can copy .db file manually)
- ❌ Advanced queries (just list sessions chronologically)
- ❌ Migrations (manually handle schema changes for now)
- ❌ Multi-user support (single user is fine)
- ❌ NFS detection (document limitation instead)

### 🎓 Success Criteria

**MVP is complete when:**
1. ✅ User can save dashboard state with files
2. ✅ User can load saved state days later
3. ✅ Files are exactly as uploaded (data integrity)
4. ✅ Session list shows name, date, file count
5. ✅ Delete session removes all associated data
6. ✅ Works on restart (persists across Python sessions)
7. ✅ All existing tests still pass
8. ✅ Basic tests for persistence layer pass

---

## 📋 Step-by-Step Implementation Plan

### Day 1: Database Foundation (6-8 hours)

#### Step 1.1: Set Up Project Structure (30 min)
**Create new persistence package:**
```bash
mkdir -p src/robomage/persistence
touch src/robomage/persistence/__init__.py
touch src/robomage/persistence/database.py
touch src/robomage/persistence/models.py
touch src/robomage/persistence/file_store.py
touch src/robomage/persistence/api.py

mkdir -p tests/persistence
touch tests/persistence/test_models.py
touch tests/persistence/test_api.py
```

**Expected output**: Clean directory structure ready for code

---

#### Step 1.2: Add SQLAlchemy to Dependencies (15 min)
**Edit `pixi.toml`:**
```toml
[dependencies]
sqlalchemy = ">=2.0,<3"
```

**Commands:**
```bash
pixi install
python -c "import sqlalchemy; print(sqlalchemy.__version__)"
```

**Expected output**: SQLAlchemy 2.x installed and importable

---

#### Step 1.3: Define Database Models (1.5 hours)
**File: `src/robomage/persistence/models.py`**

**What to implement:**
```python
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship, DeclarativeBase

class Base(DeclarativeBase):
    """Base class for all database models."""
    pass

class Session(Base):
    """Analysis session - top-level organizational unit."""
    __tablename__ = 'sessions'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    last_accessed = Column(DateTime, default=datetime.now)
    
    # Relationship to files
    files = relationship("File", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Session(id={self.id}, name='{self.name}', files={len(self.files)})>"

class File(Base):
    """Individual diffraction data file."""
    __tablename__ = 'files'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('sessions.id'), nullable=False)
    
    # File metadata
    filename = Column(String, nullable=False)
    stored_path = Column(String, nullable=False)  # Path in file store
    wavelength = Column(Float, nullable=False)
    upload_time = Column(DateTime, default=datetime.now)
    
    # Data statistics (for quick display)
    num_points = Column(Integer)
    q_min = Column(Float)
    q_max = Column(Float)
    
    # Relationship to session
    session = relationship("Session", back_populates="files")
    
    def __repr__(self):
        return f"<File(id={self.id}, filename='{self.filename}')>"
```

**Test manually:**
```python
# Quick validation script
from robomage.persistence.models import Base, Session, File
print(f"Session table: {Session.__tablename__}")
print(f"File table: {File.__tablename__}")
print("✅ Models defined successfully")
```

**Expected output**: Models import without errors, tables defined

---

#### Step 1.4: Create Database Connection Manager (1 hour)
**File: `src/robomage/persistence/database.py`**

**What to implement:**
```python
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session as DBSession
from robomage.persistence.models import Base

# Default database location
DEFAULT_DB_PATH = Path.home() / ".robomage" / "robomage.db"

class DatabaseManager:
    """Manages database connection and session creation."""
    
    def __init__(self, db_path: Path | str | None = None):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file (default: ~/.robomage/robomage.db)
        """
        if db_path is None:
            db_path = DEFAULT_DB_PATH
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create engine with SQLite-specific optimizations
        self.engine = create_engine(
            f"sqlite:///{self.db_path}",
            echo=False,  # Set True for SQL debugging
        )
        
        # Enable WAL mode for better concurrency
        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA busy_timeout=5000")  # 5 second timeout
            cursor.close()
        
        # Create tables if they don't exist
        Base.metadata.create_all(self.engine)
        
        # Session factory
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def get_session(self) -> DBSession:
        """Get a new database session."""
        return self.SessionLocal()
    
    def close(self):
        """Close database connection."""
        self.engine.dispose()

# Global database manager instance
_db_manager: DatabaseManager | None = None

def get_db_manager(db_path: Path | str | None = None) -> DatabaseManager:
    """Get or create the global database manager."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(db_path)
    return _db_manager

def get_db_session() -> DBSession:
    """Get a new database session (convenience function)."""
    return get_db_manager().get_session()
```

**Test it:**
```python
from robomage.persistence.database import get_db_manager

db_mgr = get_db_manager()
print(f"Database at: {db_mgr.db_path}")
print(f"Exists: {db_mgr.db_path.exists()}")

session = db_mgr.get_session()
print(f"Session created: {session}")
session.close()
print("✅ Database connection working")
```

**Expected output**: Database file created, connection works

---

#### Step 1.5: Implement File Storage (1.5 hours)
**File: `src/robomage/persistence/file_store.py`**

**What to implement:**
```python
import shutil
from pathlib import Path
from datetime import datetime
from robomage.data.models import DiffractionData

# Default file store location
DEFAULT_STORE_PATH = Path.home() / ".robomage" / "files"

class FileStore:
    """Manages persistent storage of diffraction data files."""
    
    def __init__(self, store_path: Path | str | None = None):
        """
        Initialize file store.
        
        Args:
            store_path: Root directory for file storage
        """
        if store_path is None:
            store_path = DEFAULT_STORE_PATH
        
        self.store_path = Path(store_path)
        self.store_path.mkdir(parents=True, exist_ok=True)
    
    def store_file(
        self,
        session_id: int,
        filename: str,
        data: DiffractionData
    ) -> Path:
        """
        Store diffraction data file.
        
        Args:
            session_id: ID of the session this file belongs to
            filename: Original filename
            data: DiffractionData object to store
        
        Returns:
            Path to stored file
        """
        # Create session directory
        session_dir = self.store_path / f"session_{session_id}"
        session_dir.mkdir(exist_ok=True)
        
        # Generate unique filename (handle duplicates)
        stored_path = session_dir / filename
        counter = 1
        while stored_path.exists():
            name = Path(filename).stem
            ext = Path(filename).suffix
            stored_path = session_dir / f"{name}_{counter}{ext}"
            counter += 1
        
        # Write data to file (simple CSV format for now)
        with open(stored_path, 'w') as f:
            f.write("# Q (A^-1), Intensity\n")
            for q, intensity in zip(data.q_values, data.intensity_values):
                f.write(f"{q},{intensity}\n")
        
        return stored_path
    
    def load_file(self, stored_path: Path | str) -> DiffractionData:
        """
        Load diffraction data from stored file.
        
        Args:
            stored_path: Path to stored file
        
        Returns:
            DiffractionData object
        """
        from robomage.data.loaders import load_chi_file
        
        # For MVP, just use existing loader
        # TODO: Handle different storage formats
        return load_chi_file(str(stored_path))
    
    def delete_session_files(self, session_id: int):
        """
        Delete all files for a session.
        
        Args:
            session_id: ID of the session to delete files for
        """
        session_dir = self.store_path / f"session_{session_id}"
        if session_dir.exists():
            shutil.rmtree(session_dir)

# Global file store instance
_file_store: FileStore | None = None

def get_file_store(store_path: Path | str | None = None) -> FileStore:
    """Get or create the global file store."""
    global _file_store
    if _file_store is None:
        _file_store = FileStore(store_path)
    return _file_store
```

**Test it:**
```python
from robomage.persistence.file_store import get_file_store
from robomage import load_test_data

store = get_file_store()
data = load_test_data()

# Store test file
stored_path = store.store_file(999, "test.chi", data)
print(f"Stored at: {stored_path}")
print(f"File exists: {stored_path.exists()}")

# Load it back
loaded_data = store.load_file(stored_path)
print(f"Loaded {len(loaded_data.q_values)} points")
print("✅ File storage working")
```

**Expected output**: File stored and loaded successfully

---

#### Step 1.6: Write Basic Tests (1 hour)
**File: `tests/persistence/test_models.py`**

**What to test:**
```python
import pytest
from robomage.persistence.models import Session, File
from robomage.persistence.database import DatabaseManager

def test_session_creation():
    """Test creating a session in the database."""
    db_mgr = DatabaseManager(":memory:")  # In-memory for testing
    db = db_mgr.get_session()
    
    session = Session(name="Test Session", description="Test description")
    db.add(session)
    db.commit()
    
    assert session.id is not None
    assert session.name == "Test Session"
    db.close()

def test_session_with_files():
    """Test session with file relationship."""
    db_mgr = DatabaseManager(":memory:")
    db = db_mgr.get_session()
    
    session = Session(name="Test Session")
    file1 = File(filename="test1.chi", wavelength=0.1665, stored_path="/tmp/test1.chi")
    file2 = File(filename="test2.chi", wavelength=0.1665, stored_path="/tmp/test2.chi")
    
    session.files.append(file1)
    session.files.append(file2)
    
    db.add(session)
    db.commit()
    
    assert len(session.files) == 2
    assert file1.session_id == session.id
    db.close()

def test_cascade_delete():
    """Test that deleting session deletes files."""
    db_mgr = DatabaseManager(":memory:")
    db = db_mgr.get_session()
    
    session = Session(name="Test Session")
    file1 = File(filename="test.chi", wavelength=0.1665, stored_path="/tmp/test.chi")
    session.files.append(file1)
    
    db.add(session)
    db.commit()
    
    session_id = session.id
    db.delete(session)
    db.commit()
    
    # Files should be deleted too
    files = db.query(File).filter_by(session_id=session_id).all()
    assert len(files) == 0
    db.close()
```

**Run tests:**
```bash
pixi run pytest tests/persistence/test_models.py -v
```

**Expected output**: All tests pass ✅

---

**End of Day 1 Checklist:**
- ✅ Database models defined (Session, File)
- ✅ Database connection working
- ✅ File storage implemented
- ✅ Basic tests passing
- ✅ Can create sessions and files programmatically

---

### Day 2: High-Level API (6-8 hours)

#### Step 2.1: Implement Session Manager API (2 hours)
**File: `src/robomage/persistence/api.py`**

**What to implement:**
```python
from datetime import datetime
from pathlib import Path
from typing import Optional

from robomage.data.models import DiffractionData
from robomage.persistence.database import get_db_session
from robomage.persistence.file_store import get_file_store
from robomage.persistence.models import Session, File

class SessionManager:
    """High-level API for session management."""
    
    def __init__(self):
        self.file_store = get_file_store()
    
    def create_session(
        self,
        name: str,
        description: str = ""
    ) -> Session:
        """
        Create a new analysis session.
        
        Args:
            name: Session name (must be unique)
            description: Optional description
        
        Returns:
            Created Session object
        
        Raises:
            ValueError: If session name already exists
        """
        db = get_db_session()
        
        # Check if name already exists
        existing = db.query(Session).filter_by(name=name).first()
        if existing:
            db.close()
            raise ValueError(f"Session '{name}' already exists")
        
        # Create session
        session = Session(name=name, description=description)
        db.add(session)
        db.commit()
        db.refresh(session)  # Get the ID
        
        session_id = session.id
        db.close()
        
        # Return detached object (safe to use outside session)
        return self.get_session(session_id)
    
    def get_session(self, session_id: int) -> Optional[Session]:
        """Get session by ID."""
        db = get_db_session()
        session = db.query(Session).filter_by(id=session_id).first()
        
        if session:
            # Eagerly load files relationship
            _ = session.files  # Trigger lazy load
            db.expunge(session)  # Detach from session
        
        db.close()
        return session
    
    def list_sessions(self, limit: int = 100) -> list[Session]:
        """
        List all sessions, most recent first.
        
        Args:
            limit: Maximum number of sessions to return
        
        Returns:
            List of Session objects
        """
        db = get_db_session()
        sessions = db.query(Session)\
            .order_by(Session.last_accessed.desc())\
            .limit(limit)\
            .all()
        
        # Eagerly load files and detach
        result = []
        for session in sessions:
            _ = session.files
            db.expunge(session)
            result.append(session)
        
        db.close()
        return result
    
    def delete_session(self, session_id: int):
        """
        Delete session and all associated data.
        
        Args:
            session_id: ID of session to delete
        """
        db = get_db_session()
        session = db.query(Session).filter_by(id=session_id).first()
        
        if session:
            # Delete files from file store
            self.file_store.delete_session_files(session_id)
            
            # Delete from database (cascade deletes File records)
            db.delete(session)
            db.commit()
        
        db.close()
    
    def add_file_to_session(
        self,
        session_id: int,
        filename: str,
        data: DiffractionData,
        wavelength: float
    ) -> File:
        """
        Add a file to a session.
        
        Args:
            session_id: Session to add file to
            filename: Original filename
            data: DiffractionData object
            wavelength: Wavelength in Angstroms
        
        Returns:
            Created File object
        """
        db = get_db_session()
        
        # Verify session exists
        session = db.query(Session).filter_by(id=session_id).first()
        if not session:
            db.close()
            raise ValueError(f"Session {session_id} not found")
        
        # Store file data
        stored_path = self.file_store.store_file(session_id, filename, data)
        
        # Create database record
        file = File(
            session_id=session_id,
            filename=filename,
            stored_path=str(stored_path),
            wavelength=wavelength,
            num_points=len(data.q_values),
            q_min=float(data.q_values.min()),
            q_max=float(data.q_values.max()),
        )
        
        db.add(file)
        
        # Update session last_accessed
        session.last_accessed = datetime.now()
        
        db.commit()
        db.refresh(file)
        
        file_id = file.id
        db.close()
        
        return self.get_file(file_id)
    
    def get_file(self, file_id: int) -> Optional[File]:
        """Get file by ID."""
        db = get_db_session()
        file = db.query(File).filter_by(id=file_id).first()
        
        if file:
            db.expunge(file)
        
        db.close()
        return file
    
    def load_file_data(self, file_id: int) -> DiffractionData:
        """
        Load the actual diffraction data for a file.
        
        Args:
            file_id: File ID to load
        
        Returns:
            DiffractionData object
        """
        file = self.get_file(file_id)
        if not file:
            raise ValueError(f"File {file_id} not found")
        
        return self.file_store.load_file(file.stored_path)
```

**Expected output**: High-level API for session operations

---

#### Step 2.2: Add Public API Exports (15 min)
**File: `src/robomage/persistence/__init__.py`**

```python
"""
Persistence layer for RoboMage.

Provides session management and file storage for the dashboard.
"""

from robomage.persistence.api import SessionManager
from robomage.persistence.models import Session, File
from robomage.persistence.database import get_db_manager, get_db_session

__all__ = [
    "SessionManager",
    "Session",
    "File",
    "get_db_manager",
    "get_db_session",
]
```

---

#### Step 2.3: Write API Tests (2 hours)
**File: `tests/persistence/test_api.py`**

```python
import pytest
from robomage import load_test_data
from robomage.persistence.api import SessionManager
from robomage.persistence.database import DatabaseManager

@pytest.fixture
def session_mgr():
    """Create session manager with in-memory database for testing."""
    # Use in-memory database for tests
    db_mgr = DatabaseManager(":memory:")
    return SessionManager()

def test_create_and_get_session(session_mgr):
    """Test creating and retrieving a session."""
    session = session_mgr.create_session("Test Session", "Test description")
    
    assert session.id is not None
    assert session.name == "Test Session"
    assert session.description == "Test description"
    
    # Retrieve it
    retrieved = session_mgr.get_session(session.id)
    assert retrieved.name == session.name

def test_duplicate_session_name(session_mgr):
    """Test that duplicate session names are rejected."""
    session_mgr.create_session("Unique Name")
    
    with pytest.raises(ValueError, match="already exists"):
        session_mgr.create_session("Unique Name")

def test_list_sessions(session_mgr):
    """Test listing sessions."""
    session_mgr.create_session("Session 1")
    session_mgr.create_session("Session 2")
    session_mgr.create_session("Session 3")
    
    sessions = session_mgr.list_sessions()
    assert len(sessions) == 3

def test_add_file_to_session(session_mgr, tmp_path):
    """Test adding files to a session."""
    session = session_mgr.create_session("Test Session")
    data = load_test_data()
    
    file = session_mgr.add_file_to_session(
        session_id=session.id,
        filename="test.chi",
        data=data,
        wavelength=0.1665
    )
    
    assert file.id is not None
    assert file.filename == "test.chi"
    assert file.wavelength == 0.1665
    assert file.num_points == len(data.q_values)

def test_load_file_data(session_mgr):
    """Test loading file data."""
    session = session_mgr.create_session("Test Session")
    original_data = load_test_data()
    
    file = session_mgr.add_file_to_session(
        session_id=session.id,
        filename="test.chi",
        data=original_data,
        wavelength=0.1665
    )
    
    # Load it back
    loaded_data = session_mgr.load_file_data(file.id)
    
    assert len(loaded_data.q_values) == len(original_data.q_values)
    assert loaded_data.q_values[0] == pytest.approx(original_data.q_values[0])

def test_delete_session(session_mgr):
    """Test deleting a session."""
    session = session_mgr.create_session("To Delete")
    session_id = session.id
    
    session_mgr.delete_session(session_id)
    
    # Should not exist
    assert session_mgr.get_session(session_id) is None
```

**Run tests:**
```bash
pixi run pytest tests/persistence/test_api.py -v
```

**Expected output**: All API tests pass ✅

---

#### Step 2.4: Test End-to-End Workflow (1 hour)
**Create manual test script: `test_persistence_manual.py`**

```python
"""Manual test of persistence layer - simulates dashboard workflow."""

from robomage import load_test_data
from robomage.persistence import SessionManager

def main():
    print("=== Testing RoboMage Persistence Layer ===\n")
    
    mgr = SessionManager()
    
    # 1. Create session
    print("1. Creating session...")
    session = mgr.create_session(
        name="LaB6 Test Session",
        description="Testing persistence layer with SRM 660b data"
    )
    print(f"   ✅ Created session ID={session.id}, name='{session.name}'")
    
    # 2. Add files
    print("\n2. Adding files to session...")
    data = load_test_data()
    
    file1 = mgr.add_file_to_session(
        session_id=session.id,
        filename="SRM_660b.chi",
        data=data,
        wavelength=0.1665
    )
    print(f"   ✅ Added file ID={file1.id}, {file1.num_points} points")
    
    # 3. List sessions
    print("\n3. Listing all sessions...")
    sessions = mgr.list_sessions()
    for s in sessions:
        print(f"   - {s.name}: {len(s.files)} files, created {s.created_at}")
    
    # 4. Load file data
    print("\n4. Loading file data...")
    loaded_data = mgr.load_file_data(file1.id)
    print(f"   ✅ Loaded {len(loaded_data.q_values)} points")
    print(f"   Q range: {loaded_data.statistics.q_range}")
    
    # 5. Simulate "close and reopen"
    print("\n5. Simulating browser restart...")
    session_id = session.id
    del mgr  # Simulate closing application
    
    print("   Creating new SessionManager...")
    mgr2 = SessionManager()
    
    print("   Loading session from database...")
    restored_session = mgr2.get_session(session_id)
    print(f"   ✅ Restored session: {restored_session.name}")
    print(f"   ✅ Has {len(restored_session.files)} files")
    
    # 6. Delete session
    print("\n6. Cleaning up...")
    mgr2.delete_session(session_id)
    print(f"   ✅ Deleted session {session_id}")
    
    print("\n=== All tests passed! ===")

if __name__ == "__main__":
    main()
```

**Run it:**
```bash
pixi run python test_persistence_manual.py
```

**Expected output**: Complete workflow works end-to-end ✅

---

**End of Day 2 Checklist:**
- ✅ SessionManager API implemented
- ✅ Can create/list/delete sessions
- ✅ Can add files to sessions
- ✅ Can load file data
- ✅ All API tests passing
- ✅ End-to-end workflow tested

---

### Day 3: Dashboard Integration (6-8 hours)

#### Step 3.1: Add Save Session UI (2 hours)
**File: `src/robomage/dashboard/layouts/main_layout.py`**

**Add to header (around line 40-80):**
```python
dbc.Col(
    [
        dbc.ButtonGroup(
            [
                dbc.Button(
                    [html.I(className="fas fa-save me-2"), "Save Session"],
                    id="save-session-btn",
                    color="primary",
                    size="sm",
                ),
                dbc.Button(
                    [html.I(className="fas fa-folder-open me-2"), "Load Session"],
                    id="load-session-btn",
                    color="secondary",
                    size="sm",
                ),
            ],
            size="sm",
        ),
    ],
    width=2,
    className="text-end",
),
```

**Add modals at end of layout (before closing container):**
```python
# Save Session Modal
dbc.Modal(
    [
        dbc.ModalHeader("Save Session"),
        dbc.ModalBody(
            [
                dbc.Label("Session Name"),
                dbc.Input(
                    id="save-session-name-input",
                    placeholder="Enter session name...",
                    type="text",
                ),
                html.Div(id="save-session-error", className="text-danger mt-2"),
            ]
        ),
        dbc.ModalFooter(
            [
                dbc.Button("Cancel", id="save-session-cancel", color="secondary"),
                dbc.Button("Save", id="save-session-confirm", color="primary"),
            ]
        ),
    ],
    id="save-session-modal",
    is_open=False,
),

# Load Session Modal
dbc.Modal(
    [
        dbc.ModalHeader("Load Session"),
        dbc.ModalBody(
            [
                dbc.Label("Select a session:"),
                html.Div(id="session-list-container"),
            ]
        ),
        dbc.ModalFooter(
            dbc.Button("Close", id="load-session-close", color="secondary"),
        ),
    ],
    id="load-session-modal",
    is_open=False,
    size="lg",
),
```

---

#### Step 3.2: Implement Save/Load Callbacks (3 hours)
**File: `src/robomage/dashboard/callbacks/persistence.py` (NEW)**

```python
"""Callbacks for session persistence."""

import dash
from dash import Input, Output, State, html, callback_context
import dash_bootstrap_components as dbc

from robomage.persistence import SessionManager
from robomage.data.loaders import load_chi_file


def register_callbacks(app: dash.Dash) -> None:
    """Register persistence callbacks."""
    
    @app.callback(
        Output("save-session-modal", "is_open"),
        [
            Input("save-session-btn", "n_clicks"),
            Input("save-session-cancel", "n_clicks"),
            Input("save-session-confirm", "n_clicks"),
        ],
        [State("save-session-modal", "is_open")],
        prevent_initial_call=True,
    )
    def toggle_save_modal(open_click, cancel_click, confirm_click, is_open):
        """Toggle save session modal."""
        return not is_open
    
    @app.callback(
        [
            Output("save-session-error", "children"),
            Output("save-session-name-input", "value"),
        ],
        [Input("save-session-confirm", "n_clicks")],
        [
            State("save-session-name-input", "value"),
            State("file-data-store", "data"),
            State("wavelength-store", "data"),
        ],
        prevent_initial_call=True,
    )
    def save_session(n_clicks, session_name, file_data, wavelength_data):
        """Save current session to database."""
        if not session_name:
            return "Please enter a session name", dash.no_update
        
        if not file_data:
            return "No files to save", dash.no_update
        
        try:
            mgr = SessionManager()
            
            # Create session
            session = mgr.create_session(name=session_name)
            
            # Add all files
            for filename, file_info in file_data.items():
                # Reconstruct DiffractionData from stored arrays
                from robomage.data.models import DiffractionData
                import numpy as np
                
                data = DiffractionData(
                    q_values=np.array(file_info["q_values"]),
                    intensity_values=np.array(file_info["intensity_values"]),
                )
                
                wavelength = wavelength_data.get(filename, 0.1665)
                
                mgr.add_file_to_session(
                    session_id=session.id,
                    filename=filename,
                    data=data,
                    wavelength=wavelength,
                )
            
            return f"✅ Session '{session_name}' saved successfully!", ""
        
        except ValueError as e:
            return str(e), dash.no_update
        except Exception as e:
            return f"Error saving session: {str(e)}", dash.no_update
    
    @app.callback(
        Output("load-session-modal", "is_open"),
        [
            Input("load-session-btn", "n_clicks"),
            Input("load-session-close", "n_clicks"),
        ],
        [State("load-session-modal", "is_open")],
        prevent_initial_call=True,
    )
    def toggle_load_modal(open_click, close_click, is_open):
        """Toggle load session modal."""
        return not is_open
    
    @app.callback(
        Output("session-list-container", "children"),
        [Input("load-session-modal", "is_open")],
        prevent_initial_call=True,
    )
    def populate_session_list(is_open):
        """Populate the session list when modal opens."""
        if not is_open:
            return dash.no_update
        
        mgr = SessionManager()
        sessions = mgr.list_sessions()
        
        if not sessions:
            return html.P("No saved sessions found.", className="text-muted")
        
        # Create list of sessions
        session_items = []
        for session in sessions:
            item = dbc.Card(
                dbc.CardBody(
                    [
                        html.H5(session.name, className="card-title"),
                        html.P(
                            f"{len(session.files)} files • "
                            f"Created {session.created_at.strftime('%Y-%m-%d %H:%M')}",
                            className="card-text text-muted",
                        ),
                        dbc.ButtonGroup(
                            [
                                dbc.Button(
                                    "Load",
                                    id={"type": "load-session-item", "session_id": session.id},
                                    color="primary",
                                    size="sm",
                                ),
                                dbc.Button(
                                    "Delete",
                                    id={"type": "delete-session-item", "session_id": session.id},
                                    color="danger",
                                    size="sm",
                                    outline=True,
                                ),
                            ],
                        ),
                    ]
                ),
                className="mb-2",
            )
            session_items.append(item)
        
        return session_items
    
    @app.callback(
        [
            Output("file-data-store", "data", allow_duplicate=True),
            Output("wavelength-store", "data", allow_duplicate=True),
            Output("load-session-modal", "is_open", allow_duplicate=True),
        ],
        [Input({"type": "load-session-item", "session_id": dash.ALL}, "n_clicks")],
        prevent_initial_call=True,
    )
    def load_session(n_clicks_list):
        """Load a session from database."""
        ctx = callback_context
        if not ctx.triggered:
            return dash.no_update, dash.no_update, dash.no_update
        
        # Find which button was clicked
        triggered_id = ctx.triggered[0]["prop_id"]
        if "load-session-item" not in triggered_id:
            return dash.no_update, dash.no_update, dash.no_update
        
        # Extract session_id from triggered ID
        import json
        button_id = json.loads(triggered_id.split(".")[0])
        session_id = button_id["session_id"]
        
        # Load session from database
        mgr = SessionManager()
        session = mgr.get_session(session_id)
        
        if not session:
            return dash.no_update, dash.no_update, dash.no_update
        
        # Build file data and wavelength stores
        file_data = {}
        wavelength_data = {}
        
        for file in session.files:
            # Load file data
            data = mgr.load_file_data(file.id)
            
            file_data[file.filename] = {
                "q_values": data.q_values.tolist(),
                "intensity_values": data.intensity_values.tolist(),
                "num_points": len(data.q_values),
            }
            
            wavelength_data[file.filename] = file.wavelength
        
        # Close modal
        return file_data, wavelength_data, False
    
    @app.callback(
        Output("session-list-container", "children", allow_duplicate=True),
        [Input({"type": "delete-session-item", "session_id": dash.ALL}, "n_clicks")],
        prevent_initial_call=True,
    )
    def delete_session(n_clicks_list):
        """Delete a session."""
        ctx = callback_context
        if not ctx.triggered:
            return dash.no_update
        
        # Find which delete button was clicked
        triggered_id = ctx.triggered[0]["prop_id"]
        if "delete-session-item" not in triggered_id:
            return dash.no_update
        
        # Extract session_id
        import json
        button_id = json.loads(triggered_id.split(".")[0])
        session_id = button_id["session_id"]
        
        # Delete from database
        mgr = SessionManager()
        mgr.delete_session(session_id)
        
        # Refresh session list
        return populate_session_list(True)
```

---

#### Step 3.3: Register Persistence Callbacks (15 min)
**File: `src/robomage/dashboard/app.py`**

**Add import:**
```python
from robomage.dashboard.callbacks import analysis, file_upload, plotting, persistence
```

**Register callbacks:**
```python
# Register callbacks
file_upload.register_callbacks(app)
plotting.register_callbacks(app)
analysis.register_callbacks(app)
persistence.register_callbacks(app)  # NEW
```

---

#### Step 3.4: Manual Testing (2 hours)
**Test plan:**

1. **Start dashboard:**
   ```bash
   pixi run python -m robomage.dashboard
   ```

2. **Upload files:**
   - Drag and drop test .chi files
   - Set wavelengths
   - Verify files show in file list

3. **Save session:**
   - Click "Save Session" button
   - Enter name: "Test Session 1"
   - Confirm save
   - Check for success message

4. **Verify persistence:**
   - Close browser tab
   - Reopen dashboard
   - Click "Load Session"
   - Should see "Test Session 1" in list
   - Click "Load"
   - Verify all files restored with correct wavelengths

5. **Test session list:**
   - Create 2-3 more sessions
   - Verify list shows all sessions
   - Check dates, file counts

6. **Test delete:**
   - Click delete on a session
   - Verify it disappears from list
   - Reload page - should still be gone

7. **Check database:**
   ```bash
   sqlite3 ~/.robomage/robomage.db
   > SELECT * FROM sessions;
   > SELECT * FROM files;
   > .quit
   ```

8. **Check file storage:**
   ```bash
   ls -la ~/.robomage/files/
   ```

**Expected result**: Complete save/load workflow works ✅

---

#### Step 3.5: Update Documentation (30 min)
**File: `README.md`**

Add persistence section:
```markdown
### 💾 Session Persistence (NEW)

RoboMage now saves your work automatically to a local database.

**Save your session:**
1. Upload files and configure analysis
2. Click "Save Session" button
3. Enter a descriptive name
4. Session saved to `~/.robomage/robomage.db`

**Load previous session:**
1. Click "Load Session" button
2. Select from your saved sessions
3. Dashboard restores exactly as you left it

**Features:**
- ✅ Persistent across browser restarts
- ✅ File data and metadata saved
- ✅ Wavelength settings preserved
- ✅ Session browser with dates
- ✅ Delete old sessions
```

---

**End of Day 3 Checklist:**
- ✅ Save Session UI implemented
- ✅ Load Session UI implemented
- ✅ Callbacks working
- ✅ Manual testing complete
- ✅ Documentation updated
- ✅ **MVP COMPLETE** 🎉

---

## 🎯 MVP Completion Criteria

**Verify these before calling MVP done:**

1. ✅ User can save current dashboard state with a name
2. ✅ User can load saved sessions days later
3. ✅ All files and wavelengths are preserved exactly
4. ✅ Session list shows name, date, file count
5. ✅ User can delete sessions
6. ✅ Database persists across Python restarts
7. ✅ All existing tests still pass
8. ✅ New persistence tests pass
9. ✅ Manual workflow tested end-to-end
10. ✅ Documentation updated

---

## 🚀 Post-MVP: What Comes Next (Phase 2)

Once MVP is working, we can add:

**Week 2 Enhancements:**
- Auto-save every 5 minutes
- Session export/import (share .db files)
- Analysis results caching
- Peak data storage
- Session tags and search
- Database size monitoring

**Week 3 Polish:**
- NFS detection and warnings
- Migration to PostgreSQL (if needed)
- Performance optimization
- Advanced queries (find similar peaks)
- Backup/restore utilities

---

## 📊 Estimated Timeline

| Task | Time | Cumulative |
|------|------|------------|
| **Day 1: Foundation** | 6-8 hours | 6-8 hours |
| - Project structure | 30 min | |
| - Add dependencies | 15 min | |
| - Database models | 1.5 hours | |
| - Connection manager | 1 hour | |
| - File storage | 1.5 hours | |
| - Basic tests | 1 hour | |
| **Day 2: API** | 6-8 hours | 12-16 hours |
| - SessionManager | 2 hours | |
| - API exports | 15 min | |
| - API tests | 2 hours | |
| - End-to-end test | 1 hour | |
| **Day 3: Integration** | 6-8 hours | 18-24 hours |
| - Save UI | 2 hours | |
| - Load UI & callbacks | 3 hours | |
| - Manual testing | 2 hours | |
| - Documentation | 30 min | |
| **TOTAL** | **18-24 hours** | **2-3 days** |

---

## ✅ Success Metrics

**MVP is successful if:**
- Takes ≤3 days to implement
- Zero data loss in testing
- Session save/load works 100% of time
- Users can close/reopen without losing work
- Database file < 10MB for typical usage
- No impact on existing features

**MVP has failed if:**
- Takes >5 days
- Data corruption occurs
- Users still lose work on restart
- Performance significantly degraded

---

## 🔧 Troubleshooting Guide

**If database file not created:**
```bash
# Check permissions
ls -la ~/.robomage/
# Should show robomage.db

# Check database manually
sqlite3 ~/.robomage/robomage.db
> .tables
> SELECT * FROM sessions;
```

**If file storage not working:**
```bash
# Check file store
ls -la ~/.robomage/files/
# Should show session_* directories
```

**If tests fail:**
```bash
# Run with verbose output
pixi run pytest tests/persistence/ -v -s

# Check database state
sqlite3 ~/.robomage/robomage.db "SELECT * FROM sessions;"
```

**If dashboard doesn't load sessions:**
- Check browser console for errors
- Check terminal for Python errors
- Verify database file exists
- Try loading session via API directly

---

## 📝 Final Checklist

Before marking MVP complete:

- [ ] Code committed to git
- [ ] All tests passing (`pixi run test`)
- [ ] Linting clean (`pixi run lint`)
- [ ] Type checking clean (`pixi run typecheck`)
- [ ] Manual workflow tested
- [ ] Documentation updated
- [ ] Database location documented
- [ ] Known limitations documented
- [ ] Ready for user testing

---

**Once complete, this MVP gives you:**
- ✅ Solid persistence foundation
- ✅ Session save/load working
- ✅ Platform for Phase 2 features (analysis caching, etc.)
- ✅ Migration path to PostgreSQL (via SQLAlchemy)
- ✅ Confidence to build advanced features on top

**Ready to start implementation?** Let me know if you want me to help with any specific step!
