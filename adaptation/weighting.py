import numpy as np
from config.settings import REFLEX_MIN_WEIGHT


class WeightManager:
    """
    Model weight management with confidence tracking.
    Combines reflex updates with GA-inferred ensemble weights.
    Produces the final ensemble prediction.
    """

    def __init__(self, model_names: list[str]):
        self.model_names = list(model_names)
        n = len(model_names)

        # operational weights (from reflex)
        self._reflex_weights: dict[str, float] = {
            name: 1.0 / n for name in model_names
        }

        # strategic weights (from GA)
        self._ga_weights: dict[str, float] = {
            name: 1.0 / n for name in model_names
        }

        # blending factor: how much to trust GA vs reflex
        # 0.0 = pure reflex, 1.0 = pure GA
        self._ga_trust: float = 0.5

        # confidence per model (0..1)
        self._confidence: dict[str, float] = {
            name: 0.5 for name in model_names
        }

        # error accumulator for confidence
        self._error_window: dict[str, list[float]] = {
            name: [] for name in model_names
        }
        self._max_window = 30

    # ── Weight updates ───────────────────────────────────────────────────

    def update_reflex(self, weights: dict[str, float]):
        """Set reflex weights (called by ReflexLayer)."""
        self._reflex_weights.update(weights)
        self._recompute_confidence()

    def update_ga(self, weights: dict[str, float]):
        """Set GA weights (called after GA generation)."""
        self._ga_weights.update(weights)

    def set_ga_trust(self, trust: float):
        """Adjust blend between reflex and GA weights."""
        self._ga_trust = float(np.clip(trust, 0.0, 1.0))

    def record_error(self, model_name: str, error: float):
        """Track error for confidence calculation."""
        if model_name in self._error_window:
            self._error_window[model_name].append(error)
            if len(self._error_window[model_name]) > self._max_window:
                self._error_window[model_name] = \
                    self._error_window[model_name][-self._max_window:]

    # ── Final weights ────────────────────────────────────────────────────

    def get_final_weights(self) -> dict[str, float]:
        """
        Blend reflex + GA weights, adjusted by confidence.
        This is the final weight used for ensemble prediction.
        """
        blended = {}
        for name in self.model_names:
            reflex_w = self._reflex_weights.get(name, 0.0)
            ga_w = self._ga_weights.get(name, 0.0)
            conf = self._confidence.get(name, 0.5)

            # blend
            w = (1 - self._ga_trust) * reflex_w + self._ga_trust * ga_w

            # scale by confidence
            w *= conf

            blended[name] = max(w, REFLEX_MIN_WEIGHT)

        # normalise
        total = sum(blended.values())
        if total > 0:
            blended = {k: v / total for k, v in blended.items()}

        return blended

    def weighted_prediction(self,
                            predictions: dict[str, np.ndarray]) -> np.ndarray:
        """Produce final ensemble prediction."""
        weights = self.get_final_weights()
        result = None
        for name, pred in predictions.items():
            w = weights.get(name, 0.0)
            pred = np.asarray(pred, dtype=np.float64)
            if result is None:
                result = w * pred
            else:
                result += w * pred
        return result if result is not None else np.array([])

    # ── Confidence ───────────────────────────────────────────────────────

    def get_confidence(self) -> dict[str, float]:
        """Return confidence scores per model."""
        return dict(self._confidence)

    def _recompute_confidence(self):
        """Update confidence based on recent error stability."""
        for name in self.model_names:
            errors = self._error_window.get(name, [])
            if len(errors) < 3:
                self._confidence[name] = 0.5
                continue

            recent = errors[-self._max_window:]
            mean_err = np.mean(recent)
            std_err = np.std(recent)

            # low mean + low variance = high confidence
            score = np.exp(-mean_err) * np.exp(-std_err)
            self._confidence[name] = float(np.clip(score, 0.05, 1.0))

    # ── Reset ────────────────────────────────────────────────────────────

    def reset(self):
        n = len(self.model_names)
        self._reflex_weights = {name: 1.0 / n for name in self.model_names}
        self._ga_weights = {name: 1.0 / n for name in self.model_names}
        self._confidence = {name: 0.5 for name in self.model_names}
        self._error_window = {name: [] for name in self.model_names}
