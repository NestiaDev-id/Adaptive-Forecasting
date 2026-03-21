import numpy as np
from genetic.ga_engine import GAEngine
from genetic.population import Population
from patterns.detector import detect
from patterns.profile import DataProfile
from models.registry import build_default_registry
from evaluation.metrics import mse
from utils.helpers import train_val_split
from utils.logger import EvolutionLogger
from config.settings import DEFAULT_VAL_RATIO


class Trainer:
    """
    Batch training pipeline.
    Trains the GA on provided data and returns the optimised model.
    """

    def __init__(self, logger: EvolutionLogger = None):
        self._log = logger or EvolutionLogger("trainer")
        self._registry = build_default_registry()
        self._ga = None
        self._profile: DataProfile = None

    def train(self, data: np.ndarray,
              max_generations: int = 100,
              population_size: int = 40,
              val_ratio: float = DEFAULT_VAL_RATIO,
              early_stop: int = 25) -> dict:
        """
        Run full training pipeline.

        Returns
        -------
        dict with keys: best_individual, profile, fitness_history, predictions
        """
        data = np.asarray(data, dtype=np.float64)

        # 1. Detect patterns
        self._profile = detect(data)
        self._log._log.info(f"Data profile: {self._profile.summary()}")

        # 2. Create profile-aware population
        population = Population.from_profile(
            self._profile,
            size=population_size,
            generation=0,
        )

        # 3. Run GA
        self._ga = GAEngine(
            population_size=population_size,
            max_generations=max_generations,
            logger=self._log,
        )

        best = self._ga.run(
            data,
            population=population,
            val_ratio=val_ratio,
            early_stop_gens=early_stop,
        )

        # 4. Record pattern → strategy mapping in memory
        self._ga.memory.record_pattern(self._profile, best)

        # 5. Generate predictions with best individual
        train, val = train_val_split(data, val_ratio)
        predictions = self._predict_with_individual(best, train, len(val))

        return {
            "best_individual": best,
            "profile": self._profile,
            "fitness_history": self._ga.fitness_history,
            "predictions": predictions,
            "val_actual": val,
            "train_data": train,
        }

    def _predict_with_individual(self, individual, train, horizon):
        weights = individual.get_normalised_weights()
        ensemble_pred = np.zeros(horizon)

        for model_name, weight in weights.items():
            if weight < 0.01:
                continue
            try:
                model = self._registry.get(model_name)
                params = individual.get_model_params(model_name)
                model.set_params(params)
                model.fit(train)
                pred = model.forecast(horizon)
                if len(pred) != horizon:
                    pred = np.resize(pred, horizon)
                if not np.all(np.isfinite(pred)):
                    pred = np.full(horizon, np.mean(train))
                ensemble_pred += weight * pred
            except Exception:
                ensemble_pred += weight * np.mean(train)

        return ensemble_pred

    @property
    def ga_engine(self) -> GAEngine:
        return self._ga

    @property
    def profile(self) -> DataProfile:
        return self._profile
