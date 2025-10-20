#!/usr/bin/env python3
"""Comprehensive tutorial for loading and analyzing diffraction data with RoboMage.

This example script demonstrates the key features of RoboMage for powder diffraction
data analysis. It shows both the modern API (recommended for new projects) and the
legacy DataFrame-based API (for compatibility with existing code).

What you'll learn:
    - How to load test data and real diffraction files
    - Accessing statistical properties and quality metrics
    - Creating publication-quality plots
    - Converting between different data formats
    - Error handling and validation patterns

Requirements:
    - matplotlib (for plotting): pixi install matplotlib
    - RoboMage with all dependencies: pixi install

Usage:
    python examples/load_data_example.py

The script will:
    1. Load SRM 660b test data using both APIs
    2. Display comprehensive data statistics
    3. Create and save a publication-quality plot
    4. Demonstrate data manipulation operations
    5. Show error handling patterns

Output files created:
    - diffraction_pattern_legacy.png (legacy API example)
    - diffraction_pattern_modern.png (modern API example)
    - comparison_plot.png (side-by-side API comparison)
"""

import matplotlib.pyplot as plt
import numpy as np

# Modern API (recommended for new projects)
from robomage.data import DiffractionData
from robomage.data import load_test_data as load_test_modern

# Legacy API (for compatibility with existing pandas workflows)
from robomage.data_io import get_data_info
from robomage.data_io import load_test_data as load_test_legacy


def demonstrate_modern_api():
    """Demonstrate the modern RoboMage API with validated data structures."""
    print("\n" + "=" * 60)
    print("MODERN API EXAMPLE (Recommended for new projects)")
    print("=" * 60)

    # Load test data using modern API
    print("Loading SRM 660b test data with modern API...")
    data = load_test_modern()

    print(f"✓ Loaded DiffractionData object with {len(data.q_values)} points")
    print(f"✓ Filename: {data.filename}")
    is_sorted = np.all(np.diff(data.q_values) >= 0)
    print(f"✓ Data automatically sorted by Q values: {is_sorted}")

    # Access rich statistical properties
    stats = data.statistics
    print("\n📊 Statistical Properties:")
    print(f"  Q range: {stats.q_range[0]:.3f} - {stats.q_range[1]:.3f} Å⁻¹")
    print(f"  Number of points: {stats.num_points}")
    print(f"  Average Q step: {stats.q_step_mean:.6f} Å⁻¹")
    print(f"  Q step uniformity (std): {stats.q_step_std:.6f} Å⁻¹")
    int_min, int_max = stats.intensity_range
    print(f"  Intensity range: {int_min:.1f} - {int_max:.1f}")
    print(f"  Mean intensity: {stats.intensity_mean:.1f} ± {stats.intensity_std:.1f}")

    # Demonstrate data operations
    print("\n🔧 Data Operations:")
    trimmed = data.trim_q_range(q_min=2.0, q_max=8.0)
    print(f"  Trimmed to Q=[2.0, 8.0]: {len(trimmed.q_values)} points")

    # Convert to DataFrame for pandas operations if needed
    df = data.to_dataframe()
    print(f"  Converted to DataFrame: {df.shape} (rows, cols)")

    # Create publication-quality plot
    print("\n📈 Creating modern API plot...")
    plt.figure(figsize=(10, 6))
    plt.plot(data.q_values, data.intensities, "b-", linewidth=1, alpha=0.8)
    plt.xlabel("Q (Å⁻¹)", fontsize=12)
    plt.ylabel("Intensity (arbitrary units)", fontsize=12)
    plt.title(
        "SRM 660b LaB₆ Diffraction Pattern (Modern API)", fontsize=14, fontweight="bold"
    )
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    # Save the plot
    plt.savefig("diffraction_pattern_modern.png", dpi=150, bbox_inches="tight")
    print("✓ Plot saved as 'diffraction_pattern_modern.png'")
    plt.close()

    return data


def demonstrate_legacy_api():
    """Demonstrate the legacy DataFrame-based API for compatibility."""
    print("\n" + "=" * 60)
    print("LEGACY API EXAMPLE (For compatibility with existing code)")
    print("=" * 60)

    # Load test data using legacy API
    print("Loading SRM 660b test data with legacy API...")
    df = load_test_legacy()

    print(f"✓ Loaded pandas DataFrame with {len(df)} rows")
    print(f"✓ Columns: {list(df.columns)}")

    # Get summary information using legacy function
    info = get_data_info(df)

    print("\n📊 Legacy Statistics:")
    print(f"  Number of points: {info['num_points']}")
    print(f"  Q range: {info['q_range'][0]:.3f} - {info['q_range'][1]:.3f} Å⁻¹")
    print(f"  Average Q step: {info['q_step_mean']:.6f} Å⁻¹")
    int_range = info["intensity_range"]
    print(f"  Intensity range: {int_range[0]:.1f} - {int_range[1]:.1f}")
    print(f"  Mean intensity: {info['intensity_mean']:.1f}")

    # Show pandas DataFrame operations
    print("\n🐼 Pandas Operations:")
    print("First 3 data points:")
    print(df.head(3).to_string(index=False))
    print("Last 3 data points:")
    print(df.tail(3).to_string(index=False))

    # Create legacy-style plot
    print("\n📈 Creating legacy API plot...")
    plt.figure(figsize=(10, 6))
    plt.plot(df["Q"], df["intensity"], "r-", linewidth=1, alpha=0.8)
    plt.xlabel("Q (Å⁻¹)", fontsize=12)
    plt.ylabel("Intensity", fontsize=12)
    plt.title(
        "SRM 660b Diffraction Pattern (Legacy API)", fontsize=14, fontweight="bold"
    )
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    # Save the plot
    plt.savefig("diffraction_pattern_legacy.png", dpi=150, bbox_inches="tight")
    print("✓ Plot saved as 'diffraction_pattern_legacy.png'")
    plt.close()

    return df


def create_comparison_plot(modern_data, legacy_df):
    """Create a side-by-side comparison of both API approaches."""
    print("\n📊 Creating API comparison plot...")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    # Modern API plot
    ax1.plot(
        modern_data.q_values, modern_data.intensities, "b-", linewidth=1, alpha=0.8
    )
    ax1.set_xlabel("Q (Å⁻¹)", fontsize=11)
    ax1.set_ylabel("Intensity", fontsize=11)
    ax1.set_title("Modern API\n(DiffractionData)", fontsize=12, fontweight="bold")
    ax1.grid(True, alpha=0.3)

    # Legacy API plot
    ax2.plot(legacy_df["Q"], legacy_df["intensity"], "r-", linewidth=1, alpha=0.8)
    ax2.set_xlabel("Q (Å⁻¹)", fontsize=11)
    ax2.set_ylabel("Intensity", fontsize=11)
    ax2.set_title("Legacy API\n(pandas DataFrame)", fontsize=12, fontweight="bold")
    ax2.grid(True, alpha=0.3)

    plt.suptitle(
        "RoboMage API Comparison: SRM 660b LaB₆", fontsize=14, fontweight="bold"
    )
    plt.tight_layout()

    plt.savefig("comparison_plot.png", dpi=150, bbox_inches="tight")
    print("✓ Comparison plot saved as 'comparison_plot.png'")
    plt.close()


def demonstrate_error_handling():
    """Show proper error handling patterns."""
    print("\n🚨 Error Handling Examples:")

    # Try to load a non-existent file
    try:
        from robomage.data import load_chi_file

        load_chi_file("nonexistent.chi")
    except FileNotFoundError as e:
        print(f"✓ Caught expected FileNotFoundError: {e}")

    # Show how modern API handles unsorted data
    try:
        # This actually works - DiffractionData auto-sorts data
        unsorted_data = DiffractionData.from_arrays(
            q_values=np.array([3.0, 2.0, 1.0]),  # Not sorted
            intensities=np.array([100, 200, 300]),
        )
        print("✓ Modern API auto-sorts unsorted Q values gracefully")
        print(f"  Sorted Q values: {unsorted_data.q_values}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")


def main():
    """Main tutorial function demonstrating RoboMage capabilities."""
    print("🔬 RoboMage Comprehensive Tutorial")
    print("Advanced Powder Diffraction Data Analysis")
    print("=" * 60)

    print("This tutorial demonstrates:")
    print("• Loading diffraction data with modern and legacy APIs")
    print("• Accessing statistical properties and quality metrics")
    print("• Creating publication-quality visualizations")
    print("• Converting between different data formats")
    print("• Proper error handling patterns")

    # Demonstrate both APIs
    modern_data = demonstrate_modern_api()
    legacy_df = demonstrate_legacy_api()

    # Create comparison visualization
    create_comparison_plot(modern_data, legacy_df)

    # Show error handling
    demonstrate_error_handling()

    print("\n🎉 Tutorial Complete!")
    print("Generated files:")
    print("  • diffraction_pattern_modern.png (modern API example)")
    print("  • diffraction_pattern_legacy.png (legacy API example)")
    print("  • comparison_plot.png (side-by-side comparison)")
    print("\nNext steps:")
    print("  • Explore the CLI: python -m robomage --help")
    print("  • Load your own .chi files with load_chi_file()")
    print("  • Check out the documentation in the source code")

    return 0


if __name__ == "__main__":
    main()
