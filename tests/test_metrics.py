"""Tests for metrics."""

import pytest
from fastapi.testclient import TestClient

from huproof.core.metrics import (
    TimingContext,
    get_all_metrics,
    get_metric_stats,
    record_counter,
    record_timing,
)


def test_record_timing() -> None:
    """Test timing metric recording."""
    record_timing("test_metric", 100.5, endpoint="test")
    stats = get_metric_stats("test_metric")
    assert stats is not None
    assert stats["mean"] == 100.5
    assert stats["count"] == 1


def test_record_counter() -> None:
    """Test counter metric recording."""
    record_counter("test_counter", value=1.0)
    record_counter("test_counter", value=2.0)
    stats = get_metric_stats("test_counter")
    assert stats is not None
    assert stats["mean"] == 1.5
    assert stats["count"] == 2


def test_timing_context() -> None:
    """Test timing context manager."""
    with TimingContext("context_test", endpoint="test"):
        import time
        time.sleep(0.01)  # Small delay
    
    stats = get_metric_stats("context_test")
    assert stats is not None
    assert stats["count"] == 1
    assert stats["mean"] > 0  # Should have recorded some time


def test_get_all_metrics() -> None:
    """Test getting all metrics."""
    record_timing("metric1", 10.0)
    record_counter("metric2", 5.0)
    all_metrics = get_all_metrics()
    assert "metric1" in all_metrics
    assert "metric2" in all_metrics


def test_metrics_endpoint(test_client: TestClient, test_headers: dict[str, str]) -> None:
    """Test metrics endpoint."""
    # Make some requests to generate metrics
    test_client.get("/api/enroll/start", headers=test_headers)
    
    # Check metrics endpoint
    resp = test_client.get("/metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert "metrics" in data

