from pydantic import BaseModel, Field


class ProfileRequest(BaseModel):
    data: list[float] = Field(..., min_length=4, description="Time series data points")


class ProfileResponse(BaseModel):
    trend_strength: float
    seasonal_strength: float
    noise_level: float
    seasonal_period: int
    data_length: int
    stationarity: float
    is_trending: bool
    is_seasonal: bool
    is_noisy: bool
    summary: str
