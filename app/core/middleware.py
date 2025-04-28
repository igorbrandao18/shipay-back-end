import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.metrics import metrics

class MetricsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get endpoint path for metrics labels
        endpoint = request.url.path
        method = request.method

        try:
            # Track active requests
            metrics.inc_active_requests(endpoint)
            
            # Track request duration
            start_time = time.time()
            response = await call_next(request)
            duration = time.time() - start_time
            
            # Record metrics
            metrics.observe_request_latency(endpoint, duration)
            metrics.observe_response_size(endpoint, len(response.body) if hasattr(response, 'body') else 0)
            metrics.inc_api_request(method, endpoint, response.status_code)
            
            # If error status code, track error
            if response.status_code >= 400:
                metrics.inc_api_error(endpoint, f'http_{response.status_code}')
            
            return response
            
        except Exception as e:
            # Track unexpected errors
            metrics.inc_api_error(endpoint, type(e).__name__)
            raise
            
        finally:
            # Always decrement active requests
            metrics.dec_active_requests(endpoint) 