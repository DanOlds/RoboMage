# 🧙‍♂️ RoboMage — Automated Powder Diffraction Framework

![CI](https://github.com/DanOlds/RoboMage/workflows/CI/badge.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/github/license/DanOlds/RoboMage)
![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)

**RoboMage** is a modular Python framework for automating **powder diffraction analysis and Rietveld refinement** across NSLS-II beamlines.

### 🔍 Key Features
- **Peak Analysis Tool**: Advanced automated peak detection and fitting with multiple profile types
- **Interactive Dashboard**: Professional 3-tab Dash UI for data import, visualization, and analysis
- **Real-time Analysis**: Integrated peak analysis service with live parameter tuning
- **Peak Visualization**: Automatic peak annotation on diffraction plots with detailed tooltips
- **Robust Data Loading**: Support for .chi and .xy files with automatic validation and error handling
- **Modern Python APIs**: Pydantic-based data models with type safety and validation
- **Statistical Analysis**: Built-in quality metrics and data summarization
- **Dual API Design**: Modern object-oriented interface + legacy pandas compatibility
- **Command-Line Tools**: Batch processing and visualization via CLI
- **Publication-Quality Plots**: Matplotlib integration for scientific visualization
- **Microservice Architecture**: Scalable peak analysis service with REST API

### 📖 API Overview

#### Data Loading
- **`load_diffraction_file(filename)`** - Auto-detect format and load data with validation
- **`load_chi_file(filename)`** - Load .chi/.xy files specifically with error handling  
- **`load_test_data()`** - Load built-in SRM 660b LaB₆ test dataset

#### Data Models
- **`DiffractionData`** - Modern Pydantic-based container with automatic validation
  - `.q_values`, `.intensity_values` - NumPy arrays with data
  - `.statistics` - Computed statistical properties (ranges, means, steps)
  - `.to_dataframe()` - Convert to pandas DataFrame for legacy workflows
  - `.trim_q_range(q_min, q_max)` - Filter data by Q range

- **`DataStatistics`** - Computed properties for quality assessment
  - `.q_range`, `.intensity_range` - Data ranges
  - `.num_points` - Number of data points
  - `.q_step_mean`, `.intensity_mean` - Statistical summaries

#### Peak Analysis Tool
RoboMage includes a comprehensive peak analysis system for automated crystallographic peak detection and fitting:

```python
# CLI Analysis (Recommended)
# Analyze single file
python peak_analyzer.py sample.chi --output results/

# Batch processing
python peak_analyzer.py "data/*.chi" --batch --parallel

# Service Mode (High-throughput workflows)
python peak_analyzer.py --service --port 8001

# Python API Integration
from robomage.clients.peak_analysis_client import PeakAnalysisClient

client = PeakAnalysisClient("http://localhost:8001")
data = robomage.load_diffraction_file("sample.chi")
response = client.analyze_diffraction_data(data)

print(f"Found {response.peaks_detected} peaks")
for peak in response.peak_list:
    print(f"Peak at Q={peak.position:.3f} (d={peak.d_spacing:.3f}Å)")
```

**Key Features:**
- **Automated Detection**: SciPy-based peak identification with configurable parameters
- **Multi-Profile Fitting**: Gaussian, Lorentzian, and Voigt peak profiles
- **Statistical Analysis**: R² goodness-of-fit metrics and quality assessment
- **Background Subtraction**: Polynomial baseline fitting and normalization
- **Multiple Interfaces**: CLI, REST API, and Python client library
- **High Performance**: Sub-second analysis for typical datasets

#### Interactive Dashboard
RoboMage includes a professional web-based dashboard for interactive data analysis:

```python
# Start the dashboard
python -m robomage.dashboard

# Custom port
python -m robomage.dashboard --port 8051 --debug

# Or via main CLI
python -m robomage --dashboard
```

**Dashboard Features:**
- **📁 Data Import Tab**: 
  - Drag-and-drop file upload for .chi and .xy files
  - Per-file wavelength management (0.1665 Å synchrotron default)
  - File validation and metadata display
  - Instant file removal with visual feedback

- **📊 Visualization Tab**:
  - Interactive Plotly plots with zoom, pan, and export
  - Multiple plot types (line, scatter, filled area)
  - Flexible axis options (Q, 2θ, d-spacing)
  - Normalization and log scale support
  - Multi-file overlay comparison

- **🔬 Analysis Tab**:
  - Real-time peak analysis service integration
  - Interactive parameter controls (prominence, distance, sensitivity)
  - Profile selection (Gaussian, Lorentzian, Voigt)
  - Automatic peak annotation on plots
  - Detailed results tables with fit quality metrics
  - Service connection status monitoring

Access dashboard at: `http://localhost:8050`

#### Legacy Compatibility
```python
# Legacy pandas-based API (for existing workflows)
from robomage.data_io import load_test_data, get_data_info

df = load_test_data()  # Returns pandas DataFrame
info = get_data_info(df)  # Get summary statistics
```

### 🏗️ Code Design

#### Dual API Architecture
RoboMage provides two complementary APIs to support different use cases:

**Modern API** (Recommended for new projects):
- Type-safe Pydantic models with automatic validation
- Immutable data structures with computed properties
- Rich error messages and data integrity guarantees
- Future-ready for advanced analysis pipelines

**Legacy API** (For existing pandas workflows):
- Direct pandas DataFrame access
- Compatible with existing analysis scripts
- Easy migration path to modern API when ready

#### Validation & Error Handling
- **Automatic Data Validation**: Q-values sorted, no NaN/inf values
- **File Format Detection**: Robust parsing with clear error messages
- **Scientific Validation**: Proper units and physically reasonable ranges
- **Type Safety**: Full MyPy compliance for development confidence

### ⚙️ Core Stack
- **Python 3.10+ / Pixi** - Modern environment management and cross-platform dependency resolution
- **Pydantic v2** - Data validation and settings management
- **NumPy / Pandas** - Scientific computing foundation
- **SciPy** - Advanced scientific algorithms for peak analysis
- **FastAPI + Uvicorn** - High-performance REST API services
- **Matplotlib** - Publication-quality plotting
- **Ruff + MyPy** - Code formatting and type checking
- **Pytest** - Comprehensive testing framework

### 🚀 Quick Start

#### Prerequisites
This project uses **[Pixi](https://pixi.sh)** for environment management - a modern, fast alternative to conda/pip that provides:
- **Cross-platform compatibility** (Windows, macOS, Linux)
- **Fast dependency resolution** with conda-forge packages
- **Reproducible environments** with lockfiles
- **Simple task management** (no need for separate Makefile/scripts)

Install pixi from [pixi.sh](https://pixi.sh) or using:
```powershell
# Windows (PowerShell)
iwr -useb https://pixi.sh/install.ps1 | iex

# macOS/Linux
curl -fsSL https://pixi.sh/install.sh | bash
```

#### Installation
```powershell
git clone https://github.com/DanOlds/RoboMage.git
cd RoboMage
pixi install
pixi run test
```

> **⚠️ IMPORTANT**: This project uses Pixi exclusively for environment and task management. Do NOT use `pip install`, `conda install`, or traditional virtual environments. All dependencies and tasks are managed through `pixi.toml`. See below for common pixi commands.

> **Alternative**: If you prefer traditional Python environments, you can use `pip install -e .` after creating a virtual environment, but pixi is recommended for the best development experience and reproducibility.

#### Basic Usage
```python
import robomage

# Load diffraction data with automatic validation
data = robomage.load_diffraction_file("sample.chi")
print(f"Loaded {len(data.q_values)} data points")

# Access statistical properties
stats = data.statistics
print(f"Q range: {stats.q_range}")
print(f"Mean intensity: {stats.intensity_mean:.1f}")

# Create publication-quality plots
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
ax.plot(data.q_values, data.intensity_values)
ax.set_xlabel("Q (Å⁻¹)")
ax.set_ylabel("Intensity")
plt.show()

# Load test data for development
test_data = robomage.load_test_data()  # Built-in SRM 660b dataset
```

#### Command Line Interface

**Data Visualization and Analysis:**
```powershell
# Analyze single file with interactive plot
pixi run python -m robomage sample.chi --plot --info

# Batch process multiple files
pixi run python -m robomage --files *.chi --output plots/
pixi run python -m robomage --files *.xy --info

# Get help
pixi run python -m robomage --help
```

**Peak Analysis Tool:**
```powershell
# Analyze single file for peaks
pixi run python peak_analyzer.py sample.chi --output results/

# Batch processing with parallel execution
pixi run python peak_analyzer.py "data/*.chi" --batch --parallel

# Start peak analysis service
pixi run python peak_analyzer.py --service --port 8001

# Verbose analysis with detailed output
pixi run python peak_analyzer.py sample.chi --verbose --plot

# Get peak analyzer help
pixi run python peak_analyzer.py --help
```


### 🖥️ Dashboard Visualization & Analysis

RoboMage includes a professional Dash-based dashboard for interactive powder diffraction analysis:

- **3-tab interface**: Data Import, Visualization, and Analysis tabs for streamlined workflows
- **Wavelength management**: Assign and display per-file wavelength (default: 0.1665 Å synchrotron)
- **Robust file handling**: Upload, validate, and remove files with a single click (red 'X' button)
- **Accurate Q→2θ conversion**: Uses file-specific wavelength for scientific correctness
- **Publication-quality plots**: Line, scatter, and filled area types with export options
- **Real-time peak analysis**: Interactive parameter controls with live peak detection service integration
- **Peak visualization**: Automatic peak annotation on plots with detailed tooltips (Q, d-spacing, intensity, FWHM)
- **Service monitoring**: Connection status indicators with helpful startup instructions
- **State management**: Seamless inter-tab data flow and persistent user selections

**To launch the dashboard:**
```powershell
pixi run python -m robomage --dashboard
# or
python -m robomage.dashboard
```

See [docs/sprint-4-visualization-dashboard.md](docs/sprint-4-visualization-dashboard.md) for full details.

### 📊 Examples & Tutorials

**Quick Example**:
```python
import robomage

# Load and analyze data
data = robomage.load_diffraction_file("my_sample.chi")
print(f"Data summary: {data.statistics.num_points} points, "
      f"Q range: {data.statistics.q_range}")

# Filter and export
filtered = data.trim_q_range(2.0, 8.0)
df = filtered.to_dataframe()
df.to_csv("filtered_data.csv")
```

**Comprehensive Tutorial**: See [`examples/load_data_example.py`](examples/load_data_example.py) for a complete walkthrough covering:
- Modern vs legacy API usage patterns
- Statistical analysis and quality assessment  
- Publication-quality visualization
- Error handling and data validation
- Format conversion workflows

### 🧪 Development Setup

**Why Pixi?** This project uses pixi instead of traditional pip/conda because:
- **Faster**: Parallel dependency resolution and caching
- **Reproducible**: Exact environment recreation across machines
- **Simple**: Single `pixi.toml` file replaces requirements.txt, environment.yml, and Makefile
- **Cross-platform**: Identical behavior on Windows, macOS, and Linux

Open the project in VS Code:
```powershell
code .
```

Run development tools:
```powershell
pixi run format    # Code formatting with ruff
pixi run lint      # Linting checks with ruff
pixi run typecheck # Type checking with mypy
pixi run test      # Full test suite with pytest
```

> **Note**: All tasks are defined in `pixi.toml` and run in the isolated pixi environment automatically.

###  Project Status
**Sprint 3 + Sprint 4 Phase 2** ✅ **COMPLETE (Nov 13, 2025)**:
- ✅ Robust data loading and validation system
- ✅ Modern Pydantic-based data models with statistical analysis
- ✅ Peak analysis microservice (FastAPI) with multi-profile fitting
- ✅ Interactive dashboard with real-time analysis integration
- ✅ Command-line interface for batch processing
- ✅ Comprehensive documentation and examples
- ✅ Full test coverage (51 tests) with CI/CD pipeline
- ✅ Type-safe codebase with MyPy compliance

**Sprint 4 Phase 3** 📋 **Planned**:
- 🔄 Publication-quality plot export and formatting
- 🔄 Advanced export options (CSV, JSON, combined results)
- 🔄 Batch processing and analysis comparison tools
- 🔄 Enhanced visualization features

**Future Development** 📋 **Roadmap**:
- 🔄 GSAS-II integration for automated Rietveld refinement
- 🔄 Advanced data pipeline with Tiled/Databroker integration
- 🔄 Machine learning-guided parameter optimization

### 📚 Documentation

- **[Development Guide](docs/DEVELOPMENT.md)** - **START HERE**: Pixi commands, workflow, best practices
- **[Complete API Documentation](src/robomage/)** - Detailed docstrings in source code
- **[Architecture & Dev Guide](.github/copilot-instructions.md)** - Architecture patterns, pixi usage, sprint status
- **[LLM Chat Guide](docs/llm-chat-guide.md)** - Quick start template for AI assistant conversations
- **[Sprint 4 Dashboard Plan](docs/sprint-4-visualization-dashboard.md)** - Dashboard implementation phases
- **[Examples](examples/)** - Working code samples and tutorials
- **[Environment Config](pixi.toml)** - Pixi environment and task definitions

---
> Developed at **Brookhaven National Laboratory (BNL)** at the **NSLS-II**.
