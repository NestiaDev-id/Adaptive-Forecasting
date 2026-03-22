import numpy as np
from fastapi import APIRouter, HTTPException

from api.app.schemas.training import TrainRequest, TrainResponse, FitnessRecord
from api.app.__utils__ import update_engine_state
from pipeline.trainer import Trainer
from evaluation.metrics import mse

router = APIRouter(tags=["training"])


@router.post("/train", response_model=TrainResponse)
async def train(req: TrainRequest):
    try:
        update_engine_state(status="training")
        data = np.array(req.data, dtype=np.float64)

        trainer = Trainer()
        result = trainer.train(
            data,
            max_generations=req.max_generations,
            population_size=req.population_size,
            val_ratio=req.val_ratio,
            early_stop=req.early_stop,
        )

        best = result["best_individual"]

        profile_dict = {
            "trend_strength": result["profile"].trend_strength,
            "seasonal_strength": result["profile"].seasonal_strength,
            "noise_level": result["profile"].noise_level,
            "seasonal_period": result["profile"].seasonal_period,
            "stationarity": result["profile"].stationarity,
            "data_length": result["profile"].data_length,
        }

        # combine all model params
        best_params = {}
        for model_name in best.get_normalised_weights():
            best_params[model_name] = best.get_model_params(model_name)

        fitness_history = [
            FitnessRecord(**record) for record in result["fitness_history"]
        ]

        val_error = float(mse(result["val_actual"], result["predictions"]))

        update_engine_state(
            status="idle",
            last_profile=profile_dict,
            total_trainings=1,
        )

        return TrainResponse(
            best_params=best_params,
            best_fitness=best.fitness,
            strategy_dna=best.get_strategy(),
            model_weights=best.get_normalised_weights(),
            profile=profile_dict,
            fitness_history=fitness_history,
            val_mse=val_error,
            predictions=result["predictions"].tolist(),
            val_actual=result["val_actual"].tolist(),
        )

    except Exception as e:
        update_engine_state(status="error")
        raise HTTPException(status_code=500, detail=str(e))
