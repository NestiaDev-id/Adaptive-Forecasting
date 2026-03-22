import sys
import os

# Ensure the project root is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings

from api.app.routes.forecast import router as forecast_router
from api.app.routes.training import router as training_router
from api.app.routes.profile import router as profile_router
from api.app.routes.stream import router as stream_router
from api.app.routes.status import router as status_router
from api.app.routes.public import router as public_router

app = FastAPI(
    title="Adaptive Forecasting Engine API",
    description="REST API for the Self-Adaptive GA-based Forecasting System",
    version="1.0.0",
)

# Security Middleware: API Key Check
@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    # Allow root for status/health checks without key
    if request.url.path == "/":
        return await call_next(request)
    
    # If key is configured, check it
    if settings.INTERNAL_API_KEY:
        api_key = request.headers.get("X-API-Key")
        if api_key != settings.INTERNAL_API_KEY:
            return JSONResponse(
                status_code=403,
                content={"detail": "Unauthorized: Invalid or missing X-API-Key"}
            )
            
    return await call_next(request)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://adaptive-forecasting.vercel.app",
        "http://localhost:5173", # Allow local dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(forecast_router, prefix="/api")
app.include_router(training_router, prefix="/api")
app.include_router(profile_router, prefix="/api")
app.include_router(stream_router, prefix="/api")
app.include_router(status_router, prefix="/api")
app.include_router(public_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "engine": "Adaptive Forecasting Engine",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": [
            "POST /api/forecast",
            "POST /api/train",
            "POST /api/profile",
            "POST /api/stream/init",
            "POST /api/stream/step",
            "POST /api/stream/reset",
            "GET  /api/status",
            "GET  /api/models",
            "GET  /api/forecast/latest",
            "GET  /api/forecast/history",
        ],
    }
