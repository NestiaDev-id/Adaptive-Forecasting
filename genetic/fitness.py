import numpy as np
from evaluation.metrics import get_metric
from config.settings import (
    STAGNATION_LIMIT, FITNESS_SWITCH_COOLDOWN,
    DIVERSITY_THRESHOLD, OVERFITTING_RATIO,
)
from utils.logger import EvolutionLogger


class AdaptiveFitness:
    """
    Fitness controller that CHANGES its objective when the system stalls.

    Lifecycle:
        Normal       → MSE
        Stagnation   → switch to MAE (different error landscape)
        Overfitting  → add regularisation penalty
        Low diversity→ add diversity bonus (reward uniqueness)

    This is how Mahoraga 'adapts when the same attack keeps failing'.
    """

    METRICS_CYCLE = ["mse", "mae", "rmse", "smape"]

    def __init__(self, logger: EvolutionLogger = None):
        self._current_metric_name: str = "mse"
        self._current_metric = get_metric("mse")
        self._metric_index: int = 0

        self._best_fitness: float = float("inf")
        self._stagnation_count: int = 0
        self._last_switch_gen: int = -FITNESS_SWITCH_COOLDOWN
        self._overfitting_penalty: float = 0.0
        self._diversity_bonus_weight: float = 0.0

        self._log = logger

    # ── Core evaluation ──────────────────────────────────────────────────

    def evaluate(self, actual: np.ndarray, predicted: np.ndarray,
                 train_error: float = None,
                 individual_vector: np.ndarray = None,
                 population_mean_vector: np.ndarray = None) -> float:
        """
        Compute fitness score for a prediction.
        Lower = better (it's an error metric).
        """
        base_error = self._current_metric(actual, predicted)

        # ── Overfitting penalty ──────────────────────────────────────
        penalty = 0.0
        if (train_error is not None and
                self._overfitting_penalty > 0 and
                base_error > 1e-10):
            ratio = base_error / max(train_error, 1e-10)
            if ratio > OVERFITTING_RATIO:
                penalty = self._overfitting_penalty * (ratio - 1.0)

        # ── Diversity bonus ──────────────────────────────────────────
        bonus = 0.0
        if (self._diversity_bonus_weight > 0 and
                individual_vector is not None and
                population_mean_vector is not None):
            dist = float(np.linalg.norm(
                individual_vector - population_mean_vector))
            bonus = self._diversity_bonus_weight * dist

        return base_error + penalty - bonus

    # ── Adaptive feedback (called once per generation) ───────────────────

    def update(self, generation: int, best_fitness: float,
               avg_fitness: float, diversity: float,
               train_error: float = None, val_error: float = None):
        """
        Check conditions and adapt the fitness function.
        Called after each generation by the GA engine.
        """

        # ── Stagnation detection ─────────────────────────────────────
        if best_fitness < self._best_fitness - 1e-10:
            self._best_fitness = best_fitness
            self._stagnation_count = 0
        else:
            self._stagnation_count += 1

        # ── React to stagnation: switch metric ───────────────────────
        if (self._stagnation_count >= STAGNATION_LIMIT and
                generation - self._last_switch_gen >= FITNESS_SWITCH_COOLDOWN):

            old_name = self._current_metric_name
            self._metric_index = (self._metric_index + 1) % len(self.METRICS_CYCLE)
            self._current_metric_name = self.METRICS_CYCLE[self._metric_index]
            self._current_metric = get_metric(self._current_metric_name)
            self._last_switch_gen = generation
            self._stagnation_count = 0

            if self._log:
                self._log.fitness_switch(
                    generation, old_name, self._current_metric_name,
                    reason=f"stagnation ({STAGNATION_LIMIT} gens)")

        # ── React to low diversity: enable diversity bonus ───────────
        if diversity < DIVERSITY_THRESHOLD:
            self._diversity_bonus_weight = 0.1
        else:
            self._diversity_bonus_weight = max(
                0.0, self._diversity_bonus_weight - 0.01)

        # ── React to overfitting ─────────────────────────────────────
        if (train_error is not None and val_error is not None and
                train_error > 1e-10):
            ratio = val_error / train_error
            if ratio > OVERFITTING_RATIO:
                self._overfitting_penalty = min(
                    self._overfitting_penalty + 0.05, 0.5)
            else:
                self._overfitting_penalty = max(
                    0.0, self._overfitting_penalty - 0.01)

    # ── State queries ────────────────────────────────────────────────────

    @property
    def current_metric_name(self) -> str:
        return self._current_metric_name

    @property
    def stagnation_count(self) -> int:
        return self._stagnation_count

    @property
    def is_stagnating(self) -> bool:
        return self._stagnation_count > STAGNATION_LIMIT // 2

    def state_summary(self) -> dict:
        return {
            "metric": self._current_metric_name,
            "stagnation": self._stagnation_count,
            "overfitting_penalty": self._overfitting_penalty,
            "diversity_bonus": self._diversity_bonus_weight,
        }
