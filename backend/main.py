"""Adaptive AI Engine — FastAPI entry point."""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from backend.config import settings
from backend.db.database import init_db
from backend.routers import auth, chat, feedback, memory, models

limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT])


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print(f"[AI Engine] DB initialized at {settings.DATABASE_URL}")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Adaptive AI Orchestration Platform — multi-model, feedback-driven, memory-enabled.",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(feedback.router)
app.include_router(memory.router)
app.include_router(models.router)


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health():
    from backend.services.gateway import gateway
    providers = gateway.available_providers()
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "providers_configured": len(providers),
        "providers": [p["id"] for p in providers],
    }
