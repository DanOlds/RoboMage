"""
Example: Loading and Working with XY Files in RoboMage

This example demonstrates how to load and analyze .xy files using RoboMage's
data loading functionality. XY files are a common two-column format for
diffraction data.
"""

from robomage.data import load_diffraction_file, load_xy_file
from robomage.data_io import load_diffraction_file_df
from pathlib import Path


def main():
    """Demonstrate XY file loading capabilities."""
    
    # Check if example .xy files exist in the project root
    project_root = Path(__file__).parent.parent
    xy_files = [
        project_root / "detector_5_roi_175-181_18-218_frames_17847-17978.xy",
        project_root / "detector_5_roi_190-196_19-219_frames_17847-17978.xy"
    ]
    
    available_files = [f for f in xy_files if f.exists()]
    
    if not available_files:
        print("No .xy example files found in project root.")
        print("This example requires the detector .xy files to be present.")
        return
    
    print("🔬 RoboMage XY File Loading Example")
    print("=" * 50)
    
    # Example 1: Modern API with validation
    print("\n📊 Method 1: Modern API (Recommended)")
    print("-" * 40)
    
    for xy_file in available_files:
        print(f"\nLoading: {xy_file.name}")
        
        # Load using the modern API with validation
        data = load_diffraction_file(xy_file)
        
        # Display comprehensive information
        stats = data.statistics
        print(f"  📈 Data points: {stats.num_points:,}")
        print(f"  📏 Q range: {stats.q_range[0]:.3f} to {stats.q_range[1]:.3f} Å⁻¹")
        print(f"  💡 Intensity range: {stats.intensity_range[0]:.0f} to {stats.intensity_range[1]:.0f}")
        print(f"  📊 Mean intensity: {stats.intensity_mean:.1f}")
        print(f"  📐 Q step uniformity: {(1 - stats.q_step_std/stats.q_step_mean)*100:.1f}%")
    
    # Example 2: Direct XY file loader
    print(f"\n🎯 Method 2: Direct XY Loader")
    print("-" * 40)
    
    xy_file = available_files[0]
    print(f"\nLoading: {xy_file.name}")
    
    # Load using the specific XY loader
    data = load_xy_file(xy_file)
    print(f"  ✅ Successfully loaded {data.statistics.num_points:,} points")
    print(f"  📁 Filename: {data.filename}")
    
    # Example 3: Legacy DataFrame API
    print(f"\n📋 Method 3: Legacy DataFrame API")
    print("-" * 40)
    
    print(f"\nLoading: {xy_file.name}")
    
    # Load using the legacy DataFrame API
    df = load_diffraction_file_df(xy_file)
    print(f"  📊 DataFrame shape: {df.shape}")
    print(f"  📝 Columns: {list(df.columns)}")
    print(f"  📈 Q range: {df['Q'].min():.3f} to {df['Q'].max():.3f} Å⁻¹")
    print(f"  💡 Intensity range: {df['intensity'].min():.0f} to {df['intensity'].max():.0f}")
    
    # Example 4: Comparing multiple files
    if len(available_files) >= 2:
        print(f"\n🔄 Method 4: Comparing Multiple Files")
        print("-" * 40)
        
        data1 = load_diffraction_file(available_files[0])
        data2 = load_diffraction_file(available_files[1])
        
        print(f"\nFile 1: {data1.filename}")
        print(f"  Mean intensity: {data1.statistics.intensity_mean:.1f}")
        
        print(f"\nFile 2: {data2.filename}")
        print(f"  Mean intensity: {data2.statistics.intensity_mean:.1f}")
        
        ratio = data2.statistics.intensity_mean / data1.statistics.intensity_mean
        print(f"\nIntensity ratio (File 2 / File 1): {ratio:.1f}x")
    
    # CLI Usage Examples
    print(f"\n🖥️  CLI Usage Examples")
    print("-" * 40)
    print("# Single file analysis:")
    print(f"pixi run python -m robomage {available_files[0].name} --info")
    print()
    print("# Multiple file comparison:")
    print("pixi run python -m robomage --files '*.xy' --info")
    print()
    print("# Dashboard with XY files:")
    print("pixi run dashboard")
    print("  # Then upload .xy files through the web interface")
    
    print(f"\n✅ Example completed successfully!")


if __name__ == "__main__":
    main()