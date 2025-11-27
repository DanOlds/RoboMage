# Workflow → Session Integration Feature

**Added to Sprint 6 Scope**: November 26, 2025  
**Implementation**: Days 5-6

---

## 🎯 Problem Statement

Currently, workflow execution results (detected peaks, filtered data, statistics) are only exported to files (CSV/JSON). Users cannot easily:
- Visualize workflow results in the dashboard
- Compare workflow outputs with other analyses
- Keep workflow results in their analysis sessions

---

## 💡 Solution

Enable seamless integration between workflow execution and session-based visualization:

```
Workflow Execution → Save to Session → Dashboard Visualization
     (port 8002)    →   (SQLite+HDF5)  →   (Interactive plots)
```

---

## 🔧 Implementation Components

### 1. New Node Type: `save_to_session`

Add workflow node that saves results directly to sessions:

```json
{
  "id": "save_1",
  "type": "save_to_session",
  "config": {
    "session_id": "current",
    "include_files": true,
    "include_results": true
  }
}
```

**What it does**:
- Extracts `DiffractionData` objects from workflow outputs
- Adds them to specified session using `SessionManager`
- Makes results immediately available in Visualization tab
- No manual export/import needed!

### 2. Dashboard UI Enhancement

Add **"Save Results to Current Session"** button in Workflow tab:
- Appears after successful workflow execution
- One-click operation
- Shows confirmation with file count
- Auto-refreshes Visualization tab

### 3. Database Schema Extension

```python
# New table: workflows
class Workflow(Base):
    id = Column(String, primary_key=True)
    name = Column(String, unique=True)
    definition = Column(JSON)  # Full workflow definition
    session_id = Column(String, ForeignKey("sessions.id"))  # Link to session
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
```

Links workflows to sessions for:
- Reproducibility (session + workflow = complete analysis record)
- Workflow templates (save successful workflows for reuse)
- Version history

### 4. SessionManager Extensions

```python
# New methods
manager.save_workflow_to_session(session_id, workflow_def, name)
manager.get_workflows_for_session(session_id)
manager.load_workflow(workflow_id)
```

---

## 🎬 User Workflow Example

**Before** (manual export/import):
1. Build workflow in Workflow tab
2. Execute workflow
3. Find exported CSV file
4. Go to Data Import tab
5. Upload CSV
6. Finally visualize

**After** (seamless integration):
1. Build workflow in Workflow tab
2. Add `save_to_session` node OR click "Save to Session" button
3. Results automatically appear in Visualization tab ✅

---

## 📊 Benefits

### For Users
- **Faster iteration**: No manual file handling
- **Better organization**: All analysis in one session
- **Reproducibility**: Workflow + data + results linked
- **Collaboration**: Share sessions with workflows intact

### For Development
- **Leverages existing code**: Uses SessionManager (Sprint 5)
- **Consistent architecture**: Same patterns as peak analysis
- **Minimal new dependencies**: Just SQLAlchemy schema extension
- **Testable**: Clear input/output contracts

---

## 📋 Deliverables (Day 5-6)

- [x] `save_to_session` node handler implementation
- [x] Database schema migration (Workflow model)
- [x] SessionManager workflow methods
- [x] Dashboard "Save to Session" button + callback
- [x] Unit tests for persistence
- [x] Integration tests for full flow
- [x] Documentation updates

---

## 🧪 Testing Strategy

### Unit Tests
```python
test_save_workflow_to_session()  # Database operations
test_save_to_session_handler()    # Node handler logic
test_workflow_persistence()       # SessionManager methods
```

### Integration Tests
```python
test_workflow_execution_to_visualization()
# 1. Execute workflow with save_to_session
# 2. Verify SessionManager has files
# 3. Load session in dashboard
# 4. Confirm files in Visualization tab
```

---

## 📚 Documentation

New/Updated docs:
- `docs/sprint-6-day-5-6-session-integration.md` - Implementation plan
- `docs/sprint-6-workflow-orchestrator-mvp.md` - Updated with integration details
- `README.md` - Add workflow → session example
- `docs/dashboard-persistence-guide.md` - Workflow persistence section

---

## 🚀 Timeline

**Estimated**: 6 hours total
- Database schema: 30 min
- Node handler: 1 hour
- SessionManager: 1 hour
- Dashboard UI: 45 min
- Testing: 2 hours
- Documentation: 30 min

**Schedule**: Sprint 6 Days 5-6

---

## 🎓 Design Decisions

### Why "current" session?
Allows workflows to be session-agnostic. Same workflow can save to different sessions based on context.

### Why both node + button?
- **Node**: Programmatic, part of workflow definition, reusable
- **Button**: Ad-hoc, for exploring results, user-friendly

### Why link workflows to sessions?
Enables complete reproducibility: "Run this workflow on this data" becomes a single operation.

---

## ✅ Success Metrics

When complete:
- ✅ User can execute workflow and see results in Viz tab (0 manual steps)
- ✅ Workflows saved with sessions for later replay
- ✅ <5 second latency from execution → visualization
- ✅ All persistence tests passing
- ✅ Documentation clear enough for new users

---

**Status**: Planned for Sprint 6 Days 5-6  
**Dependencies**: Sprint 5 (complete ✅), Sprint 6 Days 1-4 (complete ✅)  
**Risk**: Low - leverages existing, tested infrastructure
