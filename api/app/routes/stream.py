import numpy as np
from fastapi import APIRouter, HTTPException

from api.app.schemas.stream import StreamInitRequest, StreamStepRequest, StreamResponse
from api.app.__utils__ import get_online_loop, reset_online_loop

router = APIRouter(prefix="/api", tags=["stream"])


@router.post("/stream/init")
async def stream_init(req: StreamInitRequest):
    try:
        reset_online_loop()
        loop = get_online_loop()
        data = np.array(req.data, dtype=np.float64)
        loop.initialise(data)

        return {
            "status": "initialised",
            "buffer_size": loop.buffer_size,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream/step", response_model=StreamResponse)
async def stream_step(req: StreamStepRequest):
    try:
        loop = get_online_loop()
        if loop.buffer_size == 0:
            raise HTTPException(
                status_code=400,
                detail="Stream not initialised. Call /api/stream/init first.",
            )

        result = loop.step(req.value)

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
    return {"status": "reset"}
