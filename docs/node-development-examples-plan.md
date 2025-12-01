# Node Development Examples - Implementation Plan

**Date**: December 1, 2025  
**Status**: READY TO START  
**Estimated Time**: 3-4 hours  
**Goal**: Create comprehensive node development guide + working examples

## Context

After completing Week 2 Day 3 (Node I/O Inspector), we need to establish patterns for creating custom workflow nodes. This will:
- Enable easy expansion of RoboMage capabilities
- Provide templates for contributors
- Demonstrate Inspector functionality with diverse node types
- Build foundation for remaining inspection tools

## Current State

### What We Have ✅
- **Working Nodes**: LoadFilesNode, NormalizeNode, PeakAnalysisNode, ExportCSVNode
- **Base Infrastructure**: BaseNode interface, workflow orchestrator, node registration
- **Inspection System**: Complete I/O inspector with database persistence
- **Testing Framework**: Comprehensive test coverage for existing nodes

### What We Need 📋
- **Documentation**: Node development guide explaining interfaces and patterns
- **Examples**: 2-3 working example nodes with different complexity levels
- **Templates**: Boilerplate code for quick node creation
- **Integration Guide**: How to register and use custom nodes

## Implementation Plan

### Phase 1: Documentation (1-1.5 hours)

#### Deliverable 1.1: Node Development Guide
**File**: `docs/node-development-guide.md`

**Contents**:
1. **Introduction**
   - What are workflow nodes?
   - When to create a new node vs. modify existing
   - Node lifecycle overview

2. **BaseNode Interface**
   - Required methods: `execute()`, `validate_config()`
   - Optional methods: `get_output_schema()`, `cleanup()`
   - Configuration patterns with Pydantic models

3. **Design Patterns**
   - Input validation strategies
   - Output formatting conventions
   - Error handling best practices
   - Progress reporting for long-running nodes

4. **Integration**
   - Node registration system
   - How nodes appear in workflow builder
   - Inspection integration (automatic)

5. **Testing Guidelines**
   - Unit test patterns
   - Integration test examples
   - Mock data strategies

6. **Common Pitfalls**
   - NumPy serialization (learned from Inspector work)
   - File path handling
   - Session management
   - State management (nodes should be stateless)

#### Deliverable 1.2: Quick Reference
**File**: `docs/node-quick-reference.md`

**Contents**:
- Node template with TODO comments
- Common imports checklist
- Configuration schema examples
- Registration code snippet

### Phase 2: Example Nodes (1.5-2 hours)

#### Example 1: Template Node (Simple)
**File**: `examples/custom_nodes/template_node.py`

**Purpose**: Minimal working example with extensive comments

**Features**:
- Accepts single input parameter
- Performs simple transformation
- Returns structured output
- Fully documented with inline comments

**Use Case**: "Hello World" for node development

#### Example 2: Data Processing Node (Medium Complexity)
**File**: `examples/custom_nodes/background_subtraction_node.py`

**Purpose**: Show working with DiffractionData objects

**Features**:
- Accepts list of DiffractionData files
- Performs background subtraction (linear fit or constant)
- Preserves metadata and wavelength
- Validates Q-space alignment
- Returns modified DiffractionData list

**Use Case**: Real-world data processing example

#### Example 3: Analysis Node (Advanced)
**File**: `examples/custom_nodes/peak_width_analysis_node.py`

**Purpose**: Show integration with scientific libraries and complex analysis

**Features**:
- Uses scipy for peak fitting
- Calculates FWHM (Full Width Half Maximum)
- Generates statistical summaries
- Produces both numeric and plot outputs
- Demonstrates error handling for edge cases

**Use Case**: Advanced analysis with external dependencies

### Phase 3: Integration Examples (0.5-1 hour)

#### Deliverable 3.1: Node Registration Guide
**File**: `examples/custom_nodes/README.md`

**Contents**:
- How to add nodes to workflow engine
- How nodes appear in visual workflow builder
- How to test nodes with Inspector tab
- End-to-end workflow example using custom nodes

#### Deliverable 3.2: Example Workflow
**File**: `examples/custom_nodes/example_workflow.json`

**Purpose**: Demonstrate custom nodes in action

**Workflow**:
1. LoadFilesNode → Load diffraction data
2. BackgroundSubtractionNode → Clean data
3. PeakAnalysisNode → Find peaks
4. PeakWidthAnalysisNode → Analyze peak widths
5. ExportCSVNode → Export results

**Shows**: Complete pipeline using mix of built-in and custom nodes

### Phase 4: Testing (0.5 hours)

#### Deliverable 4.1: Example Tests
**File**: `examples/custom_nodes/test_custom_nodes.py`

**Contents**:
- Unit tests for each example node
- Integration test for example workflow
- Demonstrates testing patterns from guide

## File Structure

```
docs/
├── node-development-guide.md          # Comprehensive guide (NEW)
└── node-quick-reference.md            # Quick template (NEW)

examples/
└── custom_nodes/                       # New directory
    ├── README.md                       # Integration guide
    ├── __init__.py                     # Make it a package
    ├── template_node.py                # Example 1: Simple
    ├── background_subtraction_node.py  # Example 2: Medium
    ├── peak_width_analysis_node.py     # Example 3: Advanced
    ├── example_workflow.json           # Demo workflow
    └── test_custom_nodes.py            # Tests for examples

src/robomage/workflow/nodes/
├── __init__.py                         # Update to document registration
└── (existing nodes)                    # Reference implementations
```

## Success Criteria

### Documentation ✅
- [ ] Comprehensive guide covers all node development aspects
- [ ] Quick reference provides copy-paste template
- [ ] Common pitfalls documented with solutions

### Examples ✅
- [ ] Template node runs successfully
- [ ] Background subtraction processes real data
- [ ] Peak width analysis produces valid results
- [ ] All examples have inline documentation

### Integration ✅
- [ ] Example workflow executes end-to-end
- [ ] Custom nodes appear in workflow builder
- [ ] Inspector shows correct I/O data for custom nodes
- [ ] Tests pass for all examples

### User Experience ✅
- [ ] Developer can create new node in < 30 minutes using guide
- [ ] Examples cover common use cases
- [ ] Clear path from template → production node

## Technical Considerations

### Node Interface Requirements

Based on existing nodes, new nodes must:

```python
from robomage.workflow.base_node import BaseNode
from pydantic import BaseModel, Field

class MyNodeConfig(BaseModel):
    """Configuration schema with validation."""
    param1: str = Field(..., description="Required parameter")
    param2: int = Field(default=100, description="Optional with default")

class MyNode(BaseNode):
    """Node description for UI."""
    
    def execute(self, **inputs):
        """Execute node logic.
        
        Args:
            **inputs: Validated inputs from previous nodes
            
        Returns:
            dict: Outputs available to downstream nodes
        """
        # Implementation
        return {"output_key": result}
    
    @classmethod
    def validate_config(cls, config: dict) -> MyNodeConfig:
        """Validate configuration using Pydantic."""
        return MyNodeConfig(**config)
```

### Serialization Patterns

From Inspector work, we know nodes must handle:
- **NumPy arrays**: Convert to lists for JSON
- **DiffractionData**: Use model serialization
- **File paths**: Use absolute paths, validate existence
- **Large outputs**: Consider truncation for inspection

### Registration Pattern

Nodes register via:
```python
# In src/robomage/workflow/nodes/__init__.py
from .my_node import MyNode

NODE_REGISTRY = {
    "load_files": LoadFilesNode,
    "normalize": NormalizeNode,
    "my_node": MyNode,  # Add here
}
```

## Example Node Specifications

### Background Subtraction Node

**Inputs**:
- `files`: List[DiffractionData]
- `method`: "linear" | "constant" | "polynomial"
- `q_range`: Optional[tuple[float, float]] - Fit range

**Outputs**:
- `files`: List[DiffractionData] - Background-subtracted data
- `backgrounds`: List[numpy.ndarray] - Extracted backgrounds
- `fit_quality`: List[float] - R² values

**Algorithm**:
1. For each file, fit background in specified Q range
2. Subtract fitted background from intensities
3. Preserve all metadata (wavelength, filename, etc.)
4. Return modified DiffractionData objects

### Peak Width Analysis Node

**Inputs**:
- `peak_analysis_results`: dict - From PeakAnalysisNode
- `fit_profile`: "gaussian" | "lorentzian" | "voigt"

**Outputs**:
- `peak_widths`: List[dict] - FWHM for each peak
- `statistics`: dict - Mean, std, min, max widths
- `quality_flags`: List[str] - "narrow" | "medium" | "broad"

**Algorithm**:
1. Extract peak positions from analysis results
2. Fit specified profile to each peak
3. Calculate FWHM from fit parameters
4. Generate statistical summary
5. Classify peaks by width

## Testing Strategy

### Unit Tests
Each node should have tests for:
- Valid input processing
- Invalid input handling
- Edge cases (empty data, single point, etc.)
- Configuration validation
- Output schema compliance

### Integration Tests
Example workflow should test:
- Node chaining (output → input compatibility)
- Inspection data capture
- Error propagation
- Performance (workflow completes in reasonable time)

### Test Data
Use existing test data:
- `examples/pdf_SRM_660b_q.chi` - Standard reference material
- `load_test_data()` - Programmatic access
- Mock data for edge cases

## Next Steps After Completion

With node development examples in place, you can:

1. **Continue Week 2 Day 4**: Analysis Result Viewer
   - Will have diverse analysis outputs to visualize
   - Can demonstrate with custom nodes

2. **Expand Node Library**: Add more domain-specific nodes
   - Rietveld refinement integration
   - Phase identification
   - Texture analysis

3. **Community Contributions**: Enable external developers
   - Clear guide reduces friction
   - Examples provide starting point
   - Registration pattern is simple

4. **Advanced Features**: Build on foundation
   - Conditional node execution
   - Parallel processing
   - Node versioning

## Resources

### Existing Code to Reference
- `src/robomage/workflow/nodes/load_files.py` - Simple I/O node
- `src/robomage/workflow/nodes/normalize.py` - Data processing node
- `src/robomage/workflow/nodes/peak_analysis.py` - Analysis node with service client
- `src/robomage/workflow/base_node.py` - Base interface

### Related Documentation
- `docs/sprint-6-workflow-orchestrator-mvp.md` - Workflow architecture
- `docs/visual-workflow-builder-guide.md` - How nodes appear in UI
- `docs/NUMPY-SERIALIZATION-FIX.md` - Serialization patterns

## Questions to Address in Guide

1. **When to create a node vs. modify existing?**
   - Create: New algorithm, different domain, optional feature
   - Modify: Bug fix, performance improvement, core enhancement

2. **How to handle optional dependencies?**
   - Import inside execute() with try/except
   - Document in node docstring
   - Provide helpful error message if missing

3. **How to make nodes visible in workflow builder?**
   - Register in NODE_REGISTRY
   - Provide clear docstring (used as description)
   - Define configuration schema (generates form)

4. **How to test nodes without full workflow?**
   - Direct instantiation and execute() call
   - Mock inputs with dictionaries
   - Assert output structure

5. **How to handle long-running operations?**
   - No progress reporting in current system (stateless)
   - Consider chunking for very large datasets
   - Document expected runtime in docstring

## Conclusion

This plan provides everything needed to establish robust node development patterns for RoboMage. The combination of documentation and working examples will enable rapid capability expansion while maintaining code quality and consistency.

**Ready to start!** Use this plan to guide implementation in a fresh chat session.

---

**Estimated Completion**: 3-4 hours for full implementation  
**Priority**: HIGH - Foundational for future development  
**Dependencies**: None - Can start immediately  
**Next Session Goal**: Complete all 4 phases with tested, documented examples
