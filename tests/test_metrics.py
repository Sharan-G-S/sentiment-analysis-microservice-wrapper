"""
Tests for metrics collection
"""
import pytest
from app.metrics import MetricsCollector


def test_metrics_initialization():
    """Test metrics collector initialization"""
    metrics = MetricsCollector()
    
    assert metrics.total_requests == 0
    assert metrics.successful_requests == 0
    assert metrics.failed_requests == 0
    assert len(metrics.latencies) == 0


def test_record_successful_request():
    """Test recording a successful request"""
    metrics = MetricsCollector()
    
    metrics.record_request(latency_ms=100.5, success=True)
    
    assert metrics.total_requests == 1
    assert metrics.successful_requests == 1
    assert metrics.failed_requests == 0
    assert 100.5 in metrics.latencies


def test_record_failed_request():
    """Test recording a failed request"""
    metrics = MetricsCollector()
    
    metrics.record_request(latency_ms=50.0, success=False)
    
    assert metrics.total_requests == 1
    assert metrics.successful_requests == 0
    assert metrics.failed_requests == 1


def test_get_stats():
    """Test retrieving statistics"""
    metrics = MetricsCollector()
    
    metrics.record_request(100.0, True)
    metrics.record_request(200.0, True)
    metrics.record_request(150.0, False)
    
    stats = metrics.get_stats()
    
    assert stats['total_requests'] == 3
    assert stats['successful_requests'] == 2
    assert stats['failed_requests'] == 1
    assert stats['average_latency_ms'] == 150.0
    assert stats['min_latency_ms'] == 100.0
    assert stats['max_latency_ms'] == 200.0


def test_reset_metrics():
    """Test resetting metrics"""
    metrics = MetricsCollector()
    
    metrics.record_request(100.0, True)
    metrics.reset()
    
    assert metrics.total_requests == 0
    assert metrics.successful_requests == 0
    assert metrics.failed_requests == 0
    assert len(metrics.latencies) == 0
