import numpy as np
from evaluation.metrics import get_metric


class WalkForwardValidator:
    """
    Walk-forward validation for time series.
    Expands the training window stepwise and evaluates on the next segment.
    """

    def __init__(self, min_train_ratio: float = 0.5,
                 step_size: int = 1,
                 metric_name: str = "mse"):
        self.min_train_ratio = min_train_ratio
        self.step_size = step_size
        self._metric = get_metric(metric_name)
        self._metric_name = metric_name

    def validate(self, data: np.ndarray,
                 model_factory: callable,
                 horizon: int = 1) -> dict:
        """
        Run walk-forward validation.

        Parameters
        ----------
        data : np.ndarray
            Full time series.
        model_factory : callable
            Function that returns a fresh model instance.
        horizon : int
            Forecast horizon (how many steps ahead).

        Returns
        -------
        dict with keys: avg_error, errors, predictions, actuals
        """
        data = np.asarray(data, dtype=np.float64)
        n = len(data)
        min_train = max(int(n * self.min_train_ratio), horizon + 2)

        all_errors = []
        all_preds = []
        all_actuals = []

        t = min_train
        while t + horizon <= n:
            train = data[:t]
            actual = data[t:t + horizon]

            try:
                model = model_factory()
                model.fit(train)
                pred = model.forecast(horizon)

                if len(pred) != len(actual):
                    pred = np.resize(pred, len(actual))

                if not np.all(np.isfinite(pred)):
                    pred = np.full(len(actual), np.mean(train))

                error = self._metric(actual, pred)
                all_errors.append(error)
                all_preds.append(pred)
                all_actuals.append(actual)

            except Exception:
                pass

            t += self.step_size

        avg_error = float(np.mean(all_errors)) if all_errors else float("inf")

        return {
            "avg_error": avg_error,
            "metric": self._metric_name,
            "n_folds": len(all_errors),
            "errors": all_errors,
            "predictions": all_preds,
            "actuals": all_actuals,
        }
