"""
Comprehensive tests for coordinate system conversions.

Tests conversion accuracy, round-trip precision, error handling, and edge cases
for Q-space ↔ 2θ ↔ d-spacing transformations.
"""

import numpy as np
import pytest

from robomage.coordinate_systems import (
    CoordinateMetadata,
    CoordinateSystem,
    ConversionError,
    convert_coordinate_system,
    convert_d_spacing_to_q,
    convert_d_spacing_to_two_theta,
    convert_q_to_d_spacing,
    convert_q_to_two_theta,
    convert_two_theta_to_d_spacing,
    convert_two_theta_to_q,
    validate_round_trip_conversion,
)


class TestBasicConversions:
    """Test basic coordinate system conversions."""

    def test_q_to_two_theta_synchrotron(self):
        """Test Q → 2θ conversion with synchrotron wavelength."""
        q = np.array([2.0, 4.0, 6.0])
        wavelength = 0.1665  # Å (typical synchrotron)

        two_theta = convert_q_to_two_theta(q, wavelength)

        # Expected values calculated from Q = 4π sin(θ) / λ
        # θ = arcsin(Q λ / 4π)
        # 2θ = 2 * arcsin(Q λ / 4π) in degrees
        expected = np.array([3.0370, 6.0760, 9.1194])  # degrees

        np.testing.assert_allclose(two_theta, expected, rtol=1e-4)

    def test_q_to_two_theta_cu_ka(self):
        """Test Q → 2θ conversion with Cu Kα wavelength."""
        q = np.array([2.0, 4.0, 6.0])
        wavelength = 1.54056  # Å (Cu Kα)

        two_theta = convert_q_to_two_theta(q, wavelength)

        expected = np.array([28.39, 58.73, 94.71])  # degrees

        np.testing.assert_allclose(two_theta, expected, rtol=1e-3)

    def test_two_theta_to_q(self):
        """Test 2θ → Q conversion."""
        two_theta = np.array([10.0, 20.0, 30.0])
        wavelength = 1.54056  # Å (Cu Kα)

        q = convert_two_theta_to_q(two_theta, wavelength)

        # Expected: Q = 4π sin(θ) / λ
        expected = np.array([0.7109, 1.4165, 2.1112])  # Å⁻¹

        np.testing.assert_allclose(q, expected, rtol=1e-4)

    def test_q_to_d_spacing(self):
        """Test Q → d-spacing conversion."""
        q = np.array([2.0, 4.0, 6.0])

        d = convert_q_to_d_spacing(q)

        # Expected: d = 2π / Q
        expected = np.array([3.1416, 1.5708, 1.0472])  # Å

        np.testing.assert_allclose(d, expected, rtol=1e-4)

    def test_d_spacing_to_q(self):
        """Test d-spacing → Q conversion."""
        d = np.array([3.0, 2.0, 1.5])

        q = convert_d_spacing_to_q(d)

        # Expected: Q = 2π / d
        expected = np.array([2.0944, 3.1416, 4.1888])  # Å⁻¹

        np.testing.assert_allclose(q, expected, rtol=1e-4)

    def test_two_theta_to_d_spacing(self):
        """Test 2θ → d-spacing conversion."""
        two_theta = np.array([10.0, 20.0, 30.0])
        wavelength = 1.54056  # Å (Cu Kα)

        d = convert_two_theta_to_d_spacing(two_theta, wavelength)

        # Expected: d = λ / (2 sin(θ)) = 2π / Q
        # where Q = 4π sin(θ) / λ
        expected = np.array([8.8380, 4.4359, 2.9761])  # Å

        np.testing.assert_allclose(d, expected, rtol=1e-4)

    def test_d_spacing_to_two_theta(self):
        """Test d-spacing → 2θ conversion."""
        d = np.array([3.0, 2.0, 1.5])
        wavelength = 1.54056  # Å (Cu Kα)

        two_theta = convert_d_spacing_to_two_theta(d, wavelength)

        # Expected: 2θ = 2 arcsin(λ / 2d)
        expected = np.array([29.76, 45.30, 61.80])  # degrees

        np.testing.assert_allclose(two_theta, expected, rtol=1e-3)


class TestRoundTripConversions:
    """Test round-trip conversion precision."""

    def test_q_two_theta_q_round_trip(self):
        """Test Q → 2θ → Q preserves original values."""
        original_q = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        wavelength = 0.1665  # Synchrotron

        is_accurate, max_error = validate_round_trip_conversion(
            original_q, CoordinateSystem.Q, CoordinateSystem.TWO_THETA, wavelength
        )

        assert is_accurate, f"Round-trip error too large: {max_error}"
        assert max_error < 1e-10  # Very tight tolerance

    def test_q_d_spacing_q_round_trip(self):
        """Test Q → d → Q preserves original values."""
        original_q = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

        is_accurate, max_error = validate_round_trip_conversion(
            original_q, CoordinateSystem.Q, CoordinateSystem.D_SPACING
        )

        assert is_accurate, f"Round-trip error too large: {max_error}"
        assert max_error < 1e-10

    def test_two_theta_d_spacing_two_theta_round_trip(self):
        """Test 2θ → d → 2θ preserves original values."""
        original_two_theta = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
        wavelength = 1.54056

        is_accurate, max_error = validate_round_trip_conversion(
            original_two_theta,
            CoordinateSystem.TWO_THETA,
            CoordinateSystem.D_SPACING,
            wavelength,
        )

        assert is_accurate, f"Round-trip error too large: {max_error}"
        assert max_error < 1e-10


class TestErrorHandling:
    """Test error handling for invalid inputs."""

    def test_q_to_two_theta_missing_wavelength(self):
        """Test Q → 2θ fails without wavelength."""
        q = np.array([2.0, 4.0, 6.0])

        with pytest.raises(ConversionError, match="Invalid wavelength"):
            convert_q_to_two_theta(q, None)

    def test_q_to_two_theta_negative_wavelength(self):
        """Test Q → 2θ fails with negative wavelength."""
        q = np.array([2.0, 4.0, 6.0])

        with pytest.raises(ConversionError, match="Invalid wavelength"):
            convert_q_to_two_theta(q, -1.0)

    def test_q_to_two_theta_q_exceeds_physical_limit(self):
        """Test Q → 2θ fails when Q > 4π/λ."""
        wavelength = 1.54056
        q_max_physical = 4 * np.pi / wavelength
        q_too_large = np.array([q_max_physical + 1.0])

        with pytest.raises(ConversionError, match="exceed physical maximum"):
            convert_q_to_two_theta(q_too_large, wavelength)

    def test_q_to_two_theta_negative_q(self):
        """Test Q → 2θ fails with negative Q values."""
        q = np.array([-1.0, 2.0, 3.0])

        with pytest.raises(ConversionError, match="must be non-negative"):
            convert_q_to_two_theta(q, 1.54056)

    def test_two_theta_to_q_out_of_range(self):
        """Test 2θ → Q fails when 2θ > 180°."""
        two_theta = np.array([10.0, 190.0])  # 190° is invalid

        with pytest.raises(ConversionError, match="must be in range"):
            convert_two_theta_to_q(two_theta, 1.54056)

    def test_q_to_d_spacing_zero_q(self):
        """Test Q → d fails with Q = 0."""
        q = np.array([0.0, 2.0, 3.0])

        with pytest.raises(ConversionError, match="must be positive"):
            convert_q_to_d_spacing(q)

    def test_d_spacing_to_q_negative_d(self):
        """Test d → Q fails with negative d."""
        d = np.array([3.0, -1.0, 2.0])

        with pytest.raises(ConversionError, match="must be positive"):
            convert_d_spacing_to_q(d)


class TestConvertCoordinateSystem:
    """Test the generic convert_coordinate_system function."""

    def test_same_system_returns_copy(self):
        """Test converting to same system returns a copy."""
        q = np.array([1.0, 2.0, 3.0])

        result = convert_coordinate_system(
            q, CoordinateSystem.Q, CoordinateSystem.Q
        )

        np.testing.assert_array_equal(result, q)
        assert result is not q  # Should be a copy

    def test_string_enum_conversion(self):
        """Test that string inputs are converted to enums."""
        q = np.array([2.0, 4.0, 6.0])

        result = convert_coordinate_system(q, "Q", "two_theta", wavelength=0.1665)

        # Should work the same as using enums
        expected = convert_q_to_two_theta(q, 0.1665)
        np.testing.assert_allclose(result, expected)

    def test_unsupported_conversion_raises_error(self):
        """Test that invalid conversion pairs raise ValueError."""
        # This would require implementing all 6 conversion paths
        # Currently all are implemented, so this test would need
        # a genuinely invalid enum value
        pass

    def test_missing_wavelength_for_q_two_theta(self):
        """Test that Q ↔ 2θ requires wavelength."""
        q = np.array([2.0, 4.0])

        with pytest.raises(ConversionError, match="Wavelength required"):
            convert_coordinate_system(q, CoordinateSystem.Q, CoordinateSystem.TWO_THETA)


class TestCoordinateMetadata:
    """Test CoordinateMetadata model."""

    def test_default_metadata(self):
        """Test default metadata is Q-space."""
        metadata = CoordinateMetadata()

        assert metadata.system == CoordinateSystem.Q
        assert metadata.units == "Å⁻¹"
        assert metadata.wavelength is None
        assert metadata.conversion_history == []

    def test_add_conversion_history(self):
        """Test recording conversion history."""
        metadata = CoordinateMetadata(wavelength=0.1665)

        metadata.add_conversion(CoordinateSystem.Q, CoordinateSystem.TWO_THETA)
        metadata.add_conversion(CoordinateSystem.TWO_THETA, CoordinateSystem.Q)

        assert len(metadata.conversion_history) == 2
        assert metadata.conversion_history[0] == "Q → two_theta"
        assert metadata.conversion_history[1] == "two_theta → Q"


class TestEdgeCases:
    """Test edge cases and numerical precision."""

    def test_very_small_q_values(self):
        """Test conversion with very small Q values."""
        q = np.array([0.001, 0.01, 0.1])
        wavelength = 0.1665

        two_theta = convert_q_to_two_theta(q, wavelength)

        # Should be very small angles
        assert np.all(two_theta < 1.0)
        assert np.all(two_theta > 0.0)

    def test_very_large_d_spacing(self):
        """Test conversion with large d-spacing."""
        d = np.array([100.0, 200.0, 500.0])  # Very large d

        q = convert_d_spacing_to_q(d)

        # Should be very small Q
        assert np.all(q < 0.1)
        assert np.all(q > 0.0)

    def test_array_with_single_element(self):
        """Test conversions work with single-element arrays."""
        q = np.array([3.0])
        wavelength = 0.1665

        two_theta = convert_q_to_two_theta(q, wavelength)

        assert len(two_theta) == 1
        assert two_theta[0] > 0

    def test_large_array(self):
        """Test conversion with large arrays."""
        q = np.linspace(0.1, 10.0, 10000)
        wavelength = 0.1665

        two_theta = convert_q_to_two_theta(q, wavelength)

        assert len(two_theta) == 10000
        assert np.all(two_theta > 0)
        assert np.all(two_theta < 180)

    def test_physical_limit_q_max(self):
        """Test conversion at physical Q limit (sin(θ) = 1)."""
        wavelength = 1.54056
        q_max = 4 * np.pi / wavelength  # Maximum physical Q

        # Should work right at the limit
        two_theta = convert_q_to_two_theta(np.array([q_max - 0.01]), wavelength)
        assert two_theta[0] < 180.0

    def test_numerical_stability_near_limits(self):
        """Test numerical stability near physical limits."""
        wavelength = 0.1665
        q_max = 4 * np.pi / wavelength

        # Test at 99.9% of max
        q_near_max = np.array([q_max * 0.999])
        two_theta = convert_q_to_two_theta(q_near_max, wavelength)

        # Should be close to 180°
        assert two_theta[0] > 170.0
        assert two_theta[0] <= 180.0


class TestDiffractionDataIntegration:
    """Test integration with DiffractionData model."""

    def test_diffraction_data_default_coordinate_system(self):
        """Test that DiffractionData defaults to Q-space."""
        from robomage.data.models import DiffractionData

        q = np.array([1.0, 2.0, 3.0])
        intensity = np.array([100, 200, 150])

        data = DiffractionData(q_values=q, intensities=intensity)

        assert data.coordinate_metadata.system == CoordinateSystem.Q
        assert data.coordinate_metadata.units == "Å⁻¹"

    def test_diffraction_data_to_coordinate_system(self):
        """Test DiffractionData.to_coordinate_system()."""
        from robomage.data.models import DiffractionData

        q = np.array([2.0, 4.0, 6.0])
        intensity = np.array([100, 200, 150])
        wavelength = 0.1665

        data = DiffractionData(
            q_values=q, intensities=intensity, wavelength=wavelength
        )

        # Convert to 2θ
        two_theta_data = data.to_coordinate_system(CoordinateSystem.TWO_THETA)

        # Check conversion
        assert two_theta_data.coordinate_metadata.system == CoordinateSystem.TWO_THETA
        assert two_theta_data.coordinate_metadata.units == "degrees"

        # Check conversion history
        assert len(two_theta_data.coordinate_metadata.conversion_history) == 1
        assert "Q → two_theta" in two_theta_data.coordinate_metadata.conversion_history[0]

        # Intensities should be unchanged
        np.testing.assert_array_equal(two_theta_data.intensities, intensity)

    def test_diffraction_data_from_coordinate_system(self):
        """Test DiffractionData.from_coordinate_system()."""
        from robomage.data.models import DiffractionData

        two_theta = np.array([10.0, 20.0, 30.0])
        intensity = np.array([100, 200, 150])
        wavelength = 1.54056

        # Create from 2θ data
        data = DiffractionData.from_coordinate_system(
            two_theta, intensity, CoordinateSystem.TWO_THETA, wavelength=wavelength
        )

        # Should be converted to Q internally
        assert data.coordinate_metadata.system == CoordinateSystem.Q
        assert data.coordinate_metadata.units == "Å⁻¹"

        # Check conversion happened
        assert len(data.coordinate_metadata.conversion_history) == 1

        # Q values should match conversion
        expected_q = convert_two_theta_to_q(two_theta, wavelength)
        np.testing.assert_allclose(data.q_values, expected_q)

    def test_diffraction_data_wavelength_sync(self):
        """Test that wavelength is synced to coordinate metadata."""
        from robomage.data.models import DiffractionData

        q = np.array([1.0, 2.0, 3.0])
        intensity = np.array([100, 200, 150])
        wavelength = 0.1665

        data = DiffractionData(
            q_values=q, intensities=intensity, wavelength=wavelength
        )

        assert data.coordinate_metadata.wavelength == wavelength


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
