# Sprint 2: Data Pipeline MVP

**Goal**: Build `robomage plot mydata.xy` end-to-end workflow  
**Timeline**: 1 week (9 tasks)  
**Success Criteria**: Can load, visualize, and save powder diffraction data  
**Status**: 📋 Planned (not started)

## 🎯 Overview

Create a minimum viable data import/plotting workflow that establishes the foundation for all future RoboMage functionality. This sprint focuses on powder diffraction data handling, visualization, and CLI interface.

## 📋 Task List

### Task 1: Enable Data Science Dependencies ⏱️ 15 min
**Status**: Not Started  
**Description**: Uncomment numpy, pandas, matplotlib in pyproject.toml dependencies section. Run pixi install to update environment.

**Implementation**:
```toml
# In pyproject.toml, change:
dependencies = [
  "pydantic>=2",
  "numpy",        # ← Uncomment
  "pandas",       # ← Uncomment  
  "matplotlib",   # ← Uncomment
  # "sqlalchemy",  # Keep commented for now
]
```

**Commands**:
```bash
# After editing pyproject.toml
pixi install
```

---

### Task 2: Create Data Models Module ⏱️ 45 min
**Status**: Not Started  
**Description**: Create src/robomage/data/__init__.py and src/robomage/data/models.py with DiffractionData dataclass and supporting types.

**Files to create**:
- `src/robomage/data/__init__.py`
- `src/robomage/data/models.py`

**Key components**:
```python
# src/robomage/data/models.py
from dataclasses import dataclass
from pathlib import Path
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional

@dataclass
class DiffractionData:
    """Core powder diffraction dataset"""
    two_theta: np.ndarray  # 2θ values in degrees
    intensity: np.ndarray  # Intensity counts
    metadata: Dict[str, Any]
    file_path: Path
    timestamp: datetime
    
    # Optional fields for different coordinate systems
    q_space: Optional[np.ndarray] = None  # Q-space values
    d_space: Optional[np.ndarray] = None  # d-spacing values
    
    def __post_init__(self):
        """Validate data consistency"""
        if len(self.two_theta) != len(self.intensity):
            raise ValueError("two_theta and intensity arrays must have same length")
```

---

### Task 3: Implement Basic File Loader ⏱️ 1.5 hours
**Status**: Not Started  
**Description**: Create src/robomage/data/loaders.py with functions to load 2-column ASCII files (.xy, .dat) into DiffractionData objects.

**File to create**: `src/robomage/data/loaders.py`

**Key functions**:
```python
def load_diffraction_file(file_path: Path | str) -> DiffractionData:
    """Load powder diffraction data from common ASCII formats"""
    
def load_xy_file(file_path: Path) -> DiffractionData:
    """Load 2-column .xy file (2θ, intensity)"""
    
def detect_file_format(file_path: Path) -> str:
    """Auto-detect file format from extension and headers"""
```

**Supported formats**:
- `.xy` - Two-column ASCII (2θ, intensity)
- `.dat` - Generic data file
- Auto-detection of headers, comments, delimiters

---

### Task 4: Build Visualization Functions ⏱️ 1.5 hours
**Status**: Not Started  
**Description**: Implement src/robomage/visualization.py with plot_diffraction_data() function using matplotlib for publication-quality plots.

**File to update**: `src/robomage/visualization.py`

**Key functions**:
```python
def plot_diffraction_data(
    data: DiffractionData, 
    output_path: Optional[Path] = None,
    show_plot: bool = True,
    **plot_kwargs
) -> matplotlib.figure.Figure:
    """Create publication-quality powder diffraction plot"""

def plot_multiple_patterns(
    datasets: List[DiffractionData],
    output_path: Optional[Path] = None,
    **plot_kwargs
) -> matplotlib.figure.Figure:
    """Overlay multiple diffraction patterns"""
```

**Features**:
- Professional styling (fonts, colors, DPI)
- Proper axis labels with units
- Metadata integration (title, sample info)
- Export options (PNG, PDF, SVG)
- Customizable styling

---

### Task 5: Create CLI Interface ⏱️ 1 hour
**Status**: Not Started  
**Description**: Implement src/robomage/__main__.py with 'plot' command using argparse to handle 'robomage plot file.xy' workflow.

**File to update**: `src/robomage/__main__.py`

**CLI Design**:
```bash
# Basic usage
robomage plot data.xy

# With options
robomage plot data.xy --output plot.png --title "Sample XRD"

# Batch processing
robomage plot *.xy --output-dir plots/

# Multiple files overlay
robomage plot file1.xy file2.xy --overlay --output comparison.png
```

**Implementation structure**:
```python
def main():
    parser = argparse.ArgumentParser(description="RoboMage powder diffraction tools")
    subparsers = parser.add_subparsers(dest="command")
    
    # Plot command
    plot_parser = subparsers.add_parser("plot", help="Plot diffraction data")
    plot_parser.add_argument("files", nargs="+", help="Input diffraction files")
    plot_parser.add_argument("--output", "-o", help="Output file path")
    plot_parser.add_argument("--output-dir", help="Output directory for batch processing")
    # ... more options
```

---

### Task 6: Add Unit Tests ⏱️ 1.5 hours
**Status**: Not Started  
**Description**: Create tests/test_data_models.py, tests/test_loaders.py, tests/test_visualization.py with basic test cases for core functionality.

**Files to create**:
- `tests/test_data_models.py`
- `tests/test_loaders.py` 
- `tests/test_visualization.py`

**Test coverage**:
- DiffractionData validation and methods
- File loading with various formats
- Error handling (bad files, missing files)
- Plotting functions (output validation)
- CLI argument parsing

---

### Task 7: Create Sample Data ⏱️ 30 min
**Status**: Not Started  
**Description**: Add examples/ directory with sample powder diffraction data files (.xy format) for testing and demonstration.

**Directory to create**: `examples/`

**Files to include**:
- `examples/sample_quartz.xy` - Simple quartz diffraction pattern
- `examples/sample_complex.xy` - More complex multi-phase pattern
- `examples/README.md` - Data format documentation
- `examples/plot_examples.py` - Usage examples

---

### Task 8: Update Documentation ⏱️ 45 min
**Status**: Not Started  
**Description**: Update README.md with usage examples and add docstrings to all new modules and functions.

**Updates needed**:
- Add usage examples to main README.md
- Complete docstrings for all functions
- API documentation in modules
- Installation and quick start updates

**README additions**:
```markdown
## Quick Usage

```bash
# Plot a single diffraction file
pixi run robomage plot examples/sample_quartz.xy

# Batch process multiple files
pixi run robomage plot data/*.xy --output-dir plots/

# Overlay comparison
pixi run robomage plot sample1.xy sample2.xy --overlay
```
```

---

### Task 9: Integration Testing ⏱️ 30 min
**Status**: Not Started  
**Description**: Test full end-to-end workflow: robomage plot sample.xy, verify output plots, run pixi run check to ensure all tests pass.

**Testing checklist**:
- [ ] `pixi run robomage plot examples/sample_quartz.xy` works
- [ ] Output plot is generated and looks correct
- [ ] `pixi run check` passes (lint, typecheck, tests)
- [ ] Batch processing works
- [ ] Error handling works (bad input files)
- [ ] Performance is reasonable on larger files

---

## 🏗️ Architecture Overview

```
src/robomage/
├── data/
│   ├── __init__.py        # Data module exports
│   ├── models.py          # DiffractionData and core types
│   └── loaders.py         # File format handlers
├── visualization.py       # Plotting functions
├── __main__.py           # CLI entry point
└── config/               # Existing config module
    ├── __init__.py
    └── refinement_schema.py

examples/
├── sample_quartz.xy      # Test data
├── sample_complex.xy     # More complex test data
├── README.md             # Data format docs
└── plot_examples.py      # Usage examples

tests/
├── test_data_models.py   # Data model tests
├── test_loaders.py       # File loading tests
├── test_visualization.py # Plotting tests
└── test_schema.py        # Existing schema tests
```

## 🎯 Success Criteria

At sprint completion, all of these should work:

```bash
# Basic functionality
pixi install
pixi run robomage plot examples/sample_quartz.xy

# Quality assurance
pixi run check  # All tests pass

# Advanced usage
pixi run robomage plot examples/*.xy --output-dir plots/
```

## 🚀 Future Integration Points

This MVP creates foundation for:

- **GSAS-II Integration**: `DiffractionData` → refinement input
- **Tiled/Databroker**: Replace file loader with API calls
- **Database Storage**: Persist `DiffractionData` objects
- **Web Interface**: API endpoints using same data models
- **Batch Processing**: Orchestrator using established patterns
- **Peak Finding**: Operate on `DiffractionData` objects
- **Background Subtraction**: Preprocessing pipeline

## 📝 Notes

- Keep file formats simple initially (2-column ASCII)
- Focus on powder diffraction workflows (not single crystal)
- Maintain compatibility with existing config system
- Design for extensibility (more file formats, coordinate systems)
- Prioritize code quality and testing from the start

---

**Created**: October 17, 2025  
**Next Review**: When ready to start Sprint 2  
**Dependencies**: Sprint 1 complete (CI/CD, project structure)