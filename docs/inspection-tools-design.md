# Advanced Inspection & Debugging Tools - Design Document

**Created**: December 1, 2025  
**Status**: Planning Phase  
**Target**: Week 2+ Post-Sprint 8  
**Purpose**: Prepare for expanding RoboMage's capability suite with advanced workflow and analysis inspection tools

---

## Executive Summary

With Sprint 8's visual workflow builder complete and all tests passing, RoboMage is ready for advanced **inspection and debugging capabilities** that will help users understand, troubleshoot, and optimize their powder diffraction analysis workflows.

This document outlines the architecture for **5 key inspection tools** that will enhance scientific productivity and enable deeper insight into data processing pipelines.

---

## Design Principles

1. **Non-Invasive** - Inspection tools should not affect workflow execution
2. **Real-Time** - Show live data as workflows execute
3. **Persistent** - Save inspection results for later review
4. **Extensible** - Easy to add new inspectors for future node types
5. **User-Friendly** - Visual, intuitive interfaces in dashboard
6. **Production-Ready** - No performance impact on normal workflow execution

---

## Tool 1: Node I/O Inspector 🔍

### Purpose
Visualize data flowing **into and out of** each workflow node to understand transformations and debug data flow issues.

### User Stories
- **As a scientist**, I want to see what data enters a `normalize` node so I can verify it's correct before normalization
- **As a developer**, I want to inspect node outputs to debug why a workflow fails
- **As a beamline operator**, I want to validate that peak positions are being passed correctly between nodes

### Architecture

#### Data Capture Layer
```python
# Location: src/robomage/orchestrator.py

class WorkflowOrchestrator:
    def __init__(self, enable_inspection: bool = False):
        self.enable_inspection = enable_inspection
        self.inspection_data = {}  # Store I/O snapshots
    
    async def _execute_node(self, node_id: str, inputs: Any) -> Any:
        """Execute node and optionally capture I/O."""
        
        # Capture input
        if self.enable_inspection:
            self.inspection_data[node_id] = {
                "input": self._serialize_for_inspection(inputs),
                "timestamp_in": datetime.now()
            }
        
        # Execute node
        output = await self.node_handlers[node_type](inputs, config)
        
        # Capture output
        if self.enable_inspection:
            self.inspection_data[node_id].update({
                "output": self._serialize_for_inspection(output),
                "timestamp_out": datetime.now(),
                "duration_ms": (datetime.now() - timestamp_in).total_seconds() * 1000
            })
        
        return output
```

#### Storage Schema
```python
# Location: src/robomage/persistence/models.py

class NodeInspection(Base):
    """Store node I/O inspection data."""
    
    __tablename__ = "node_inspections"
    
    id = Column(Integer, primary_key=True)
    workflow_execution_id = Column(Integer, ForeignKey("workflow_executions.id"))
    node_id = Column(String, nullable=False)
    node_type = Column(String, nullable=False)
    
    # I/O data (JSON)
    input_data = Column(JSON)  # Serialized input snapshot
    output_data = Column(JSON)  # Serialized output snapshot
    
    # Metadata
    input_shape = Column(String)  # e.g., "list[DiffractionData] (3 files)"
    output_shape = Column(String)  # e.g., "list[DiffractionData] (3 files, normalized)"
    duration_ms = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
```

#### Dashboard UI Component
```python
# Location: src/robomage/dashboard/components/node_inspector.py

def create_node_inspector_panel(node_id: str, inspection_data: dict) -> html.Div:
    """Create inspection panel showing node I/O."""
    
    return dbc.Card([
        dbc.CardHeader(f"Node Inspector: {node_id}"),
        dbc.CardBody([
            # Input section
            html.H5("Input Data"),
            dcc.Graph(figure=create_data_summary_plot(inspection_data["input"])),
            html.Pre(json.dumps(inspection_data["input"], indent=2)),
            
            # Output section
            html.H5("Output Data"),
            dcc.Graph(figure=create_data_summary_plot(inspection_data["output"])),
            html.Pre(json.dumps(inspection_data["output"], indent=2)),
            
            # Statistics
            html.H5("Execution Statistics"),
            html.P(f"Duration: {inspection_data['duration_ms']:.2f} ms"),
            html.P(f"Input shape: {inspection_data['input_shape']}"),
            html.P(f"Output shape: {inspection_data['output_shape']}"),
        ])
    ])
```

### Implementation Plan
1. **Week 2 Day 1**: Add inspection hooks to `WorkflowOrchestrator`
2. **Week 2 Day 2**: Implement `NodeInspection` database model
3. **Week 2 Day 3**: Create dashboard inspector panel
4. **Week 2 Day 4**: Add tests and documentation

---

## Tool 2: Analysis Result Viewer 📊

### Purpose
Provide **detailed inspection** of peak analysis results beyond the simple table in the Analysis tab.

### User Stories
- **As a scientist**, I want to see fit quality plots for each peak to assess fitting accuracy
- **As a crystallographer**, I want to compare peak parameters across multiple files
- **As a beamline user**, I want to export detailed analysis reports

### Features

#### Detailed Peak Inspection
- **Individual peak plots** - Show raw data, fitted curve, residuals
- **Fit quality metrics** - R², FWHM, area, background subtraction quality
- **Parameter correlation** - Heat maps showing peak position vs. intensity correlations
- **Time series** - Track peak evolution across multiple measurements

#### Comparison Tools
- **Side-by-side comparison** - Compare 2-3 analysis results simultaneously
- **Difference plots** - Highlight changes between analyses
- **Statistical summaries** - Mean, std dev, outlier detection across files

#### Export Capabilities
- **PDF reports** - Publication-ready analysis summaries
- **CSV exports** - All peak parameters with metadata
- **JSON exports** - Complete analysis results for external tools

### Architecture

#### Enhanced Data Model
```python
# Location: src/robomage/data/models.py (extend existing)

class DetailedPeakAnalysis(BaseModel):
    """Extended peak analysis with fit quality data."""
    
    peak_id: str
    position: float
    intensity: float
    fwhm: float
    
    # New fields for inspection
    fitted_curve: list[float]  # Y values of fitted curve
    residuals: list[float]  # Difference between data and fit
    background_curve: list[float]  # Background curve
    r_squared: float
    chi_squared: float
    fit_quality: Literal["excellent", "good", "fair", "poor"]
    
    # Correlation data
    adjacent_peaks: list[str]  # IDs of nearby peaks
    peak_family: Optional[str]  # For grouped peaks (doublets, etc.)
```

#### Dashboard Component
```python
# Location: src/robomage/dashboard/layouts/analysis_viewer_layout.py

def create_analysis_viewer_tab() -> dbc.Tab:
    """Create detailed analysis viewer tab."""
    
    return dbc.Tab(
        label="Analysis Viewer",
        children=[
            dbc.Row([
                # File/analysis selector
                dbc.Col(create_analysis_selector(), width=3),
                
                # Main viewer area
                dbc.Col([
                    # Peak list with thumbnails
                    create_peak_gallery(),
                    
                    # Detailed peak inspector (appears on click)
                    html.Div(id="peak-detail-panel")
                ], width=9)
            ]),
            
            # Comparison mode
            html.Div(id="comparison-panel", style={"display": "none"})
        ]
    )
```

### Implementation Plan
1. **Week 2 Day 5**: Extend peak analysis response models
2. **Week 3 Day 1**: Implement detailed plotting functions
3. **Week 3 Day 2**: Create analysis viewer tab layout
4. **Week 3 Day 3**: Add comparison and export features

---

## Tool 3: Workflow Debugger 🐛

### Purpose
Enable **step-by-step execution** of workflows with breakpoints and variable inspection.

### User Stories
- **As a developer**, I want to pause workflow execution at a specific node to inspect state
- **As a scientist**, I want to run only part of a workflow for testing
- **As a pipeline designer**, I want to see which nodes are slow

### Features

#### Execution Control
- **Breakpoints** - Pause execution before/after specific nodes
- **Step mode** - Execute one node at a time
- **Continue mode** - Resume normal execution
- **Skip nodes** - Bypass specific nodes for testing

#### State Inspection
- **Variable viewer** - See all data at breakpoint
- **Call stack** - View node execution history
- **Performance profiler** - CPU/memory usage per node

### Architecture

#### Debugger Core
```python
# Location: src/robomage/debugger/workflow_debugger.py

class WorkflowDebugger:
    """Interactive workflow debugger."""
    
    def __init__(self, orchestrator: WorkflowOrchestrator):
        self.orchestrator = orchestrator
        self.breakpoints = set()  # Node IDs to pause at
        self.step_mode = False
        self.current_node = None
        self.paused = False
    
    def set_breakpoint(self, node_id: str):
        """Add breakpoint at node."""
        self.breakpoints.add(node_id)
    
    async def execute_with_debugging(self, workflow: WorkflowDefinition):
        """Execute workflow with debug hooks."""
        for node in workflow.topologically_sorted_nodes:
            # Check breakpoint
            if node.id in self.breakpoints or self.step_mode:
                self.paused = True
                self.current_node = node
                await self._wait_for_continue()
            
            # Execute node
            output = await self.orchestrator.execute_node(node)
            
            # Update debug state
            self.execution_state[node.id] = {
                "output": output,
                "timestamp": datetime.now(),
                "status": "completed"
            }
```

#### Dashboard UI
```python
# Location: src/robomage/dashboard/components/workflow_debugger_panel.py

def create_debugger_controls() -> html.Div:
    """Create debugger control panel."""
    
    return dbc.Card([
        dbc.CardHeader("Workflow Debugger"),
        dbc.CardBody([
            # Execution controls
            dbc.ButtonGroup([
                dbc.Button("▶️ Continue", id="debugger-continue"),
                dbc.Button("⏸️ Pause", id="debugger-pause"),
                dbc.Button("⏭️ Step", id="debugger-step"),
                dbc.Button("⏹️ Stop", id="debugger-stop"),
            ]),
            
            # Breakpoint manager
            html.H5("Breakpoints"),
            dcc.Dropdown(
                id="breakpoint-selector",
                options=[],  # Populated from workflow nodes
                multi=True
            ),
            
            # Current state display
            html.Div(id="debugger-state"),
            
            # Performance profiler
            dcc.Graph(id="performance-profile")
        ])
    ])
```

### Implementation Plan
1. **Week 3 Day 4**: Implement `WorkflowDebugger` core class
2. **Week 3 Day 5**: Add debugging hooks to orchestrator
3. **Week 4 Day 1**: Create debugger UI components
4. **Week 4 Day 2**: Add tests and documentation

---

## Tool 4: Data Profiler 📈

### Purpose
Provide **statistical summaries and quality metrics** for data at any point in the workflow.

### User Stories
- **As a scientist**, I want to see data quality metrics before running expensive analysis
- **As a beamline operator**, I want to detect anomalies in incoming data
- **As a data analyst**, I want statistical summaries for QC reports

### Features

#### Statistical Metrics
- **Basic stats** - Mean, median, std dev, min/max, quartiles
- **Quality indicators** - SNR, outlier detection, data completeness
- **Distribution plots** - Histograms, box plots, violin plots
- **Trend detection** - Linear fits, drift detection

#### Anomaly Detection
- **Outlier identification** - Statistical methods (Z-score, IQR)
- **Pattern matching** - Compare to reference datasets
- **Alert system** - Flag suspicious data automatically

### Architecture

```python
# Location: src/robomage/analysis/data_profiler.py

class DataProfiler:
    """Statistical profiling for diffraction data."""
    
    def profile(self, data: DiffractionData) -> DataProfile:
        """Generate comprehensive data profile."""
        
        return DataProfile(
            # Basic statistics
            num_points=len(data.q_values),
            q_range=(data.q_values.min(), data.q_values.max()),
            intensity_stats=self._compute_stats(data.intensities),
            
            # Quality metrics
            snr=self._compute_snr(data),
            completeness=self._check_completeness(data),
            outlier_count=self._detect_outliers(data),
            
            # Advanced analytics
            noise_level=self._estimate_noise(data),
            background_level=self._estimate_background(data),
            feature_count=self._count_features(data),
        )
```

### Implementation Plan
1. **Week 4 Day 3**: Implement `DataProfiler` class
2. **Week 4 Day 4**: Create profiler dashboard component
3. **Week 4 Day 5**: Add anomaly detection algorithms

---

## Tool 5: Session Comparison Tool 🔀

### Purpose
Enable **side-by-side comparison** of analysis sessions to track changes and improvements.

### User Stories
- **As a scientist**, I want to compare results before/after parameter changes
- **As a researcher**, I want to track analysis evolution over time
- **As a collaborator**, I want to share and compare analysis approaches

### Features

#### Comparison Views
- **File comparison** - Which files changed between sessions
- **Parameter comparison** - Highlight changed analysis parameters
- **Result comparison** - Show differences in peak lists, fits, etc.
- **Visual diff** - Side-by-side plots with difference overlay

#### History Tracking
- **Session timeline** - Chronological view of all sessions
- **Change log** - Automatic tracking of what changed
- **Rollback capability** - Restore previous session state

### Architecture

```python
# Location: src/robomage/persistence/session_comparison.py

class SessionComparator:
    """Compare two analysis sessions."""
    
    def compare(self, session_a_id: int, session_b_id: int) -> SessionComparison:
        """Generate detailed comparison report."""
        
        session_a = self.manager.get_session(session_a_id)
        session_b = self.manager.get_session(session_b_id)
        
        return SessionComparison(
            # File differences
            added_files=self._find_added_files(session_a, session_b),
            removed_files=self._find_removed_files(session_a, session_b),
            modified_files=self._find_modified_files(session_a, session_b),
            
            # Analysis differences
            analysis_changes=self._compare_analyses(session_a, session_b),
            
            # Statistical comparison
            stats_comparison=self._compare_statistics(session_a, session_b),
        )
```

### Implementation Plan
1. **Week 5 Day 1**: Implement `SessionComparator` class
2. **Week 5 Day 2**: Create comparison dashboard tab
3. **Week 5 Day 3**: Add visual diff tools

---

## Integration Architecture

### Dashboard Layout Extension
```
Current Tabs:
1. Data Import
2. Visualization
3. Analysis
4. Workflow Builder

New Tabs:
5. Node Inspector (Tool 1)
6. Analysis Viewer (Tool 2)
7. Workflow Debugger (Tool 3)
8. Data Profiler (Tool 4)
9. Session Compare (Tool 5)
```

### Performance Considerations

#### Inspection Overhead
- **Toggle-able** - Inspection can be disabled for production runs
- **Sampling** - Only capture every Nth execution for high-throughput workflows
- **Lazy loading** - Load inspection data on-demand, not automatically

#### Storage Impact
- **Retention policy** - Auto-delete inspection data older than N days
- **Compression** - Use gzip for large JSON inspection blobs
- **Selective storage** - Only store inspection data for "interesting" nodes

---

## Implementation Timeline

### Week 2: Foundation (5 days)
- **Days 1-2**: Node I/O Inspector (data capture)
- **Days 3-4**: Node I/O Inspector (dashboard UI)
- **Day 5**: Analysis Result Viewer (data model extensions)

### Week 3: Core Tools (5 days)
- **Days 1-3**: Analysis Result Viewer (complete)
- **Days 4-5**: Workflow Debugger (core + UI)

### Week 4: Advanced Features (5 days)
- **Days 1-2**: Workflow Debugger (complete + test)
- **Days 3-5**: Data Profiler

### Week 5: Comparison & Polish (5 days)
- **Days 1-3**: Session Comparison Tool
- **Days 4-5**: Integration testing, documentation, polish

**Total Estimated Time**: 4-5 weeks (20-25 days)

---

## Testing Strategy

### Unit Tests
- Test each inspector component independently
- Mock workflow execution for fast testing
- Validate data serialization/deserialization

### Integration Tests
- Test full workflow execution with inspection enabled
- Verify dashboard UI interactions
- Test database storage and retrieval

### Performance Tests
- Measure inspection overhead (target: <5% slowdown)
- Test with large datasets (10k+ points)
- Verify memory usage stays reasonable

---

## Success Criteria

### Quantitative Metrics
- ✅ All 5 tools implemented and tested
- ✅ <5% performance overhead with inspection enabled
- ✅ 100% test coverage for new components
- ✅ All documentation complete

### Qualitative Metrics
- ✅ Users can diagnose workflow failures faster
- ✅ Scientists gain confidence in analysis results
- ✅ Developers can debug complex workflows efficiently
- ✅ Positive user feedback from beta testing

---

## Future Enhancements (Beyond Week 5)

### AI-Powered Insights
- **Auto-diagnosis** - AI suggests fixes for common workflow failures
- **Pattern recognition** - AI identifies unusual data patterns
- **Parameter optimization** - AI recommends optimal analysis parameters

### Collaborative Features
- **Shared inspections** - Team members can view each other's inspection results
- **Annotation system** - Add notes to inspection data
- **Diff reviews** - Code review-style workflow for analysis changes

### Advanced Visualization
- **3D data visualization** - For multi-dimensional datasets
- **Animation** - Show data flow through workflow as animation
- **Interactive plots** - Drill down into any data point

---

## Dependencies

### Required Before Starting
- ✅ Sprint 8 complete (visual workflow builder)
- ✅ All tests passing (100%)
- ✅ Documentation up to date

### External Dependencies
- None - all tools use existing infrastructure

### New Libraries (if needed)
- `plotly` - Already installed for dashboard
- `scikit-learn` - For advanced anomaly detection (optional)
- `dash-cytoscape` - Already installed for workflow canvas

---

## Risk Assessment

### Low Risk
- ✅ All tools are additive (no breaking changes)
- ✅ Can be developed incrementally
- ✅ Performance impact is controllable (toggle on/off)

### Medium Risk
- ⚠️ Dashboard may become complex with 9 tabs
  - **Mitigation**: Consider tab grouping or secondary navigation
- ⚠️ Storage requirements may grow large
  - **Mitigation**: Retention policy + compression

### High Risk
- None identified

---

## Conclusion

The proposed inspection and debugging tools will **significantly enhance** RoboMage's usability for both scientists and developers. By providing deep insight into workflow execution, data transformations, and analysis results, these tools will:

1. **Reduce debugging time** by 50-75%
2. **Increase user confidence** in analysis results
3. **Enable advanced workflows** that were previously too complex
4. **Improve reproducibility** through detailed provenance tracking

**Recommendation**: Begin implementation in Week 2 (December 8, 2025) after Week 1 cleanup tasks are complete and tested.

---

**Document Status**: ✅ Complete  
**Ready for Review**: Yes  
**Next Step**: Present to team for feedback, then begin Week 2 implementation
