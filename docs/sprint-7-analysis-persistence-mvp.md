# Sprint 7: Analysis Result Persistence MVP

**Date**: November 27, 2025  
**Status**: Planning  
**Prerequisites**: Sprint 6 Days 5-6 Complete ✅  
**Branch**: TBD (new sprint)

---

## 🎯 Objective

Add **extensible analysis result storage** to the RoboMage persistence layer, enabling:
- ✅ Peak detection results persist across page reloads
- ✅ Multiple analysis types supported (peak detection, Rietveld, phase ID, etc.)
- ✅ Analysis versioning and provenance tracking
- ✅ Flexible JSON storage adapts to each analysis type's needs

**Philosophy**: This is an **MVP of the pattern** we'll use as we add more analysis capabilities. Peak detection is just the first of many analysis types including GSAS-II Rietveld refinement.

---

## 📋 Deliverables

### 1. Database Schema Extension
**File**: `src/robomage/persistence/models.py`

**New Model**:
```python
class AnalysisResult(Base):
    """
    Generic analysis result storage with extensible JSON schema.
    
    Supports multiple analysis types:
    - peak_detection: Peak positions, fits, quality metrics
    - rietveld: GSAS-II refinement results (future)
    - phase_identification: Phase matching results (future)
    - texture_analysis: Pole figures, ODF (future)
    
    Each analysis type defines its own result_data schema while
    sharing common metadata fields.
    """
    __tablename__ = "analysis_results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Link to file
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    file = relationship("File", back_populates="analysis_results")
    
    # Analysis metadata
    analysis_type = Column(String, nullable=False, index=True)
    """Type of analysis: 'peak_detection', 'rietveld', 'phase_id', etc."""
    
    analysis_version = Column(String, nullable=True)
    """Tool version for reproducibility (e.g., 'robomage-0.1.0', 'gsas-ii-1.0')"""
    
    # Timing
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Flexible result storage
    result_data = Column(JSON, nullable=False)
    """
    Analysis-specific results in JSON format.
    Schema depends on analysis_type.
    See examples below.
    """
    
    parameters = Column(JSON, nullable=True)
    """
    Analysis parameters used to generate results.
    Enables reproducibility and parameter comparison.
    Example: {"profile": "gaussian", "min_prominence": 0.01}
    """
    
    quality_metrics = Column(JSON, nullable=True)
    """
    Optional quality/goodness-of-fit metrics.
    Example: {"overall_r_squared": 0.982, "rwp": 8.2, "gof": 1.34}
    """
    
    # Add index for common queries
    __table_args__ = (
        Index('idx_file_analysis_type', 'file_id', 'analysis_type'),
    )


# Update File model
class File(Base):
    __tablename__ = "files"
    # ... existing fields ...
    
    analysis_results = relationship(
        "AnalysisResult",
        back_populates="file",
        cascade="all, delete-orphan",
        order_by="desc(AnalysisResult.created_at)"
    )
```

**Migration Strategy**:
- SQLAlchemy `Base.metadata.create_all()` creates new table automatically
- Existing data unaffected (backward compatible)
- No migration script needed for development

---

### 2. Result Data Schemas by Analysis Type

**Peak Detection** (Current MVP):
```json
{
  "peaks": [
    {
      "position": 2.856,        // Q (Å⁻¹)
      "height": 1234.5,         // Intensity
      "width": 0.045,           // FWHM
      "area": 55.67,            // Integrated area
      "d_spacing": 2.199,       // d (Å)
      "r_squared": 0.985        // Fit quality
    }
  ],
  "num_peaks_detected": 5,
  "num_peaks_fitted": 5,
  "overall_r_squared": 0.982
}
```

**Parameters Example**:
```json
{
  "profile_type": "gaussian",
  "min_prominence": 0.01,
  "min_distance": 0.1,
  "fit_background": true
}
```

**Quality Metrics Example**:
```json
{
  "overall_r_squared": 0.982,
  "mean_fit_quality": 0.978,
  "failed_fits": 0
}
```

**Future - Rietveld Refinement** (Extensible Pattern):
```json
{
  "phases": [
    {
      "name": "LaB6",
      "space_group": "Pm-3m",
      "fraction": 0.95,
      "lattice_params": {
        "a": 4.1569,
        "b": 4.1569,
        "c": 4.1569,
        "alpha": 90.0,
        "beta": 90.0,
        "gamma": 90.0
      }
    }
  ],
  "rwp": 8.2,
  "rexp": 6.1,
  "gof": 1.34,
  "refined_params": {...}
}
```

**Future - Phase Identification**:
```json
{
  "matches": [
    {
      "phase_name": "Silicon",
      "pdf_id": "00-027-1402",
      "score": 0.95,
      "matched_peaks": 12
    }
  ],
  "search_parameters": {...}
}
```

---

### 3. SessionManager API Extensions
**File**: `src/robomage/persistence/api.py`

**New Methods**:
```python
class SessionManager:
    """High-level API for managing analysis sessions."""
    
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
            
        Example:
            >>> mgr = SessionManager()
            >>> result_id = mgr.save_analysis_result(
            ...     file_id=42,
            ...     analysis_type="peak_detection",
            ...     result_data={"peaks": [...], "num_peaks_detected": 5},
            ...     parameters={"profile": "gaussian", "min_prominence": 0.01},
            ...     quality_metrics={"overall_r_squared": 0.982}
            ... )
        """
        
    def get_analysis_results(
        self,
        file_id: int,
        analysis_type: str | None = None
    ) -> list[AnalysisResult]:
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
            ...     file_id=42,
            ...     analysis_type="peak_detection"
            ... )
        """
        
    def get_latest_analysis(
        self,
        file_id: int,
        analysis_type: str
    ) -> AnalysisResult | None:
        """
        Get the most recent analysis result of a specific type for a file.
        
        Args:
            file_id: Database ID of the file
            analysis_type: Type identifier to filter by
            
        Returns:
            Most recent AnalysisResult or None if not found
            
        Example:
            >>> latest_peak_analysis = mgr.get_latest_analysis(
            ...     file_id=42,
            ...     analysis_type="peak_detection"
            ... )
        """
        
    def delete_analysis_result(self, analysis_id: int) -> bool:
        """
        Delete an analysis result by ID.
        
        Args:
            analysis_id: Database ID of the AnalysisResult
            
        Returns:
            True if deleted, False if not found
        """
```

**Implementation Details**:
```python
def save_analysis_result(
    self,
    file_id: int,
    analysis_type: str,
    result_data: dict,
    parameters: dict | None = None,
    quality_metrics: dict | None = None,
    analysis_version: str | None = None,
) -> int:
    """Save an analysis result to the database."""
    from datetime import datetime
    from .models import AnalysisResult
    
    result = AnalysisResult(
        file_id=file_id,
        analysis_type=analysis_type,
        result_data=result_data,
        parameters=parameters,
        quality_metrics=quality_metrics,
        analysis_version=analysis_version,
        created_at=datetime.utcnow()
    )
    
    self.db.add(result)
    self.db.commit()
    self.db.refresh(result)
    
    return result.id
```

---

### 4. Dashboard Integration
**File**: `src/robomage/dashboard/callbacks/workflow.py`

**Update Workflow Save Callback**:
```python
@app.callback(
    ...,
    Output("analysis-results-store", "data", allow_duplicate=True),
    ...
)
def save_workflow_results_to_session(...):
    """Save workflow results to current session."""
    
    # ... existing file save logic ...
    
    # NEW: Save analysis results to database
    if analysis_results:
        mgr = SessionManager()
        session_files = mgr.get_session_files(session_id)
        
        for filename, analysis_data in analysis_results.items():
            # Find file_id for this filename
            file_record = next(
                (f for f in session_files if f.original_filename == filename),
                None
            )
            
            if file_record:
                # Save peak detection result
                mgr.save_analysis_result(
                    file_id=file_record.id,
                    analysis_type="peak_detection",
                    result_data=analysis_data,
                    parameters={
                        "profile_type": profile,
                        "min_prominence": min_prominence,
                        "min_distance": min_distance
                    },
                    quality_metrics={
                        "overall_r_squared": analysis_data.get("metadata", {}).get("overall_r_squared", 0.0)
                    },
                    analysis_version="robomage-0.1.0"
                )
    
    # Return updated stores including analysis_results
    return (..., analysis_results, ...)
```

**File**: `src/robomage/dashboard/callbacks/persistence.py`

**Update Session Load Helper**:
```python
def _load_session_files(mgr: SessionManager, session_id: int) -> tuple[dict, dict, dict]:
    """
    Helper function to load files and analysis results from a session.
    
    Returns:
        Tuple of (file_data, wavelength_data, analysis_results)
    """
    session_files = mgr.get_session_files(session_id)
    
    if not session_files:
        return {}, {"current_wavelength": 0.1665, "source_type": "standard"}, {}
    
    file_data = {}
    analysis_results = {}
    loaded_wavelength = 0.1665
    
    for session_file in session_files:
        # Load diffraction data
        diffraction = mgr.file_store.load_file(session_file.stored_path)
        if diffraction is None:
            continue
            
        filename = diffraction.filename or "unknown.chi"
        
        # ... existing file_data construction ...
        
        # NEW: Load analysis results for this file
        peak_results = mgr.get_latest_analysis(
            file_id=session_file.id,
            analysis_type="peak_detection"
        )
        
        if peak_results:
            analysis_results[filename] = peak_results.result_data
    
    wavelength_data = {
        "current_wavelength": loaded_wavelength,
        "source_type": "standard"
    }
    
    return file_data, wavelength_data, analysis_results
```

**Update Callback Signatures**:
```python
# Auto-create callback already returns analysis_results ✓
# Load session callback already returns analysis_results ✓
# Just need to update _load_session_files to return 3-tuple
```

---

### 5. Testing

**Unit Tests** (`tests/test_analysis_persistence.py`):
```python
def test_save_analysis_result(session_manager, sample_file):
    """Test saving a peak detection result."""
    result_data = {
        "peaks": [
            {"position": 2.856, "height": 1234.5, "r_squared": 0.985}
        ],
        "num_peaks_detected": 1
    }
    
    result_id = session_manager.save_analysis_result(
        file_id=sample_file.id,
        analysis_type="peak_detection",
        result_data=result_data,
        parameters={"profile": "gaussian"},
        quality_metrics={"overall_r_squared": 0.982}
    )
    
    assert result_id > 0

def test_get_analysis_results(session_manager, sample_file_with_analysis):
    """Test retrieving analysis results."""
    results = session_manager.get_analysis_results(sample_file_with_analysis.id)
    assert len(results) > 0
    assert results[0].analysis_type == "peak_detection"

def test_get_latest_analysis(session_manager, sample_file_with_multiple_analyses):
    """Test getting most recent analysis."""
    latest = session_manager.get_latest_analysis(
        sample_file_with_multiple_analyses.id,
        "peak_detection"
    )
    assert latest is not None
    assert latest.created_at > sample_file_with_multiple_analyses.analysis_results[1].created_at
```

**Integration Tests** (`tests/test_workflow_analysis_persistence.py`):
```python
def test_workflow_save_persists_analysis():
    """Test that workflow save persists analysis results to database."""
    # 1. Run workflow with peak analysis
    # 2. Save results to session
    # 3. Reload page (clear stores)
    # 4. Verify analysis results restored from database
    # 5. Check Analysis tab displays results

def test_multiple_analysis_types():
    """Test storing multiple analysis types for same file."""
    # 1. Save peak detection result
    # 2. Save future Rietveld result (mock data)
    # 3. Verify both stored and retrievable
    # 4. Verify filtering by type works
```

---

## 🏗️ Implementation Plan

### Phase 1: Database & API (Day 1)
**Tasks**:
1. ✅ Add `AnalysisResult` model to `models.py`
2. ✅ Update `File` model with `analysis_results` relationship
3. ✅ Implement `save_analysis_result()` in SessionManager
4. ✅ Implement `get_analysis_results()` in SessionManager
5. ✅ Implement `get_latest_analysis()` in SessionManager
6. ✅ Write unit tests for new API methods

**Validation**:
- All unit tests pass
- Can save and retrieve peak detection results
- Multiple results per file supported

### Phase 2: Dashboard Integration (Day 2)
**Tasks**:
1. ✅ Update `_load_session_files()` to return 3-tuple
2. ✅ Add analysis result loading logic
3. ✅ Update workflow save callback to persist results
4. ✅ Update callback signatures (already done in Sprint 6)
5. ✅ Add debug logging for verification

**Validation**:
- Workflow save persists analysis results
- Session load restores analysis results
- Analysis tab displays results after page reload

### Phase 3: Testing & Documentation (Day 3)
**Tasks**:
1. ✅ Integration tests for full roundtrip
2. ✅ Manual testing of UI workflow
3. ✅ Update user documentation
4. ✅ Update API reference docs
5. ✅ Clean up debug logging

**Validation**:
- All tests pass (unit + integration)
- User guide includes analysis persistence
- API documentation complete

---

## 🎯 Success Criteria

| Criterion | Validation |
|-----------|------------|
| Peak detection results persist across page reloads | Manual test: Run workflow → Save → Reload → Analysis tab shows results |
| Multiple analysis results per file supported | Unit test: Save 2 peak analyses for same file, both retrievable |
| Analysis parameters stored | Unit test: Verify parameters field populated and queryable |
| Quality metrics stored | Unit test: Verify quality_metrics field populated |
| Session load restores analysis | Integration test: Full workflow roundtrip |
| Extensible to future analysis types | Code review: JSON schema supports arbitrary structures |
| Backward compatible | Existing tests pass without modification |

---

## 📊 Benefits of This Design

### 1. Extensibility
- **JSON Storage**: Each analysis type defines its own schema
- **Type Identifier**: `analysis_type` field enables filtering and routing
- **No Schema Changes**: Adding Rietveld results requires zero database changes

### 2. Provenance & Reproducibility
- **Parameters Tracked**: Exact settings used to generate results
- **Version Tracking**: Tool version stored for reproducibility
- **Timestamps**: Created_at enables temporal queries

### 3. Flexibility
- **Multiple Results**: Multiple analyses per file (e.g., different parameters)
- **Quality Comparison**: Query by quality metrics to find best results
- **Type Filtering**: Retrieve only specific analysis types

### 4. Query Performance
- **Indexed**: `idx_file_analysis_type` speeds up common queries
- **Ordered**: Results sorted by created_at descending (latest first)
- **Lazy Loading**: SQLAlchemy relationship enables efficient queries

### 5. Future-Proof
- **GSAS-II Ready**: Rietveld refinement results fit naturally
- **Phase ID Ready**: Phase matching results supported
- **Tool Agnostic**: Any analysis tool's results can be stored

---

## 🔮 Future Enhancements (Post-MVP)

### Analysis History Viewer
- Show all analyses performed on a file
- Compare different parameter sets
- Visualize quality trends over time

### Analysis Export
- Export to CSV with peak positions
- Generate PDF reports with plots
- JSON export for external tools

### Analysis Versioning
- Track parameter changes over time
- Compare results from different versions
- Migration tools for schema updates

### Analysis Comparison
- Side-by-side comparison of different analyses
- Statistical comparison of quality metrics
- Visual diff tools for peak lists

### GSAS-II Integration
- Store Rietveld refinement results
- Link to GSAS project files
- Import/export GSAS formats

---

## 📚 Related Documentation

**Sprint 6 Completion**:
- `docs/sprint-6-days-5-6-COMPLETE.md` - Session integration work completed

**Persistence Layer**:
- `docs/sprint-5-persistence-architecture.md` - Database design philosophy
- `docs/persistence-quick-reference.md` - API usage examples
- `docs/session-storage-expansion-guide.md` - How to extend the system

**Workflow System**:
- `docs/sprint-6-workflow-orchestrator-mvp.md` - Workflow engine architecture
- `docs/WORKFLOW-SESSION-INTEGRATION-SUMMARY.md` - Integration patterns

**User Guides**:
- `docs/dashboard-persistence-guide.md` - Session persistence user documentation

---

## ✅ Definition of Done

- [ ] `AnalysisResult` model added to database schema
- [ ] `File` model relationship configured
- [ ] SessionManager API methods implemented
- [ ] Unit tests written and passing
- [ ] Dashboard callbacks updated to persist/restore results
- [ ] Integration tests written and passing
- [ ] Manual testing completed (workflow → save → reload → verify)
- [ ] Documentation updated (API reference, user guide)
- [ ] Debug logging cleaned up
- [ ] Code reviewed for extensibility
- [ ] Ready to merge to main

---

**Next Steps**: Begin Phase 1 implementation in new chat session  
**Context File**: Use this document to start new conversation with full context
