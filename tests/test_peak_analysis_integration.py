"""
Tests for the peak analysis service and client.

This module contains integration tests for the peak analysis service,
client library, and CLI functionality.
"""

import json
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import pytest

from robomage.clients.peak_analysis_client import (
    PeakAnalysisClient,
    PeakAnalysisServiceError,
)
from robomage.data.models import DiffractionData


@pytest.fixture
def sample_diffraction_data():
    """Create sample diffraction data for testing."""
    # Generate synthetic diffraction pattern with peaks
    q_values = np.linspace(1.0, 10.0, 1000)

    # Background
    background = 100 + 50 * np.exp(-q_values / 5)

    # Add some peaks
    peaks = [
        (2.5, 1000, 0.1),  # position, height, width
        (4.0, 800, 0.15),
        (6.5, 600, 0.12),
        (8.0, 400, 0.18),
    ]

    intensities = background.copy()
    for pos, height, width in peaks:
        peak = height * np.exp(-0.5 * ((q_values - pos) / width) ** 2)
        intensities += peak

    # Add some noise
    noise = np.random.normal(0, 20, len(q_values))
    intensities += noise
    intensities = np.maximum(intensities, 0)  # Ensure non-negative

    return DiffractionData(
        q_values=q_values,
        intensities=intensities,
        filename="test_sample.chi",
        sample_name="Test Sample",
    )


class TestPeakAnalysisModels:
    """Test the Pydantic models for peak analysis."""

    def test_diffraction_data_input_validation(self):
        """Test DiffractionDataInput validation."""
        # Import the service models
        import sys

        services_dir = Path(__file__).parent.parent / "services"
        sys.path.insert(0, str(services_dir))

        from peak_analysis.models import DiffractionDataInput

        # Valid data
        data = DiffractionDataInput(
            q_values=[1.0, 2.0, 3.0],
            intensities=[100.0, 200.0, 150.0],
            filename="test.chi",
        )
        assert len(data.q_values) == 3
        assert len(data.intensities) == 3

        # Invalid data - different lengths
        with pytest.raises(ValueError):
            DiffractionDataInput(q_values=[1.0, 2.0], intensities=[100.0, 200.0, 150.0])

        # Invalid data - empty arrays
        with pytest.raises(ValueError):
            DiffractionDataInput(q_values=[], intensities=[])

    def test_analysis_config_defaults(self):
        """Test default analysis configuration."""
        import sys

        services_dir = Path(__file__).parent.parent / "services"
        sys.path.insert(0, str(services_dir))

        from peak_analysis.models import AnalysisConfig

        config = AnalysisConfig()
        assert config.detection.min_prominence == 0.01
        assert config.detection.min_distance == 0.1
        assert config.fitting.profile_type == "gaussian"
        assert config.fitting.background_type == "linear"
        assert config.compute_uncertainties is True
        assert config.quality_threshold == 0.95


class TestPeakAnalysisEngine:
    """Test the core peak analysis engine."""

    def test_engine_initialization(self):
        """Test engine can be initialized."""
        import sys

        services_dir = Path(__file__).parent.parent / "services"
        sys.path.insert(0, str(services_dir))

        from peak_analysis.engine import PeakAnalysisEngine

        engine = PeakAnalysisEngine()
        assert engine.version == "1.0.0"

    def test_peak_detection(self, sample_diffraction_data):
        """Test peak detection on synthetic data."""
        import sys

        services_dir = Path(__file__).parent.parent / "services"
        sys.path.insert(0, str(services_dir))

        from peak_analysis.engine import PeakAnalysisEngine
        from peak_analysis.models import AnalysisConfig, DiffractionDataInput

        # Convert to service format
        data_input = DiffractionDataInput(
            q_values=sample_diffraction_data.q_values.tolist(),
            intensities=sample_diffraction_data.intensities.tolist(),
            filename=sample_diffraction_data.filename,
            sample_name=sample_diffraction_data.sample_name,
        )

        # Analyze with default config
        engine = PeakAnalysisEngine()
        config = AnalysisConfig()
        result = engine.analyze_peaks(data_input, config)

        # Check results
        assert result.metadata.success is True
        assert result.metadata.num_peaks_detected > 0
        assert len(result.peaks) > 0
        assert result.background is not None

        # Check peak properties
        for peak in result.peaks:
            assert peak.position > 0
            assert peak.height > 0
            assert peak.width > 0
            assert peak.area > 0
            assert 0 <= peak.r_squared <= 1


class TestPeakAnalysisService:
    """Test the FastAPI service."""

    @pytest.fixture(scope="class")
    def service_process(self):
        """Start the service for testing."""
        services_dir = Path(__file__).parent.parent / "services" / "peak_analysis"
        main_py = services_dir / "main.py"

        if not main_py.exists():
            pytest.skip("Service main.py not found")

        # Start service
        process = subprocess.Popen(
            ["python", str(main_py), "--port", "8002"],
            cwd=str(services_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

        # Wait for service to start
        client = PeakAnalysisClient("http://127.0.0.1:8002")
        if not client.wait_for_service(max_wait=15.0):
            process.terminate()
            pytest.skip("Service failed to start")

        yield process

        # Clean up
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

    def test_service_health(self, service_process):
        """Test service health endpoint."""
        client = PeakAnalysisClient("http://127.0.0.1:8002")

        health = client.health_check()
        assert health["status"] == "healthy"
        assert health["dependencies_ok"] is True
        assert "version" in health
        assert health["uptime_seconds"] >= 0

    def test_service_analysis(self, service_process, sample_diffraction_data):
        """Test service analysis endpoint."""
        client = PeakAnalysisClient("http://127.0.0.1:8002")

        # Perform analysis
        result = client.analyze_peaks(sample_diffraction_data)

        # Check response structure
        assert "peaks" in result
        assert "metadata" in result
        assert "background" in result

        # Check metadata
        metadata = result["metadata"]
        assert metadata["success"] is True
        assert metadata["num_peaks_detected"] >= 0
        assert metadata["processing_time_ms"] > 0

        # Check peaks
        peaks = result["peaks"]
        assert isinstance(peaks, list)

        for peak in peaks:
            assert "peak_id" in peak
            assert "position" in peak
            assert "height" in peak
            assert "width" in peak
            assert "area" in peak
            assert "r_squared" in peak

    def test_service_error_handling(self, service_process):
        """Test service error handling."""
        client = PeakAnalysisClient("http://127.0.0.1:8002")

        # Test with invalid data
        with pytest.raises(PeakAnalysisServiceError):
            client.analyze_peaks_raw(
                q_values=[1, 2],  # Too few points
                intensities=[100, 200],
            )


class TestPeakAnalysisCLI:
    """Test the command-line interface."""

    def test_cli_help(self):
        """Test CLI help output."""
        cli_script = Path(__file__).parent.parent / "peak_analyzer.py"

        result = subprocess.run(
            ["python", str(cli_script), "--help"],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        # Check return code and basic content
        if result.returncode != 0:
            print(f"STDERR: {result.stderr}")
        assert result.returncode == 0
        assert "Peak Analysis Tool" in result.stdout
        assert "--output" in result.stdout
        assert "--service" in result.stdout

    def test_cli_analysis(self, sample_diffraction_data):
        """Test CLI analysis functionality."""
        cli_script = Path(__file__).parent.parent / "peak_analyzer.py"

        # Create temporary input file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".chi", delete=False) as f:
            for q, intensity in zip(
                sample_diffraction_data.q_values,
                sample_diffraction_data.intensities,
                strict=True,
            ):
                f.write(f"{q:.6f} {intensity:.1f}\n")
            temp_file = f.name

        try:
            # Create temporary output directory
            with tempfile.TemporaryDirectory() as output_dir:
                # Run CLI analysis
                result = subprocess.run(
                    ["python", str(cli_script), temp_file, "--output", output_dir],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    encoding="utf-8",
                )

                # Check that analysis completed
                if result.returncode != 0:
                    print(f"STDOUT: {result.stdout}")
                    print(f"STDERR: {result.stderr}")
                assert result.returncode == 0
                assert "Analysis completed" in result.stdout

                # Check output files
                output_path = Path(output_dir)
                json_files = list(output_path.glob("*.json"))
                csv_files = list(output_path.glob("*.csv"))

                assert len(json_files) > 0
                assert len(csv_files) > 0

                # Check JSON content
                with open(json_files[0]) as f:
                    result_data = json.load(f)
                    assert "peaks" in result_data
                    assert "metadata" in result_data

        finally:
            # Clean up temporary file
            Path(temp_file).unlink()


if __name__ == "__main__":
    # Run tests when script is executed directly
    pytest.main([__file__, "-v"])
