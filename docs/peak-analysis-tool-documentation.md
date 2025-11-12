# Peak Analysis Tool Documentation

## Overview

The Peak Analysis Tool is a comprehensive scientific software package for automated peak detection, fitting, and analysis of powder diffraction data. It provides both standalone functionality and seamless integration with the RoboMage crystallographic analysis framework.

## Architecture

### Service-Based Design
The peak analysis functionality is implemented as a microservice architecture with multiple interaction modes:

- **Standalone Service**: Independent FastAPI REST service
- **Direct Engine**: In-process analysis without service dependencies  
- **Client Library**: HTTP client for distributed analysis workflows
- **CLI Interface**: Command-line tool for batch processing and scripting

### Core Components

```
RoboMage/
├── services/peak_analysis/          # Microservice implementation
│   ├── README.md                    # Service documentation
│   ├── __init__.py                  # Package exports and metadata
│   ├── main.py                      # FastAPI service entry point
│   ├── engine.py                    # Core scientific algorithms
│   └── models.py                    # Pydantic data models
├── src/robomage/clients/            # Client library
│   └── peak_analysis_client.py      # HTTP client implementation
├── peak_analyzer.py                 # CLI interface
└── tests/                          # Comprehensive test suite
    └── test_peak_analysis_integration.py
```

## Scientific Capabilities

### Peak Detection
- **Algorithm**: SciPy `find_peaks` with configurable parameters
- **Features**: Height, prominence, distance, and width filtering
- **Preprocessing**: Signal smoothing and noise reduction
- **Performance**: Sub-second detection for 1000+ peaks

### Peak Fitting
- **Profiles**: Gaussian, Lorentzian, and Voigt functions
- **Optimization**: Non-linear least squares with SciPy `curve_fit`
- **Statistics**: R² goodness-of-fit calculation for quality assessment
- **Constraints**: Physical parameter bounds and convergence criteria

### Background Subtraction
- **Methods**: Polynomial baseline fitting (orders 1-5)
- **Features**: Iterative background estimation
- **Validation**: Automatic quality checks and outlier detection

### Data Analysis
- **Q-space Processing**: Native Q-value (Å⁻¹) support
- **d-spacing Calculation**: Automatic conversion using d = 2π/Q
- **Statistical Analysis**: Comprehensive fit quality metrics
- **Error Handling**: Robust validation with scientific context

## Usage Modes

### 1. CLI Analysis (Recommended for most users)

```bash
# Basic analysis
python peak_analyzer.py data.chi --output results/

# Batch processing with glob patterns
python peak_analyzer.py "data/*.chi" --batch --parallel

# Verbose output with statistical details
python peak_analyzer.py data.chi --verbose --plot
```

### 2. Service Mode (For high-throughput workflows)

```bash
# Start service
python peak_analyzer.py --service --port 8001 --host 0.0.0.0

# Test service health
curl http://localhost:8001/health

# Analyze via REST API
curl -X POST http://localhost:8001/analyze \
  -H "Content-Type: application/json" \
  -d @sample_data.json
```

### 3. Python API (For integration and scripting)

```python
from robomage import load_diffraction_file
from robomage.clients.peak_analysis_client import PeakAnalysisClient

# Load data using RoboMage
data = load_diffraction_file("sample.chi")

# Analyze with service client
client = PeakAnalysisClient("http://localhost:8001")
response = client.analyze_diffraction_data(data)

print(f"Detected {response.peaks_detected} peaks")
for peak in response.peak_list:
    print(f"Peak at Q={peak.position:.3f} (d={peak.d_spacing:.3f}Å)")
```

### 4. Direct Engine (For embedded applications)

```python
import sys
sys.path.insert(0, "services")
from peak_analysis.engine import PeakAnalysisEngine
from peak_analysis.models import AnalysisConfig

# Direct analysis without service
engine = PeakAnalysisEngine()
result = engine.analyze(q_values, intensities, AnalysisConfig())
```

## Configuration Options

### Peak Detection Parameters
```json
{
  "peak_detection": {
    "height_threshold": 0.1,    // Minimum peak height (fraction of max)
    "prominence": 0.05,         // Peak prominence requirement  
    "distance": 5,              // Minimum distance between peaks
    "width": [1, 50]           // Peak width constraints (data points)
  }
}
```

### Fitting Configuration
```json
{
  "fitting": {
    "profile_type": "gaussian", // gaussian, lorentzian, voigt
    "r_squared_threshold": 0.95,// Minimum acceptable fit quality
    "max_iterations": 1000,     // Optimization iteration limit
    "convergence_tolerance": 1e-6
  }
}
```

### Background Subtraction
```json
{
  "background": {
    "subtract": true,           // Enable background subtraction
    "method": "polynomial",     // Background fitting method
    "order": 3,                 // Polynomial order (1-5)
    "iterations": 3             // Iterative refinement steps
  }
}
```

## Output Formats

### JSON (Default)
Structured data with complete analysis metadata:
```json
{
  "peaks_detected": 15,
  "peaks_fitted": 8,
  "processing_time_ms": 85.2,
  "overall_r_squared": 0.892,
  "peak_list": [
    {
      "peak_id": 0,
      "position": 1.51,
      "d_spacing": 4.16,
      "height": 5556,
      "width": 0.070,
      "r_squared": 0.981,
      "profile_type": "gaussian"
    }
  ]
}
```

### CSV Export
Tabular format for spreadsheet analysis:
```csv
ID,Position(A^-1),d-spacing(A),Height,Width,R^2,Profile
0,1.5109,4.159,5556,0.070,0.981,gaussian
1,2.1368,2.940,10236,0.073,0.995,gaussian
```

### Console Output
Human-readable summary with statistics and warnings:
```
=== Peak Analysis Results ===
File: LaB6_standard.chi
Peaks detected: 39
Peaks fitted: 5
Overall R^2: 0.814
Processing time: 106.0 ms

=== Peak Details ===
ID | Position (A^-1) | d-spacing (A) | Height | Width | R^2
---------------------------------------------------------
 0 |      1.5109     |     4.159     |  5556  | 0.070 | 0.981
 1 |      2.1368     |     2.940     | 10236  | 0.073 | 0.995
```

## Performance Characteristics

### Computational Efficiency
- **Analysis Time**: 50-200ms for typical datasets (1000-4000 points)
- **Peak Detection**: ~10ms for 50 peaks using optimized SciPy algorithms
- **Peak Fitting**: ~2ms per peak for Gaussian profiles
- **Memory Usage**: ~10MB for standard diffraction datasets

### Scalability
- **Batch Processing**: Parallel execution across CPU cores
- **Service Mode**: Concurrent request handling via FastAPI async
- **Memory Efficiency**: Streaming processing for large datasets
- **Network Optimization**: Connection pooling and request batching

### Quality Assurance
- **Validation**: Comprehensive input data validation
- **Error Recovery**: Robust error handling with retry logic
- **Statistical Verification**: R² and residual analysis for fit quality
- **Convergence Monitoring**: Optimization progress tracking

## Integration Points

### RoboMage Framework
- **Data Models**: Native `DiffractionData` object support
- **Loaders**: Compatible with all RoboMage file format loaders
- **Pipeline**: Seamless integration with analysis workflows
- **Metadata**: Preservation of experimental parameters and provenance

### External Software
- **GSAS-II**: Future integration for Rietveld refinement workflows
- **MATCH!**: Peak list export for phase identification
- **JADE**: Compatible peak position and intensity formats
- **Jupyter**: Interactive analysis and visualization workflows

### Development Tools
- **Testing**: Comprehensive test suite with real diffraction data
- **CI/CD**: GitHub Actions for automated testing and deployment
- **Documentation**: Auto-generated API docs with OpenAPI/Swagger
- **Type Safety**: Full mypy compatibility with static type checking

## File Format Support

### Input Formats
- **CHI**: Q-space data files (Q, intensity columns)
- **DAT**: Generic two-column ASCII data
- **XY**: Simple X-Y data format
- **Future**: XRD, RAW, and other crystallographic formats

### Output Compatibility
- **JSON**: Machine-readable with full metadata
- **CSV**: Spreadsheet and statistical software compatibility
- **ASCII**: Human-readable tabular format
- **Future**: CIF and other crystallographic exchange formats

## Installation and Dependencies

### Core Dependencies
```toml
# Production dependencies
scipy = ">=1.10.0"     # Scientific computing
fastapi = ">=0.100.0"  # REST API framework
uvicorn = ">=0.20.0"   # ASGI server
pydantic = ">=2.0"     # Data validation
numpy = "*"            # Numerical computing
requests = "*"         # HTTP client

# Development dependencies  
pytest = "*"           # Testing framework
mypy = "*"            # Type checking
ruff = "*"            # Code formatting/linting
```

### Environment Setup
```bash
# Using Pixi (recommended)
pixi install
pixi run python peak_analyzer.py --help

# Using pip
pip install -e .[dev,peak-analysis]
python peak_analyzer.py --help
```

## Error Handling and Troubleshooting

### Common Issues

1. **Module Import Errors**
   - Ensure RoboMage is installed: `pip install -e .`
   - Check Python path when running from source

2. **Service Connection Errors**
   - Verify service is running: `curl http://localhost:8001/health`
   - Check firewall settings for network access

3. **Data Validation Errors**
   - Ensure Q-values are monotonically increasing
   - Verify data contains no NaN or infinite values
   - Check intensity values are positive

4. **Fitting Convergence Issues**
   - Reduce R² threshold for noisy data
   - Increase maximum iterations
   - Try different peak profile types

### Debugging Options
```bash
# Verbose output with detailed logging
python peak_analyzer.py data.chi --verbose

# Service debug mode with detailed error traces
python peak_analyzer.py --service --debug --log-level DEBUG

# Direct engine analysis to bypass service dependencies
python peak_analyzer.py data.chi --direct
```

## Future Development

### Planned Features
- **Machine Learning**: AI-enhanced peak identification
- **Real-time Processing**: WebSocket support for streaming data
- **Advanced Profiles**: Pseudo-Voigt and asymmetric peak shapes
- **Parallel Fitting**: Multi-threading for large datasets

### Integration Roadmap
- **Database Storage**: Peak analysis results persistence
- **Visualization**: Real-time plotting with matplotlib/plotly
- **Cloud Deployment**: Containerized service deployment
- **GSAS-II Integration**: Automated Rietveld refinement workflows

## Contributing

### Development Workflow
1. Fork the repository and create a feature branch
2. Install development dependencies: `pixi install`
3. Run tests: `pixi run test`
4. Check code quality: `pixi run check`
5. Submit pull request with comprehensive tests

### Code Standards
- **Type Safety**: Full mypy compliance required
- **Testing**: Minimum 90% code coverage
- **Documentation**: Comprehensive docstrings and examples
- **Performance**: Benchmark critical algorithms

This documentation provides a comprehensive guide to the Peak Analysis Tool, covering all aspects from basic usage to advanced integration patterns. The tool represents a significant advancement in automated crystallographic analysis capabilities within the RoboMage framework.