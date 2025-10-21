#!/usr/bin/env python3
"""
Peak Analysis CLI - Standalone scientific peak analysis tool.

This script provides a command-line interface for the peak analysis service,
allowing users to analyze powder diffraction data for peaks through various
modes: standalone analysis, service mode, or Python API.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# Add the RoboMage source to Python path if running from source
if __name__ == "__main__":
    script_dir = Path(__file__).parent.absolute()
    robomage_src = script_dir.parent / "src"
    if robomage_src.exists():
        sys.path.insert(0, str(robomage_src))

try:
    from robomage.clients.peak_analysis_client import (
        PeakAnalysisClient,
        PeakAnalysisServiceError,
    )
    from robomage.data.loaders import load_diffraction_file
except ImportError as e:
    print(f"Error importing RoboMage modules: {e}")
    print("Please ensure RoboMage is properly installed or run from source directory")
    sys.exit(1)


class PeakAnalyzerCLI:
    """Command-line interface for peak analysis."""

    def __init__(self):
        self.service_process = None
        self.service_port = 8001

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def cleanup(self):
        """Clean up any running services."""
        if self.service_process:
            print("Stopping peak analysis service...")
            self.service_process.terminate()
            try:
                self.service_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.service_process.kill()
                self.service_process.wait()
            self.service_process = None

    def start_service(self, port: int = 8001, dev_mode: bool = False) -> bool:
        """
        Start the peak analysis service.

        Args:
            port: Port to run service on
            dev_mode: Whether to run in development mode

        Returns:
            True if service started successfully
        """
        services_dir = Path(__file__).parent / "services" / "peak_analysis"
        if not services_dir.exists():
            print(f"Error: Service directory not found at {services_dir}")
            return False

        main_py = services_dir / "main.py"
        if not main_py.exists():
            print(f"Error: Service main.py not found at {main_py}")
            return False

        cmd = [
            sys.executable,
            str(main_py),
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "info",
        ]

        if dev_mode:
            cmd.append("--dev")

        print(f"Starting peak analysis service on port {port}...")

        try:
            self.service_process = subprocess.Popen(
                cmd,
                cwd=str(services_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )

            # Wait for service to start
            client = PeakAnalysisClient(f"http://127.0.0.1:{port}")
            if client.wait_for_service(max_wait=30.0):
                print(f"[OK] Peak analysis service started on http://127.0.0.1:{port}")
                self.service_port = port
                return True
            else:
                print("[ERROR] Service failed to start within 30 seconds")
                self.cleanup()
                return False

        except Exception as e:
            print(f"[ERROR] Failed to start service: {e}")
            return False

    def analyze_file(
        self,
        file_path: str,
        output_dir: str | None = None,
        config: dict | None = None,
        service_mode: bool = False,
        port: int = 8001,
    ) -> bool:
        """
        Analyze a single diffraction file.

        Args:
            file_path: Path to diffraction data file
            output_dir: Output directory for results
            config: Analysis configuration
            service_mode: Whether to use service mode
            port: Service port (if using service mode)

        Returns:
            True if analysis succeeded
        """
        try:
            # Load data
            print(f"Loading data from {file_path}...")
            data = load_diffraction_file(file_path)
            print(f"[OK] Loaded {data.statistics.num_points} data points")

            if service_mode:
                # Use service
                return self._analyze_with_service(
                    data, file_path, output_dir, config, port
                )
            else:
                # Use direct engine
                return self._analyze_direct(data, file_path, output_dir, config)

        except Exception as e:
            print(f"[ERROR] Error analyzing {file_path}: {e}")
            return False

    def _analyze_with_service(
        self,
        data,
        file_path: str,
        output_dir: str | None,
        config: dict | None,
        port: int,
    ) -> bool:
        """Analyze using the service."""
        print("Using peak analysis service...")

        try:
            with PeakAnalysisClient(f"http://127.0.0.1:{port}") as client:
                # Check service health
                health = client.health_check()
                if health.get("status") != "healthy":
                    print("[ERROR] Service is not healthy")
                    return False

                # Perform analysis
                result = client.analyze_peaks(data, config)

                # Process results
                return self._process_results(result, file_path, output_dir)

        except PeakAnalysisServiceError as e:
            print(f"[ERROR] Service error: {e}")
            return False

    def _analyze_direct(
        self, data, file_path: str, output_dir: str | None, config: dict | None
    ) -> bool:
        """Analyze using direct engine import."""
        print("Using direct analysis engine...")

        try:
            # Import engine locally to avoid service dependency
            services_path = Path(__file__).parent / "services"
            sys.path.insert(0, str(services_path))

            # Now import the modules
            import peak_analysis.engine
            import peak_analysis.models

            # Convert data
            data_input = peak_analysis.models.DiffractionDataInput(
                q_values=data.q_values.tolist(),
                intensities=data.intensities.tolist(),
                filename=data.filename,
                sample_name=data.sample_name,
            )

            # Create config
            if config is None:
                analysis_config = peak_analysis.models.AnalysisConfig()
            else:
                analysis_config = peak_analysis.models.AnalysisConfig(**config)

            # Run analysis
            engine = peak_analysis.engine.PeakAnalysisEngine()
            result = engine.analyze_peaks(data_input, analysis_config)

            # Process results
            return self._process_results(result.model_dump(), file_path, output_dir)

        except Exception as e:
            print(f"[ERROR] Direct analysis error: {e}")
            return False

    def _process_results(
        self, result: dict, file_path: str, output_dir: str | None
    ) -> bool:
        """Process and save analysis results."""
        metadata = result.get("metadata", {})
        peaks = result.get("peaks", [])

        # Print summary
        print("\n=== Peak Analysis Results ===")
        print(f"File: {file_path}")
        print(f"Peaks detected: {metadata.get('num_peaks_detected', 0)}")
        print(f"Peaks fitted: {metadata.get('num_peaks_fitted', 0)}")
        print(f"Overall R^2: {metadata.get('overall_r_squared', 0):.3f}")
        print(f"Processing time: {metadata.get('processing_time_ms', 0):.1f} ms")

        if metadata.get("warnings"):
            print("\nWarnings:")
            for warning in metadata["warnings"]:
                print(f"  [WARNING] {warning}")

        if peaks:
            print(f"\n=== Peak Details ({len(peaks)} peaks) ===")
            print("ID | Position (A^-1) | d-spacing (A) | Height | Width | R^2")
            print("-" * 60)
            for peak in peaks:
                print(
                    f"{peak['peak_id']:2d} | "
                    f"{peak['position']:11.4f} | "
                    f"{peak['d_spacing']:10.3f} | "
                    f"{peak['height']:6.0f} | "
                    f"{peak['width']:5.3f} | "
                    f"{peak['r_squared']:.3f}"
                )

        # Save results if output directory specified
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            base_name = Path(file_path).stem

            # Save JSON results
            json_file = output_path / f"{base_name}_peaks.json"
            with open(json_file, "w") as f:
                json.dump(result, f, indent=2)
            print(f"\n[OK] Results saved to {json_file}")

            # Save CSV summary
            csv_file = output_path / f"{base_name}_peaks.csv"
            self._save_peaks_csv(peaks, csv_file)
            print(f"[OK] Peak summary saved to {csv_file}")

        return metadata.get("success", False)

    def _save_peaks_csv(self, peaks: list, csv_file: Path):
        """Save peaks to CSV file."""
        import csv

        with open(csv_file, "w", newline="") as f:
            if not peaks:
                f.write("No peaks detected\n")
                return

            writer = csv.writer(f)
            writer.writerow(
                [
                    "peak_id",
                    "position_A_inv",
                    "d_spacing_A",
                    "height",
                    "width",
                    "area",
                    "r_squared",
                    "profile_type",
                ]
            )

            for peak in peaks:
                writer.writerow(
                    [
                        peak["peak_id"],
                        peak["position"],
                        peak["d_spacing"],
                        peak["height"],
                        peak["width"],
                        peak["area"],
                        peak["r_squared"],
                        peak["profile_type"],
                    ]
                )


def create_parser():
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Peak Analysis Tool - Scientific peak analysis for powder diffraction"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze single file
  peak-analyzer sample.chi --output results/
  
  # Use service mode
  peak-analyzer sample.chi --service --port 8001
  
  # Batch processing
  peak-analyzer data/*.chi --output batch_results/
  
  # Run as service
  peak-analyzer --service --port 8001
  
  # Custom configuration
  peak-analyzer sample.chi --config analysis_config.json
        """,
    )

    # Input files
    parser.add_argument(
        "files", nargs="*", help="Diffraction data files to analyze (.chi, .xy, .dat)"
    )

    # Output options
    parser.add_argument(
        "--output", "-o", help="Output directory for results (JSON, CSV, plots)"
    )

    # Service options
    parser.add_argument(
        "--service",
        "-s",
        action="store_true",
        help="Run as service or use service mode for analysis",
    )

    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=8001,
        help="Port for service mode (default: 8001)",
    )

    parser.add_argument(
        "--dev",
        action="store_true",
        help="Run service in development mode with auto-reload",
    )

    # Analysis options
    parser.add_argument(
        "--config", "-c", help="JSON configuration file for analysis parameters"
    )

    parser.add_argument(
        "--min-height",
        type=float,
        help="Minimum peak height (relative to max intensity)",
    )

    parser.add_argument(
        "--min-prominence",
        type=float,
        default=0.01,
        help="Minimum peak prominence (default: 0.01)",
    )

    parser.add_argument(
        "--min-distance",
        type=float,
        default=0.1,
        help="Minimum distance between peaks (A^-1, default: 0.1)",
    )

    parser.add_argument(
        "--profile",
        choices=["gaussian", "lorentzian", "voigt", "pseudo_voigt"],
        default="gaussian",
        help="Peak profile function (default: gaussian)",
    )

    # General options
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    return parser


def main():
    """Main entry point for peak analyzer CLI."""
    parser = create_parser()
    args = parser.parse_args()

    # Load configuration if provided
    config = {}
    if args.config:
        try:
            with open(args.config) as f:
                config = json.load(f)
        except Exception as e:
            print(f"Error loading config file: {e}")
            return 1

    # Apply command-line overrides to config
    detection_config = config.setdefault("detection", {})
    fitting_config = config.setdefault("fitting", {})

    if args.min_height is not None:
        detection_config["min_height"] = args.min_height
    if args.min_prominence is not None:
        detection_config["min_prominence"] = args.min_prominence
    if args.min_distance is not None:
        detection_config["min_distance"] = args.min_distance
    if args.profile:
        fitting_config["profile_type"] = args.profile

    # Service-only mode (no files to analyze)
    if args.service and not args.files:
        print("Running peak analysis service...")

        # Import and run service directly
        services_dir = Path(__file__).parent / "services" / "peak_analysis"
        main_py = services_dir / "main.py"

        if not main_py.exists():
            print(f"Error: Service not found at {main_py}")
            return 1

        # Run service
        cmd = [
            sys.executable,
            str(main_py),
            "--host",
            "127.0.0.1",
            "--port",
            str(args.port),
        ]

        if args.dev:
            cmd.append("--dev")

        try:
            subprocess.run(cmd, cwd=str(services_dir))
            return 0
        except KeyboardInterrupt:
            print("\nService stopped by user")
            return 0
        except Exception as e:
            print(f"Error running service: {e}")
            return 1

    # File analysis mode
    if not args.files:
        print("Error: No files specified for analysis")
        parser.print_help()
        return 1

    # Expand glob patterns
    import glob

    all_files = []
    for pattern in args.files:
        matches = glob.glob(pattern)
        if matches:
            all_files.extend(matches)
        else:
            # Not a glob pattern, treat as literal filename
            all_files.append(pattern)

    if not all_files:
        print("Error: No files found matching the specified patterns")
        return 1

    # Process files
    success_count = 0
    total_count = len(all_files)

    with PeakAnalyzerCLI() as cli:
        # Start service if requested
        if args.service:
            if not cli.start_service(args.port, args.dev):
                print("Failed to start service")
                return 1

        # Process each file
        for i, file_path in enumerate(all_files, 1):
            print(f"\n[{i}/{total_count}] Processing {file_path}")

            if not os.path.exists(file_path):
                print(f"[ERROR] File not found: {file_path}")
                continue

            success = cli.analyze_file(
                file_path, args.output, config, args.service, args.port
            )

            if success:
                success_count += 1
                print(f"[OK] Analysis completed for {file_path}")
            else:
                print(f"[ERROR] Analysis failed for {file_path}")

    # Summary
    print("\n=== Summary ===")
    print(f"Files processed: {success_count}/{total_count}")

    if success_count == total_count:
        print("[OK] All files analyzed successfully")
        return 0
    else:
        print(f"[ERROR] {total_count - success_count} files failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
