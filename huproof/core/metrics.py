"""Metrics and monitoring utilities."""

from time import perf_counter
from typing import Any, Optional

from .logging import get_logger

logger = get_logger()

# Simple in-memory metrics (for PoC; use Prometheus for production)
_metrics: dict[str, list[float]] = {}


def record_timing(metric_name: str, duration_ms: float, **labels: Any) -> None:
    """Record a timing metric.
    
    Parameters
    ----------
    metric_name: str
        Name of the metric (e.g., "proof_generation_time")
    duration_ms: float
        Duration in milliseconds
    labels: dict
        Additional labels for context
    """
    if metric_name not in _metrics:
        _metrics[metric_name] = []
    _metrics[metric_name].append(duration_ms)
    
    logger.info(
        "metric_timing",
        metric=metric_name,
        ms=round(duration_ms, 2),
        **labels,
    )


def record_counter(metric_name: str, value: float = 1.0, **labels: Any) -> None:
    """Record a counter metric.
    
    Parameters
    ----------
    metric_name: str
        Name of the metric (e.g., "enrollments_total")
    value: float
        Counter increment (default: 1.0)
    labels: dict
        Additional labels for context
    """
    if metric_name not in _metrics:
        _metrics[metric_name] = []
    _metrics[metric_name].append(value)
    
    logger.info(
        "metric_counter",
        metric=metric_name,
        value=value,
        **labels,
    )


def get_metric_stats(metric_name: str) -> Optional[dict[str, float]]:
    """Get statistics for a metric.
    
    Returns mean, min, max, count, or None if metric doesn't exist.
    """
    if metric_name not in _metrics or not _metrics[metric_name]:
        return None
    
    values = _metrics[metric_name]
    return {
        "count": len(values),
        "mean": sum(values) / len(values),
        "min": min(values),
        "max": max(values),
    }


def get_all_metrics() -> dict[str, dict[str, float]]:
    """Get statistics for all metrics."""
    return {
        name: get_metric_stats(name) or {}
        for name in _metrics.keys()
    }


class TimingContext:
    """Context manager for timing operations."""
    
    def __init__(self, metric_name: str, **labels: Any):
        self.metric_name = metric_name
        self.labels = labels
        self.start_time: Optional[float] = None
    
    def __enter__(self):
        self.start_time = perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            duration_ms = (perf_counter() - self.start_time) * 1000.0
            record_timing(self.metric_name, duration_ms, **self.labels)
        return False

