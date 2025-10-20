import argparse
import sys
from pathlib import Path

from .data_io import get_data_info, load_chi_file, load_test_data


def plot_data(df, output_dir=".", filename=None, show=True, save=True):
    """
    Create a plot of the diffraction data.

    Args:
        df: DataFrame with Q and intensity columns
        output_dir: Directory to save the plot
        filename: Optional custom filename for the plot
        show: Whether to display the plot interactively
        save: Whether to save the plot to file
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
    """
    Create a plot of multiple diffraction datasets on the same axes.

    Args:
        datasets: List of DataFrames with Q and intensity columns
        labels: List of labels for each dataset
        output_dir: Directory to save the plot
        filename: Optional custom filename for the plot
        show: Whether to display the plot interactively
        save: Whether to save the plot to file
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
