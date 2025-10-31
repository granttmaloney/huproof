"""Rate limiting utilities for API endpoints."""

from functools import wraps
from typing import Callable

from fastapi import Request, HTTPException, status
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .logging import get_logger

logger = get_logger()

# Create limiter instance
limiter = Limiter(key_func=get_remote_address)


def get_client_ip(request: Request) -> str:
    """Extract client IP from request for rate limiting."""
    if hasattr(request.state, "client_ip"):
        return request.state.client_ip
    # Fallback to slowapi's default
    return get_remote_address(request)


# Rate limit decorators
def rate_limit_enroll_start() -> Callable:
    """Rate limit for enrollment start endpoint (5 per minute per IP)."""
    return limiter.limit("5/minute", key_func=get_client_ip)


def rate_limit_login_start() -> Callable:
    """Rate limit for login start endpoint (10 per minute per IP)."""
    return limiter.limit("10/minute", key_func=get_client_ip)


def rate_limit_finish() -> Callable:
    """Rate limit for finish endpoints (20 per minute per IP)."""
    return limiter.limit("20/minute", key_func=get_client_ip)


def setup_rate_limit_handler(app) -> None:
    """Set up rate limit error handler for the FastAPI app."""
    app.state.limiter = limiter


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> HTTPException:
    """Custom rate limit exceeded handler."""
    logger.warning("rate_limit_exceeded", ip=get_client_ip(request), path=request.url.path)
    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Rate limit exceeded. Please try again later.",
    )

