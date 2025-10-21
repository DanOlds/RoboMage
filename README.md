# 🧙‍♂️ RoboMage — Automated Powder Diffraction Framework

![CI](https://github.com/DanOlds/RoboMage/workflows/CI/badge.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/github/license/DanOlds/RoboMage)
![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)

**RoboMage** is a modular Python framework for automating **powder diffraction analysis and Rietveld refinement** across NSLS-II beamlines.

### 🔍 Key Features
- **Robust Data Loading**: Support for .chi files with automatic validation and error handling
- **Modern Python APIs**: Pydantic-based data models with type safety and validation
- **Statistical Analysis**: Built-in quality metrics and data summarization
- **Dual API Design**: Modern object-oriented interface + legacy pandas compatibility
- **Command-Line Tools**: Batch processing and visualization via CLI
- **Publication-Quality Plots**: Matplotlib integration for scientific visualization

### 📖 API Overview

#### Data Loading
- **`load_diffraction_file(filename)`** - Auto-detect format and load data with validation
- **`load_chi_file(filename)`** - Load .chi files specifically with error handling  
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
- **Python 3.10+ / Pixi** - Modern environment management
- **Pydantic v2** - Data validation and settings management
- **NumPy / Pandas** - Scientific computing foundation
- **Matplotlib** - Publication-quality plotting
- **Ruff + MyPy** - Code formatting and type checking
- **Pytest** - Comprehensive testing framework

### 🚀 Quick Start

#### Installation
```powershell
git clone https://github.com/DanOlds/RoboMage.git
cd RoboMage
pixi install
pixi run test
```

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
```powershell
# Analyze single file with interactive plot
pixi run python -m robomage sample.chi --plot --info

# Batch process multiple files
pixi run python -m robomage --files *.chi --output plots/

# Get help
pixi run python -m robomage --help
```

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

Open the project in VS Code:
```powershell
code .
```

Run development tools:
```powershell
pixi run format    # Code formatting
pixi run lint      # Linting checks  
pixi run typecheck # Type checking
pixi run test      # Full test suite
```

###  Project Status
**Current (Week 2)** ✅ **Complete**:
- ✅ Robust data loading and validation system
- ✅ Modern Pydantic-based data models with statistical analysis
- ✅ Command-line interface for batch processing
- ✅ Comprehensive documentation and examples
- ✅ Full test coverage with CI/CD pipeline
- ✅ Type-safe codebase with MyPy compliance

**Future Development** 📋 **Planned**:
- 🔄 GSAS-II integration for automated Rietveld refinement
- 🔄 Advanced data pipeline with Tiled/Databroker integration
- 🔄 Web interface and workflow automation
- 🔄 Machine learning-guided parameter optimization

### 📚 Documentation

- **[Complete API Documentation](src/robomage/)** - Detailed docstrings in source code
- **[Architecture Overview](docs/README_full.md)** - Detailed technical design
- **[Sprint Planning](docs/sprint-2-data-pipeline.md)** - Development roadmap
- **[Examples](examples/)** - Working code samples and tutorials

---
> Developed at **Brookhaven National Laboratory (BNL)** at the **NSLS-II**.
