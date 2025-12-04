"""
Coordinate System Contract - Integration Demo

This script demonstrates the coordinate system metadata contract in action.
It shows:
1. Creating data in different coordinate systems
2. Automatic conversion by the orchestrator
3. Metadata tracking and logging
4. Error handling for missing wavelength
"""

import asyncio
import logging
import numpy as np

from robomage.coordinate_systems import CoordinateSystem, convert_q_to_two_theta
from robomage.data.models import DiffractionData

# Set up logging to see conversion messages
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)


def demo_basic_conversions():
    """Demonstrate basic coordinate conversions."""
    print("\n" + "="*60)
    print("DEMO 1: Basic Coordinate Conversions")
    print("="*60)
    
    q = np.array([2.0, 4.0, 6.0])
    wavelength = 0.1665  # Synchrotron
    
    print(f"\nQ values: {q} Å⁻¹")
    print(f"Wavelength: {wavelength} Å")
    
    two_theta = convert_q_to_two_theta(q, wavelength)
    print(f"2θ values: {two_theta} degrees")
    
    # Show it's reversible
    from robomage.coordinate_systems import convert_two_theta_to_q
    q_back = convert_two_theta_to_q(two_theta, wavelength)
    print(f"Round-trip Q: {q_back} Å⁻¹")
    print(f"Round-trip error: {np.max(np.abs(q - q_back)):.2e}")


def demo_diffraction_data_conversion():
    """Demonstrate DiffractionData coordinate conversion."""
    print("\n" + "="*60)
    print("DEMO 2: DiffractionData Conversion")
    print("="*60)
    
    # Create Q-space data
    data_q = DiffractionData(
        q_values=np.array([2.0, 4.0, 6.0]),
        intensities=np.array([100, 200, 150]),
        wavelength=0.1665,
        filename="demo_sample.chi"
    )
    
    print(f"\nOriginal data:")
    print(f"  System: {data_q.coordinate_metadata.system.value}")
    print(f"  Units: {data_q.coordinate_metadata.units}")
    print(f"  Values: {data_q.q_values}")
    
    # Convert to 2θ
    data_2theta = data_q.to_coordinate_system(CoordinateSystem.TWO_THETA)
    
    print(f"\nConverted to 2θ:")
    print(f"  System: {data_2theta.coordinate_metadata.system.value}")
    print(f"  Units: {data_2theta.coordinate_metadata.units}")
    print(f"  Values: {data_2theta.q_values}")  # Now contains 2θ!
    print(f"  Conversion history: {data_2theta.coordinate_metadata.conversion_history}")
    
    # Intensities unchanged
    assert np.array_equal(data_q.intensities, data_2theta.intensities)
    print(f"  Intensities preserved: ✅")


def demo_from_coordinate_system():
    """Demonstrate creating DiffractionData from 2θ."""
    print("\n" + "="*60)
    print("DEMO 3: Create from 2θ Data")
    print("="*60)
    
    # Simulate loading 2θ data from file
    two_theta_values = np.array([10.0, 20.0, 30.0])
    intensities = np.array([100, 200, 150])
    wavelength = 1.54056  # Cu Kα
    
    print(f"\nInput 2θ data: {two_theta_values} degrees")
    
    # Create DiffractionData (automatically converts to Q)
    data = DiffractionData.from_coordinate_system(
        two_theta_values,
        intensities,
        CoordinateSystem.TWO_THETA,
        wavelength=wavelength
    )
    
    print(f"\nDiffractionData created:")
    print(f"  System: {data.coordinate_metadata.system.value}")  # Q
    print(f"  Q values: {data.q_values} Å⁻¹")
    print(f"  Conversion history: {data.coordinate_metadata.conversion_history}")


def demo_metadata_tracking():
    """Demonstrate metadata and history tracking."""
    print("\n" + "="*60)
    print("DEMO 4: Metadata Tracking")
    print("="*60)
    
    data = DiffractionData(
        q_values=np.array([2.0, 4.0, 6.0]),
        intensities=np.array([100, 200, 150]),
        wavelength=0.1665
    )
    
    print("\nPerforming conversions:")
    print(f"  Start: {data.coordinate_metadata.system.value}")
    
    # Q → 2θ
    data_2theta = data.to_coordinate_system(CoordinateSystem.TWO_THETA)
    print(f"  After Q→2θ: {data_2theta.coordinate_metadata.system.value}")
    print(f"    History: {data_2theta.coordinate_metadata.conversion_history}")
    
    # 2θ → d-spacing
    data_d = data_2theta.to_coordinate_system(CoordinateSystem.D_SPACING)
    print(f"  After 2θ→d: {data_d.coordinate_metadata.system.value}")
    print(f"    History: {data_d.coordinate_metadata.conversion_history}")
    
    # d → Q
    data_q_final = data_d.to_coordinate_system(CoordinateSystem.Q)
    print(f"  After d→Q: {data_q_final.coordinate_metadata.system.value}")
    print(f"    History: {data_q_final.coordinate_metadata.conversion_history}")
    
    # Verify round-trip accuracy
    error = np.max(np.abs(data.q_values - data_q_final.q_values))
    print(f"\nRound-trip error: {error:.2e}")
    print(f"Round-trip accurate: {'✅' if error < 1e-10 else '❌'}")


def demo_error_handling():
    """Demonstrate error handling."""
    print("\n" + "="*60)
    print("DEMO 5: Error Handling")
    print("="*60)
    
    # Test 1: Missing wavelength
    print("\n1. Attempting Q→2θ without wavelength:")
    data_no_wavelength = DiffractionData(
        q_values=np.array([2.0, 4.0, 6.0]),
        intensities=np.array([100, 200, 150])
    )
    
    try:
        data_no_wavelength.to_coordinate_system(CoordinateSystem.TWO_THETA)
        print("  ❌ Should have raised error!")
    except Exception as e:
        print(f"  ✅ Caught error: {str(e)[:100]}...")
    
    # Test 2: Invalid Q values
    print("\n2. Attempting conversion with invalid Q:")
    from robomage.coordinate_systems import ConversionError
    
    wavelength = 1.54056
    q_max_physical = 4 * np.pi / wavelength
    q_invalid = np.array([q_max_physical + 1.0])
    
    try:
        convert_q_to_two_theta(q_invalid, wavelength)
        print("  ❌ Should have raised error!")
    except ConversionError as e:
        print(f"  ✅ Caught error: {str(e)[:100]}...")


def demo_node_contract():
    """Demonstrate node coordinate requirements."""
    print("\n" + "="*60)
    print("DEMO 6: Node Coordinate Requirements")
    print("="*60)
    
    from robomage.workflow.nodes.registry import NodeRegistry
    
    # Show node requirements
    nodes_to_check = ['load_files', 'peak_analysis', 'gsasii_refinement']
    
    for node_type in nodes_to_check:
        metadata = NodeRegistry.get_metadata(node_type)
        if metadata and metadata.coordinate_requirements:
            req = metadata.coordinate_requirements
            print(f"\n{node_type}:")
            print(f"  Input:  {req.get('input_coordinates', 'any')}")
            print(f"  Output: {req.get('output_coordinates', 'same as input')}")
            print(f"  Needs wavelength: {req.get('requires_wavelength', False)}")


async def demo_orchestrator_conversion():
    """Demonstrate orchestrator automatic conversion."""
    print("\n" + "="*60)
    print("DEMO 7: Orchestrator Automatic Conversion")
    print("="*60)
    
    # Create test data in 2θ space
    two_theta_data = DiffractionData.from_coordinate_system(
        np.array([10.0, 20.0, 30.0]),
        np.array([100, 200, 150]),
        CoordinateSystem.TWO_THETA,
        wavelength=1.54056,
        filename="test_2theta.dat"
    )
    
    print("\nInput data:")
    print(f"  System: {two_theta_data.coordinate_metadata.system.value}")
    print(f"  Values: {two_theta_data.q_values[:3]} ... (Å⁻¹ after auto-conversion)")
    
    # The orchestrator would convert this to Q before passing to a node
    # that requires Q (demonstrated in unit tests)
    
    print("\nOrchestrator would automatically:")
    print("  1. Check node coordinate requirements")
    print("  2. Detect coordinate system mismatch")
    print("  3. Log conversion: 'Converting file.chi: two_theta → Q'")
    print("  4. Execute node with converted data")
    print("  5. Track conversion in metadata")
    
    print("\nSee tests/test_coordinate_systems.py for full integration tests")


def main():
    """Run all demos."""
    print("\n" + "="*70)
    print("COORDINATE SYSTEM METADATA CONTRACT - INTEGRATION DEMO")
    print("="*70)
    
    demo_basic_conversions()
    demo_diffraction_data_conversion()
    demo_from_coordinate_system()
    demo_metadata_tracking()
    demo_error_handling()
    demo_node_contract()
    asyncio.run(demo_orchestrator_conversion())
    
    print("\n" + "="*70)
    print("✅ ALL DEMOS COMPLETED SUCCESSFULLY")
    print("="*70)
    print("\nKey Takeaways:")
    print("  • Q-space is the canonical internal format")
    print("  • Conversions are automatic and logged")
    print("  • Complete metadata tracking and history")
    print("  • Clear error messages for missing wavelength")
    print("  • Nodes declare coordinate requirements")
    print("  • Round-trip conversions preserve precision")
    print("\nSee docs/COORDINATE-SYSTEM-QUICK-REF.md for API reference")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
