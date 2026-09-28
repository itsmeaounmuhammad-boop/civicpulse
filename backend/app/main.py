"""
CivicPulse FastAPI application entrypoint.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from redis.asyncio import Redis

from app.config import get_settings
from app.database import engine
from app.logging_config import configure_logging
from app.middleware import RequestIDMiddleware
from app.routes import complaints, meta, system

settings = get_settings()
configure_logging(settings.log_level)

logger = logging.getLogger("civicpulse.lifespan")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    app.state.db_engine = engine
    app.state.redis = Redis.from_url(settings.redis_url, decode_responses=True)
    logger.info("application startup complete")

    yield

    # --- Shutdown (SIGTERM handling) ---
    # Uvicorn stops accepting new connections and waits for in-flight
    # requests to finish before this block runs. Here we close the
    # resources those requests were using.
    logger.info("application shutdown initiated, draining connections")
    await app.state.redis.aclose()
    await app.state.db_engine.dispose()
    logger.info("application shutdown complete")


app = FastAPI(
    title="CivicPulse API",
    description="Municipal complaint intake, triage and operations platform",
    version="0.1.0",
    lifespan=lifespan,
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    The API contract requires 400 with a field-level error body,
    not FastAPI's default 422.
    """
    errors = [
        {
            "field": ".".join(str(part) for part in err["loc"] if part != "body"),
            "message": err["msg"],
        }
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=400,
        content={"detail": "Validation failed", "errors": errors},
    )


app.add_middleware(RequestIDMiddleware)

app.include_router(system.router)
app.include_router(complaints.router)
app.include_router(meta.router)