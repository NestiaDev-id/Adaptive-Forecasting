import numpy as np
from evaluation.metrics import mse, mae


class UncertaintyEstimator:
    """
    Prediction confidence scoring based on:
    1. Ensemble agreement (low disagreement = high confidence)
    2. Error stability (consistent errors = more predictable)
    3. Prediction interval estimation
    """

    def __init__(self, window_size: int = 20):
        self._error_history: list[float] = []
        self._window = window_size

    def record_error(self, error: float):
        self._error_history.append(error)
        if len(self._error_history) > self._window:
            self._error_history = self._error_history[-self._window:]

    def confidence_score(self,
                         model_predictions: dict[str, np.ndarray],
                         weights: dict[str, float]) -> float:
        """
        Compute confidence in the ensemble prediction (0..1).
        High agreement among well-weighted models → high confidence.
        """
        preds = []
        ws = []
        for name, pred in model_predictions.items():
            w = weights.get(name, 0.0)
            if w > 0.01:
                preds.append(np.asarray(pred, dtype=np.float64))
                ws.append(w)

        if len(preds) < 2:
            return 0.5

        # weighted disagreement
        weighted_mean = sum(w * p for w, p in zip(ws, preds)) / sum(ws)
        disagreement = sum(
            w * np.mean((p - weighted_mean) ** 2)
            for w, p in zip(ws, preds)
        ) / sum(ws)

        # normalise disagreement to 0..1
        scale = max(np.std(weighted_mean), 1e-10)
        normalised_dis = min(disagreement / (scale ** 2), 1.0)

        # error stability component
        stability = 1.0
        if len(self._error_history) >= 5:
            err_std = np.std(self._error_history[-self._window:])
            err_mean = np.mean(np.abs(self._error_history[-self._window:]))
            if err_mean > 1e-10:
                cv = err_std / err_mean  # coefficient of variation
                stability = np.exp(-cv)

        confidence = (1.0 - normalised_dis) * stability
        return float(np.clip(confidence, 0.0, 1.0))

    def prediction_interval(self,
                            ensemble_pred: np.ndarray,
                            level: float = 0.95) -> tuple[np.ndarray, np.ndarray]:
        """
        Estimate prediction intervals based on historical error distribution.
        """
        if len(self._error_history) < 5:
            margin = np.std(ensemble_pred) * 2 if len(ensemble_pred) > 1 else 1.0
            return ensemble_pred - margin, ensemble_pred + margin

        errors = np.array(self._error_history)
        error_std = np.std(errors)

        # approximate z-score for the given level
        z = 1.96 if level >= 0.95 else 1.645 if level >= 0.90 else 1.28

        # widen interval further into the future
        horizons = np.arange(1, len(ensemble_pred) + 1)
        widening = np.sqrt(horizons)

        margin = z * error_std * widening

        lower = ensemble_pred - margin
        upper = ensemble_pred + margin
        return lower, upper
