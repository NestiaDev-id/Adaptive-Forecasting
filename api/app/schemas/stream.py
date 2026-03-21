from pydantic import BaseModel, Field


class StreamInitRequest(BaseModel):
    data: list[float] = Field(..., min_length=10, description="Initial historical data")


class StreamStepRequest(BaseModel):
    value: float = Field(..., description="New data point")


class StreamResponse(BaseModel):
    prediction: float
    confidence: float
    weights: dict[str, float]
    drift_detected: bool
    buffer_size: int
