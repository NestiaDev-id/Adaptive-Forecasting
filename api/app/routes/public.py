"""
Public API — Cached endpoint for frontend consumers.

This endpoint reads the latest forecast result from Redis and serves it
with Edge Cache headers (s-maxage=6) so that Vercel CDN can cache the
response for 6 seconds. Thousands of users hitting this endpoint within
that window will be served from cache without triggering any Redis calls.
"""

from datetime import datetime, timezone
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from api.app.__utils__ import get_redis, get_engine_state

router = APIRouter(tags=["public"])

# Redis keys used by the worker
REDIS_LATEST_FORECAST = "public:latest_forecast"
REDIS_FORECAST_HISTORY = "public:forecast_history"


@router.get("/forecast/latest")
async def get_latest_forecast():
    """
    Return the most recent forecast computed by the background worker.
    Served with Cache-Control headers for Vercel Edge Cache (6s TTL).
    """
    redis = get_redis()

    # Try Redis first
    if redis.is_connected:
        cached = redis.get(REDIS_LATEST_FORECAST)
        if cached:
            response = JSONResponse(content={
                "source": "redis",
                "data": cached,
                "cached_at": cached.get("timestamp", None),
            })
            # Edge Cache: hold for 6s, serve stale while revalidating
            response.headers["Cache-Control"] = "s-maxage=6, stale-while-revalidate"
            return response

    # Fallback: return in-memory engine state (local dev)
    state = get_engine_state()
    return JSONResponse(content={
        "source": "memory",
        "data": {
            "status": state["status"],
            "last_profile": state["last_profile"],
            "last_best_individual": state["last_best_individual"],
            "total_forecasts": state["total_forecasts"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    })


@router.get("/forecast/history")
async def get_forecast_history():
    """
    Return the forecast history (last N entries) stored by the worker.
    Useful for showing trend comparisons (today vs yesterday).
    """
    redis = get_redis()

    if redis.is_connected:
        history = redis.get(REDIS_FORECAST_HISTORY)
        if history and isinstance(history, list):
            response = JSONResponse(content={
                "source": "redis",
                "count": len(history),
                "data": history,
            })
            response.headers["Cache-Control"] = "s-maxage=30, stale-while-revalidate"
            return response

    return JSONResponse(content={
        "source": "memory",
        "count": 0,
        "data": [],
        "message": "No history available. Worker not running or Redis not connected.",
    })
