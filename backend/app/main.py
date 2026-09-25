from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.logging_config import configure_logging

settings = get_settings()
configure_logging(settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup/shutdown hooks (DB pool, graceful SIGTERM drain, etc.)
    # will be filled in during Phase 5.
    yield


app = FastAPI(
    title="CivicPulse API",
    description="Municipal complaint intake, triage and operations platform",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> dict[str, str]:
    """
    Liveness probe. Must NOT touch the database — just proves the process is alive.
    """
    return {"status": "ok"}