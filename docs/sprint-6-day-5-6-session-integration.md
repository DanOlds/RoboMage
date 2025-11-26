# Sprint 6 Day 5-6: Persistence + Session Integration Plan

**Date**: November 26, 2025  
**Status**: Planning  
**Prerequisites**: Days 1-4 Complete ✅

---

## 🎯 Objectives

Enable workflows to seamlessly integrate with the RoboMage session persistence system, allowing:
1. **Save workflow results to sessions** for immediate visualization
2. **Store workflow definitions** in SQLite database
3. **Link workflows to sessions** for reproducibility
4. **Load workflows from saved sessions**

---

## 📋 Deliverables

### 1. Database Schema Extensions
**File**: `src/robomage/persistence/models.py`

```python
class Workflow(Base):
    """Workflow definition storage."""
    __tablename__ = "workflows"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    definition = Column(JSON, nullable=False)  # WorkflowDefinition as JSON
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    
    # Optional link to session
    session_id = Column(String, ForeignKey("sessions.id"), nullable=True)
    session = relationship("Session", back_populates="workflows")

# Update Session model
class Session(Base):
    # ... existing fields ...
    workflows = relationship("Workflow", back_populates="session", cascade="all, delete-orphan")
```

**Migration**:
- Add alembic migration or handle with `Base.metadata.create_all()`
- Existing sessions unaffected (backward compatible)

---

### 2. New Node Handler: `save_to_session`
**File**: `src/robomage/workflow/nodes/output_nodes.py`

```python
async def save_to_session_handler(
    config: dict[str, Any],
    inputs: dict[str, Any],
    context: Any
) -> dict:
    """
    Save workflow results into a session for dashboard visualization.
    
    This enables seamless workflow → visualization integration by extracting
    DiffractionData objects from workflow execution and adding them to the
    specified session.
    
    Config Parameters:
        - session_id: str
            Target session ID. Use "current" for active dashboard session,
            or provide specific session ID. If session doesn't exist, it will
            be created with this ID as the name.
        
        - include_files: bool (default: True)
            Whether to save DiffractionData objects to session
        
        - include_results: bool (default: True)
            Whether to save analysis results (peaks, statistics) as metadata
        
        - overwrite_duplicates: bool (default: False)
            If True, replaces existing files with same name
    
    Inputs:
        - files: List[DiffractionData] (optional)
            Diffraction data to save to session
        
        - results: List[dict] (optional)
            Analysis results (peak lists, statistics, etc.)
    
    Outputs:
        Dictionary with operation summary:
        {
            "session_id": str,
            "files_saved": int,
            "results_saved": int,
            "status": "success" | "partial" | "error",
            "errors": List[str]
        }
    
    Example Workflow:
        ```json
        {
          "nodes": [
            {"id": "load_1", "type": "load_files", "config": {"directory": "data/"}},
            {"id": "analyze_1", "type": "peak_analysis", "config": {...}},
            {"id": "save_1", "type": "save_to_session", "config": {
              "session_id": "my_analysis_session",
              "include_files": true,
              "include_results": true
            }}
          ],
          "edges": [
            {"source": "load_1", "target": "analyze_1"},
            {"source": "analyze_1", "target": "save_1"}
          ]
        }
        ```
    
    Raises:
        ValueError: If session_id is invalid or session creation fails
        RuntimeError: If persistence layer is unavailable
    """
    from robomage.persistence.api import SessionManager
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Extract config
    session_id = config.get("session_id", "current")
    include_files = config.get("include_files", True)
    include_results = config.get("include_results", True)
    overwrite = config.get("overwrite_duplicates", False)
    
    logger.info(f"Saving workflow results to session: {session_id}")
    
    # Initialize session manager
    try:
        manager = SessionManager()
    except Exception as e:
        raise RuntimeError(f"Failed to initialize SessionManager: {e}")
    
    # Handle "current" session ID (from dashboard context)
    if session_id == "current":
        # Get from context if provided, otherwise create new
        session_id = context.metadata.get("active_session_id")
        if not session_id:
            # Create new session with timestamp
            from datetime import datetime
            session_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            logger.info(f"No active session, creating new: {session_id}")
    
    # Ensure session exists
    try:
        session = manager.get_session(session_id)
    except Exception:
        # Create session if it doesn't exist
        logger.info(f"Creating new session: {session_id}")
        manager.create_session(name=session_id, description="Created by workflow execution")
        session = manager.get_session(session_id)
    
    files_saved = 0
    results_saved = 0
    errors = []
    
    # Save DiffractionData files
    if include_files:
        files = inputs.get("files", inputs.get("input", []))
        for i, data in enumerate(files):
            try:
                # Generate filename if not present
                filename = getattr(data, "filename", None)
                if not filename:
                    filename = f"workflow_output_{i}.chi"
                
                # Get wavelength
                wavelength = getattr(data, "wavelength", None)
                
                # Add to session
                manager.add_file_to_session(
                    session_id=session_id,
                    diffraction_data=data,
                    filename=filename,
                    wavelength=wavelength
                )
                files_saved += 1
                logger.debug(f"Saved file {filename} to session {session_id}")
                
            except Exception as e:
                error_msg = f"Failed to save file {i}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
    
    # Save analysis results as session metadata
    if include_results:
        results = inputs.get("results", [])
        if results:
            try:
                # Store as JSON in session notes/metadata
                # (This might require extending Session model with metadata field)
                # For now, we'll serialize and store in description
                import json
                results_summary = {
                    "workflow_results": {
                        "num_files": len(results),
                        "timestamp": datetime.now().isoformat(),
                        "results": [
                            {
                                "filename": r.get("filename", "unknown"),
                                "num_peaks": r.get("metadata", {}).get("num_peaks_detected", 0)
                            }
                            for r in results
                        ]
                    }
                }
                
                # Update session with results summary
                # (Implementation depends on whether we add metadata field to Session)
                results_saved = len(results)
                logger.info(f"Saved {results_saved} analysis results to session")
                
            except Exception as e:
                error_msg = f"Failed to save results metadata: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
    
    # Determine status
    if errors and (files_saved == 0 and results_saved == 0):
        status = "error"
    elif errors:
        status = "partial"
    else:
        status = "success"
    
    return {
        "session_id": session_id,
        "files_saved": files_saved,
        "results_saved": results_saved,
        "status": status,
        "errors": errors
    }
```

**Register Handler**:
```python
# services/workflow_engine/main.py
async def register_node_handlers():
    # ... existing handlers ...
    orchestrator.register_node_handler("save_to_session", output_nodes.save_to_session_handler)
```

---

### 3. Dashboard UI: "Save to Session" Button
**File**: `src/robomage/dashboard/callbacks/workflow.py`

Add callback for saving execution results to current session:

```python
@callback(
    Output("save-to-session-alert", "children"),
    Output("save-to-session-alert", "is_open"),
    Input("save-results-to-session-btn", "n_clicks"),
    State("execution-results-store", "data"),
    State("active-session-store", "data"),
    prevent_initial_call=True
)
def save_workflow_results_to_session(n_clicks, execution_results, active_session):
    """
    Extract workflow execution results and save to active session.
    
    This allows users to run a workflow and immediately visualize
    results in the Visualization tab without manual export/import.
    """
    if not execution_results:
        return "No execution results to save", True
    
    if not active_session or not active_session.get("session_id"):
        return "No active session. Please load or create a session first.", True
    
    session_id = active_session["session_id"]
    
    from robomage.persistence.api import SessionManager
    manager = SessionManager()
    
    files_saved = 0
    errors = []
    
    # Extract DiffractionData from execution results
    for node_result in execution_results.get("node_results", []):
        node_id = node_result.get("node_id")
        output = node_result.get("output")
        
        # Skip failed nodes
        if node_result.get("status") != "completed":
            continue
        
        # Handle different output types
        if isinstance(output, list):
            for i, item in enumerate(output):
                # Check if this looks like DiffractionData
                if isinstance(item, dict) and "q_values" in item:
                    try:
                        # Reconstruct DiffractionData from dict
                        from robomage.data.models import DiffractionData
                        data = DiffractionData(**item)
                        
                        filename = item.get("filename", f"{node_id}_output_{i}.chi")
                        wavelength = item.get("wavelength")
                        
                        manager.add_file_to_session(
                            session_id=session_id,
                            diffraction_data=data,
                            filename=filename,
                            wavelength=wavelength
                        )
                        files_saved += 1
                        
                    except Exception as e:
                        errors.append(f"Failed to save {node_id} output {i}: {str(e)}")
    
    # Build alert message
    if files_saved > 0:
        message = (
            f"✅ Successfully saved {files_saved} files to session '{session_id}'. "
            f"Switch to the Visualization tab to view results."
        )
        if errors:
            message += f" Note: {len(errors)} items could not be saved."
        color = "success"
    else:
        message = "⚠️ No diffraction data found in workflow results to save."
        if errors:
            message += f" Errors: {'; '.join(errors)}"
        color = "warning"
    
    return dbc.Alert(message, color=color), True
```

**Update Layout** (`workflow_layout.py`):
```python
# Add button to execution results area
dbc.Button([
    html.I(className="fas fa-save me-2"),
    "Save Results to Current Session"
], id="save-results-to-session-btn", color="success", className="mt-2"),

# Add alert placeholder
dbc.Alert(id="save-to-session-alert", is_open=False, duration=6000),
```

---

### 4. Workflow Persistence in SessionManager
**File**: `src/robomage/persistence/api.py`

Extend SessionManager with workflow methods:

```python
class SessionManager:
    # ... existing methods ...
    
    def save_workflow_to_session(
        self,
        session_id: str,
        workflow_definition: dict,
        workflow_name: str,
        workflow_description: str = ""
    ) -> str:
        """
        Save a workflow definition and link it to a session.
        
        Args:
            session_id: Target session ID
            workflow_definition: WorkflowDefinition as dict
            workflow_name: Unique name for workflow
            workflow_description: Optional description
        
        Returns:
            Workflow ID
        """
        from datetime import datetime
        import uuid
        
        workflow_id = str(uuid.uuid4())
        
        with self._get_session() as db_session:
            workflow = Workflow(
                id=workflow_id,
                name=workflow_name,
                description=workflow_description,
                definition=workflow_definition,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                session_id=session_id
            )
            db_session.add(workflow)
            db_session.commit()
        
        return workflow_id
    
    def get_workflows_for_session(self, session_id: str) -> list[dict]:
        """Get all workflows linked to a session."""
        with self._get_session() as db_session:
            session = db_session.query(Session).filter_by(id=session_id).first()
            if not session:
                raise ValueError(f"Session {session_id} not found")
            
            return [
                {
                    "id": wf.id,
                    "name": wf.name,
                    "description": wf.description,
                    "definition": wf.definition,
                    "created_at": wf.created_at.isoformat(),
                    "updated_at": wf.updated_at.isoformat()
                }
                for wf in session.workflows
            ]
    
    def load_workflow(self, workflow_id: str) -> dict:
        """Load a workflow definition by ID."""
        with self._get_session() as db_session:
            workflow = db_session.query(Workflow).filter_by(id=workflow_id).first()
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            return {
                "id": workflow.id,
                "name": workflow.name,
                "description": workflow.description,
                "definition": workflow.definition,
                "session_id": workflow.session_id,
                "created_at": workflow.created_at.isoformat(),
                "updated_at": workflow.updated_at.isoformat()
            }
```

---

### 5. Dashboard Workflow Persistence
**File**: `src/robomage/dashboard/callbacks/workflow.py`

Add callbacks for saving/loading workflows with sessions:

```python
@callback(
    Output("save-workflow-modal", "is_open"),
    Output("save-workflow-status", "children"),
    Input("save-workflow-btn", "n_clicks"),
    Input("confirm-save-workflow-btn", "n_clicks"),
    State("workflow-json-editor", "value"),
    State("workflow-name-input", "value"),
    State("active-session-store", "data"),
    State("save-workflow-modal", "is_open"),
    prevent_initial_call=True
)
def handle_workflow_save(save_clicks, confirm_clicks, workflow_json, workflow_name, active_session, is_open):
    """Save current workflow to database and link to active session."""
    from dash.callback_context import ctx
    
    if ctx.triggered_id == "save-workflow-btn":
        # Open modal
        return True, dash.no_update
    
    elif ctx.triggered_id == "confirm-save-workflow-btn":
        # Save workflow
        if not workflow_name:
            return True, dbc.Alert("Please enter a workflow name", color="warning")
        
        try:
            import json
            workflow_def = json.loads(workflow_json)
            
            from robomage.persistence.api import SessionManager
            manager = SessionManager()
            
            session_id = active_session.get("session_id") if active_session else None
            
            workflow_id = manager.save_workflow_to_session(
                session_id=session_id,
                workflow_definition=workflow_def,
                workflow_name=workflow_name
            )
            
            return False, dbc.Alert(
                f"✅ Workflow '{workflow_name}' saved successfully!",
                color="success"
            )
            
        except Exception as e:
            return True, dbc.Alert(f"Error saving workflow: {str(e)}", color="danger")
    
    return is_open, dash.no_update
```

---

## 📊 Testing Plan

### Unit Tests
**File**: `tests/persistence/test_workflow_persistence.py`

```python
def test_save_workflow_to_session(session_manager, temp_db):
    """Test saving workflow definition to session."""
    session_id = session_manager.create_session("Test Session")
    
    workflow_def = {
        "nodes": [{"id": "test", "type": "load_files"}],
        "edges": []
    }
    
    workflow_id = session_manager.save_workflow_to_session(
        session_id=session_id,
        workflow_definition=workflow_def,
        workflow_name="Test Workflow"
    )
    
    assert workflow_id is not None
    
    # Verify retrieval
    loaded = session_manager.load_workflow(workflow_id)
    assert loaded["definition"] == workflow_def
    assert loaded["session_id"] == session_id

def test_save_to_session_node_handler():
    """Test save_to_session node handler."""
    # Create mock inputs with DiffractionData
    # Execute handler
    # Verify files added to session
    pass
```

### Integration Tests
**File**: `tests/test_workflow_session_integration.py`

```python
async def test_workflow_to_visualization_flow():
    """
    End-to-end test: Execute workflow → Save to session → Verify in visualization.
    """
    # 1. Execute workflow with save_to_session node
    # 2. Verify session contains files
    # 3. Load session in dashboard
    # 4. Verify files appear in visualization tab
    pass
```

---

## 🎯 Success Criteria

- ✅ Workflows can be saved to SQLite database
- ✅ Workflows linked to sessions
- ✅ `save_to_session` node handler working
- ✅ Dashboard button saves execution results to active session
- ✅ Results immediately visible in Visualization tab
- ✅ All tests passing (persistence + integration)
- ✅ Documentation updated

---

## 📚 Documentation Updates

Update these docs:
- `README.md`: Add workflow → session integration example
- `docs/dashboard-persistence-guide.md`: Add workflow persistence section
- `docs/sprint-6-workflow-orchestrator-mvp.md`: Mark Day 5-6 complete

---

## 🚀 Implementation Order

1. **Database schema** (models.py) - 30 min
2. **save_to_session handler** (output_nodes.py) - 1 hour
3. **SessionManager methods** (api.py) - 1 hour
4. **Dashboard button callback** (workflow.py) - 45 min
5. **Testing** (unit + integration) - 2 hours
6. **Documentation** - 30 min

**Total Estimated Time**: ~6 hours

---

## 🔗 Dependencies

- Sprint 5 persistence layer (complete ✅)
- Sprint 6 Days 1-4 (complete ✅)
- No new external dependencies required

---

**Ready to implement on Day 5-6 of Sprint 6!** 🚀
