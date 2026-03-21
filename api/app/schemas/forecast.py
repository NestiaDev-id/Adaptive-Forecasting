from pydantic import BaseModel, Field


class ForecastRequest(BaseModel):
    data: list[float] = Field(..., min_length=10, description="Time series data points")
    horizon: int = Field(default=12, ge=1, le=100, description="Steps to forecast ahead")
    generations: int = Field(default=50, ge=5, le=500, description="Max GA generations")
    population: int = Field(default=30, ge=10, le=200, description="GA population size")
    val_ratio: float = Field(default=0.2, ge=0.05, le=0.5, description="Validation ratio")


class DriftEvent(BaseModel):
    method: str
    magnitude: float
    location: int


class AdaptationEvent(BaseModel):
    action: str
    confidence: float
    reason: str


class ForecastResponse(BaseModel):
    forecast: list[float]
    forecast_lower: list[float]
    forecast_upper: list[float]
    confidence: float

    val_predictions: list[float]
    val_actual: list[float]
    val_mse: float

    profile: dict
    best_individual: dict
    final_weights: dict[str, float]

    drift_events: list[DriftEvent]
    adaptation_history: list[AdaptationEvent]
    fitness_history: list[dict]
