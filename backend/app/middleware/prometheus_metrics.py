"""
=========================================================================
Prometheus Metrics Middleware - FastAPI Performance Monitoring
SDLC Orchestrator - Week 5 Day 2 (Performance & Load Testing)

Purpose:
- Expose /metrics endpoint for Prometheus scraping
- Collect API latency (p50, p95, p99)
- Track request rate (requests/second)
- Monitor error rate (4xx, 5xx)
- Measure request/response sizes

Metrics Exposed:
- http_request_duration_seconds (histogram) - API latency
- http_requests_total (counter) - Total requests
- http_requests_in_progress (gauge) - Active requests
- http_request_size_bytes (summary) - Request size
- http_response_size_bytes (summary) - Response size
- http_exceptions_total (counter) - Unhandled exceptions

Performance Targets (SDLC 4.9):
- p50 latency: <50ms
- p95 latency: <100ms ⭐ CRITICAL
- p99 latency: <200ms
- Error rate: <0.1%
- Throughput: >1000 req/s

OWASP ASVS Compliance:
- V11.1.5: Performance monitoring integrated
=========================================================================
"""

import time
from typing import Callable

from fastapi import Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    REGISTRY,
    Counter,
    Gauge,
    Histogram,
    Summary,
    generate_latest,
)
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


# ============================================================================
# PROMETHEUS METRICS DEFINITIONS
# ============================================================================

# Histogram: API latency distribution (buckets: 10ms, 50ms, 100ms, 200ms, 500ms, 1s, 2s, 5s)
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency (seconds)",
    ["method", "endpoint", "status"],
    buckets=(0.01, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0),
)

# Counter: Total HTTP requests
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

# Gauge: Active HTTP requests (in-flight)
http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently in progress",
    ["method", "endpoint"],
)

# Summary: Request size distribution
http_request_size_bytes = Summary(
    "http_request_size_bytes",
    "HTTP request size (bytes)",
    ["method", "endpoint"],
)

# Summary: Response size distribution
http_response_size_bytes = Summary(
    "http_response_size_bytes",
    "HTTP response size (bytes)",
    ["method", "endpoint", "status"],
)

# Counter: Unhandled exceptions
http_exceptions_total = Counter(
    "http_exceptions_total",
    "Total unhandled exceptions",
    ["method", "endpoint", "exception_type"],
)


class PrometheusMetricsMiddleware(BaseHTTPMiddleware):
    """
    Prometheus metrics collection middleware for FastAPI.

    Middleware Order (CRITICAL):
    1. SecurityHeadersMiddleware (first - add headers to all responses)
    2. RateLimiterMiddleware (second - block before processing)
    3. **PrometheusMetricsMiddleware** (third - measure after rate limiting)
    4. CORSMiddleware (fourth - CORS headers)
    5. GZipMiddleware (last - compress response)

    Usage:
        app.add_middleware(PrometheusMetricsMiddleware)

    Exposed Endpoint:
        GET /metrics - Prometheus scrape endpoint
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Collect metrics for each HTTP request.

        Args:
            request: FastAPI request object
            call_next: Next middleware in chain

        Returns:
            Response with metrics collected
        """
        # Extract request details
        method = request.method
        endpoint = request.url.path

        # Skip metrics collection for /metrics endpoint itself
        if endpoint == "/metrics":
            return await call_next(request)

        # Normalize endpoint (replace UUIDs with {id} placeholder)
        endpoint_normalized = self._normalize_endpoint(endpoint)

        # Track request size (Content-Length header)
        request_size = int(request.headers.get("Content-Length", 0))
        http_request_size_bytes.labels(method=method, endpoint=endpoint_normalized).observe(
            request_size
        )

        # Track active requests (increment gauge)
        http_requests_in_progress.labels(method=method, endpoint=endpoint_normalized).inc()

        # Start timer
        start_time = time.time()

        try:
            # Process request
            response = await call_next(request)

            # Calculate latency
            latency = time.time() - start_time
            status_code = response.status_code

            # Track latency histogram
            http_request_duration_seconds.labels(
                method=method, endpoint=endpoint_normalized, status=status_code
            ).observe(latency)

            # Track total requests counter
            http_requests_total.labels(
                method=method, endpoint=endpoint_normalized, status=status_code
            ).inc()

            # Track response size (Content-Length header)
            response_size = int(response.headers.get("Content-Length", 0))
            http_response_size_bytes.labels(
                method=method, endpoint=endpoint_normalized, status=status_code
            ).observe(response_size)

            return response

        except Exception as e:
            # Track exceptions
            http_exceptions_total.labels(
                method=method,
                endpoint=endpoint_normalized,
                exception_type=type(e).__name__,
            ).inc()

            # Re-raise exception (let FastAPI exception handlers deal with it)
            raise

        finally:
            # Decrement active requests gauge
            http_requests_in_progress.labels(
                method=method, endpoint=endpoint_normalized
            ).dec()

    def _normalize_endpoint(self, endpoint: str) -> str:
        """
        Normalize endpoint path (replace UUIDs with {id} placeholder).

        Examples:
        - /api/v1/gates/550e8400-e29b-41d4-a716-446655440000 → /api/v1/gates/{id}
        - /api/v1/evidence/abc-123/download → /api/v1/evidence/{id}/download

        Args:
            endpoint: Raw endpoint path

        Returns:
            Normalized endpoint path
        """
        import re

        # Replace UUID patterns with {id}
        # UUID format: 8-4-4-4-12 hex digits (e.g., 550e8400-e29b-41d4-a716-446655440000)
        endpoint = re.sub(
            r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            "/{id}",
            endpoint,
            flags=re.IGNORECASE,
        )

        # Replace numeric IDs with {id}
        endpoint = re.sub(r"/\d+", "/{id}", endpoint)

        return endpoint


def metrics_endpoint() -> Response:
    """
    Prometheus /metrics endpoint.

    Returns Prometheus metrics in text format.

    Usage:
        app.add_api_route("/metrics", metrics_endpoint, methods=["GET"])

    Returns:
        Response with Prometheus metrics (text/plain)
    """
    metrics_data = generate_latest(REGISTRY)
    return Response(content=metrics_data, media_type=CONTENT_TYPE_LATEST)


# ============================================================================
# USEFUL PROMETHEUS QUERIES (PromQL)
# ============================================================================

"""
API Latency (p50):
histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))

API Latency (p95) ⭐ CRITICAL:
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

API Latency (p99):
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))

Request Rate (requests/second):
rate(http_requests_total[1m])

Error Rate (4xx/5xx):
rate(http_requests_total{status=~"4..|5.."}[1m]) / rate(http_requests_total[1m]) * 100

Active Requests:
http_requests_in_progress

Top 5 Slowest Endpoints (by p95 latency):
topk(5, histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])))

Request Size (p95):
histogram_quantile(0.95, rate(http_request_size_bytes_sum[5m]) / rate(http_request_size_bytes_count[5m]))

Response Size (p95):
histogram_quantile(0.95, rate(http_response_size_bytes_sum[5m]) / rate(http_response_size_bytes_count[5m]))

Exception Rate:
rate(http_exceptions_total[1m])
"""
