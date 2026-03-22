import numpy as np
from fastapi import APIRouter, HTTPException

from api.app.schemas.forecast import (
    ForecastRequest, ForecastResponse, DriftEvent, AdaptationEvent,
)
from api.app.__utils__ import update_engine_state
from pipeline.orchestrator import Orchestrator

router = APIRouter(tags=["forecast"])


@router.post("/forecast", response_model=ForecastResponse)
async def forecast(req: ForecastRequest):
    try:
        update_engine_state(status="forecasting")
        data = np.array(req.data, dtype=np.float64)

        engine = Orchestrator(
            ga_generations=req.generations,
            ga_population=req.population,
            forecast_horizon=req.horizon,
        )

        result = engine.run(data, val_ratio=req.val_ratio)

        # serialise profile
        profile_dict = {
            "trend_strength": result["profile"].trend_strength,
            "seasonal_strength": result["profile"].seasonal_strength,
            "noise_level": result["profile"].noise_level,
            "seasonal_period": result["profile"].seasonal_period,
            "stationarity": result["profile"].stationarity,
            "data_length": result["profile"].data_length,
        }

        # serialise best individual
        best = result["best_individual"]
        best_dict = {
            "fitness": best.fitness,
            "mutation_rate": best.mutation_rate,
            "crossover_rate": best.crossover_rate,
            "mutation_step": best.mutation_step,
            "model_weights": best.get_normalised_weights(),
            "holt_winters_params": best.get_model_params("holt_winters"),
            "arima_params": best.get_model_params("arima"),
        }

        # serialise drift events
        drift_events = [
            DriftEvent(
                method=de.method,
                magnitude=de.magnitude,
                location=de.location,
            )
            for de in result["drift_events"]
        ]

        # serialise adaptation history
        adaptations = [
            AdaptationEvent(
                action=aa.action,
                confidence=aa.confidence,
                reason=aa.reason,
            )
            for aa in result["adaptation_history"]
        ]

        update_engine_state(
            status="idle",
            last_profile=profile_dict,
            last_best_individual=best_dict,
            total_forecasts=1,
        )

        return ForecastResponse(
            forecast=result["forecast"].tolist(),
            forecast_lower=result["forecast_lower"].tolist(),
            forecast_upper=result["forecast_upper"].tolist(),
            confidence=result["confidence"],
            val_predictions=result["val_predictions"].tolist(),
            val_actual=result["val_actual"].tolist(),
            val_mse=result["val_mse"],
            profile=profile_dict,
            best_individual=best_dict,
            final_weights=result["final_weights"],
            drift_events=drift_events,
            adaptation_history=adaptations,
            fitness_history=result["fitness_history"],
        )

    except Exception as e:
        update_engine_state(status="error")
        raise HTTPException(status_code=500, detail=str(e))
