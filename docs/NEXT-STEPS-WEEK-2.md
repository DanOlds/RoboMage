# RoboMage - Next Steps: Week 2 Implementation Plan

**Created**: December 1, 2025  
**Status**: Ready to Begin  
**Target Start**: Next Chat Session  
**Duration**: 5 days (Week 2)

---

## 🎯 Week 2 Objective

Implement **Node I/O Inspector** and begin **Analysis Result Viewer** foundation to enable visualization of data flowing through workflow nodes and detailed inspection of peak analysis results.

---

## ✅ Prerequisites (COMPLETE)

Before starting Week 2, these must be done:
- ✅ Sprint 8 Visual Workflow Builder complete
- ✅ All 233 tests passing (100%)
- ✅ Test suite cleaned up and organized
- ✅ Documentation up to date
- ✅ Deprecation warnings resolved (449 → 10)
- ✅ Architecture design complete (`docs/inspection-tools-design.md`)

**Status**: All prerequisites met! Ready to begin implementation.

---

## 📅 Week 2 Daily Plan

### **Day 1: Node I/O Inspector - Data Capture Layer**

#### Objective
Add inspection hooks to the workflow orchestrator to capture node inputs and outputs during execution.

#### Tasks
1. **Extend WorkflowOrchestrator** (`src/robomage/orchestrator.py`)
   - Add `enable_inspection: bool` parameter to `__init__`
   - Add `inspection_data: dict` to store I/O snapshots
   - Create `_serialize_for_inspection()` method
   - Add inspection hooks in `_execute_node()` method

2. **Create Data Models** (`src/robomage/inspection/models.py` - NEW)
   - `NodeIOSnapshot` - Captures input/output at a point in time
   - `InspectionMetadata` - Timing, duration, node type info
   - Pydantic models with JSON serialization

3. **Write Unit Tests** (`tests/test_node_inspector.py` - NEW)
   - Test inspection can be enabled/disabled
   - Test data capture works correctly
   - Test serialization handles all data types
   - Test no performance impact when disabled

#### Code Example
```python
# src/robomage/orchestrator.py additions

from typing import Any, Optional
from datetime import datetime
from robomage.inspection.models import NodeIOSnapshot

class WorkflowOrchestrator:
    def __init__(self, enable_inspection: bool = False):
        self.enable_inspection = enable_inspection
        self.inspection_data: dict[str, NodeIOSnapshot] = {}
        # ... existing code
    
    def _serialize_for_inspection(self, data: Any) -> dict:
        """Serialize data for inspection storage."""
        if isinstance(data, list):
            if data and hasattr(data[0], 'model_dump'):
                return {
                    "type": "list[DiffractionData]",
                    "count": len(data),
                    "sample": data[0].model_dump() if data else None
                }
        # Add more type handlers
        return {"type": str(type(data)), "repr": repr(data)[:1000]}
    
    async def _execute_node(self, node_id: str, node_type: str, 
                           inputs: Any, config: dict) -> Any:
        """Execute node and optionally capture I/O."""
        start_time = datetime.now()
        
        # Capture input
        if self.enable_inspection:
            self.inspection_data[node_id] = NodeIOSnapshot(
                node_id=node_id,
                node_type=node_type,
                input_data=self._serialize_for_inspection(inputs),
                timestamp_in=start_time
            )
        
        # Execute node (existing logic)
        handler = self.node_handlers[node_type]
        output = await handler(inputs, config)
        
        # Capture output
        if self.enable_inspection:
            self.inspection_data[node_id].output_data = \
                self._serialize_for_inspection(output)
            self.inspection_data[node_id].timestamp_out = datetime.now()
            self.inspection_data[node_id].duration_ms = \
                (datetime.now() - start_time).total_seconds() * 1000
        
        return output
```

#### Acceptance Criteria
- [ ] Orchestrator can enable/disable inspection mode
- [ ] I/O data captured correctly for all node types
- [ ] Serialization handles DiffractionData, lists, dicts, primitives
- [ ] Unit tests pass with 100% coverage
- [ ] No performance impact when inspection disabled (<1% overhead)

#### Files to Create/Modify
- **NEW**: `src/robomage/inspection/__init__.py`
- **NEW**: `src/robomage/inspection/models.py`
- **MODIFY**: `src/robomage/orchestrator.py`
- **NEW**: `tests/test_node_inspector.py`

#### Estimated Time: 6-8 hours

---

### **Day 2: Node I/O Inspector - Database Storage**

#### Objective
Persist inspection data to database for later retrieval and analysis.

#### Tasks
1. **Create Database Model** (`src/robomage/persistence/models.py`)
   - Add `NodeInspection` table
   - Foreign key to workflow execution
   - JSON columns for I/O data
   - Indexes for fast queries

2. **Extend SessionManager** (`src/robomage/persistence/api.py`)
   - Add `save_inspection_data()` method
   - Add `get_inspection_data()` method
   - Add `delete_inspection_data()` method
   - Handle bulk saves efficiently

3. **Add to Workflow Service** (`services/workflow_engine/main.py`)
   - Enable inspection mode via API parameter
   - Save inspection data after execution
   - Return inspection data in response (optional)

4. **Write Tests** (`tests/test_node_inspection_persistence.py` - NEW)
   - Test save/load roundtrip
   - Test query by workflow/node
   - Test cascade delete
   - Test performance with large datasets

#### Code Example
```python
# src/robomage/persistence/models.py additions

class NodeInspection(Base):
    """Store node I/O inspection data."""
    
    __tablename__ = "node_inspections"
    
    id = Column(Integer, primary_key=True)
    workflow_execution_id = Column(Integer, nullable=True)  # Optional link
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=True)
    
    # Node identification
    node_id = Column(String, nullable=False, index=True)
    node_type = Column(String, nullable=False, index=True)
    
    # I/O data (JSON serialized)
    input_data = Column(JSON)
    output_data = Column(JSON)
    
    # Metadata
    input_shape = Column(String)  # Human-readable summary
    output_shape = Column(String)
    duration_ms = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    session = relationship("Session", back_populates="inspections")

# Also update Session model
class Session(Base):
    # ... existing fields
    inspections = relationship("NodeInspection", back_populates="session",
                              cascade="all, delete-orphan")
```

#### Acceptance Criteria
- [ ] NodeInspection table created with proper schema
- [ ] SessionManager can save/load inspection data
- [ ] Database migration runs successfully
- [ ] All tests pass (no regressions)
- [ ] Inspection data persists across sessions

#### Files to Create/Modify
- **MODIFY**: `src/robomage/persistence/models.py`
- **MODIFY**: `src/robomage/persistence/api.py`
- **MODIFY**: `services/workflow_engine/main.py`
- **NEW**: `tests/test_node_inspection_persistence.py`

#### Estimated Time: 6-8 hours

---

### **Day 3: Node I/O Inspector - Dashboard UI (Part 1)**

#### Objective
Create dashboard tab with basic node inspection visualization.

#### Tasks
1. **Create Inspector Layout** (`src/robomage/dashboard/layouts/inspector_layout.py` - NEW)
   - Tab structure with node selector
   - Input/output display panels
   - Execution statistics section

2. **Create Inspector Component** (`src/robomage/dashboard/components/node_inspector_panel.py` - NEW)
   - Node I/O display component
   - Data summary visualizations
   - JSON viewer with syntax highlighting

3. **Add to Main Dashboard** (`src/robomage/dashboard/__main__.py`)
   - Register new "Inspector" tab (5th tab)
   - Wire up initial layout

4. **Basic Callbacks** (`src/robomage/dashboard/callbacks/inspector.py` - NEW)
   - Load inspection data for selected workflow
   - Display node I/O on node selection
   - Show execution timeline

#### Code Example
```python
# src/robomage/dashboard/layouts/inspector_layout.py

import dash_bootstrap_components as dbc
from dash import html, dcc

def create_inspector_tab() -> dbc.Tab:
    """Create Node I/O Inspector tab."""
    
    return dbc.Tab(
        label="🔍 Inspector",
        tab_id="inspector-tab",
        children=[
            dbc.Container([
                html.H2("Node I/O Inspector"),
                html.P("Visualize data flowing through workflow nodes"),
                
                dbc.Row([
                    # Left: Workflow/Node selector
                    dbc.Col([
                        html.H5("Select Workflow"),
                        dcc.Dropdown(
                            id="inspector-workflow-selector",
                            placeholder="Choose workflow execution..."
                        ),
                        
                        html.Hr(),
                        
                        html.H5("Nodes"),
                        html.Div(id="inspector-node-list")
                    ], width=3),
                    
                    # Right: I/O display
                    dbc.Col([
                        dbc.Tabs([
                            dbc.Tab(
                                label="Input Data",
                                children=[html.Div(id="inspector-input-panel")]
                            ),
                            dbc.Tab(
                                label="Output Data",
                                children=[html.Div(id="inspector-output-panel")]
                            ),
                            dbc.Tab(
                                label="Statistics",
                                children=[html.Div(id="inspector-stats-panel")]
                            ),
                        ])
                    ], width=9)
                ])
            ], fluid=True)
        ]
    )
```

#### Acceptance Criteria
- [ ] Inspector tab appears in dashboard
- [ ] Can select workflow from dropdown
- [ ] Can select node from list
- [ ] Input/output data displays correctly
- [ ] Statistics show duration, data shapes
- [ ] UI is responsive and professional

#### Files to Create/Modify
- **NEW**: `src/robomage/dashboard/layouts/inspector_layout.py`
- **NEW**: `src/robomage/dashboard/components/node_inspector_panel.py`
- **NEW**: `src/robomage/dashboard/callbacks/inspector.py`
- **MODIFY**: `src/robomage/dashboard/__main__.py`
- **NEW**: `tests/test_dashboard_inspector.py`

#### Estimated Time: 6-8 hours

---

### **Day 4: Node I/O Inspector - Dashboard UI (Part 2)**

#### Objective
Add advanced visualizations and interactive features to inspector.

#### Tasks
1. **Add Data Visualizations**
   - Plot Q vs intensity for DiffractionData inputs/outputs
   - Show data transformation effects
   - Diff visualization (input vs output)

2. **Add Timeline View**
   - Visual timeline of node execution
   - Color-coded by duration
   - Click to jump to node details

3. **Add Export Features**
   - Export inspection data as JSON
   - Export plots as PNG/SVG
   - Copy to clipboard functionality

4. **Polish UI**
   - Add loading states
   - Add error handling
   - Add helpful tooltips
   - Responsive design

#### Acceptance Criteria
- [ ] Plots display correctly for diffraction data
- [ ] Timeline shows execution flow visually
- [ ] Export functions work correctly
- [ ] UI handles errors gracefully
- [ ] All inspector tests pass

#### Files to Modify
- **MODIFY**: `src/robomage/dashboard/components/node_inspector_panel.py`
- **MODIFY**: `src/robomage/dashboard/callbacks/inspector.py`
- **MODIFY**: `tests/test_dashboard_inspector.py`

#### Estimated Time: 6-8 hours

---

### **Day 5: Analysis Result Viewer - Foundation**

#### Objective
Extend peak analysis data models and plan detailed result viewer UI.

#### Tasks
1. **Extend Analysis Models** (`src/robomage/data/models.py`)
   - Add fitted curve data to peak results
   - Add residuals array
   - Add background curve
   - Add fit quality classification

2. **Update Peak Analysis Service** (`services/peak_analysis/main.py`)
   - Return extended data in response
   - Store fitted curves, residuals
   - Calculate additional quality metrics

3. **Design Viewer Architecture**
   - Sketch out detailed peak viewer UI
   - Plan comparison features
   - Design export formats

4. **Create Initial Layout** (`src/robomage/dashboard/layouts/analysis_viewer_layout.py` - NEW)
   - Tab structure placeholder
   - Peak gallery component skeleton
   - Detail panel placeholder

#### Code Example
```python
# src/robomage/data/models.py additions

class DetailedPeakInfo(BaseModel):
    """Extended peak information with fit quality data."""
    
    # Existing fields
    position: float
    intensity: float
    fwhm: float
    area: float
    d_spacing: float
    
    # NEW: Fit quality data
    fitted_curve: list[float] = Field(description="Y values of fitted curve")
    residuals: list[float] = Field(description="Data - fit")
    background_curve: list[float] = Field(description="Estimated background")
    
    # NEW: Quality metrics
    r_squared: float = Field(ge=0.0, le=1.0)
    chi_squared: float = Field(ge=0.0)
    fit_quality: Literal["excellent", "good", "fair", "poor"]
    
    # NEW: Context
    adjacent_peak_ids: list[str] = Field(default_factory=list)
    peak_family: Optional[str] = None  # For doublets, multiplets
    
    @property
    def quality_score(self) -> float:
        """Unified quality score 0-100."""
        return self.r_squared * 100
```

#### Acceptance Criteria
- [ ] Extended data models defined and validated
- [ ] Peak analysis service returns new fields
- [ ] Initial viewer layout created
- [ ] Architecture documented
- [ ] No regressions in existing functionality

#### Files to Create/Modify
- **MODIFY**: `src/robomage/data/models.py`
- **MODIFY**: `services/peak_analysis/main.py`
- **MODIFY**: `services/peak_analysis/engine.py`
- **NEW**: `src/robomage/dashboard/layouts/analysis_viewer_layout.py`
- **MODIFY**: `tests/test_data_models.py`

#### Estimated Time: 6-8 hours

---

## 📦 Deliverables Checklist

By end of Week 2, these should be complete:

### Node I/O Inspector
- [ ] Data capture in orchestrator (toggle-able)
- [ ] Database storage with NodeInspection table
- [ ] Dashboard tab with node selector
- [ ] Input/output visualization
- [ ] Execution statistics display
- [ ] Timeline view
- [ ] Export functionality
- [ ] 100% test coverage for new code

### Analysis Result Viewer
- [ ] Extended data models with fit curves
- [ ] Peak analysis service updated
- [ ] Initial viewer layout created
- [ ] Architecture documented
- [ ] Foundation for Week 3 implementation

### Documentation
- [ ] Update README with Inspector feature
- [ ] Create Inspector user guide
- [ ] Update architecture docs
- [ ] Code examples in docstrings

### Testing
- [ ] All existing tests still pass (233/233)
- [ ] New tests for inspector (target: 20+ tests)
- [ ] Integration tests for dashboard
- [ ] Performance tests (inspection overhead <5%)

---

## 🔧 Development Setup

### Before Starting Each Day

1. **Start in fresh environment**:
   ```bash
   cd /nsls2/users/dolds/dev/RoboMage
   git pull origin main  # If working across sessions
   pixi shell
   ```

2. **Verify tests pass**:
   ```bash
   pixi run test
   # Should see: 233 passed, ~10 warnings
   ```

3. **Start required services** (for dashboard testing):
   ```bash
   pixi run start-all
   # Or individually:
   pixi run python services/peak_analysis/main.py --port 8001 &
   pixi run python services/workflow_engine/main.py --port 8002 &
   python -m robomage.dashboard &
   ```

### After Each Day

1. **Run quality checks**:
   ```bash
   pixi run check  # Runs format, lint, typecheck, test
   ```

2. **Verify no regressions**:
   ```bash
   pixi run test
   # Should see: 233+ passed (more tests added)
   ```

3. **Update documentation**:
   - Mark tasks complete in this file
   - Update relevant docs with changes
   - Add examples to code

---

## 🎯 Success Criteria

### Quantitative
- [ ] All 233+ existing tests pass
- [ ] At least 20 new tests added for inspector
- [ ] <5% performance overhead with inspection enabled
- [ ] Zero performance impact when disabled
- [ ] All code passes ruff lint/format
- [ ] All code passes mypy typecheck (core library)

### Qualitative
- [ ] Inspector tab is intuitive and easy to use
- [ ] Data visualizations are clear and informative
- [ ] UI is responsive and professional
- [ ] Code is well-documented with examples
- [ ] Architecture is extensible for future tools

---

## 📚 Reference Documents

### Essential Reading Before Starting
1. **`docs/inspection-tools-design.md`** - Complete architecture for all 5 tools
2. **`docs/WEEK-1-COMPLETION.md`** - What was accomplished in Week 1
3. **`.github/copilot-instructions.md`** - Project architecture and patterns

### Code References
1. **`src/robomage/orchestrator.py`** - Workflow execution engine
2. **`src/robomage/persistence/models.py`** - Database schema
3. **`src/robomage/dashboard/layouts/workflow_layout.py`** - Example dashboard tab
4. **`src/robomage/dashboard/callbacks/workflow.py`** - Example callbacks

### Testing References
1. **`tests/test_workflow_orchestrator.py`** - Orchestrator test patterns
2. **`tests/test_analysis_persistence.py`** - Database persistence tests
3. **`tests/test_dashboard_workflow.py`** - Dashboard UI tests

---

## 🚨 Common Pitfalls to Avoid

### Performance
- ⚠️ **Don't store full data arrays** - Use summaries/samples for inspection
- ⚠️ **Don't enable inspection by default** - Should be opt-in
- ⚠️ **Don't block execution** - Inspection should be async/non-blocking

### Database
- ⚠️ **Don't forget indexes** - Add indexes on frequently queried columns
- ⚠️ **Don't forget cascade delete** - Inspection data should delete with session
- ⚠️ **Don't store binary data** - Use JSON for portability

### UI/UX
- ⚠️ **Don't overwhelm users** - Show summaries first, details on demand
- ⚠️ **Don't forget loading states** - Show spinners for async operations
- ⚠️ **Don't skip error handling** - Gracefully handle missing data

### Testing
- ⚠️ **Don't skip performance tests** - Must verify <5% overhead
- ⚠️ **Don't forget edge cases** - Test with empty data, large data, errors
- ⚠️ **Don't forget cleanup** - Clean up test databases, temp files

---

## 🎓 Learning Resources

### Dash Components Used
- **dbc.Tab** - Tab containers (already used extensively)
- **dcc.Graph** - Plotly charts (already used for plots)
- **dcc.Dropdown** - Selection widgets (already used)
- **html.Pre** - Formatted JSON display (for raw data view)

### Plotly Charts Needed
- **go.Scatter** - Line plots for diffraction data
- **go.Bar** - Bar charts for execution times
- **go.Figure** - Timeline visualization
- **make_subplots** - Multiple plots side-by-side

### SQLAlchemy Patterns
- **JSON column type** - For flexible data storage
- **Relationship cascade** - Auto-delete child records
- **Indexes** - Speed up queries
- **Bulk operations** - Insert multiple records efficiently

---

## 📞 Getting Help

### If Stuck on Architecture
→ Re-read `docs/inspection-tools-design.md` (700+ lines of detailed design)

### If Stuck on Code Patterns
→ Look at existing similar code:
- Orchestrator patterns: `src/robomage/orchestrator.py`
- Database patterns: `src/robomage/persistence/models.py`
- Dashboard patterns: `src/robomage/dashboard/layouts/workflow_layout.py`

### If Stuck on Testing
→ Look at existing test patterns:
- Unit tests: `tests/test_workflow_orchestrator.py`
- Database tests: `tests/test_analysis_persistence.py`
- Dashboard tests: `tests/test_dashboard_workflow.py`

### If Tests Fail
→ Check `docs/TROUBLESHOOTING.md` (730 lines of solutions)

---

## 🎯 Starting the Next Chat Session

### What to Say
```
Hi! I'm ready to implement Week 2 of the RoboMage inspection tools.

Context:
- All Week 1 quick wins complete (233/233 tests passing)
- Starting Day 1: Node I/O Inspector data capture layer
- Full plan in docs/NEXT-STEPS-WEEK-2.md
- Architecture in docs/inspection-tools-design.md

Let's begin with Task 1: Extending WorkflowOrchestrator with inspection hooks.
```

### What to Attach
1. This file: `docs/NEXT-STEPS-WEEK-2.md`
2. Architecture: `docs/inspection-tools-design.md`
3. Current orchestrator: `src/robomage/orchestrator.py`

### What to Expect
The assistant will help you:
1. Create the inspection models
2. Add hooks to the orchestrator
3. Write comprehensive tests
4. Verify no performance impact
5. Move to Day 2 tasks

---

## ✅ Daily Progress Tracking

### Day 1: Data Capture
- [ ] Extended WorkflowOrchestrator
- [ ] Created inspection models
- [ ] Added serialization logic
- [ ] Wrote unit tests
- [ ] Verified performance

### Day 2: Database Storage
- [ ] Created NodeInspection table
- [ ] Extended SessionManager
- [ ] Updated workflow service
- [ ] Wrote persistence tests
- [ ] Verified migrations

### Day 3: Dashboard UI (Part 1)
- [ ] Created inspector layout
- [ ] Created inspector component
- [ ] Added to main dashboard
- [ ] Wrote basic callbacks
- [ ] Tested UI functionality

### Day 4: Dashboard UI (Part 2)
- [ ] Added visualizations
- [ ] Added timeline view
- [ ] Added export features
- [ ] Polished UI/UX
- [ ] All tests passing

### Day 5: Analysis Viewer Foundation
- [ ] Extended data models
- [ ] Updated peak service
- [ ] Designed viewer architecture
- [ ] Created initial layout
- [ ] Documented changes

---

## 🏆 Week 2 Completion Criteria

Week 2 is complete when:
- ✅ Node I/O Inspector fully functional
- ✅ Dashboard has working Inspector tab
- ✅ All data captures and persists correctly
- ✅ Visualizations display properly
- ✅ Export functions work
- ✅ Analysis viewer foundation ready for Week 3
- ✅ All tests pass (233+ total)
- ✅ Documentation updated
- ✅ No performance regressions

**When these are met, you're ready for Week 3: Complete Analysis Result Viewer + Workflow Debugger!**

---

**Created**: December 1, 2025  
**Status**: Ready to Begin  
**Next Update**: End of Day 1 (mark tasks complete)  
**Questions?** Check `docs/inspection-tools-design.md` or `docs/TROUBLESHOOTING.md`

---

**Good luck with Week 2! 🚀**
