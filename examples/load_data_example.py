#!/usr/bin/env python3
"""
Example script showing how to load and examine diffraction data.
"""

from robomage.data_io import load_test_data, get_data_info, load_chi_file
import matplotlib.pyplot as plt


def main():
    print("RoboMage Data Loading Example")
    print("=" * 40)
    
    # Load the test data
    print("Loading SRM 660b test data...")
    df = load_test_data()
    
    # Get summary information
    info = get_data_info(df)
    
    print(f"\nData Summary:")
    print(f"  Number of points: {info['num_points']}")
    print(f"  Q range: {info['q_range'][0]:.3f} - {info['q_range'][1]:.3f} Å⁻¹")
    print(f"  Average Q step: {info['q_step_mean']:.6f} Å⁻¹")
    print(f"  Intensity range: {info['intensity_range'][0]:.1f} - {info['intensity_range'][1]:.1f}")
    print(f"  Mean intensity: {info['intensity_mean']:.1f}")
    
    # Show first few data points
    print(f"\nFirst 5 data points:")
    print(df.head())
    
    # Show last few data points  
    print(f"\nLast 5 data points:")
    print(df.tail())
    
    # Create a simple plot
    print(f"\nCreating plot...")
    plt.figure(figsize=(10, 6))
    plt.plot(df['Q'], df['intensity'], 'b-', linewidth=1)
    plt.xlabel('Q (Å⁻¹)')
    plt.ylabel('Intensity')
    plt.title('SRM 660b Diffraction Pattern')
    plt.grid(True, alpha=0.3)
    
    # Save the plot
    plt.savefig('diffraction_pattern.png', dpi=150, bbox_inches='tight')
    print("Plot saved as 'diffraction_pattern.png'")
    
    plt.show()


if __name__ == "__main__":
    main()