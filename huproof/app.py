from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware

from .config.settings import get_settings
from .core.logging import configure_logging
from .db.session import init_db
from .api import enroll, login


configure_logging()
settings = get_settings()

app = FastAPI(title="huproof", version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def root() -> dict[str, str]:
    return {"app": settings.app_name, "version": settings.app_version}


@app.on_event("startup")
def on_startup() -> None:
    init_db()


app.include_router(enroll.router, prefix="/api/enroll", tags=["enroll"])
app.include_router(login.router, prefix="/api/login", tags=["login"])


