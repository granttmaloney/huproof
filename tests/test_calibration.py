"""Tests for calibration utilities."""

from huproof.core.calibration import (
    calculate_l1_distance,
    average_features,
    calculate_adaptive_tau,
    calculate_template_quality,
)


def test_l1_distance() -> None:
    """Test L1 distance calculation."""
    vec1 = [10, 20, 30]
    vec2 = [12, 18, 32]
    assert calculate_l1_distance(vec1, vec2) == 6  # |10-12| + |20-18| + |30-32| = 2+2+2


def test_average_features() -> None:
    """Test feature averaging."""
    samples = [
        [10, 20, 30],
        [12, 18, 32],
        [11, 19, 31],
    ]
    avg = average_features(samples)
    assert avg == [11, 19, 31]  # Rounded averages


def test_calculate_adaptive_tau() -> None:
    """Test adaptive tau calculation."""
    template = [10, 20, 30]
    samples = [
        [12, 18, 32],  # distance: 6
        [11, 19, 31],  # distance: 3
        [13, 21, 29],  # distance: 5
    ]
    # Mean ~4.67, stddev ~1.25, so tau should be ~4.67 + 2*1.25 = ~7.17, but clamped to base 400
    tau = calculate_adaptive_tau(template, samples, base_tau=400)
    assert tau >= 400  # Should be at least base_tau
    
    # With lower base_tau, should use adaptive value
    tau2 = calculate_adaptive_tau(template, samples, base_tau=10)
    assert tau2 >= 10
    assert tau2 <= 20  # Reasonable upper bound for this test


def test_calculate_template_quality() -> None:
    """Test template quality calculation."""
    template = [10, 20, 30]
    samples = [
        [12, 18, 32],
        [11, 19, 31],
        [13, 21, 29],
    ]
    quality = calculate_template_quality(template, samples)
    assert "mean_distance" in quality
    assert "stddev_distance" in quality
    assert "consistency_score" in quality
    assert 0 <= quality["consistency_score"] <= 1

