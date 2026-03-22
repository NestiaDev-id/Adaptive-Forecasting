import numpy as np
from fastapi import APIRouter, HTTPException

from api.app.schemas.stream import StreamInitRequest, StreamStepRequest, StreamResponse
from api.app.__utils__ import get_online_loop, reset_online_loop, get_redis

router = APIRouter(tags=["stream"])

# Redis key constants
REDIS_STREAM_BUFFER = "stream:buffer"
REDIS_STREAM_WEIGHTS = "stream:weights"
REDIS_STREAM_META = "stream:meta"


def _save_stream_state_to_redis(loop, weights: dict | None = None):
    """Persist current stream state to Redis for serverless recovery."""
    redis = get_redis()
    if not redis.is_connected:
        return

    redis.set(REDIS_STREAM_BUFFER, {
        "data": loop._buffer[-500:],  # keep last 500 points max
        "step": loop._step,
    })

    if weights:
        redis.set(REDIS_STREAM_WEIGHTS, weights)


def _load_stream_state_from_redis():
    """Load stream state from Redis (called when in-memory loop is empty)."""
    redis = get_redis()
    if not redis.is_connected:
        return None
    return redis.get(REDIS_STREAM_BUFFER)


@router.post("/stream/init")
async def stream_init(req: StreamInitRequest):
    try:
        reset_online_loop()
        loop = get_online_loop()
        data = np.array(req.data, dtype=np.float64)
        loop.initialise(data)

        # Persist to Redis
        _save_stream_state_to_redis(loop)

        return {
            "status": "initialised",
            "buffer_size": loop.buffer_size,
            "redis_synced": get_redis().is_connected,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream/step", response_model=StreamResponse)
async def stream_step(req: StreamStepRequest):
    try:
        loop = get_online_loop()

        # If buffer is empty (cold start), try recovering from Redis
        if loop.buffer_size == 0:
            saved = _load_stream_state_from_redis()
            if saved and saved.get("data"):
                loop.initialise(np.array(saved["data"], dtype=np.float64))
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Stream not initialised. Call /api/stream/init first.",
                )

        result = loop.step(req.value)

        # Persist updated state to Redis
        _save_stream_state_to_redis(loop, result.get("weights"))

        return StreamResponse(
            prediction=result["prediction"],
            confidence=result["confidence"],
            weights=result["weights"],
            drift_detected=result["drift_detected"],
            buffer_size=loop.buffer_size,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream/reset")
async def stream_reset():
    reset_online_loop()

    # Clear Redis state
    redis = get_redis()
    if redis.is_connected:
        redis.delete(REDIS_STREAM_BUFFER)
        redis.delete(REDIS_STREAM_WEIGHTS)
        redis.delete(REDIS_STREAM_META)

    return {"status": "reset", "redis_cleared": redis.is_connected}
