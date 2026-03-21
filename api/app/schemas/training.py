from pydantic import BaseModel, Field


class TrainRequest(BaseModel):
    data: list[float] = Field(..., min_length=10, description="Time series data points")
    max_generations: int = Field(default=80, ge=5, le=500)
    population_size: int = Field(default=40, ge=10, le=200)
    val_ratio: float = Field(default=0.2, ge=0.05, le=0.5)
    early_stop: int = Field(default=25, ge=5, le=100)


class FitnessRecord(BaseModel):
    gen: int
    best: float
    avg: float
    diversity: float
    metric: str
    avg_mutation: float


class TrainResponse(BaseModel):
    best_params: dict
    best_fitness: float
    strategy_dna: dict
    model_weights: dict[str, float]
    profile: dict
    fitness_history: list[FitnessRecord]
    val_mse: float
    predictions: list[float]
    val_actual: list[float]
