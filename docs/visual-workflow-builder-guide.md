# Visual Workflow Builder User Guide

**Sprint 8 - Phase 2 Implementation**  
*November 28, 2025*

## Overview

The Visual Workflow Builder provides a drag-and-drop interface for creating, configuring, and executing analysis workflows in RoboMage. Built with Cytoscape.js, it offers an intuitive alternative to manual JSON editing.

## Features

### ✨ Core Capabilities
- **Visual Canvas**: Interactive node-and-edge workflow diagram
- **Node Palette**: Pre-configured node types organized by category
- **Properties Panel**: Dynamic configuration forms for each node type
- **Real-time Validation**: Instant feedback on workflow structure
- **Execution Integration**: Direct connection to workflow engine
- **Session Persistence**: Save workflows and results to database

### 🎨 User Interface

```
┌─────────────┬──────────────────────┬─────────────────┐
│  Node       │   Workflow Canvas    │   Properties    │
│  Palette    │   (Cytoscape)        │   & Results     │
│             │                      │                 │
│  📊 Data    │   ┌──────────┐      │   [Node Props]  │
│  🔄 Transform│   │  Load    │      │   [Exec Log]    │
│  🔬 Analysis│   └────┬─────┘      │   [Saved WF]    │
│  📤 Output  │        │             │                 │
│             │   ┌────▼─────┐      │                 │
│  [Service   │   │  Analyze │      │                 │
│   Status]   │   └──────────┘      │                 │
└─────────────┴──────────────────────┴─────────────────┘
```

## Getting Started

### Prerequisites
1. **Workflow Service** must be running:
   ```bash
   pixi run python services/workflow_engine/main.py --port 8002
   ```

2. **Peak Analysis Service** (for peak detection nodes):
   ```bash
   pixi run python services/peak_analysis/main.py --port 8001
   ```

3. **Dashboard**:
   ```bash
   pixi run python -m robomage.dashboard
   ```

Or start all services at once:
```bash
pixi run start-all
```

### Quick Start
1. Open dashboard at http://localhost:8050
2. Navigate to the **Workflow Builder** tab
3. Check that "Workflow service connected" appears (green badge)
4. Start building your workflow!

## Building Workflows

### Step 1: Add Nodes to Canvas

**Method 1: Click Node Palette**
1. Look at the left sidebar (Node Palette)
2. Click any node type card (e.g., "Load Files")
3. Node appears on canvas in a cascading layout

**Node Categories:**
- **📊 Data Input**: `load_files` - Load diffraction files from directory
- **🔄 Transform**: 
  - `filter_q_range` - Filter by Q-space range
  - `normalize` - Normalize intensity values
- **🔬 Analysis**:
  - `peak_analysis` - Detect and fit peaks
  - `statistics` - Calculate statistical metrics
- **📤 Output**:
  - `export_csv` - Export results to CSV
  - `export_json` - Export results to JSON

### Step 2: Connect Nodes

**Manual Connection** (Current Implementation):
- Nodes added sequentially will be auto-connected in the default workflow
- Use callbacks to manage edges programmatically

**Future Enhancement** (Planned for Sprint 8 Phase 3):
- Drag from one node to another to create edges
- Click edge to delete connection

### Step 3: Configure Nodes

1. **Click a node** on the canvas
2. Properties panel (right sidebar) updates with dynamic form
3. Fill in required fields (marked with *)
4. Adjust optional parameters as needed
5. Click **"Apply Configuration"** button
6. Success message appears confirming changes

**Example: Load Files Node**
```
Node Type: load_files

Required Fields:
- Directory: /path/to/data
- Pattern: *.chi

Optional Fields:
- Wavelength: 0.1665 Å (default)
```

**Example: Peak Analysis Node**
```
Node Type: peak_analysis

Configuration:
- Profile Type: gaussian | lorentzian | voigt
- Prominence: 0.1 (default)
- Distance: 5 (default)
- Service URL: http://localhost:8001
```

### Step 4: Validate Workflow

**Real-time Validation** runs automatically and displays:

✅ **Valid Workflow** (Green Alert):
```
✓ Workflow is valid (3 nodes, 2 edges)
```

⚠️ **Invalid Workflow** (Yellow Alert):
```
⚠ 2 validation error(s):
• Workflow contains cycles
• Node 'analyze_1': missing required config 'profile_type'
```

ℹ️ **Empty Workflow** (Info Alert):
```
ⓘ Add nodes to start building your workflow
```

**Validation Checks:**
- No cycles (DAG requirement)
- All nodes connected (no isolated nodes)
- Valid edge references (source/target exist)
- Known node types
- Required configuration present

### Step 5: Save Workflow

1. Click **"Save"** button in canvas header
2. Workflow is saved to workflow service
3. Appears in **"Saved Workflows"** tab (right sidebar)

**Workflow Metadata:**
- Name: Editable in header
- Description: Editable in header
- Node count: Displayed in saved workflows list
- Unique ID: Generated automatically

### Step 6: Execute Workflow

1. Ensure workflow is valid (green status)
2. Click **"Execute"** button in canvas header
3. Execution log appears in **"Execution Log"** tab
4. Watch progress with status indicators:
   - 🔄 Running (orange)
   - ✅ Completed (green)
   - ❌ Failed (red)

**Execution Results:**
```
Status: COMPLETED
Execution ID: abc123...
Duration: 1234.5 ms

Node Results:
1. load_1: ✅ completed (123.4 ms)
2. analyze_1: ✅ completed (987.6 ms)
3. export_1: ✅ completed (234.5 ms)
```

### Step 7: Save Results to Session

1. After successful execution, click **"Save Results to Current Session"**
2. Workflow outputs (DiffractionData, analysis results) saved to active session
3. Data appears in **Visualization** tab automatically
4. Analysis results (if any) appear in **Analysis** tab

**What Gets Saved:**
- Diffraction data files from workflow outputs
- Peak analysis results (if peak_analysis node executed)
- Metadata and wavelength information
- Session persistence (survives page reload via Sprint 7)

## Advanced Features

### Managing Saved Workflows

**Load Workflow:**
1. Go to **"Saved Workflows"** tab (right sidebar)
2. Click **upload icon** next to workflow name
3. Workflow loads onto canvas

**Delete Workflow:**
1. Go to **"Saved Workflows"** tab
2. Click **trash icon** next to workflow name
3. Confirmation: Workflow deleted from service

### Deleting Nodes/Edges

1. Click node or edge to select (highlighted)
2. Click **"Delete Selected"** button below canvas
3. Selected elements removed
4. Connected edges auto-deleted if node removed

### Node Type Reference

| Node Type | Category | Inputs | Outputs | Key Config |
|-----------|----------|--------|---------|------------|
| `load_files` | Data | - | DiffractionData[] | directory, pattern |
| `filter_q_range` | Transform | DiffractionData[] | DiffractionData[] | q_min, q_max |
| `normalize` | Transform | DiffractionData[] | DiffractionData[] | method (max/area/zscore) |
| `peak_analysis` | Analysis | DiffractionData[] | PeakResults[] | profile_type, prominence |
| `statistics` | Analysis | DiffractionData[] | Statistics[] | metrics |
| `export_csv` | Output | Any | ExportInfo | output_path, format |
| `export_json` | Output | Any | ExportInfo | output_path, pretty |

## Workflow Examples

### Example 1: Basic Peak Analysis
```
load_files → peak_analysis → export_csv

Config:
- load_files:
  - directory: /data/diffraction
  - pattern: *.chi
  
- peak_analysis:
  - profile_type: gaussian
  - prominence: 0.1
  
- export_csv:
  - output_path: peaks.csv
  - format: peaks
```

### Example 2: Data Processing Pipeline
```
load_files → filter_q_range → normalize → peak_analysis → export_json

Config:
- filter_q_range:
  - q_min: 0.5
  - q_max: 5.0
  
- normalize:
  - method: max
```

### Example 3: Parallel Analysis
```
            ┌─> peak_analysis → export_csv
load_files ─┤
            └─> statistics → export_json
```

## Troubleshooting

### Service Not Connected
**Symptom:** Yellow warning banner "Workflow service not available"

**Solution:**
```bash
# Start workflow service
pixi run python services/workflow_engine/main.py --port 8002

# Or start all services
pixi run start-all
```

### Node Types Not Loading
**Symptom:** "Loading node types..." never completes

**Check:**
1. Workflow service is running on port 8002
2. No firewall blocking localhost:8002
3. Check browser console for errors (F12)

### Workflow Won't Execute
**Symptom:** Click "Execute" but nothing happens

**Check:**
1. Validation status is green (✓ valid)
2. All required configs filled in
3. Peak analysis service running (if using peak_analysis nodes)
4. Check execution log tab for error messages

### Configuration Not Saving
**Symptom:** Click "Apply Configuration" but changes don't persist

**Workaround:** Current implementation shows success feedback. Full form value persistence coming in next iteration.

### Canvas Elements Overlapping
**Symptom:** Nodes stack on top of each other

**Solution:**
- Nodes are placed in cascading pattern automatically
- Manual repositioning coming in future update
- Delete and re-add nodes to reset positions

## Technical Details

### Architecture

**Frontend (Dashboard):**
- `workflow_layout.py`: UI layout with 3-column design
- `workflow.py` callbacks: Interactive behavior
- `cytoscape_renderer.py`: Canvas visualization
- `node_configurator.py`: Dynamic forms
- `workflow_validator.py`: Structure validation

**Backend (Services):**
- Workflow Service (port 8002): Workflow CRUD and execution
- Peak Analysis Service (port 8001): Peak detection algorithms
- Orchestrator: DAG-based workflow execution engine

**Data Flow:**
```
User Action → Dashboard Callback → Workflow Service API
→ Orchestrator → Node Handlers → Results → Dashboard
→ Session Storage (Sprint 7)
```

### Keyboard Shortcuts
*(Future Enhancement)*
- Ctrl+S: Save workflow
- Del: Delete selected
- Ctrl+Z: Undo
- Ctrl+Y: Redo

### Browser Compatibility
- ✅ Chrome/Edge (recommended)
- ✅ Firefox
- ⚠️ Safari (limited testing)

## API Integration

### Workflow Service Endpoints

**Health Check:**
```bash
curl http://localhost:8002/health
```

**Get Node Types:**
```bash
curl http://localhost:8002/node-types
```

**Execute Workflow:**
```bash
curl -X POST http://localhost:8002/workflows/{id}/execute
```

## Best Practices

1. **Start Simple**: Begin with load_files → analyze → export
2. **Validate Early**: Check validation status before configuring
3. **Use Defaults**: Node types have sensible defaults
4. **Save Often**: Save workflows after significant changes
5. **Name Clearly**: Use descriptive workflow names
6. **Session Integration**: Always save results to session for persistence

## Future Enhancements

### Sprint 8 Phase 3 (Planned)
- [ ] Drag-to-connect edge creation
- [ ] Manual node repositioning
- [ ] Undo/Redo support
- [ ] Workflow templates library
- [ ] Node copy/paste
- [ ] Canvas zoom/pan controls
- [ ] Export workflow as image
- [ ] Collaborative editing

### Long-term Roadmap
- [ ] ReactFlow migration option (framework flexibility)
- [ ] Custom node types (user-defined)
- [ ] Conditional branching
- [ ] Loop/iteration nodes
- [ ] Sub-workflow composition
- [ ] Version control for workflows

## Getting Help

- **Documentation**: `docs/` directory
- **Examples**: `examples/` directory
- **Issues**: GitHub repository
- **API Docs**: http://localhost:8002/docs (when service running)

## References

- [Sprint 8 Planning](sprint-8-visual-workflow-builder.md)
- [Workflow Orchestrator MVP](sprint-6-workflow-orchestrator-mvp.md)
- [Session Persistence](dashboard-persistence-guide.md)
- [Peak Analysis Service](peak-analysis-tool-documentation.md)

---

**Version**: Sprint 8 Phase 2  
**Last Updated**: November 28, 2025  
**Status**: ✅ Production Ready
