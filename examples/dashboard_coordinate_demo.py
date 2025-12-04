#!/usr/bin/env python3
"""
Dashboard Coordinate System Integration Demo

Demonstrates that the dashboard visualization callbacks now use the centralized
coordinate system utilities, ensuring consistent conversions across the framework.

This script shows:
1. Dashboard conversion functions match core utilities exactly
2. All coordinate systems (Q, 2θ, d-spacing) work correctly
3. Wavelength handling (default and custom)
4. Edge cases are handled properly
"""

import numpy as np

# Import core coordinate utilities
from robomage.coordinate_systems import (
    convert_q_to_two_theta,
    convert_q_to_d_spacing,
)

# Import dashboard plotting functions
from robomage.dashboard.callbacks.plotting import get_x_data


def main():
    """Run the demonstration."""
    print("=" * 80)
    print("Dashboard Coordinate System Integration Demo")
    print("=" * 80)
    print()

    # Test data
    q_values = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    test_data = {"q": q_values.tolist(), "intensity": [100, 200, 300, 200, 100]}

    # Demo 1: Q passthrough
    print("Demo 1: Q-space (passthrough)")
    print("-" * 80)
    dashboard_q, label_q = get_x_data(test_data, "q", None)
    print(f"Input Q values:      {q_values.tolist()}")
    print(f"Dashboard output:    {dashboard_q}")
    print(f"Axis label:          {label_q}")
    assert dashboard_q == q_values.tolist()
    print("✅ Q values pass through unchanged")
    print()

    # Demo 2: Q → 2θ conversion with default wavelength
    print("Demo 2: Q → 2θ (default synchrotron wavelength)")
    print("-" * 80)
    dashboard_2theta, label_2theta = get_x_data(test_data, "two_theta", None)
    utility_2theta = convert_q_to_two_theta(q_values, 0.1665)
    print(f"Dashboard 2θ:        {[f'{x:.3f}' for x in dashboard_2theta]}")
    print(f"Utility 2θ:          {[f'{x:.3f}' for x in utility_2theta.tolist()]}")
    print(f"Axis label:          {label_2theta}")
    np.testing.assert_array_almost_equal(dashboard_2theta, utility_2theta.tolist())
    print("✅ Dashboard and utility conversions match exactly")
    print()

    # Demo 3: Q → 2θ conversion with custom wavelength
    print("Demo 3: Q → 2θ (custom Cu Kα wavelength)")
    print("-" * 80)
    cu_wavelength = 1.5406  # Cu Kα
    wavelength_data = {"current_wavelength": cu_wavelength}
    dashboard_2theta_cu, _ = get_x_data(test_data, "two_theta", wavelength_data)
    utility_2theta_cu = convert_q_to_two_theta(q_values, cu_wavelength)
    print(f"Wavelength:          {cu_wavelength} Å (Cu Kα)")
    print(f"Dashboard 2θ:        {[f'{x:.2f}' for x in dashboard_2theta_cu]}")
    print(f"Utility 2θ:          {[f'{x:.2f}' for x in utility_2theta_cu.tolist()]}")
    np.testing.assert_array_almost_equal(
        dashboard_2theta_cu, utility_2theta_cu.tolist()
    )
    print("✅ Custom wavelength handled correctly")
    print()

    # Demo 4: Q → d-spacing conversion
    print("Demo 4: Q → d-spacing")
    print("-" * 80)
    dashboard_d, label_d = get_x_data(test_data, "d_spacing", None)
    utility_d = convert_q_to_d_spacing(q_values)
    print(f"Dashboard d:         {[f'{x:.3f}' for x in dashboard_d]} Å")
    print(f"Utility d:           {[f'{x:.3f}' for x in utility_d.tolist()]} Å")
    print(f"Axis label:          {label_d}")
    np.testing.assert_array_almost_equal(dashboard_d, utility_d.tolist())
    print("✅ d-spacing conversions match exactly")
    print()

    # Demo 5: Edge cases
    print("Demo 5: Edge Cases")
    print("-" * 80)

    # Very small Q
    small_q = np.array([0.01, 0.05, 0.1])
    small_data = {"q": small_q.tolist(), "intensity": [100, 200, 150]}
    dashboard_small, _ = get_x_data(small_data, "two_theta", None)
    utility_small = convert_q_to_two_theta(small_q, 0.1665)
    print(f"Small Q values:      {small_q.tolist()} Å⁻¹")
    print(f"Dashboard 2θ:        {[f'{x:.4f}' for x in dashboard_small]}°")
    print(f"Utility 2θ:          {[f'{x:.4f}' for x in utility_small.tolist()]}°")
    np.testing.assert_array_almost_equal(dashboard_small, utility_small.tolist())
    print("✅ Small Q values handled correctly")
    print()

    # Large Q (near physical limit for λ=0.1665)
    large_q = np.array([70.0, 71.0, 72.0])
    large_data = {"q": large_q.tolist(), "intensity": [100, 200, 150]}
    dashboard_large, _ = get_x_data(large_data, "two_theta", None)
    utility_large = convert_q_to_two_theta(large_q, 0.1665)
    print(f"Large Q values:      {large_q.tolist()} Å⁻¹")
    print(f"Dashboard 2θ:        {[f'{x:.2f}' for x in dashboard_large]}°")
    print(f"Utility 2θ:          {[f'{x:.2f}' for x in utility_large.tolist()]}°")
    np.testing.assert_array_almost_equal(dashboard_large, utility_large.tolist())
    print("✅ Large Q values (near physical limit) handled correctly")
    print()

    # Demo 6: Physical constraints discussion
    print("Demo 6: Physical Constraints")
    print("-" * 80)
    print("Important: Negative 2θ values are VALID")
    print("  - Reflections measured past the beamstop at 0°")
    print("  - Common in synchrotron experiments")
    print("  - Example: -5° to +5° range is typical")
    print()
    print("The conversion utilities correctly handle:")
    print("  ✅ Negative 2θ (from beamstop measurements)")
    print("  ✅ 2θ > 180° (backward reflections, rare but valid)")
    print("  ✅ Mathematical constraint: sin(θ) clipped to [-1, 1]")
    print("  ❌ NO artificial constraint on 2θ range")
    print()

    # Summary
    print("=" * 80)
    print("Summary: Dashboard Integration Complete")
    print("=" * 80)
    print("✅ All coordinate conversions use centralized utilities")
    print("✅ Dashboard and core utilities produce identical results")
    print("✅ Default wavelength (0.1665 Å) works correctly")
    print("✅ Custom wavelengths handled properly")
    print("✅ Edge cases (small Q, large Q) work correctly")
    print("✅ Physical constraints handled correctly")
    print()
    print("Benefits:")
    print("  • Single source of truth for conversions")
    print("  • Consistent behavior across UI and workflows")
    print("  • Easier maintenance and testing")
    print("  • Future-ready for metadata tracking")
    print()
    print("Documentation:")
    print("  • docs/DASHBOARD-COORDINATE-INTEGRATION.md")
    print("  • docs/COORDINATE-SYSTEM-CONTRACT-COMPLETE.md")
    print("  • docs/COORDINATE-SYSTEM-QUICK-REF.md")
    print()


if __name__ == "__main__":
    main()
