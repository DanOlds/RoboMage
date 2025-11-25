# RoboMage Persistence Layer - Quick Reference

**Version**: 1.0 | **Status**: Production Ready | **Tests**: 23/23 passing

## 30-Second Overview

The persistence layer saves and restores dashboard sessions with all uploaded files and wavelength settings.

```python
from robomage.persistence import SessionManager
from robomage import load_diffraction_file

mgr = SessionManager()

# Save session
session_id = mgr.create_session("My Analysis")
data = load_diffraction_file("sample.chi")
mgr.add_file_to_session(session_id, "sample.chi", 0.1665, data)

# Load session later
files = mgr.get_session_files(session_id)
for file_obj in files:
    data = mgr.load_file_data(file_obj.id)
    wavelength = file_obj.wavelength
```

## Common Tasks

### Create and Save a Session

```python
from robomage.persistence import SessionManager

mgr = SessionManager()

# Create session
session_id = mgr.create_session(
    name="November 2025 Analysis",
    description="SRM 660b calibration data"
)

# Add files (repeat for each file)
mgr.add_file_to_session(
    session_id=session_id,
    filename="sample.chi",
    wavelength=0.1665,  # NSLS-II synchrotron
    data=diffraction_data_object
)
```

### List and Load Sessions

```python
# List all sessions
sessions = mgr.list_sessions()
for session in sessions:
    print(f"{session.id}: {session.name} ({len(session.files)} files)")

# Load specific session
session_id = 1
files = mgr.get_session_files(session_id)

for file_obj in files:
    # Get metadata (fast)
    print(f"File: {file_obj.filename}")
    print(f"Wavelength: {file_obj.wavelength} Å")
    print(f"Points: {file_obj.num_points}")
    
    # Load full data (slower)
    data = mgr.load_file_data(file_obj.id)
```

### Delete a Session

```python
# Delete session and all files
mgr.delete_session(session_id)
# Removes:
# - Database records
# - Physical files from ~/.robomage/files/session_X/
```

## API Quick Reference

### SessionManager Methods

| Method | Use Case | Speed |
|--------|----------|-------|
| `create_session(name, desc)` | Create new session | Fast |
| `list_sessions()` | Show all sessions | Fast |
| `get_session(id)` | Get session details | Fast |
| `delete_session(id)` | Remove session | Medium |
| `add_file_to_session(...)` | Save file | Medium |
| `get_session_files(id)` | List files in session | Fast |
| `get_file(id)` | Get file metadata | Fast |
| `load_file_data(id)` | Load full dataset | Slow |

### Session Object

```python
session.id              # int: Primary key
session.name            # str: Unique name
session.description     # str: Optional description
session.created_at      # datetime: When created
session.last_accessed   # datetime: Last access
session.files           # list[File]: Related files
```

### File Object

```python
file.id                 # int: Primary key
file.session_id         # int: Parent session
file.filename           # str: Original name
file.stored_path        # str: Full path on disk
file.wavelength         # float: X-ray wavelength (Å)
file.upload_time        # datetime: When uploaded
file.num_points         # int: Data points
file.q_min              # float: Min Q (Å⁻¹)
file.q_max              # float: Max Q (Å⁻¹)
```

## Error Handling

```python
# Duplicate session name
try:
    mgr.create_session("Existing Name")
except ValueError as e:
    print(f"Name already exists: {e}")

# Missing session
session = mgr.get_session(999)
if session is None:
    print("Session not found")

# Missing file
try:
    data = mgr.load_file_data(999)
except ValueError as e:
    print(f"File not found: {e}")
```

## Storage Locations

```
~/.robomage/
├── robomage.db          # SQLite database
└── files/               # Physical files
    ├── session_1/
    │   ├── sample.chi
    │   └── background.xy
    └── session_2/
        └── data.chi
```

## Dashboard Integration

### Save Current State

```python
def save_dashboard_session(name, description, uploaded_files_list):
    """Save current dashboard state to session."""
    mgr = SessionManager()
    session_id = mgr.create_session(name, description)
    
    for file_info in uploaded_files_list:
        mgr.add_file_to_session(
            session_id,
            file_info['filename'],
            file_info['wavelength'],
            file_info['data']
        )
    
    return session_id
```

### Restore Saved State

```python
def load_dashboard_session(session_id):
    """Restore dashboard state from session."""
    mgr = SessionManager()
    files = mgr.get_session_files(session_id)
    
    restored_files = []
    for file_obj in files:
        data = mgr.load_file_data(file_obj.id)
        restored_files.append({
            'filename': file_obj.filename,
            'wavelength': file_obj.wavelength,
            'data': data
        })
    
    return restored_files
```

## Performance Tips

**Fast**: Use `get_file()` for UI display (metadata from database)

**Slow**: Only call `load_file_data()` when you need the full dataset

```python
# ✅ GOOD - Fast display of file list
files = mgr.get_session_files(session_id)
for f in files:
    print(f"{f.filename}: {f.num_points} points")

# ❌ SLOW - Loads all data from disk
files = mgr.get_session_files(session_id)
for f in files:
    data = mgr.load_file_data(f.id)  # Disk I/O!
    print(f"{f.filename}: {len(data.q_values)} points")
```

## Testing

```bash
# Run all persistence tests
pixi run pytest tests/persistence/ -v

# Run specific test
pixi run pytest tests/persistence/test_api.py::test_end_to_end_workflow -v

# Check test coverage
pixi run pytest tests/persistence/ --cov=src/robomage/persistence
```

## Troubleshooting

**Database locked**: Already handled with 5-second busy timeout and WAL mode

**Missing files**: Always use `delete_session()`, don't delete files manually

**Duplicate names**: Check existing names before creating:
```python
existing = {s.name for s in mgr.list_sessions()}
if name in existing:
    # Generate unique name or show error
```

## More Information

- Full documentation: `docs/persistence-layer-documentation.md` (996 lines)
- Implementation plan: `docs/sprint-5-mvp-implementation-plan.md`
- Technology review: `docs/sprint-5-tech-review.md`
- Test examples: `tests/persistence/test_api.py`

---

**Quick Start**: Import `SessionManager`, create session, add files, done! ✅
