"""
Test Dashboard Integration with Coordinate System Utilities

Verifies that dashboard plotting callbacks use the centralized coordinate
system utilities and produce identical results to the core conversion functions.
"""

import numpy as np
import pytest

from robomage.coordinate_systems import (
    convert_q_to_two_theta,
    convert_q_to_d_spacing,
)
from robomage.dashboard.callbacks.plotting import get_x_data


class TestDashboardCoordinateIntegration:
    """Test dashboard uses centralized coordinate system utilities."""

    def test_dashboard_uses_centralized_q_to_two_theta(self):
        """Dashboard Q→2θ conversion should match centralized utility."""
        q_values = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        wavelength = 0.1665  # Synchrotron default

        # Get dashboard conversion
        test_data = {"q": q_values.tolist(), "intensity": [100] * len(q_values)}
        wavelength_data = {"current_wavelength": wavelength}
        dashboard_2theta, label = get_x_data(test_data, "two_theta", wavelength_data)

        # Get centralized utility conversion
        utility_2theta = convert_q_to_two_theta(q_values, wavelength)

        # Should be identical
        np.testing.assert_array_almost_equal(
            dashboard_2theta,
            utility_2theta.tolist(),
            decimal=10,
            err_msg="Dashboard and utility Q→2θ conversions must match exactly",
        )

        assert label == "2θ (degrees)"

    def test_dashboard_uses_centralized_q_to_d_spacing(self):
        """Dashboard Q→d-spacing conversion should match centralized utility."""
        q_values = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

        # Get dashboard conversion
        test_data = {"q": q_values.tolist(), "intensity": [100] * len(q_values)}
        dashboard_d, label = get_x_data(test_data, "d_spacing", None)

        # Get centralized utility conversion
        utility_d = convert_q_to_d_spacing(q_values)

        # Should be identical
        np.testing.assert_array_almost_equal(
            dashboard_d,
            utility_d.tolist(),
            decimal=10,
            err_msg="Dashboard and utility Q→d conversions must match exactly",
        )

        assert label == "d-spacing (Å)"

    def test_dashboard_q_passthrough(self):
        """Dashboard should pass through Q values unchanged."""
        q_values = [1.0, 2.0, 3.0, 4.0, 5.0]
        test_data = {"q": q_values, "intensity": [100] * len(q_values)}

        dashboard_q, label = get_x_data(test_data, "q", None)

        assert dashboard_q == q_values
        assert label == "Q (Å⁻¹)"

    def test_dashboard_default_wavelength(self):
        """Dashboard should use default wavelength when not provided."""
        q_values = np.array([1.0, 2.0, 3.0])
        test_data = {"q": q_values.tolist(), "intensity": [100, 200, 150]}

        # No wavelength data provided
        dashboard_2theta, label = get_x_data(test_data, "two_theta", None)

        # Should use default synchrotron wavelength (0.1665 Å)
        expected_2theta = convert_q_to_two_theta(q_values, 0.1665)

        np.testing.assert_array_almost_equal(
            dashboard_2theta,
            expected_2theta.tolist(),
            decimal=10,
        )

    def test_dashboard_custom_wavelength(self):
        """Dashboard should use custom wavelength from store."""
        q_values = np.array([1.0, 2.0, 3.0])
        test_data = {"q": q_values.tolist(), "intensity": [100, 200, 150]}

        # Custom wavelength (e.g., Cu Kα)
        custom_wavelength = 1.5406
        wavelength_data = {"current_wavelength": custom_wavelength}

        dashboard_2theta, _ = get_x_data(test_data, "two_theta", wavelength_data)

        # Should use custom wavelength
        expected_2theta = convert_q_to_two_theta(q_values, custom_wavelength)

        np.testing.assert_array_almost_equal(
            dashboard_2theta,
            expected_2theta.tolist(),
            decimal=10,
        )

    def test_dashboard_handles_edge_cases(self):
        """Dashboard should handle edge cases like utility functions."""
        # Very small Q values
        q_small = np.array([0.01, 0.05, 0.1])
        test_data = {"q": q_small.tolist(), "intensity": [100, 200, 150]}

        dashboard_2theta, _ = get_x_data(test_data, "two_theta", None)
        expected_2theta = convert_q_to_two_theta(q_small, 0.1665)

        np.testing.assert_array_almost_equal(
            dashboard_2theta, expected_2theta.tolist(), decimal=10
        )

        # Large Q values (near physical limit)
        q_large = np.array([70.0, 71.0, 72.0])  # Near 4π/λ for λ=0.1665
        test_data = {"q": q_large.tolist(), "intensity": [100, 200, 150]}

        dashboard_2theta, _ = get_x_data(test_data, "two_theta", None)
        expected_2theta = convert_q_to_two_theta(q_large, 0.1665)

        np.testing.assert_array_almost_equal(
            dashboard_2theta, expected_2theta.tolist(), decimal=10
        )

    def test_dashboard_unknown_axis_defaults_to_q(self):
        """Dashboard should default to Q for unknown axis types."""
        q_values = [1.0, 2.0, 3.0]
        test_data = {"q": q_values, "intensity": [100, 200, 150]}

        # Unknown axis type
        dashboard_data, label = get_x_data(test_data, "invalid_axis", None)

        assert dashboard_data == q_values
        assert label == "Q (Å⁻¹)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
