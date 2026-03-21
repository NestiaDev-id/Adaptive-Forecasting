import numpy as np
from config.settings import REFLEX_DECAY, REFLEX_ERROR_SENSITIVITY, REFLEX_MIN_WEIGHT


class ReflexLayer:
    """
    Layer 1 — Instant error-based weight update.
    The fastest adaptation: adjusts model weights every prediction step
    based on recent error. No GA needed — pure reactive.

    w_i = exp(-sensitivity * error_i)  → normalise
    """

    def __init__(self, model_names: list[str],
                 decay: float = REFLEX_DECAY,
                 sensitivity: float = REFLEX_ERROR_SENSITIVITY,
                 min_weight: float = REFLEX_MIN_WEIGHT):
        self.model_names = list(model_names)
        self.decay = decay
        self.sensitivity = sensitivity
        self.min_weight = min_weight

        # current weights (uniform start)
        n = len(model_names)
        self._weights: dict[str, float] = {
            name: 1.0 / n for name in model_names
        }

        # error history per model (recent window)
        self._error_history: dict[str, list[float]] = {
            name: [] for name in model_names
        }
        self._window = 20

    # ── Core update ──────────────────────────────────────────────────────

    def update(self, errors: dict[str, float]):
        """
        Update weights based on latest errors.

        Parameters
        ----------
        errors : dict
            {model_name: error_value} for the latest prediction step.
        """
        # record history
        for name in self.model_names:
            if name in errors:
                self._error_history[name].append(errors[name])
                if len(self._error_history[name]) > self._window:
                    self._error_history[name] = \
                        self._error_history[name][-self._window:]

        # compute raw weights: exp(-sensitivity * recent_avg_error)
        raw_weights = {}
        for name in self.model_names:
            if self._error_history[name]:
                recent_errors = self._error_history[name][-self._window:]
                avg_error = np.mean(recent_errors)
                raw_weights[name] = np.exp(-self.sensitivity * avg_error)
            else:
                raw_weights[name] = 1.0

        # Apply decay (blend with previous weights)
        for name in self.model_names:
            self._weights[name] = (
                self.decay * self._weights[name] +
                (1 - self.decay) * raw_weights.get(name, self._weights[name])
            )

        # floor + normalise
        self._normalise()

    def get_weights(self) -> dict[str, float]:
        """Return current normalised weights."""
        return dict(self._weights)

    def weighted_prediction(self,
                            predictions: dict[str, np.ndarray]) -> np.ndarray:
        """Combine model predictions using current weights."""
        result = None
        for name, pred in predictions.items():
            w = self._weights.get(name, 0.0)
            if result is None:
                result = w * np.asarray(pred, dtype=np.float64)
            else:
                result += w * np.asarray(pred, dtype=np.float64)
        return result if result is not None else np.array([])

    # ── Reset ────────────────────────────────────────────────────────────

    def reset(self):
        """Reset weights to uniform (used after drift detection)."""
        n = len(self.model_names)
        self._weights = {name: 1.0 / n for name in self.model_names}
        self._error_history = {name: [] for name in self.model_names}

    # ── Private ──────────────────────────────────────────────────────────

    def _normalise(self):
        # apply floor
        for name in self.model_names:
            self._weights[name] = max(self._weights[name], self.min_weight)
        # normalise to sum=1
        total = sum(self._weights.values())
        if total > 0:
            self._weights = {k: v / total for k, v in self._weights.items()}
