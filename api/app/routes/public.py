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


# Redis key for cached earthquake data
REDIS_QUAKE_CACHE = "public:bmkg_quakes"


@router.get("/public/earthquakes")
async def get_bmkg_earthquakes():
    """
    Return real-time BMKG earthquake data.
    Fetches from BMKG Nuxt payload, caches in Redis for 60s.
    Falls back to local JSON file if BMKG is unreachable.
    """
    import json as _json
    import os as _os

    redis = get_redis()

    # 1. Check Redis cache first (60s TTL)
    if redis.is_connected:
        cached = redis.get(REDIS_QUAKE_CACHE)
        if cached and isinstance(cached, dict) and cached.get("earthquakes"):
            response = JSONResponse(content=cached)
            response.headers["Cache-Control"] = "s-maxage=30, stale-while-revalidate"
            return response

    # 2. Fetch live from BMKG
    quakes = await _fetch_bmkg_live()

    if quakes:
        result = {
            "source": "BMKG_live",
            "count": len(quakes),
            "earthquakes": quakes,
        }
        # Cache in Redis for 60 seconds
        if redis.is_connected:
            redis.set(REDIS_QUAKE_CACHE, result, ttl_seconds=60)

        response = JSONResponse(content=result)
        response.headers["Cache-Control"] = "s-maxage=30, stale-while-revalidate"
        return response

    # 3. Fallback: read from local file (for local dev)
    local_path = _os.path.join(
        _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.dirname(__file__)))),
        "data", "raw", "bmkg_quakes_realtime.json"
    )
    if _os.path.exists(local_path):
        with open(local_path, "r", encoding="utf-8") as f:
            data = _json.load(f)
        return JSONResponse(content={
            "source": "local_file",
            "count": data.get("count", 0),
            "earthquakes": data.get("earthquakes", []),
        })

    return JSONResponse(content={
        "source": "none",
        "count": 0,
        "earthquakes": [],
        "message": "No earthquake data available.",
    })


async def _fetch_bmkg_live() -> list[dict] | None:
    """Fetch and parse BMKG Nuxt payload for real-time earthquake data."""
    import httpx

    PAYLOAD_URL = "https://www.bmkg.go.id/gempabumi/gempabumi-realtime/_payload.json"

    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.get(PAYLOAD_URL)
            if resp.status_code != 200:
                return None
            raw = resp.json()
            return _parse_nuxt_quake_payload(raw)
    except Exception:
        return None


def _parse_nuxt_quake_payload(raw: list) -> list[dict]:
    """Parse BMKG Nuxt _payload.json into clean earthquake dicts."""
    if not isinstance(raw, list) or len(raw) < 3:
        return []

    flat = raw
    quakes = []

    for item in flat:
        if not isinstance(item, dict):
            continue
        if not all(k in item for k in ("eventid", "waktu", "lintang", "bujur", "dalam", "mag", "area")):
            continue

        def resolve(val):
            if isinstance(val, int) and 0 <= val < len(flat):
                resolved = flat[val]
                if isinstance(resolved, (str, int, float)):
                    return resolved
            return val

        try:
            eventid = resolve(item["eventid"])
            waktu = resolve(item["waktu"])
            lintang = item["lintang"]
            bujur = item["bujur"]
            dalam = item["dalam"]
            mag = item["mag"]
            area = resolve(item["area"])

            # Resolve index references for numeric fields
            if isinstance(lintang, int) and 0 <= lintang < len(flat):
                lintang = flat[lintang]
            if isinstance(bujur, int) and 0 <= bujur < len(flat):
                bujur = flat[bujur]
            if isinstance(dalam, int) and 0 <= dalam < len(flat):
                dalam = flat[dalam]
            if isinstance(mag, int) and 0 <= mag < len(flat):
                mag = flat[mag]

            quakes.append({
                "eventid": str(eventid),
                "datetime": str(waktu),
                "latitude": float(lintang) if lintang is not None else None,
                "longitude": float(bujur) if bujur is not None else None,
                "depth_km": float(dalam) if dalam is not None else None,
                "magnitude": float(mag) if mag is not None else None,
                "area": str(area),
            })
        except (ValueError, TypeError, IndexError):
            continue

    return quakes
