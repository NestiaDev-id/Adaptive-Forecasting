import numpy as np
from fastapi import APIRouter, HTTPException

from api.app.schemas.profile import ProfileRequest, ProfileResponse
from patterns.detector import detect

router = APIRouter(tags=["profile"])


@router.post("/profile", response_model=ProfileResponse)
async def analyse_profile(req: ProfileRequest):
    try:
        data = np.array(req.data, dtype=np.float64)
        profile = detect(data)

        return ProfileResponse(
            trend_strength=profile.trend_strength,
            seasonal_strength=profile.seasonal_strength,
            noise_level=profile.noise_level,
            seasonal_period=profile.seasonal_period,
            data_length=profile.data_length,
            stationarity=profile.stationarity,
            is_trending=profile.is_trending,
            is_seasonal=profile.is_seasonal,
            is_noisy=profile.is_noisy,
            summary=profile.summary(),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
