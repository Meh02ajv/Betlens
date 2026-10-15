"""
BetLens FastAPI application entry point.
"""
import asyncio
import sys
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import setup_logging

# Module routers
from app.modules.auth.router import router as auth_router
from app.modules.users.router import router as users_router
from app.modules.sports_data.router import router as sports_router
from app.modules.predictions.router import router as predictions_router
from app.modules.odds_value.router import router as odds_router
from app.modules.assistant.router import router as assistant_router
from app.modules.notifications.router import router as notifications_router
from app.modules.billing.router import router as billing_router
from app.modules.admin.router import router as admin_router
from app.modules.sports_data.live_router import router as live_router

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    if settings.sentry_dsn:
        sentry_sdk.init(dsn=settings.sentry_dsn, environment=settings.app_env)
    yield


app = FastAPI(
    title="BetLens API",
    description="Sports statistics and probability analytics API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Global error handler ──────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"code": "internal_error", "message": "An unexpected error occurred", "details": None},
    )


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.app_env}


# ── API v1 routers ────────────────────────────────────────────────────────────
PREFIX = "/api/v1"

app.include_router(auth_router, prefix=f"{PREFIX}/auth", tags=["auth"])
app.include_router(users_router, prefix=f"{PREFIX}/me", tags=["users"])
app.include_router(sports_router, prefix=PREFIX, tags=["sports"])
app.include_router(predictions_router, prefix=PREFIX, tags=["predictions"])
app.include_router(odds_router, prefix=PREFIX, tags=["odds & value"])
app.include_router(assistant_router, prefix=f"{PREFIX}/chat", tags=["assistant"])
app.include_router(notifications_router, prefix=f"{PREFIX}/notifications", tags=["notifications"])
app.include_router(billing_router, prefix=f"{PREFIX}/billing", tags=["billing"])
app.include_router(admin_router, prefix=f"{PREFIX}/admin", tags=["admin"])
app.include_router(live_router, prefix=PREFIX, tags=["live data"])