"""Template calibration and adaptive threshold calculation."""

from typing import Sequence

from .logging import get_logger

logger = get_logger()


def calculate_l1_distance(features1: Sequence[int], features2: Sequence[int]) -> int:
    """Calculate L1 (Manhattan) distance between two feature vectors.
    
    Parameters
    ----------
    features1: Sequence[int]
        First feature vector
    features2: Sequence[int]
        Second feature vector
        
    Returns
    -------
    int
        Sum of absolute differences
    """
    if len(features1) != len(features2):
        raise ValueError("Feature vectors must have same length")
    return sum(abs(a - b) for a, b in zip(features1, features2))


def average_features(feature_vectors: Sequence[Sequence[int]]) -> list[int]:
    """Average multiple feature vectors to create a more stable template.
    
    Parameters
    ----------
    feature_vectors: Sequence[Sequence[int]]
        List of feature vectors to average
        
    Returns
    -------
    list[int]
        Averaged feature vector (rounded to integers)
    """
    if not feature_vectors:
        raise ValueError("At least one feature vector required")
    
    n = len(feature_vectors)
    length = len(feature_vectors[0])
    
    # Ensure all vectors have same length
    for vec in feature_vectors:
        if len(vec) != length:
            raise ValueError("All feature vectors must have same length")
    
    # Average each position
    averaged = []
    for i in range(length):
        avg = sum(vec[i] for vec in feature_vectors) / n
        averaged.append(int(round(avg)))
    
    return averaged


def calculate_adaptive_tau(
    template: Sequence[int],
    samples: Sequence[Sequence[int]],
    base_tau: int = 400,
    multiplier: float = 2.0,
) -> int:
    """Calculate adaptive threshold (tau) based on sample variance.
    
    Uses mean + multiplier * stddev to set threshold that accommodates
    natural typing variation while rejecting impostors.
    
    Parameters
    ----------
    template: Sequence[int]
        Reference template vector
    samples: Sequence[Sequence[int]]
        Sample feature vectors from enrollment
    base_tau: int
        Minimum threshold (fallback if variance is too low)
    multiplier: float
        Standard deviation multiplier (higher = more lenient)
        
    Returns
    -------
    int
        Adaptive threshold value
    """
    if not samples:
        logger.warning("no_samples_for_tau", using_base=base_tau)
        return base_tau
    
    # Calculate distances from template to each sample
    distances = [calculate_l1_distance(template, sample) for sample in samples]
    
    if len(distances) < 2:
        # Not enough samples for variance, use base + small margin
        mean_dist = distances[0] if distances else 0
        return max(base_tau, int(mean_dist * 1.5))
    
    # Calculate mean and standard deviation
    mean_dist = sum(distances) / len(distances)
    variance = sum((d - mean_dist) ** 2 for d in distances) / len(distances)
    stddev = variance ** 0.5
    
    # Adaptive threshold: mean + multiplier * stddev
    adaptive_tau = int(mean_dist + multiplier * stddev)
    
    # Ensure it's at least base_tau
    tau = max(base_tau, adaptive_tau)
    
    logger.info(
        "adaptive_tau_calculated",
        mean=round(mean_dist, 2),
        stddev=round(stddev, 2),
        tau=tau,
        base_tau=base_tau,
    )
    
    return tau


def calculate_template_quality(
    template: Sequence[int],
    samples: Sequence[Sequence[int]],
) -> dict[str, float]:
    """Calculate quality metrics for a template.
    
    Returns metrics like consistency (lower variance = better) and
    average distance from template.
    
    Parameters
    ----------
    template: Sequence[int]
        Template vector
    samples: Sequence[Sequence[int]]
        Sample vectors
        
    Returns
    -------
    dict[str, float]
        Quality metrics: mean_distance, stddev_distance, consistency_score
    """
    if not samples:
        return {"mean_distance": 0.0, "stddev_distance": 0.0, "consistency_score": 0.0}
    
    distances = [calculate_l1_distance(template, sample) for sample in samples]
    mean_dist = sum(distances) / len(distances)
    variance = sum((d - mean_dist) ** 2 for d in distances) / len(distances)
    stddev = variance ** 0.5
    
    # Consistency score: lower stddev = higher consistency (0-1 scale, normalized)
    # Normalize by assuming max reasonable stddev is ~200
    consistency_score = max(0.0, min(1.0, 1.0 - (stddev / 200.0)))
    
    return {
        "mean_distance": round(mean_dist, 2),
        "stddev_distance": round(stddev, 2),
        "consistency_score": round(consistency_score, 3),
    }

