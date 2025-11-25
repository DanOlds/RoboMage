# Session Storage Expansion Guide

**Version**: 1.0  
**Date**: November 25, 2025  
**Status**: Reference Documentation

## Overview

This guide explains how to expand RoboMage's session storage system to store additional data types such as analysis results, plot views, user preferences, or custom metadata. The session persistence layer is designed to be extensible while maintaining data integrity and backward compatibility.

## Current Architecture

### Core Components

1. **Database Layer** (`src/robomage/persistence/database.py`)
   - SQLAlchemy ORM with SQLite backend
   - WAL mode for concurrent access
   - Connection pooling and session management

2. **Data Models** (`src/robomage/persistence/models.py`)
   - `Session` - Top-level container for analysis sessions
   - `File` - Metadata for individual diffraction files
   - Relationships and cascade deletes

3. **File Storage** (`src/robomage/persistence/file_store.py`)
   - HDF5-based physical file storage
   - Organized by session ID
   - Efficient binary data handling

4. **High-level API** (`src/robomage/persistence/api.py`)
   - `SessionManager` - Main interface for session operations
   - Coordinated database and file operations
   - Transaction management

5. **Dashboard Integration** (`src/robomage/dashboard/callbacks/persistence.py`)
   - Save/load/manage UI callbacks
   - Storage configuration
   - Debug information display

## Expansion Patterns

### Pattern 1: Add New Database Table

**Use Case**: Store structured metadata (e.g., peak analysis results, user settings)

**Steps**:

1. **Define SQLAlchemy Model** (`persistence/models.py`):

```python
from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship

class AnalysisResult(Base):
    """Store peak analysis results for a session."""
    __tablename__ = "analysis_results"
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"))
    file_id = Column(Integer, ForeignKey("files.id", ondelete="CASCADE"))
    
    # Analysis metadata
    analysis_type = Column(String, nullable=False)  # e.g., "peak_detection"
    timestamp = Column(DateTime, nullable=False)
    
    # Results as JSON for flexibility
    parameters = Column(JSON)  # Input parameters
    results = Column(JSON)     # Output results
    
    # Relationships
    session = relationship("Session", back_populates="analysis_results")
    file = relationship("File", back_populates="analysis_results")

# Update Session model
class Session(Base):
    # ... existing fields ...
    analysis_results = relationship(
        "AnalysisResult",
        back_populates="session",
        cascade="all, delete-orphan"
    )

# Update File model  
class File(Base):
    # ... existing fields ...
    analysis_results = relationship(
        "AnalysisResult",
        back_populates="file",
        cascade="all, delete-orphan"
    )
```

2. **Add API Methods** (`persistence/api.py`):

```python
def add_analysis_result(
    self,
    session_id: int,
    file_id: int,
    analysis_type: str,
    parameters: dict,
    results: dict,
) -> AnalysisResult:
    """
    Store analysis results for a file.
    
    Args:
        session_id: Session ID
        file_id: File ID  
        analysis_type: Type of analysis (e.g., "peak_detection")
        parameters: Analysis input parameters
        results: Analysis output results
        
    Returns:
        AnalysisResult object
    """
    db = self.db_manager.get_session()
    try:
        result = AnalysisResult(
            session_id=session_id,
            file_id=file_id,
            analysis_type=analysis_type,
            timestamp=datetime.now(),
            parameters=parameters,
            results=results,
        )
        db.add(result)
        db.commit()
        db.refresh(result)
        return result
    finally:
        db.close()

def get_analysis_results(
    self,
    session_id: int,
    analysis_type: str | None = None
) -> list[AnalysisResult]:
    """Get all analysis results for a session."""
    db = self.db_manager.get_session()
    try:
        query = select(AnalysisResult).where(
            AnalysisResult.session_id == session_id
        )
        if analysis_type:
            query = query.where(AnalysisResult.analysis_type == analysis_type)
        return db.execute(query).scalars().all()
    finally:
        db.close()
```

3. **Create Database Migration**:

Since we use SQLAlchemy with `create_all()`, new tables are created automatically. For production deployments with existing databases, you would use Alembic migrations:

```python
# Install: pixi add alembic
# Initialize: pixi run alembic init alembic
# Create migration: pixi run alembic revision --autogenerate -m "Add analysis results"
# Apply: pixi run alembic upgrade head
```

### Pattern 2: Add Fields to Existing Table

**Use Case**: Store simple additional metadata (e.g., user notes, tags)

**Steps**:

1. **Add Column to Model** (`persistence/models.py`):

```python
class Session(Base):
    # ... existing fields ...
    
    # New fields
    tags = Column(String)  # Comma-separated tags
    notes = Column(String)  # User notes
    color_scheme = Column(String, default="default")  # Plot preferences
```

2. **Update API Methods** (`persistence/api.py`):

```python
def update_session_metadata(
    self,
    session_id: int,
    tags: str | None = None,
    notes: str | None = None,
    color_scheme: str | None = None,
) -> None:
    """Update session metadata fields."""
    db = self.db_manager.get_session()
    try:
        session = db.get(Session, session_id)
        if tags is not None:
            session.tags = tags
        if notes is not None:
            session.notes = notes
        if color_scheme is not None:
            session.color_scheme = color_scheme
        db.commit()
    finally:
        db.close()
```

### Pattern 3: Store Large Binary Data

**Use Case**: Store plots, images, or large arrays (e.g., fitted data, background)

**Steps**:

1. **Extend File Store** (`persistence/file_store.py`):

```python
def store_analysis_data(
    self,
    session_id: int,
    file_id: int,
    analysis_type: str,
    data: dict[str, np.ndarray],
) -> Path:
    """
    Store analysis data (fitted peaks, background, etc.).
    
    Args:
        session_id: Session ID
        file_id: File ID
        analysis_type: Type of analysis
        data: Dictionary of numpy arrays to store
        
    Returns:
        Path to stored HDF5 file
    """
    session_dir = self._get_session_dir(session_id)
    filename = f"analysis_{file_id}_{analysis_type}.h5"
    file_path = session_dir / filename
    
    with h5py.File(file_path, "w") as f:
        for key, array in data.items():
            f.create_dataset(key, data=array, compression="gzip")
            
    return file_path

def load_analysis_data(
    self,
    session_id: int,
    file_id: int,
    analysis_type: str,
) -> dict[str, np.ndarray]:
    """Load previously stored analysis data."""
    session_dir = self._get_session_dir(session_id)
    filename = f"analysis_{file_id}_{analysis_type}.h5"
    file_path = session_dir / filename
    
    if not file_path.exists():
        raise FileNotFoundError(f"Analysis data not found: {file_path}")
        
    data = {}
    with h5py.File(file_path, "r") as f:
        for key in f.keys():
            data[key] = f[key][:]
            
    return data
```

2. **Update SessionManager** (`persistence/api.py`):

```python
def save_peak_analysis(
    self,
    session_id: int,
    file_id: int,
    parameters: dict,
    results: dict,
    fitted_data: dict[str, np.ndarray] | None = None,
) -> int:
    """
    Save complete peak analysis with optional fitted data.
    
    Args:
        session_id: Session ID
        file_id: File ID
        parameters: Analysis parameters
        results: Analysis results (peaks, statistics)
        fitted_data: Optional fitted curves, backgrounds, etc.
        
    Returns:
        Analysis result ID
    """
    # Store metadata in database
    result = self.add_analysis_result(
        session_id, file_id, "peak_detection", parameters, results
    )
    
    # Store large arrays separately if provided
    if fitted_data:
        file_path = self.file_store.store_analysis_data(
            session_id, file_id, "peak_detection", fitted_data
        )
        # Optionally store path in database
        result.data_path = str(file_path)
        db = self.db_manager.get_session()
        try:
            db.commit()
        finally:
            db.close()
            
    return result.id
```

### Pattern 4: Store Plot Views and Preferences

**Use Case**: Save plot configurations, zoom levels, user preferences

**Steps**:

1. **Create View Model** (`persistence/models.py`):

```python
class PlotView(Base):
    """Store plot view configurations."""
    __tablename__ = "plot_views"
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"))
    
    # View metadata
    name = Column(String, nullable=False)  # e.g., "Default View"
    view_type = Column(String)  # e.g., "diffraction", "peak_analysis"
    created_at = Column(DateTime, nullable=False)
    is_default = Column(Boolean, default=False)
    
    # View configuration as JSON
    config = Column(JSON)  # {
                          #   "x_axis": "q",
                          #   "y_axis": "intensity",
                          #   "plot_type": "line",
                          #   "x_range": [2.0, 8.0],
                          #   "y_range": null,
                          #   "log_scale": false,
                          #   "colors": ["#1f77b4", "#ff7f0e"],
                          #   "show_peaks": true
                          # }
    
    # Relationship
    session = relationship("Session", back_populates="plot_views")

class Session(Base):
    # ... existing fields ...
    plot_views = relationship(
        "PlotView",
        back_populates="session",
        cascade="all, delete-orphan"
    )
```

2. **Add View Management** (`persistence/api.py`):

```python
def save_plot_view(
    self,
    session_id: int,
    name: str,
    view_type: str,
    config: dict,
    is_default: bool = False,
) -> PlotView:
    """Save a plot view configuration."""
    db = self.db_manager.get_session()
    try:
        # If setting as default, unset other defaults
        if is_default:
            db.execute(
                update(PlotView)
                .where(PlotView.session_id == session_id)
                .where(PlotView.view_type == view_type)
                .values(is_default=False)
            )
            
        view = PlotView(
            session_id=session_id,
            name=name,
            view_type=view_type,
            config=config,
            is_default=is_default,
            created_at=datetime.now(),
        )
        db.add(view)
        db.commit()
        db.refresh(view)
        return view
    finally:
        db.close()

def get_default_view(
    self,
    session_id: int,
    view_type: str,
) -> PlotView | None:
    """Get the default view for a session and type."""
    db = self.db_manager.get_session()
    try:
        return db.execute(
            select(PlotView)
            .where(PlotView.session_id == session_id)
            .where(PlotView.view_type == view_type)
            .where(PlotView.is_default == True)
        ).scalar_one_or_none()
    finally:
        db.close()
```

## Dashboard Integration

### Adding Save/Load UI

When adding new storage capabilities, integrate with the dashboard:

1. **Add UI Controls** (`dashboard/layouts/main_layout.py`):

```python
# Add buttons/inputs for new feature
dbc.Button("Save Analysis", id="save-analysis-button"),
dbc.Button("Load View", id="load-view-button"),
```

2. **Create Callbacks** (`dashboard/callbacks/`):

```python
# Create new callback file for feature
# e.g., dashboard/callbacks/analysis_persistence.py

@app.callback(
    Output("analysis-save-status", "children"),
    Input("save-analysis-button", "n_clicks"),
    State("session-id-store", "data"),
    State("current-analysis-results", "data"),
)
def save_analysis_results(n_clicks, session_id, results):
    """Save current analysis results to session."""
    if not n_clicks or not session_id:
        return dash.no_update
        
    mgr = SessionManager()
    mgr.save_peak_analysis(session_id, file_id, parameters, results)
    
    return dbc.Alert("Analysis saved!", color="success")
```

3. **Register Callbacks** (`dashboard/app.py`):

```python
from robomage.dashboard.callbacks import (
    persistence,
    file_upload,
    plotting,
    analysis,
    analysis_persistence,  # New
)

def create_dash_app():
    # ... existing code ...
    
    # Register callbacks
    persistence.register_persistence_callbacks(app)
    file_upload.register_file_upload_callbacks(app)
    plotting.register_plotting_callbacks(app)
    analysis.register_analysis_callbacks(app)
    analysis_persistence.register_analysis_persistence_callbacks(app)  # New
```

## Testing New Features

### Unit Tests

Create tests for new database models and API methods:

```python
# tests/test_analysis_persistence.py

def test_save_analysis_result(tmp_path):
    """Test saving analysis results."""
    db_path = tmp_path / "test.db"
    mgr = SessionManager(db_path=db_path)
    
    # Create session and file
    session_id = mgr.create_session("Test", "Test session")
    data = load_test_data()
    file_id = mgr.add_file_to_session(session_id, "test.chi", 0.1665, data).id
    
    # Save analysis result
    result = mgr.add_analysis_result(
        session_id=session_id,
        file_id=file_id,
        analysis_type="peak_detection",
        parameters={"prominence": 0.1},
        results={"peaks_found": 5},
    )
    
    assert result.id is not None
    assert result.analysis_type == "peak_detection"
    
    # Verify retrieval
    results = mgr.get_analysis_results(session_id)
    assert len(results) == 1
    assert results[0].results["peaks_found"] == 5
```

### Integration Tests

Test complete workflows:

```python
def test_analysis_save_load_workflow(tmp_path):
    """Test complete analysis save and load workflow."""
    db_path = tmp_path / "test.db"
    mgr = SessionManager(db_path=db_path)
    
    # Create session and analyze
    session_id = mgr.create_session("Analysis Test", "Test")
    data = load_test_data()
    file_id = mgr.add_file_to_session(session_id, "test.chi", 0.1665, data).id
    
    # Perform analysis
    fitted_data = {
        "fitted_intensity": np.random.rand(100),
        "background": np.random.rand(100),
    }
    
    result_id = mgr.save_peak_analysis(
        session_id, file_id,
        parameters={"prominence": 0.1},
        results={"peaks": [1.5, 2.3, 3.7]},
        fitted_data=fitted_data,
    )
    
    # Load and verify
    results = mgr.get_analysis_results(session_id)
    assert len(results) == 1
    
    loaded_data = mgr.file_store.load_analysis_data(
        session_id, file_id, "peak_detection"
    )
    assert np.allclose(loaded_data["fitted_intensity"], fitted_data["fitted_intensity"])
```

## Best Practices

### 1. Use JSON for Flexible Metadata

Store structured but flexible data as JSON:

```python
# Good: JSON for flexible nested structures
config = Column(JSON)  # Can evolve without schema changes

# Use for:
# - User preferences
# - Analysis parameters
# - Variable-length lists
# - Nested configurations
```

### 2. Use Separate Tables for Collections

Store collections of items in separate tables with foreign keys:

```python
# Good: Separate table for 1-to-many relationships
class AnalysisResult(Base):
    session_id = Column(Integer, ForeignKey("sessions.id"))
    
# Not ideal: JSON array in Session table
# session.analysis_results = Column(JSON)  # Hard to query
```

### 3. Store Large Arrays in HDF5

Use HDF5 for large binary data:

```python
# Good: HDF5 for numpy arrays
file_store.store_analysis_data(session_id, file_id, "peaks", {
    "fitted_intensity": fitted_curve,  # Large array
    "background": background,           # Large array
})

# Not ideal: JSON/BLOB in database
# result.fitted_data = fitted_curve.tolist()  # Inefficient, size limits
```

### 4. Maintain Cascade Deletes

Ensure cleanup when sessions are deleted:

```python
# Always use cascade on relationships
class AnalysisResult(Base):
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"))
    
class Session(Base):
    analysis_results = relationship(
        "AnalysisResult",
        cascade="all, delete-orphan"  # Important!
    )
```

### 5. Version Your Data

Include version information for future migrations:

```python
class AnalysisResult(Base):
    # ... other fields ...
    schema_version = Column(Integer, default=1)
    
# When loading:
if result.schema_version == 1:
    # Handle old format
elif result.schema_version == 2:
    # Handle new format
```

## Migration Strategy

### Adding New Fields (Backward Compatible)

1. Add fields with defaults or nullable
2. Update API methods to handle both old and new data
3. Provide migration utility if needed

```python
# Migration utility example
def migrate_sessions_to_v2(mgr: SessionManager):
    """Add tags to all existing sessions."""
    db = mgr.db_manager.get_session()
    try:
        sessions = db.execute(select(Session)).scalars().all()
        for session in sessions:
            if not session.tags:  # New field
                session.tags = "untagged"
        db.commit()
    finally:
        db.close()
```

### Breaking Changes (Use Carefully)

For breaking changes, provide explicit migration tools:

```python
# Version 1 -> Version 2 migration
def migrate_analysis_results_v1_to_v2(db_path: Path):
    """Migrate analysis results from v1 to v2 schema."""
    # 1. Backup database
    shutil.copy(db_path, db_path.with_suffix(".db.backup"))
    
    # 2. Load with old schema
    # 3. Transform data
    # 4. Save with new schema
    # 5. Update version markers
```

## Examples

### Complete Example: Storing Peak Analysis

```python
# 1. Define models
class PeakAnalysisResult(Base):
    """Complete peak analysis results."""
    __tablename__ = "peak_analysis_results"
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"))
    file_id = Column(Integer, ForeignKey("files.id", ondelete="CASCADE"))
    timestamp = Column(DateTime, nullable=False)
    
    # Analysis configuration
    profile_type = Column(String)  # "gaussian", "lorentzian", "voigt"
    prominence = Column(Float)
    distance = Column(Float)
    
    # Summary results (JSON)
    summary = Column(JSON)  # {"peaks_found": 5, "r_squared": 0.98}
    
    # Individual peaks (JSON array)
    peaks = Column(JSON)  # [{"position": 1.5, "height": 100, ...}, ...]
    
    # Path to fitted data (HDF5)
    fitted_data_path = Column(String)
    
    # Relationships
    session = relationship("Session", back_populates="peak_analyses")
    file = relationship("File", back_populates="peak_analyses")

# 2. Add SessionManager method
def save_peak_analysis_complete(
    self,
    session_id: int,
    file_id: int,
    profile_type: str,
    prominence: float,
    distance: float,
    summary: dict,
    peaks: list[dict],
    fitted_data: dict[str, np.ndarray],
) -> int:
    """Save complete peak analysis with all data."""
    # Store fitted data in HDF5
    data_path = self.file_store.store_analysis_data(
        session_id, file_id, "peak_detection", fitted_data
    )
    
    # Store metadata in database
    db = self.db_manager.get_session()
    try:
        analysis = PeakAnalysisResult(
            session_id=session_id,
            file_id=file_id,
            timestamp=datetime.now(),
            profile_type=profile_type,
            prominence=prominence,
            distance=distance,
            summary=summary,
            peaks=peaks,
            fitted_data_path=str(data_path),
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        return analysis.id
    finally:
        db.close()

# 3. Use in application
mgr = SessionManager()
session_id = mgr.create_session("Peak Analysis", "SRM 660b")
data = load_diffraction_file("sample.chi")
file_id = mgr.add_file_to_session(session_id, "sample.chi", 0.1665, data).id

# Perform analysis
analysis_id = mgr.save_peak_analysis_complete(
    session_id=session_id,
    file_id=file_id,
    profile_type="gaussian",
    prominence=0.1,
    distance=5,
    summary={"peaks_found": 5, "r_squared": 0.98},
    peaks=[
        {"position": 1.5, "height": 100, "fwhm": 0.05},
        {"position": 2.3, "height": 80, "fwhm": 0.04},
    ],
    fitted_data={
        "fitted_intensity": fitted_curve,
        "background": background_curve,
        "residuals": residuals,
    },
)

# Later: Load complete analysis
analysis = mgr.get_peak_analysis(analysis_id)
fitted_data = mgr.file_store.load_analysis_data(
    session_id, file_id, "peak_detection"
)
```

## Summary

The RoboMage session storage system is designed for extensibility:

- ✅ **Add new tables** for structured metadata
- ✅ **Extend existing models** with new fields
- ✅ **Use HDF5** for large binary data
- ✅ **JSON columns** for flexible configurations
- ✅ **Maintain relationships** with cascade deletes
- ✅ **Version your schemas** for future migrations
- ✅ **Test thoroughly** with unit and integration tests
- ✅ **Integrate with dashboard** for user-friendly access

By following these patterns, you can extend the persistence layer to support any future analysis workflow while maintaining data integrity and system reliability.

## References

- **Current Implementation**: `src/robomage/persistence/`
- **Database Models**: `src/robomage/persistence/models.py`
- **API Layer**: `src/robomage/persistence/api.py`
- **Dashboard Integration**: `src/robomage/dashboard/callbacks/persistence.py`
- **Tests**: `tests/test_session_persistence_integration.py`

For questions or clarifications, refer to the inline documentation in the source code or consult the development team.
