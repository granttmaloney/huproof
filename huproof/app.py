from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config.settings import get_settings
from .core.logging import configure_logging
from .core.ratelimit import setup_rate_limit_handler, rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from .db.session import init_db
from .api import enroll, login, logout


configure_logging()
settings = get_settings()

app = FastAPI(
    title="huproof",
    version=settings.app_version,
    description="Human-in-the-Loop ZK Auth API - Privacy-preserving, unlinkable liveness proof using keystroke dynamics",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Set up rate limiting
setup_rate_limit_handler(app)
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/health",
    summary="Health check",
    description="Check API health status and version information.",
)
def health() -> dict[str, str | dict[str, str]]:
    """Health check endpoint with version info."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": "development" if settings.db_url.startswith("sqlite") else "production",
    }


@app.get(
    "/metrics",
    summary="Metrics",
    description="Get aggregated metrics (timing, counters). PoC implementation - use Prometheus for production.",
)
def metrics() -> dict[str, Any]:
    """Get current metrics statistics."""
    from .core.metrics import get_all_metrics
    
    return {
        "metrics": get_all_metrics(),
    }


@app.get("/")
def root() -> dict[str, str]:
    return {"app": settings.app_name, "version": settings.app_version}


@app.on_event("startup")
def on_startup() -> None:
    init_db()


app.include_router(enroll.router, prefix="/api/enroll", tags=["enroll"])
app.include_router(login.router, prefix="/api/login", tags=["login"])
app.include_router(logout.router, prefix="/api", tags=["auth"])


