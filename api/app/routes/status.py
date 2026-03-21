from fastapi import APIRouter

from api.app.__utils__ import get_engine_state
from models.registry import build_default_registry, build_full_registry

router = APIRouter(prefix="/api", tags=["status"])


@router.get("/status")
async def status():
    state = get_engine_state()
    return {
        "engine": "Adaptive Forecasting Engine",
        "version": "1.0.0",
        "status": state["status"],
        "total_forecasts": state["total_forecasts"],
        "total_trainings": state["total_trainings"],
        "last_profile": state["last_profile"],
    }


@router.get("/models")
async def list_models():
    default = build_default_registry()
    full = build_full_registry()

    return {
        "default_models": default.list_models(),
        "all_models": full.list_models(),
        "note": "Default registry excludes LSTM for GA speed. Use build_full_registry() for all models.",
    }
