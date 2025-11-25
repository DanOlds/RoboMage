# RoboMage Persistence Layer Documentation

**Version**: 1.0  
**Date**: November 25, 2025  
**Status**: Production Ready

## Overview

The RoboMage persistence layer provides session-based storage for powder diffraction analysis workflows. It enables users to save their analysis sessions (including uploaded files and wavelength settings) and restore them later, facilitating reproducible science and long-term data management.

### Key Features

- **Session Management**: Create, list, load, and delete analysis sessions
- **File Storage**: Persistent storage of .chi and .xy diffraction data files
- **Metadata Tracking**: Automatic capture of wavelengths, data ranges, and timestamps
- **Data Integrity**: Verified data roundtrip with numpy.allclose() validation
- **Concurrent Access**: SQLite WAL mode for multi-window dashboard support
- **Cascade Delete**: Automatic cleanup of files when sessions are deleted

## Architecture

### Component Structure

```
src/robomage/persistence/
├── __init__.py          # Public API exports
├── models.py            # SQLAlchemy ORM models (Session, File)
├── database.py          # Database connection management
├── file_store.py        # Physical file storage
└── api.py               # High-level SessionManager API
```

### Data Flow

```
Dashboard → SessionManager → Database (SQLite)
                          ↓
                     FileStore → Disk Storage
                                 ~/.robomage/files/session_X/
```

### Storage Layout

```
~/.robomage/
├── robomage.db          # SQLite database (sessions + file metadata)
└── files/               # Physical file storage
    ├── session_1/
    │   ├── sample.chi
    │   └── background.xy
    ├── session_2/
    │   └── srm660b.chi
    └── session_3/
        ├── data.chi
        └── data_1.chi   # Auto-numbered duplicates
```

## Components

### 1. Database Models (`models.py`)

#### Session Model

Represents an analysis session containing one or more diffraction files.

**Database Table**: `sessions`

**Fields**:
- `id` (int, primary key): Auto-incrementing session ID
- `name` (str, unique): User-provided session name
- `description` (str, optional): Session description
- `created_at` (datetime): Creation timestamp
- `last_accessed` (datetime): Last access timestamp (auto-updated)
- `files` (relationship): One-to-many relationship with File model

**Cascade Behavior**: Deleting a session automatically deletes all associated files (both database records and physical files).

**Example**:
```python
from robomage.persistence import Session

session = Session(
    name="November 2025 Analysis",
    description="SRM 660b calibration data"
)
# Auto-populated: created_at, last_accessed
```

#### File Model

Represents a single diffraction data file within a session.

**Database Table**: `files`

**Fields**:
- `id` (int, primary key): Auto-incrementing file ID
- `session_id` (int, foreign key): Reference to parent session
- `filename` (str): Original filename (e.g., "sample.chi")
- `stored_path` (str): Full path to stored file on disk
- `wavelength` (float): X-ray wavelength in Angstroms
- `upload_time` (datetime): Upload timestamp
- `num_points` (int): Number of Q-intensity data points
- `q_min` (float): Minimum Q value (Å⁻¹)
- `q_max` (float): Maximum Q value (Å⁻¹)
- `session` (relationship): Back-reference to parent Session

**Statistics Storage**: The `num_points`, `q_min`, and `q_max` fields enable quick display of file metadata without loading the full dataset from disk.

**Example**:
```python
from robomage.persistence import File

file_record = File(
    session_id=1,
    filename="sample.chi",
    stored_path="/home/user/.robomage/files/session_1/sample.chi",
    wavelength=0.1665,
    num_points=4098,
    q_min=0.456,
    q_max=33.351
)
```

### 2. Database Manager (`database.py`)

Handles SQLite database connection and session creation with production-ready optimizations.

#### DatabaseManager Class

**Key Features**:
- **WAL Mode**: Write-Ahead Logging for concurrent read/write access
- **Busy Timeout**: 5-second wait for locked database (prevents errors)
- **Auto-schema Creation**: Tables created automatically on first run
- **Singleton Pattern**: Global instance via `get_db_manager()`

**Configuration**:
```python
from robomage.persistence import DatabaseManager

# Production use (default location)
db_mgr = DatabaseManager()
# → ~/.robomage/robomage.db

# Custom location
db_mgr = DatabaseManager("/path/to/custom.db")

# Testing (in-memory)
db_mgr = DatabaseManager(":memory:")
```

**SQLite Pragmas**:
- `PRAGMA journal_mode=WAL`: Enables concurrent readers with single writer
- `PRAGMA busy_timeout=5000`: Wait 5 seconds when database is locked

**Session Management**:
```python
# Get a database session
db = db_mgr.get_session()

try:
    # Perform database operations
    session = db.get(Session, 1)
    session.name = "Updated Name"
    db.commit()
finally:
    db.close()  # Always close sessions
```

#### Global Singleton Functions

**`get_db_manager(db_path=None)`**:
- Returns global DatabaseManager instance
- Creates instance on first call with provided `db_path`
- Subsequent calls ignore `db_path` and return existing instance

**`get_db_session()`**:
- Convenience function for getting a new database session
- Equivalent to `get_db_manager().get_session()`

**Important**: For testing, create DatabaseManager instances directly to avoid singleton pollution:
```python
# Testing - create isolated instance
db_mgr = DatabaseManager(":memory:")
mgr = SessionManager(db_path=":memory:")
mgr.db_manager = db_mgr  # Inject dependency
```

### 3. File Store (`file_store.py`)

Manages physical storage of diffraction data files on disk.

#### FileStore Class

**Key Features**:
- **Session Isolation**: Files organized in `session_X/` subdirectories
- **Format Compatibility**: Stores data in whitespace-separated format compatible with existing loaders
- **Duplicate Handling**: Auto-numbers duplicate filenames (`file.chi`, `file_1.chi`, `file_2.chi`)
- **Extension Support**: Preserves .chi and .xy extensions

**Storage Format**:
```
# Q (A^-1)  Intensity
0.456749  100.5
0.467891  150.2
0.479033  120.8
...
```

**API**:

**`store_file(session_id, filename, data)`**:
- Stores DiffractionData to disk
- Creates session directory if needed
- Handles duplicate filenames automatically
- Returns Path to stored file

**`load_file(stored_path)`**:
- Loads data from stored file
- Auto-detects .chi vs .xy format
- Returns DiffractionData object

**`delete_session_files(session_id)`**:
- Removes entire session directory and all files
- Called automatically by SessionManager.delete_session()

**Example**:
```python
from robomage.persistence import FileStore
from robomage import load_test_data

store = FileStore()
data = load_test_data()

# Store file
path = store.store_file(1, "sample.chi", data)
# → ~/.robomage/files/session_1/sample.chi

# Load file
loaded_data = store.load_file(path)
# Data integrity verified with numpy.allclose()

# Delete all files for session
store.delete_session_files(1)
```

### 4. SessionManager API (`api.py`)

High-level API that coordinates database and file storage operations.

#### SessionManager Class

The primary interface for all persistence operations. Ensures atomic operations and maintains consistency between database records and physical files.

**Initialization**:
```python
from robomage.persistence import SessionManager

# Production use
mgr = SessionManager()

# Custom database location
mgr = SessionManager(db_path="/path/to/db.sqlite")

# Testing
mgr = SessionManager(db_path=":memory:")
```

#### Core Methods

**`create_session(name, description="")`** → `int`

Creates a new analysis session with unique name validation.

**Arguments**:
- `name` (str): Unique session name
- `description` (str, optional): Session description

**Returns**: Session ID (integer primary key)

**Raises**: `ValueError` if session name already exists

**Example**:
```python
mgr = SessionManager()
session_id = mgr.create_session(
    "November 2025 Analysis",
    "SRM 660b calibration with synchrotron data"
)
print(f"Created session {session_id}")
```

---

**`get_session(session_id)`** → `Session | None`

Retrieves a session by ID and updates its `last_accessed` timestamp.

**Arguments**:
- `session_id` (int): Session ID to retrieve

**Returns**: Session object or None if not found

**Side Effect**: Updates `last_accessed` timestamp

**Example**:
```python
session = mgr.get_session(1)
if session:
    print(f"Session: {session.name}")
    print(f"Files: {len(session.files)}")
    print(f"Last accessed: {session.last_accessed}")
```

---

**`list_sessions()`** → `list[Session]`

Lists all sessions ordered by most recently accessed first.

**Returns**: List of Session objects

**Example**:
```python
sessions = mgr.list_sessions()
for session in sessions:
    file_count = len(session.files)
    print(f"{session.name}: {file_count} files (last: {session.last_accessed})")
```

---

**`delete_session(session_id)`** → `None`

Deletes a session and all associated files (database + disk).

**Arguments**:
- `session_id` (int): Session ID to delete

**Raises**: `ValueError` if session does not exist

**Operation Order**:
1. Delete physical files from disk
2. Delete database records (cascade handles file table)

**Example**:
```python
mgr.delete_session(1)
# Removes:
# - Database records for session 1
# - All file records in session 1
# - Directory ~/.robomage/files/session_1/ and all contents
```

---

**`add_file_to_session(session_id, filename, wavelength, data)`** → `File`

Adds a diffraction data file to a session with atomic storage.

**Arguments**:
- `session_id` (int): Session to add file to
- `filename` (str): Original filename (e.g., "sample.chi")
- `wavelength` (float): X-ray wavelength in Angstroms
- `data` (DiffractionData): Data object to store

**Returns**: File object with database record

**Raises**: `ValueError` if session does not exist

**Operation Order**:
1. Verify session exists
2. Store physical file to disk
3. Create database record with metadata
4. Update session's `last_accessed` timestamp

**Metadata Captured**:
- `num_points`: `len(data.q_values)`
- `q_min`: `data.q_values.min()`
- `q_max`: `data.q_values.max()`

**Example**:
```python
from robomage import load_diffraction_file

data = load_diffraction_file("sample.chi")
file_obj = mgr.add_file_to_session(
    session_id=1,
    filename="sample.chi",
    wavelength=0.1665,  # NSLS-II XPD beamline
    data=data
)

print(f"Stored at: {file_obj.stored_path}")
print(f"Points: {file_obj.num_points}")
print(f"Q range: {file_obj.q_min:.3f} - {file_obj.q_max:.3f} Å⁻¹")
```

---

**`get_session_files(session_id)`** → `list[File]`

Retrieves all files for a session.

**Arguments**:
- `session_id` (int): Session ID to get files for

**Returns**: List of File objects (may be empty)

**Example**:
```python
files = mgr.get_session_files(1)
for f in files:
    print(f"{f.filename}: {f.num_points} points @ {f.wavelength} Å")
```

---

**`load_file_data(file_id)`** → `DiffractionData`

Loads the full diffraction dataset from a stored file.

**Arguments**:
- `file_id` (int): File ID to load

**Returns**: DiffractionData object

**Raises**: `ValueError` if file does not exist

**Example**:
```python
# Load just metadata (fast - from database)
file_obj = mgr.get_file(1)
print(f"Q range: {file_obj.q_min} - {file_obj.q_max}")

# Load full data (slower - from disk)
data = mgr.load_file_data(1)
print(f"Loaded {len(data.q_values)} points")
```

---

**`get_file(file_id)`** → `File | None`

Retrieves file metadata without loading the full dataset.

**Arguments**:
- `file_id` (int): File ID to retrieve

**Returns**: File object or None if not found

**Use Case**: Quick display of file information in UI without loading full data

**Example**:
```python
file_obj = mgr.get_file(1)
if file_obj:
    print(f"Filename: {file_obj.filename}")
    print(f"Wavelength: {file_obj.wavelength} Å")
    print(f"Uploaded: {file_obj.upload_time}")
```

## Testing

### Test Coverage

**Total Tests**: 23 persistence tests across 3 files (508 lines)

**Test Files**:
- `test_models.py`: 5 tests - ORM models and relationships
- `test_file_store.py`: 5 tests - File storage operations
- `test_api.py`: 13 tests - SessionManager API and workflows

### Test Categories

**Unit Tests** (10 tests):
- Session creation and unique name validation
- File relationships and cascade delete
- File store initialization and path handling
- Format compatibility (.chi and .xy)

**Integration Tests** (8 tests):
- Store and load file with data integrity verification
- Add file to session with metadata capture
- Delete session with physical file cleanup
- Multiple session isolation

**End-to-End Tests** (5 tests):
- Complete workflow: create → add files → load → delete
- Multi-file sessions with different wavelengths
- Session listing and ordering
- Error handling for nonexistent resources

### Running Tests

```bash
# All persistence tests
pixi run pytest tests/persistence/ -v

# Specific test file
pixi run pytest tests/persistence/test_api.py -v

# Single test
pixi run pytest tests/persistence/test_api.py::test_end_to_end_workflow -v

# With coverage
pixi run pytest tests/persistence/ --cov=src/robomage/persistence --cov-report=term-missing
```

### Test Fixtures

**`session_mgr` fixture** (in test_api.py):
```python
@pytest.fixture
def session_mgr():
    """Create SessionManager with isolated temporary database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        file_store_path = Path(tmpdir) / "files"
        file_store_path.mkdir()
        
        # Create isolated instances (avoid singleton)
        db_mgr = DatabaseManager(db_path=db_path)
        file_store = FileStore(store_path=file_store_path)
        
        mgr = SessionManager(db_path=db_path)
        mgr.db_manager = db_mgr
        mgr.file_store = file_store
        
        yield mgr
```

**Key Design**: Uses dependency injection to avoid singleton pollution between tests. Each test gets a fresh database and file store.

## Usage Examples

### Complete Workflow

```python
from robomage import load_diffraction_file
from robomage.persistence import SessionManager

# Initialize manager
mgr = SessionManager()

# Create session
session_id = mgr.create_session(
    "Rietveld Refinement",
    "Al2O3 sample with multiple temperatures"
)

# Add files with different wavelengths
files = [
    ("room_temp.chi", 1.54056),    # Cu Kα
    ("100K.chi", 0.1665),          # Synchrotron
    ("77K.xy", 0.1665),
]

for filename, wavelength in files:
    data = load_diffraction_file(filename)
    mgr.add_file_to_session(session_id, filename, wavelength, data)

print(f"Session {session_id} created with {len(files)} files")
```

### Loading Saved Session

```python
# List available sessions
sessions = mgr.list_sessions()
for session in sessions:
    print(f"{session.id}: {session.name} ({len(session.files)} files)")

# Load specific session
session_id = 1
files = mgr.get_session_files(session_id)

# Restore data to dashboard
for file_obj in files:
    data = mgr.load_file_data(file_obj.id)
    wavelength = file_obj.wavelength
    
    # Pass to dashboard state
    # dashboard_state.add_file(file_obj.filename, wavelength, data)
```

### Session Management

```python
# Get session with metadata
session = mgr.get_session(1)
print(f"Name: {session.name}")
print(f"Created: {session.created_at}")
print(f"Last accessed: {session.last_accessed}")

# List files with details
for file_obj in session.files:
    print(f"  {file_obj.filename}:")
    print(f"    Wavelength: {file_obj.wavelength} Å")
    print(f"    Points: {file_obj.num_points}")
    print(f"    Q range: {file_obj.q_min:.3f} - {file_obj.q_max:.3f} Å⁻¹")

# Delete old session
mgr.delete_session(1)
```

### Error Handling

```python
from robomage.persistence import SessionManager

mgr = SessionManager()

# Handle duplicate session names
try:
    mgr.create_session("Analysis 1")
    mgr.create_session("Analysis 1")  # Raises ValueError
except ValueError as e:
    print(f"Error: {e}")  # "Session with name 'Analysis 1' already exists"

# Handle missing resources
session = mgr.get_session(999)  # Returns None
if session is None:
    print("Session not found")

try:
    mgr.delete_session(999)  # Raises ValueError
except ValueError as e:
    print(f"Error: {e}")  # "Session 999 not found"
```

## Implementation Details

### Database Schema

**SQLite Schema** (auto-generated by SQLAlchemy):

```sql
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR UNIQUE NOT NULL,
    description TEXT,
    created_at DATETIME NOT NULL,
    last_accessed DATETIME NOT NULL
);

CREATE TABLE files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    filename VARCHAR NOT NULL,
    stored_path VARCHAR NOT NULL,
    wavelength FLOAT NOT NULL,
    upload_time DATETIME NOT NULL,
    num_points INTEGER,
    q_min FLOAT,
    q_max FLOAT,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE INDEX ix_files_session_id ON files(session_id);
```

### Cascade Delete Behavior

When a session is deleted:
1. SQLAlchemy relationship cascade triggers: `cascade="all, delete-orphan"`
2. Database foreign key triggers (if supported by SQLite version)
3. FileStore removes physical directory: `shutil.rmtree(session_dir)`

**Result**: Complete cleanup with no orphaned data.

### Concurrency Model

**Write Operations** (Session Creation, File Addition, Deletion):
- Acquire database lock via SQLite
- Busy timeout allows 5-second wait
- WAL mode allows concurrent reads during write

**Read Operations** (List Sessions, Get Files, Load Data):
- No lock required (WAL mode)
- Multiple dashboard windows can read simultaneously
- Updates to `last_accessed` use brief lock

**Limitations**:
- Single writer at a time (SQLite limitation)
- Not suitable for multi-user server deployment
- Ideal for single-user localhost dashboard

### Data Integrity

**Storage Format Verification**:
- Stores data in whitespace-separated format
- Compatible with `load_chi_file()` and `load_xy_file()`
- Tested with 4098-point datasets using `numpy.allclose()`

**Metadata Consistency**:
- `num_points` verified against `len(data.q_values)`
- `q_min/q_max` calculated from actual data
- Wavelength preserved exactly as provided

**File Uniqueness**:
- Duplicate filenames auto-numbered (`file.chi`, `file_1.chi`)
- Prevents accidental overwrites
- Each file gets unique stored_path

## Performance Considerations

### Database Operations

**Fast Operations** (< 1ms):
- `get_session()` - Single row lookup by primary key
- `get_file()` - Single row lookup by primary key
- `list_sessions()` - Full table scan (acceptable for < 1000 sessions)

**Medium Operations** (< 10ms):
- `create_session()` - Insert + unique constraint check
- `add_file_to_session()` - Insert + relationship update
- `get_session_files()` - Filtered query by foreign key

**Slow Operations** (100ms - 1s):
- `load_file_data()` - Disk I/O to read full dataset
- `delete_session()` - Cascade delete + directory removal

### File Storage

**Storage Size**:
- ~50KB per 4098-point dataset (text format)
- Session with 10 files: ~500KB
- 100 sessions: ~50MB (negligible)

**Load Times** (4098 points):
- Metadata from database: < 1ms
- Full data from disk: ~10-50ms (depends on disk speed)

**Optimization**: Use `get_file()` for UI display, only call `load_file_data()` when full dataset is needed.

### Scalability

**Expected Usage**:
- 10-100 sessions per user
- 5-20 files per session
- 1000-10000 points per file

**Database Size Estimates**:
- 100 sessions: < 100KB (metadata only)
- 1000 files: < 1MB

**Disk Usage**:
- 100 sessions × 10 files × 50KB: ~50MB
- Well within practical limits for beamline workstations

## Integration with Dashboard

### Recommended UI Flow

**Save Session**:
1. User clicks "Save Session" button in dashboard header
2. Modal appears requesting session name and description
3. Dashboard collects current state (all loaded files + wavelengths)
4. Call `SessionManager.create_session(name, description)`
5. For each loaded file, call `add_file_to_session()`
6. Display success message with session ID

**Load Session**:
1. User clicks "Load Session" button
2. Display list from `mgr.list_sessions()`
3. User selects session
4. Call `mgr.get_session_files(session_id)`
5. For each file, call `mgr.load_file_data(file_id)`
6. Restore dashboard state with loaded data + wavelengths

**Session Management**:
1. "Manage Sessions" panel shows `mgr.list_sessions()`
2. Display: name, file count, created date, last accessed
3. Delete button calls `mgr.delete_session(session_id)`
4. Confirmation dialog before deletion

### Dashboard State Mapping

**Current Dashboard State** (to be saved):
```python
# In dashboard callbacks/file_upload.py
uploaded_files = [
    {
        'filename': 'sample.chi',
        'wavelength': 0.1665,
        'data': DiffractionData(...)
    },
    # ...
]
```

**Save to Session**:
```python
from robomage.persistence import SessionManager

def save_session(session_name, session_description, uploaded_files):
    mgr = SessionManager()
    session_id = mgr.create_session(session_name, session_description)
    
    for file_info in uploaded_files:
        mgr.add_file_to_session(
            session_id,
            file_info['filename'],
            file_info['wavelength'],
            file_info['data']
        )
    
    return session_id
```

**Load from Session**:
```python
def load_session(session_id):
    mgr = SessionManager()
    files = mgr.get_session_files(session_id)
    
    uploaded_files = []
    for file_obj in files:
        data = mgr.load_file_data(file_obj.id)
        uploaded_files.append({
            'filename': file_obj.filename,
            'wavelength': file_obj.wavelength,
            'data': data
        })
    
    return uploaded_files
```

## API Reference Summary

### SessionManager

| Method | Arguments | Returns | Description |
|--------|-----------|---------|-------------|
| `create_session` | `name`, `description=""` | `int` | Create new session |
| `get_session` | `session_id` | `Session \| None` | Get session by ID |
| `list_sessions` | - | `list[Session]` | List all sessions |
| `delete_session` | `session_id` | `None` | Delete session + files |
| `add_file_to_session` | `session_id`, `filename`, `wavelength`, `data` | `File` | Add file to session |
| `get_session_files` | `session_id` | `list[File]` | Get all files in session |
| `load_file_data` | `file_id` | `DiffractionData` | Load full dataset |
| `get_file` | `file_id` | `File \| None` | Get file metadata |

### Session Model

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | int | Primary key |
| `name` | str | Unique session name |
| `description` | str \| None | Optional description |
| `created_at` | datetime | Creation timestamp |
| `last_accessed` | datetime | Last access timestamp |
| `files` | list[File] | Related files |

### File Model

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | int | Primary key |
| `session_id` | int | Foreign key to session |
| `filename` | str | Original filename |
| `stored_path` | str | Path to stored file |
| `wavelength` | float | X-ray wavelength (Å) |
| `upload_time` | datetime | Upload timestamp |
| `num_points` | int \| None | Number of data points |
| `q_min` | float \| None | Minimum Q value (Å⁻¹) |
| `q_max` | float \| None | Maximum Q value (Å⁻¹) |
| `session` | Session | Parent session |

## Troubleshooting

### Database Locked Errors

**Symptom**: `sqlite3.OperationalError: database is locked`

**Cause**: Another process has exclusive write lock

**Solution**:
1. Check for unclosed database sessions in code
2. Increase busy timeout (already set to 5000ms)
3. Ensure WAL mode is enabled (already configured)

**Verification**:
```python
import sqlite3
conn = sqlite3.connect("~/.robomage/robomage.db")
cursor = conn.cursor()
cursor.execute("PRAGMA journal_mode")
print(cursor.fetchone())  # Should print ('wal',)
```

### Missing Files After Session Load

**Symptom**: Database records exist but files missing from disk

**Cause**: Manual deletion of `~/.robomage/files/` directory

**Solution**:
```python
# Clean up orphaned database records
mgr = SessionManager()
files = mgr.get_session_files(session_id)

for file_obj in files:
    if not Path(file_obj.stored_path).exists():
        print(f"Orphaned file: {file_obj.filename}")
        # Manual cleanup required
```

**Prevention**: Always use `mgr.delete_session()` instead of manual file deletion.

### Duplicate Session Names

**Symptom**: `ValueError: Session with name 'X' already exists`

**Cause**: Attempting to create session with existing name

**Solution**:
```python
# Check if name exists before creating
sessions = mgr.list_sessions()
existing_names = {s.name for s in sessions}

name = "Analysis 1"
counter = 1
while name in existing_names:
    counter += 1
    name = f"Analysis {counter}"

session_id = mgr.create_session(name)
```

### Test Isolation Issues

**Symptom**: Tests pass individually but fail when run together

**Cause**: Singleton instances persisting between tests

**Solution**: Use dependency injection in test fixtures (see Test Fixtures section above).

## Future Enhancements

### Potential Additions

1. **Session Export/Import**: Export session to .zip file for sharing
2. **Session Tags**: Categorize sessions with tags
3. **File Notes**: Per-file annotations and comments
4. **Analysis Results Storage**: Store peak analysis results with session
5. **Provenance Tracking**: Record which files were used for refinement
6. **Session Snapshots**: Version history for sessions
7. **Multi-user Support**: PostgreSQL backend for shared beamline database

### Migration Path

Current architecture supports future migration to PostgreSQL:
- SQLAlchemy abstracts database specifics
- Change `database.py` connection string
- Models remain unchanged
- Add user authentication layer

## Version History

### v1.0 (November 25, 2025)
- Initial production release
- Session and File models with cascade delete
- SQLite with WAL mode and busy timeout
- FileStore with session-based organization
- SessionManager with 8 core methods
- 23 comprehensive tests (100% passing)
- Complete documentation

## References

### Related Documentation
- `docs/sprint-5-persistence-architecture.md` - Design specifications
- `docs/sprint-5-mvp-implementation-plan.md` - Implementation guide
- `docs/sprint-5-tech-review.md` - Technology decisions
- `README.md` - User-facing API overview

### External Resources
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [SQLite WAL Mode](https://www.sqlite.org/wal.html)
- [Pydantic Models](https://docs.pydantic.dev/)

## Contact

For questions or issues related to the persistence layer:
- Review test files in `tests/persistence/` for usage examples
- Check this documentation for API reference
- Consult `docs/sprint-5-*.md` for design rationale

---

**Document Status**: Complete and verified against implementation  
**Code Status**: Production ready - all tests passing  
**Last Updated**: November 25, 2025
