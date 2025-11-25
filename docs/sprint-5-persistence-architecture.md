# Sprint 5: Persistence Architecture Design

## 📋 Executive Summary

**Goal**: Implement a robust persistence layer for RoboMage to enable session management, analysis result caching, and historical data tracking - essential foundation for advanced visualization and collaboration features.

**Status**: Design Phase  
**Priority**: HIGH - Blocking advanced visualization features  
**Estimated Duration**: 5-7 days  
**Prerequisites**: Sprint 4 Phase 2 Complete ✅

---

## 🎯 Problem Statement

### Current Limitations
1. **Ephemeral State**: All data lost on browser refresh (dcc.Store is client-side only)
2. **No Analysis History**: Cannot compare results across sessions or time
3. **Redundant Computation**: Same files re-analyzed repeatedly
4. **No Collaboration**: Cannot share sessions between users or machines
5. **No Provenance**: Parameter history and analysis lineage not tracked
6. **Blocks Phase 3**: Advanced visualization requires queryable historical data

### User Impact
- Scientists lose hours of work from browser crashes
- Waste compute resources re-analyzing identical datasets
- Cannot generate comparative reports across experiments
- No audit trail for publication reproducibility

---

## 🏗️ Architecture Overview

### Design Principles
1. **Start Simple**: SQLite for single-user, local-first operation
2. **Upgrade Path**: Design allows migration to PostgreSQL for multi-user
3. **Separation of Concerns**: Data layer independent of dashboard UI
4. **ACID Compliance**: Reliable transactions for scientific data integrity
5. **Performance**: Fast local queries with intelligent caching
6. **Portability**: SQLite database files are portable and shareable

### High-Level Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      Dashboard Layer                          │
│  (Dash UI - src/robomage/dashboard/)                         │
└────────────────┬─────────────────────────────────────────────┘
                 │ Uses
                 ▼
┌──────────────────────────────────────────────────────────────┐
│                   Persistence API Layer                       │
│  (src/robomage/persistence/api.py)                           │
│  - High-level operations (save_session, load_analysis, etc.) │
│  - Abstraction over database implementation                  │
└────────────────┬─────────────────────────────────────────────┘
                 │ Uses
                 ▼
┌──────────────────────────────────────────────────────────────┐
│                  Database Access Layer                        │
│  (SQLAlchemy ORM - src/robomage/persistence/)                │
│  ├── models.py          - ORM models (Sessions, Files, etc.) │
│  ├── database.py        - Session factory, connection mgmt   │
│  ├── file_store.py      - File system operations             │
│  └── queries.py         - Common query patterns              │
└────────────────┬─────────────────────────────────────────────┘
                 │ Connects to
                 ▼
┌──────────────────────────────────────────────────────────────┐
│                     Storage Layer                             │
│  ├── SQLite Database   - Metadata, sessions, results         │
│  │   (~/.robomage/robomage.db)                               │
│  └── File Store        - Raw .chi/.xy files, exports         │
│      (~/.robomage/files/)                                    │
└──────────────────────────────────────────────────────────────┘
```

---

## 📊 Data Model Design

### Entity Relationship Diagram

```
┌─────────────────┐
│    Session      │
│─────────────────│
│ id (PK)         │───┐
│ name            │   │
│ description     │   │ One-to-Many
│ created_at      │   │
│ last_accessed   │   │
│ tags (JSON)     │   │
└─────────────────┘   │
                      │
                      ▼
                ┌─────────────────┐
                │      File       │
                │─────────────────│
                │ id (PK)         │───┐
                │ session_id (FK) │   │
                │ filename        │   │
                │ original_path   │   │ One-to-Many
                │ stored_path     │   │
                │ wavelength      │   │
                │ upload_time     │   │
                │ file_hash       │   │
                │ metadata (JSON) │   │
                └─────────────────┘   │
                                      │
                                      ▼
                                ┌─────────────────┐
                                │    Analysis     │
                                │─────────────────│
                                │ id (PK)         │───┐
                                │ file_id (FK)    │   │
                                │ analysis_type   │   │ One-to-Many
                                │ parameters (JSON│   │
                                │ timestamp       │   │
                                │ duration_ms     │   │
                                │ success         │   │
                                │ error_msg       │   │
                                └─────────────────┘   │
                                                      │
                                                      ▼
                                                ┌─────────────────┐
                                                │      Peak       │
                                                │─────────────────│
                                                │ id (PK)         │
                                                │ analysis_id (FK)│
                                                │ position_q      │
                                                │ intensity       │
                                                │ fwhm            │
                                                │ d_spacing       │
                                                │ profile_type    │
                                                │ fit_quality     │
                                                │ fit_params(JSON)│
                                                └─────────────────┘
```

### Database Schema

#### Sessions Table
```sql
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tags JSON,  -- Flexible tagging: ["experiment-1", "synchrotron", "LaB6"]
    UNIQUE(name)
);
```

#### Files Table
```sql
CREATE TABLE files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    original_path TEXT,
    stored_path TEXT NOT NULL,  -- Path in file store
    wavelength REAL NOT NULL,   -- Angstroms
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_hash TEXT,             -- SHA256 for deduplication
    file_size INTEGER,          -- Bytes
    num_points INTEGER,         -- Number of data points
    q_min REAL,                 -- Q range minimum
    q_max REAL,                 -- Q range maximum
    metadata JSON,              -- Additional file-specific metadata
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE INDEX idx_files_session ON files(session_id);
CREATE INDEX idx_files_hash ON files(file_hash);
```

#### Analyses Table
```sql
CREATE TABLE analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    analysis_type TEXT NOT NULL,  -- 'peak_detection', 'rietveld', etc.
    parameters JSON NOT NULL,     -- All analysis parameters
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration_ms INTEGER,          -- Execution time
    success BOOLEAN NOT NULL,
    error_msg TEXT,
    peaks_detected INTEGER,
    quality_score REAL,           -- Overall quality metric
    results JSON,                 -- Full analysis results
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
);

CREATE INDEX idx_analyses_file ON analyses(file_id);
CREATE INDEX idx_analyses_type ON analyses(analysis_type);
CREATE INDEX idx_analyses_timestamp ON analyses(timestamp);
```

#### Peaks Table
```sql
CREATE TABLE peaks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id INTEGER NOT NULL,
    peak_index INTEGER NOT NULL,  -- Peak number in this analysis
    position_q REAL NOT NULL,     -- Q value (Å⁻¹)
    position_2theta REAL,         -- 2θ value (degrees)
    d_spacing REAL NOT NULL,      -- d-spacing (Å)
    intensity REAL NOT NULL,
    height REAL,
    fwhm REAL,
    profile_type TEXT,            -- 'gaussian', 'lorentzian', 'voigt'
    fit_quality REAL,             -- R² or similar metric
    fit_params JSON,              -- Profile-specific fit parameters
    FOREIGN KEY (analysis_id) REFERENCES analyses(id) ON DELETE CASCADE
);

CREATE INDEX idx_peaks_analysis ON peaks(analysis_id);
CREATE INDEX idx_peaks_position ON peaks(position_q);
CREATE INDEX idx_peaks_d_spacing ON peaks(d_spacing);
```

#### User Preferences Table (Future)
```sql
CREATE TABLE preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT DEFAULT 'default',  -- For future multi-user support
    key TEXT NOT NULL,
    value JSON NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, key)
);
```

---

## 🔧 Technology Stack Evaluation

### Database: SQLite vs PostgreSQL vs Others

#### Option 1: SQLite (RECOMMENDED for Phase 1)

**Pros:**
- ✅ Zero configuration - single file database
- ✅ Built into Python standard library
- ✅ Perfect for single-user, local-first workflows
- ✅ Fast for read-heavy workloads (typical for analysis review)
- ✅ Portable - entire database is one file
- ✅ ACID compliant with good transaction support
- ✅ Easy backup (copy file)
- ✅ No server process needed
- ✅ Works offline (critical for beamline computers)

**Cons:**
- ⚠️ Limited concurrent writes (readers don't block, writers do)
- ⚠️ Not ideal for multi-user web applications
- ⚠️ File locking issues on NFS (avoid network drives)

**Verdict**: **Excellent choice** for RoboMage's current use case - scientists working on local workstations analyzing their own data.

#### Option 2: PostgreSQL

**Pros:**
- ✅ Excellent concurrent access
- ✅ Advanced querying and indexing
- ✅ Strong for multi-user scenarios
- ✅ Better for large-scale deployments

**Cons:**
- ❌ Requires server setup and administration
- ❌ Overkill for single-user local analysis
- ❌ Network dependency (problematic at beamlines)
- ❌ More complex deployment

**Verdict**: **Overkill** for current needs, but good migration target if RoboMage becomes a shared facility service.

#### Option 3: NoSQL (MongoDB, Redis)

**Pros:**
- ✅ Flexible schema
- ✅ Fast for certain workloads

**Cons:**
- ❌ No ACID guarantees (MongoDB)
- ❌ Requires server process
- ❌ Overkill for structured scientific data
- ❌ SQL is better for relational queries we need

**Verdict**: **Not recommended** - scientific data is relational, SQL is better fit.

### ORM: SQLAlchemy vs Raw SQL vs Pydantic-SQLModel

#### Option 1: SQLAlchemy 2.0 (RECOMMENDED)

**Pros:**
- ✅ Industry standard, mature, well-documented
- ✅ Excellent query builder and ORM
- ✅ Type hints support in 2.0
- ✅ Migration path (Alembic integration)
- ✅ Works with both SQLite and PostgreSQL
- ✅ Team likely has experience with it

**Cons:**
- ⚠️ Learning curve for complex queries
- ⚠️ Can be verbose for simple operations

**Verdict**: **Best choice** for maintainable, scalable database layer.

#### Option 2: Pydantic + SQLModel

**Pros:**
- ✅ Integrates with existing Pydantic models
- ✅ Simpler syntax than SQLAlchemy
- ✅ Built on SQLAlchemy Core

**Cons:**
- ⚠️ Less mature, smaller community
- ⚠️ Some advanced SQLAlchemy features harder to access
- ⚠️ RoboMage already uses Pydantic for data models (potential confusion)

**Verdict**: **Consider**, but SQLAlchemy is more proven for this scale.

#### Option 3: Raw SQL with sqlite3

**Pros:**
- ✅ No dependencies
- ✅ Full control
- ✅ Maximum performance

**Cons:**
- ❌ No type safety
- ❌ SQL injection risks
- ❌ Manual migration management
- ❌ Harder to maintain
- ❌ No abstraction for PostgreSQL migration

**Verdict**: **Not recommended** - maintenance burden too high.

### File Storage Strategy

#### Option 1: Local File System (RECOMMENDED)

**Approach:**
```
~/.robomage/
├── robomage.db              # SQLite database
└── files/
    ├── sessions/
    │   └── {session_id}/
    │       ├── uploads/     # Original .chi/.xy files
    │       └── exports/     # Generated plots, reports
    └── cache/               # Temporary analysis artifacts
```

**Pros:**
- ✅ Simple and fast
- ✅ No additional dependencies
- ✅ Easy to inspect and debug
- ✅ Works offline

**Cons:**
- ⚠️ Not suitable for distributed systems
- ⚠️ Manual cleanup needed

**Verdict**: **Perfect** for local-first scientific workflows.

#### Option 2: Object Storage (S3, MinIO)

**Pros:**
- ✅ Scalable
- ✅ Redundancy

**Cons:**
- ❌ Requires network
- ❌ Adds complexity
- ❌ Not needed for current scale

**Verdict**: **Overkill** for current needs.

### Migration Management

#### Option 1: Alembic (RECOMMENDED)

**Pros:**
- ✅ Industry standard with SQLAlchemy
- ✅ Automatic migration generation
- ✅ Rollback support
- ✅ Version control friendly

**Cons:**
- ⚠️ Additional dependency
- ⚠️ Learning curve

**Verdict**: **Recommended** for maintainable schema evolution.

#### Option 2: Manual SQL Scripts

**Pros:**
- ✅ Simple
- ✅ Full control

**Cons:**
- ❌ Error-prone
- ❌ No rollback
- ❌ Hard to track

**Verdict**: **Not recommended** - will cause problems as schema evolves.

---

## 📁 Implementation Structure

```
src/robomage/persistence/
├── __init__.py              # Public API exports
├── api.py                   # High-level API (SessionManager, AnalysisCache)
├── database.py              # Database connection, session factory
├── models.py                # SQLAlchemy ORM models
├── file_store.py            # File system operations
├── queries.py               # Common query patterns
├── migrations/              # Alembic migrations
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
└── config.py                # Configuration (DB path, file store path)

tests/
├── test_persistence_api.py
├── test_models.py
├── test_file_store.py
└── fixtures/                # Test data
```

---

## 🔌 API Design

### High-Level API (Public Interface)

```python
# src/robomage/persistence/api.py

from robomage.data.models import DiffractionData
from robomage.persistence.models import Session, File, Analysis

class SessionManager:
    """High-level session management API."""
    
    def create_session(
        self, 
        name: str, 
        description: str = "",
        tags: list[str] = None
    ) -> Session:
        """Create a new analysis session."""
    
    def get_session(self, session_id: int) -> Session:
        """Retrieve session by ID."""
    
    def list_sessions(
        self, 
        tags: list[str] = None,
        limit: int = 100
    ) -> list[Session]:
        """List all sessions, optionally filtered by tags."""
    
    def delete_session(self, session_id: int) -> None:
        """Delete session and all associated data."""


class FileManager:
    """File upload and storage management."""
    
    def add_file(
        self,
        session_id: int,
        filename: str,
        data: DiffractionData,
        wavelength: float,
        metadata: dict = None
    ) -> File:
        """Add a file to a session."""
    
    def get_file(self, file_id: int) -> File:
        """Retrieve file metadata by ID."""
    
    def load_file_data(self, file_id: int) -> DiffractionData:
        """Load the actual diffraction data for a file."""
    
    def list_session_files(self, session_id: int) -> list[File]:
        """List all files in a session."""


class AnalysisCache:
    """Analysis result caching and retrieval."""
    
    def save_analysis(
        self,
        file_id: int,
        analysis_type: str,
        parameters: dict,
        results: dict,
        peaks: list[dict] = None
    ) -> Analysis:
        """Save analysis results."""
    
    def get_analysis(
        self,
        file_id: int,
        parameters: dict
    ) -> Analysis | None:
        """Retrieve cached analysis if parameters match."""
    
    def list_file_analyses(self, file_id: int) -> list[Analysis]:
        """List all analyses for a file."""
    
    def compare_peaks(
        self,
        analysis_ids: list[int]
    ) -> dict:
        """Compare peaks across multiple analyses."""


class ReportGenerator:
    """Query historical data for reports and comparisons."""
    
    def get_session_summary(self, session_id: int) -> dict:
        """Generate summary statistics for a session."""
    
    def find_similar_peaks(
        self,
        d_spacing: float,
        tolerance: float = 0.01
    ) -> list[dict]:
        """Find peaks across all analyses near a d-spacing."""
    
    def get_analysis_history(
        self,
        file_id: int = None,
        days: int = 30
    ) -> list[Analysis]:
        """Get analysis history for reporting."""
```

### Usage Examples

```python
# Create a new session
from robomage.persistence import SessionManager, FileManager, AnalysisCache

session_mgr = SessionManager()
session = session_mgr.create_session(
    name="LaB6 Calibration Nov 2025",
    description="Standard reference material analysis",
    tags=["calibration", "SRM660b", "synchrotron"]
)

# Add files to session
file_mgr = FileManager()
data = robomage.load_diffraction_file("sample.chi")
file = file_mgr.add_file(
    session_id=session.id,
    filename="sample.chi",
    data=data,
    wavelength=0.1665,
    metadata={"beamline": "NSLS-II", "temperature": "298K"}
)

# Cache analysis results
cache = AnalysisCache()
analysis = cache.save_analysis(
    file_id=file.id,
    analysis_type="peak_detection",
    parameters={"prominence": 0.1, "profile": "gaussian"},
    results={"peaks_detected": 15, "r_squared": 0.98},
    peaks=[{"position_q": 2.5, "intensity": 1000, ...}, ...]
)

# Retrieve cached analysis (avoids recomputation)
cached = cache.get_analysis(
    file_id=file.id,
    parameters={"prominence": 0.1, "profile": "gaussian"}
)
if cached:
    print(f"Using cached result from {cached.timestamp}")
else:
    # Run new analysis
    pass
```

---

## 🔄 Dashboard Integration Strategy

### Minimal Changes Required

The dashboard currently uses `dcc.Store` for state. We'll add persistence as an *additional* layer, not a replacement:

```python
# Current: dcc.Store (ephemeral)
dcc.Store(id="file-data-store")  # Client-side only

# New: Hybrid approach
dcc.Store(id="file-data-store")      # Fast client-side cache
dcc.Store(id="current-session-id")   # Track active session

# Callbacks auto-save to database
@app.callback(...)
def handle_file_upload(...):
    # 1. Update dcc.Store (immediate UI response)
    # 2. Save to database (background persistence)
    session_mgr.add_file(...)
    return updated_store
```

### Session Restoration UI

Add to dashboard header:
```python
# New UI components
dbc.Button("Save Session", id="save-session-btn")
dbc.Button("Load Session", id="load-session-btn")
dbc.Modal(id="session-browser-modal")  # Browse/search sessions
```

---

## 🚀 Implementation Phases

### Phase 1: Core Infrastructure (Days 1-2)
- Set up SQLAlchemy models
- Create database initialization
- Implement basic SessionManager and FileManager
- Unit tests for core models

**Deliverable**: Can create sessions and store file metadata

### Phase 2: File Storage (Day 3)
- Implement FileStore for .chi/.xy files
- File deduplication by hash
- File retrieval and validation

**Deliverable**: Files uploaded to dashboard are persisted

### Phase 3: Analysis Caching (Day 4)
- Implement AnalysisCache
- Peak storage and retrieval
- Cache hit/miss logic

**Deliverable**: Analysis results cached and reused

### Phase 4: Dashboard Integration (Day 5)
- Update dashboard callbacks to use persistence API
- Session save/load UI
- Session browser modal

**Deliverable**: Dashboard has full persistence support

### Phase 5: Testing & Documentation (Days 6-7)
- Comprehensive integration tests
- Performance benchmarks
- Migration from existing dcc.Store data (if needed)
- User documentation

**Deliverable**: Production-ready persistence layer

---

## 📊 Success Metrics

### Functional Requirements
- ✅ Sessions persist across browser restarts
- ✅ Uploaded files stored and retrievable
- ✅ Analysis results cached correctly
- ✅ Cache hit rate > 80% for repeated analyses
- ✅ Session load time < 500ms for typical session (10 files)
- ✅ Database operations never block UI
- ✅ Data integrity maintained (ACID compliance)

### Performance Requirements
- ✅ File upload and store < 100ms (local disk)
- ✅ Analysis cache lookup < 10ms
- ✅ Session list query < 50ms
- ✅ Peak comparison query < 200ms (1000 peaks)

### Quality Requirements
- ✅ 100% test coverage for persistence layer
- ✅ No data loss scenarios
- ✅ Graceful handling of corrupted databases
- ✅ Clear error messages for all failure modes

---

## 🔍 Open Questions for Review

### Technology Choices to Validate:
1. **SQLite vs PostgreSQL**: Is local-first the right approach?
2. **SQLAlchemy vs SQLModel**: Which ORM fits RoboMage better?
3. **Alembic**: Worth the complexity for schema migrations?
4. **File storage location**: `~/.robomage/` vs project directory?

### Design Decisions to Validate:
1. **Session model**: Is the session concept intuitive for scientists?
2. **Automatic caching**: Should all analyses auto-cache, or opt-in?
3. **File deduplication**: Should identical files (by hash) be deduplicated?
4. **Database location**: Single shared DB vs per-project DBs?

### Integration Concerns:
1. **Backward compatibility**: How to handle existing dashboard usage?
2. **Migration path**: Tool to import existing analysis results?
3. **Multi-user**: How much to design for future multi-user support?
4. **Pixi integration**: Any pixi.toml changes needed?

---

## 🎯 Next Steps

1. **Review this document** - Critical evaluation of choices
2. **Validate with users** - Does session model match workflow?
3. **Prototype core models** - Quick proof of concept
4. **Decision on alternatives** - Finalize technology stack
5. **Begin implementation** - Phase 1 development

---

## 📚 References

- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [SQLite Performance Tuning](https://www.sqlite.org/pragma.html)
- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [Dash dcc.Store Limitations](https://dash.plotly.com/dash-core-components/store)
