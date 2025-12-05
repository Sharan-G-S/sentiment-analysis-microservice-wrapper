"""
Metrics collection for monitoring service performance
"""
import time
from dataclasses import dataclass, field
from typing import List
from threading import Lock


@dataclass
class MetricsCollector:
    """
    Thread-safe metrics collector
    Tracks requests, latencies, and errors
    """
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    latencies: List[float] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    _lock: Lock = field(default_factory=Lock)
    
    def record_request(self, latency_ms: float, success: bool = True):
        """
        Record a request with its latency and status
        
        Args:
            latency_ms: Request processing time in milliseconds
            success: Whether the request was successful
        """
        with self._lock:
            self.total_requests += 1
            if success:
                self.successful_requests += 1
            else:
                self.failed_requests += 1
            
            self.latencies.append(latency_ms)
            
            # Keep only last 1000 latencies to avoid memory growth
            if len(self.latencies) > 1000:
                self.latencies = self.latencies[-1000:]
    
    def get_stats(self) -> dict:
        """
        Get current metrics statistics
        
        Returns:
            Dictionary with current metrics
        """
        with self._lock:
            avg_latency = (
                sum(self.latencies) / len(self.latencies)
                if self.latencies else 0.0
            )
            
            return {
                'total_requests': self.total_requests,
                'successful_requests': self.successful_requests,
                'failed_requests': self.failed_requests,
                'success_rate': (
                    self.successful_requests / self.total_requests * 100
                    if self.total_requests > 0 else 0.0
                ),
                'average_latency_ms': round(avg_latency, 2),
                'min_latency_ms': round(min(self.latencies), 2) if self.latencies else 0.0,
                'max_latency_ms': round(max(self.latencies), 2) if self.latencies else 0.0,
                'uptime_seconds': round(time.time() - self.start_time, 2)
            }
    
    def reset(self):
        """Reset all metrics"""
        with self._lock:
            self.total_requests = 0
            self.successful_requests = 0
            self.failed_requests = 0
            self.latencies = []
            self.start_time = time.time()
