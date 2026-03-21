import sys
import os

# Ensure the project root is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.app.routes.forecast import router as forecast_router
from api.app.routes.training import router as training_router
from api.app.routes.profile import router as profile_router
from api.app.routes.stream import router as stream_router
from api.app.routes.status import router as status_router

app = FastAPI(
    title="Adaptive Forecasting Engine API",
    description="REST API for the Self-Adaptive GA-based Forecasting System",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(forecast_router)
app.include_router(training_router)
app.include_router(profile_router)
app.include_router(stream_router)
app.include_router(status_router)


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
        ],
    }
