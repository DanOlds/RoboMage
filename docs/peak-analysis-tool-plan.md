# Peak Analysis Tool: Independent Scientific Software

## Overview
Design and build a **standalone peak analysis tool** for powder diffraction data that provides comprehensive peak detection, fitting, and analysis capabilities. This tool will be usable independently or as a service component within the RoboMage ecosystem.

## Tool Identity
- **Name**: `peak-analyzer` (or `diffpeak`)
- **Purpose**: Professional peak analysis for powder diffraction patterns
- **Target Users**: Crystallographers, materials scientists, beamline users
- **Distribution**: Standalone Python package + optional service mode
- **Integration**: Can be used by RoboMage, but doesn't require it

## Core Scientific Capabilities

### Peak Detection
- **Algorithm**: scipy.signal.find_peaks with scientific parameter tuning
- **Peak Types**: Bragg peaks, amorphous humps, background features
- **Sensitivity Control**: Height, prominence, width, and distance thresholds
- **Noise Handling**: Robust detection in noisy experimental data

### Peak Fitting
- **Profile Functions**: Gaussian, Lorentzian, Voigt, pseudo-Voigt
- **Background Models**: Polynomial, spline, Chebyshev, manual
- **Simultaneous Fitting**: Multiple peaks with shared parameters
- **Uncertainty Quantification**: Confidence intervals and fit quality metrics

### Data Analysis
- **Peak Positions**: Accurate Q-space and d-spacing determination
- **Integrated Intensities**: Peak areas with background subtraction
- **Peak Widths**: FWHM analysis for crystallite size/strain
- **Quality Assessment**: Signal-to-noise, fit reliability scores

## User Interfaces

### 1. Command-Line Interface (Primary)
```bash
# Basic peak analysis
peak-analyzer sample.chi --output results/

# Advanced configuration
peak-analyzer sample.chi \
  --min-height 0.05 \
  --min-distance 0.1 \
  --fit-profile voigt \
  --background-order 3 \
  --output-format json,csv,plot

# Batch processing
peak-analyzer data/*.chi --output-dir batch_results/ --parallel 4

# Interactive mode
peak-analyzer sample.chi --interactive
```

### 2. Python API
```python
import peak_analyzer

# Load and analyze
data = peak_analyzer.load_data("sample.chi")
results = peak_analyzer.analyze_peaks(
    data, 
    min_height=0.05,
    fit_peaks=True,
    background_order=3
)

# Access results
print(f"Found {len(results.peaks)} peaks")
for peak in results.peaks:
    print(f"Q={peak.position:.3f}, d={peak.d_spacing:.3f} Å")

# Plotting
peak_analyzer.plot_results(data, results, save="analysis.png")
```

### 3. REST API Service Mode
```bash
# Start service
peak-analyzer --service --port 8001

# Use via HTTP
curl -X POST http://localhost:8001/analyze \
  -H "Content-Type: application/json" \
  -d @request.json
```

### 4. Future Web GUI
- **Interactive plotting** with peak selection/editing
- **Parameter tuning** with real-time preview
- **Batch job management** and progress monitoring
- **Result comparison** and visualization tools

## Technical Architecture

### Core Components
```
peak_analyzer/
├── __init__.py              # Public API
├── __main__.py              # CLI entry point
├── core/
│   ├── detection.py         # Peak finding algorithms
│   ├── fitting.py           # Profile fitting routines
│   ├── background.py        # Background subtraction
│   └── analysis.py          # Result analysis and metrics
├── data/
│   ├── loaders.py           # File format support
│   ├── models.py            # Data structures (Pydantic)
│   └── exporters.py         # Output format writers
├── gui/
│   ├── cli.py               # Command-line interface
│   ├── service.py           # FastAPI service mode
│   └── web/                 # Future web interface
├── utils/
│   ├── validation.py        # Input validation
│   ├── plotting.py          # Matplotlib integration
│   └── config.py            # Configuration management
└── tests/                   # Comprehensive test suite
```

### Data Models
```python
# Core data structures
class DiffractionPattern:
    q_values: np.ndarray
    intensities: np.ndarray
    metadata: Dict[str, Any]

class PeakFitConfig:
    min_height: float = 0.05
    min_distance: float = 0.1
    profile_type: str = "voigt"
    background_order: int = 3
    fit_individual: bool = True

class Peak:
    position: float           # Q position (Å⁻¹)
    d_spacing: float         # d-spacing (Å)
    intensity: float         # Peak height
    area: float              # Integrated intensity
    fwhm: float             # Full width at half maximum
    fit_quality: float      # R-squared or similar
    uncertainty: float      # Position uncertainty

class AnalysisResults:
    peaks: List[Peak]
    background_coefficients: np.ndarray
    fit_statistics: Dict[str, float]
    processing_metadata: Dict[str, Any]
```

## File Format Support

### Input Formats
- **.chi files**: Two-column Q, intensity data
- **.xy files**: Generic two-column ASCII
- **.dat files**: Flexible delimited data
- **JSON**: Structured data with metadata
- **Future**: .cif, .xye, GSAS formats

### Output Formats
- **JSON**: Complete analysis results with metadata
- **CSV**: Peak list for spreadsheet analysis
- **PNG/PDF**: Publication-quality plots
- **HDF5**: Efficient binary storage for large datasets

## CLI Design Philosophy

### Simple by Default
```bash
# Minimal usage - sensible defaults
peak-analyzer sample.chi
# -> Finds peaks, saves to sample_peaks.json and sample_analysis.png
```

### Powerful When Needed
```bash
# Advanced usage with full control
peak-analyzer sample.chi \
  --config analysis_config.json \
  --min-height 0.02 \
  --profile-type pseudo-voigt \
  --background spline \
  --output-format json,csv,hdf5,plot \
  --plot-style publication \
  --parallel-jobs 8 \
  --verbose
```

### Batch Processing Native
```bash
# Process entire directories
peak-analyzer data/ --recursive --filter "*.chi" --output results/

# Parallel processing with progress
peak-analyzer data/*.chi --parallel 4 --progress-bar
```

## Integration Points

### RoboMage Integration
```python
# RoboMage uses peak-analyzer as a service
from robomage.services import PeakAnalysisService

service = PeakAnalysisService()
results = service.analyze(diffraction_data, config)
```

### Other Tool Integration
```python
# Other projects can use the Python API
import peak_analyzer

# Or the service API
import requests
response = requests.post("http://localhost:8001/analyze", json=data)
```

### Workflow Integration
```bash
# Unix pipeline friendly
cat sample.chi | peak-analyzer --input stdin --output stdout | process_peaks.py

# Configuration file driven
peak-analyzer --config batch_config.yaml
```

## Quality Assurance

### Scientific Validation
- **Test against known standards** (LaB₆, Si, etc.)
- **Compare with manual analysis** results
- **Validate peak positions** against crystallographic databases
- **Benchmark performance** against existing tools

### Software Quality
- **Comprehensive test suite** with pytest
- **Continuous integration** with automated testing
- **Type safety** with mypy
- **Code quality** with ruff formatting/linting
- **Documentation** with examples and tutorials

### User Experience
- **Clear error messages** with helpful suggestions
- **Progress indicators** for long-running operations
- **Sensible defaults** that work for most cases
- **Extensive help** and examples

## Distribution Strategy

### Development Phase
1. **Standalone package**: Independent pip/conda installation
2. **Service mode**: Can run as HTTP service
3. **RoboMage integration**: Used as external service

### Future Distribution
1. **PyPI package**: `pip install peak-analyzer`
2. **Conda package**: `conda install peak-analyzer`
3. **Container image**: `docker run peak-analyzer`
4. **Web service**: Hosted analysis service

## Success Metrics

### Functionality
- [ ] Accurately detects peaks in test diffraction data
- [ ] Provides reliable peak fitting with uncertainty estimates
- [ ] Handles various background types and noise levels
- [ ] Processes typical datasets in reasonable time (<30s)

### Usability
- [ ] Clear CLI with helpful error messages
- [ ] Python API that's intuitive for scientists
- [ ] Service mode that's reliable and performant
- [ ] Documentation that enables independent usage

### Integration
- [ ] Works seamlessly with RoboMage orchestrator
- [ ] Can be used by other projects without dependencies
- [ ] Service API is well-documented and stable
- [ ] Performance is acceptable for production workflows

## Timeline and Phases

### Phase 1: Core Tool (Sprint 3 - 2 weeks)
- ✅ Basic CLI with peak detection and fitting
- ✅ Python API for programmatic usage
- ✅ Service mode with REST API
- ✅ JSON/CSV output formats

### Phase 2: Enhancement (Future Sprint)
- 🔄 Advanced fitting algorithms and background models
- 🔄 Interactive plotting and visualization
- 🔄 Batch processing optimizations
- 🔄 Additional file format support

### Phase 3: GUI and Polish (Future)
- 🔄 Web-based interactive interface
- 🔄 Advanced visualization and comparison tools
- 🔄 Plugin architecture for custom analysis
- 🔄 Integration with crystallographic databases

This tool will be a valuable standalone contribution to the crystallography community while serving as the foundation for RoboMage's analysis capabilities.