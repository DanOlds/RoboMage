"""Command-line interface for RoboMage powder diffraction analysis.

This module provides the main entry point for RoboMage's command-line interface,
enabling users to load, analyze, and visualize powder diffraction data from
the terminal. It supports both single-file and multi-file processing workflows
with flexible plotting and analysis options.

Key Features:
    - Load diffraction data from .chi files or use built-in test data
    - Generate publication-quality plots with matplotlib
    - Compare multiple datasets with overlay plots
    - Extract and display statistical summaries
    - Support for glob patterns for batch processing
    - Flexible output directory management

Usage Examples:
    # Load and display test data
    python -m robomage test --plot

    # Process a single file with statistics
    python -m robomage sample.chi --info --save-plot plot.png

    # Compare multiple files
    python -m robomage --files *.chi --plot

    # Batch processing with verbose output
    python -m robomage --files data/*.chi --output results/ --verbose

Command-line Arguments:
    input_file: Optional single file or 'test' for built-in data
    --files/-f: Process multiple files (supports glob patterns)
    --output/-o: Output directory for saved plots
    --info/-i: Display detailed data statistics
    --plot/-p: Show interactive plots
    --save-plot: Save plot with custom filename
    --verbose/-v: Enable detailed output
    --config/-c: Configuration file (planned feature)

File Formats:
    - .chi files: Two-column text files (Q in Å⁻¹, intensity)
    - Test data: Built-in SRM 660b LaB₆ standard

Output:
    - PNG plots with 150 DPI resolution
    - Statistical summaries to stdout
    - Error messages with helpful diagnostics

Dependencies:
    - matplotlib: Required for plotting functionality
    - numpy: Used by matplotlib for data handling
    - pandas: Data manipulation through data_io module

Architecture:
    This module uses the legacy data_io interface for compatibility with
    existing workflows. Future versions may migrate to the modern
    data.loaders and data.models APIs for enhanced functionality.

See Also:
    - robomage.data.loaders: Modern data loading API
    - robomage.data.models: Validated data structures
    - robomage.data_io: Legacy DataFrame-based interface
"""

import argparse
import sys
from pathlib import Path

from .data_io import get_data_info, load_chi_file, load_test_data


def plot_data(df, output_dir=".", filename=None, show=True, save=True):
    """Create a publication-quality plot of diffraction data.

    Generates a matplotlib figure showing the diffraction pattern with
    properly labeled axes, grid, and title. Supports both interactive
    display and file output with customizable parameters.

    Args:
        df: DataFrame with 'Q' and 'intensity' columns containing the
            diffraction data to plot.
        output_dir: Directory to save the plot file. Defaults to current
            directory.
        filename: Custom filename for saved plot. If None, uses default
            'diffraction_pattern.png'.
        show: If True, display the plot interactively using plt.show().
        save: If True, save the plot to file in the output directory.

    Returns:
        bool: True if plotting succeeded, False if matplotlib is not available.

    Raises:
        ImportError: Handled internally - prints error message if matplotlib
            is not installed.

    Plot Features:
        - Figure size: 10x6 inches for good aspect ratio
        - Blue line plot with 1pt linewidth
        - Labeled axes: Q (Å⁻¹) vs Intensity
        - Semi-transparent grid for readability
        - 150 DPI resolution for publication quality
        - Tight bounding box to minimize whitespace

    Example:
        >>> import pandas as pd
        >>> df = pd.DataFrame({"Q": [1, 2, 3], "intensity": [100, 200, 150]})
        >>> success = plot_data(df, output_dir="plots", show=False)
        >>> if success:
        ...     print("Plot created successfully")

    Note:
        If matplotlib is not available, the function prints an installation
        message and returns False without raising an exception.
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print(
            "Error: matplotlib is required for plotting. "
            "Install with 'pixi install matplotlib'"
        )
        return False

    # Create the plot
    plt.figure(figsize=(10, 6))
    plt.plot(df["Q"], df["intensity"], "b-", linewidth=1)
    plt.xlabel("Q (Å⁻¹)")
    plt.ylabel("Intensity")
    plt.title("Diffraction Pattern")
    plt.grid(True, alpha=0.3)

    # Save the plot if requested
    if save:
        if filename is None:
            filename = "diffraction_pattern.png"

        output_path = Path(output_dir) / filename
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"Plot saved as '{output_path}'")

    if show:
        plt.show()
    else:
        plt.close()

    return True


def plot_multiple_data(
    datasets, labels, output_dir=".", filename=None, show=True, save=True
):
    """Create overlay plots comparing multiple diffraction datasets.

    Generates a single matplotlib figure showing multiple diffraction patterns
    on the same axes for direct comparison. Each dataset is plotted with a
    different color and includes a legend for identification.

    Args:
        datasets: List of DataFrames, each with 'Q' and 'intensity' columns
            containing diffraction data to compare.
        labels: List of strings providing labels for each dataset in the legend.
            Must have the same length as datasets.
        output_dir: Directory to save the plot file. Defaults to current
            directory.
        filename: Custom filename for saved plot. If None, uses default
            'diffraction_comparison.png'.
        show: If True, display the plot interactively using plt.show().
        save: If True, save the plot to file in the output directory.

    Returns:
        bool: True if plotting succeeded, False if matplotlib is not available.

    Raises:
        ImportError: Handled internally - prints error message if matplotlib
            or numpy is not installed.

    Plot Features:
        - Figure size: 12x8 inches for multi-dataset visibility
        - Color cycling using matplotlib's tab10 colormap
        - Semi-transparent lines (alpha=0.8) to show overlaps
        - Legend positioned outside plot area (upper left)
        - Dynamic title showing number of files compared
        - Tight layout with proper spacing
        - 150 DPI resolution for publication quality

    Example:
        >>> import pandas as pd
        >>> df1 = pd.DataFrame({"Q": [1, 2, 3], "intensity": [100, 200, 150]})
        >>> df2 = pd.DataFrame({"Q": [1, 2, 3], "intensity": [80, 180, 120]})
        >>> datasets = [df1, df2]
        >>> labels = ["Sample A", "Sample B"]
        >>> success = plot_multiple_data(datasets, labels, show=False)

    Note:
        - Requires both matplotlib and numpy for color cycling
        - Legend may extend beyond plot area for many datasets
        - Colors automatically cycle for up to 10 datasets
    """
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print(
            "Error: matplotlib is required for plotting. "
            "Install with 'pixi install matplotlib'"
        )
        return False

    # Create the plot
    plt.figure(figsize=(12, 8))

    # Color cycle for different datasets
    colors = plt.cm.tab10(np.linspace(0, 1, len(datasets)))

    for _i, (df, label, color) in enumerate(
        zip(datasets, labels, colors, strict=False)
    ):
        plt.plot(
            df["Q"], df["intensity"], color=color, linewidth=1, label=label, alpha=0.8
        )

    plt.xlabel("Q (Å⁻¹)")
    plt.ylabel("Intensity")
    plt.title(f"Diffraction Patterns Comparison ({len(datasets)} files)")
    plt.grid(True, alpha=0.3)
    plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()

    # Save the plot if requested
    if save:
        if filename is None:
            filename = "diffraction_comparison.png"

        output_path = Path(output_dir) / filename
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"Plot saved as '{output_path}'")

    if show:
        plt.show()
    else:
        plt.close()

    return True


def main():
    """Main entry point for the RoboMage command-line interface.

    Parses command-line arguments, loads diffraction data files, performs
    requested analysis and visualization operations, and handles errors
    gracefully. This function orchestrates the entire CLI workflow.

    Command-line Arguments Processing:
        - Handles both single-file and multi-file modes
        - Supports glob patterns for batch processing
        - Validates input files and provides helpful error messages
        - Manages output directory creation and file naming

    Workflow:
        1. Parse and validate command-line arguments
        2. Determine input files (single, multiple, or test data)
        3. Load all specified data files
        4. Display summary information if requested
        5. Generate plots if requested (single or comparison mode)
        6. Handle errors and provide user-friendly messages

    Returns:
        int: Exit code (0 for success, 1 for error) suitable for sys.exit().

    Error Handling:
        - File not found errors with helpful messages
        - matplotlib import errors with installation instructions
        - Invalid file format errors with format requirements
        - Graceful degradation when optional features unavailable

    Examples:
        The function is typically called via:
        >>> if __name__ == "__main__":
        ...     sys.exit(main())

        Command-line usage examples:
        $ python -m robomage test --info --plot
        $ python -m robomage sample.chi --save-plot result.png
        $ python -m robomage --files *.chi --output plots/ --verbose

    Note:
        This function uses the legacy data_io interface. Future versions
        may migrate to the modern data.loaders API for enhanced validation
        and functionality.
    """
    parser = argparse.ArgumentParser(
        description="RoboMage: Automated powder diffraction analysis framework"
    )
    parser.add_argument(
        "input_file",
        nargs="?",  # Single optional file
        help=(
            "Input data file to process (.chi format), or 'test' to use "
            "built-in test data"
        ),
    )
    parser.add_argument(
        "--files",
        "-f",
        nargs="+",  # One or more files required when used
        help=(
            "Process multiple files for comparison. Supports glob patterns like '*.chi'"
        ),
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output directory (default: current directory)",
        default=".",
    )
    parser.add_argument("--config", "-c", help="Configuration file path")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )
    parser.add_argument(
        "--info", "-i", action="store_true", help="Show data summary information"
    )
    parser.add_argument(
        "--plot",
        "-p",
        action="store_true",
        help="Display an interactive plot of the data (no file saved)",
    )
    parser.add_argument(
        "--save-plot",
        metavar="FILENAME",
        help="Save plot to file with custom filename (no interactive display)",
    )

    args = parser.parse_args()

    # Determine which files to process
    if args.files:
        # Use --files option (multi-file mode)
        input_files = []
        for pattern in args.files:
            if pattern.lower() == "test":
                input_files.append("test")
            else:
                # Handle glob patterns
                from glob import glob

                matches = glob(pattern)
                if matches:
                    input_files.extend(matches)
                else:
                    # If no glob matches, treat as literal filename
                    input_files.append(pattern)

        if not input_files:
            print("No files found matching the specified patterns.")
            return 1
    elif args.input_file:
        # Single file mode
        input_files = [args.input_file]
    else:
        print(
            "No input specified. Use a single file argument, 'test', or --files option."
        )
        print("Run with --help for usage information.")
        return 1

    try:
        # Load data from all files
        datasets = []
        labels = []

        for input_file in input_files:
            if input_file.lower() == "test":
                if args.verbose:
                    print("Loading built-in SRM 660b test data...")
                df = load_test_data()
                labels.append("SRM 660b (test)")
            else:
                if args.verbose:
                    print(f"Loading data from: {input_file}")
                df = load_chi_file(input_file)
                # Use just the filename (without path) as label
                labels.append(Path(input_file).name)

            datasets.append(df)

        # Show basic info
        total_points = sum(len(df) for df in datasets)
        print(f"Loaded {len(datasets)} file(s) with {total_points} total data points")

        # Show detailed info if requested
        if args.info or args.verbose:
            print("\nData Summary:")
            for i, (df, label) in enumerate(zip(datasets, labels, strict=False)):
                info = get_data_info(df)
                print(f"  File {i + 1} ({label}):")
                print(f"    Points: {len(df)}")
                print(
                    f"    Q range: {info['q_range'][0]:.3f} - "
                    f"{info['q_range'][1]:.3f} Å⁻¹"
                )
                print(
                    f"    Intensity range: {info['intensity_range'][0]:.1f} - "
                    f"{info['intensity_range'][1]:.1f}"
                )

        if args.verbose:
            print(f"Output directory: {args.output}")
            if args.config:
                print(f"Using config: {args.config}")

        # Handle plotting
        if args.plot or args.save_plot:
            if args.verbose:
                print("\nCreating plot...")

            if len(datasets) == 1:
                # Single file - use original plotting function
                df = datasets[0]
                if args.save_plot:
                    success = plot_data(
                        df, output_dir=args.output, filename=args.save_plot, show=False
                    )
                else:
                    success = plot_data(
                        df, output_dir=args.output, filename=None, show=True, save=False
                    )
            else:
                # Multiple files - use multi-dataset plotting
                if args.save_plot:
                    success = plot_multiple_data(
                        datasets,
                        labels,
                        output_dir=args.output,
                        filename=args.save_plot,
                        show=False,
                    )
                else:
                    success = plot_multiple_data(
                        datasets,
                        labels,
                        output_dir=args.output,
                        filename=None,
                        show=True,
                        save=False,
                    )

            if not success:
                return 1

        # TODO: Add your actual processing logic here
        print("RoboMage processing complete!")
        return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
