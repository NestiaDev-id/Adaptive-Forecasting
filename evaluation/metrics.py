import numpy as np


def mse(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Mean Squared Error."""
    actual = np.asarray(actual, dtype=np.float64)
    predicted = np.asarray(predicted, dtype=np.float64)
    return float(np.mean((actual - predicted) ** 2))


def rmse(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Root Mean Squared Error."""
    return float(np.sqrt(mse(actual, predicted)))


def mae(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Mean Absolute Error."""
    actual = np.asarray(actual, dtype=np.float64)
    predicted = np.asarray(predicted, dtype=np.float64)
    return float(np.mean(np.abs(actual - predicted)))


def mape(actual: np.ndarray, predicted: np.ndarray,
         epsilon: float = 1e-10) -> float:
    """
    Mean Absolute Percentage Error (%).
    Uses epsilon to avoid division by zero.
    """
    actual = np.asarray(actual, dtype=np.float64)
    predicted = np.asarray(predicted, dtype=np.float64)
    return float(np.mean(np.abs((actual - predicted) /
                                (np.abs(actual) + epsilon))) * 100)


def smape(actual: np.ndarray, predicted: np.ndarray,
          epsilon: float = 1e-10) -> float:
    """
    Symmetric Mean Absolute Percentage Error (%).
    More balanced than MAPE when values are near zero.
    """
    actual = np.asarray(actual, dtype=np.float64)
    predicted = np.asarray(predicted, dtype=np.float64)
    denom = np.abs(actual) + np.abs(predicted) + epsilon
    return float(np.mean(2.0 * np.abs(actual - predicted) / denom) * 100)


def r_squared(actual: np.ndarray, predicted: np.ndarray) -> float:
    """
    R² (coefficient of determination).
    1.0 = perfect, 0.0 = same as mean, negative = worse than mean.
    """
    actual = np.asarray(actual, dtype=np.float64)
    predicted = np.asarray(predicted, dtype=np.float64)
    ss_res = np.sum((actual - predicted) ** 2)
    ss_tot = np.sum((actual - np.mean(actual)) ** 2)
    if ss_tot < 1e-12:
        return 0.0
    return float(1.0 - ss_res / ss_tot)


# ---------------------------------------------------------------------------
# Registry – get metric function by name
# ---------------------------------------------------------------------------
METRIC_REGISTRY: dict[str, callable] = {
    "mse":  mse,
    "rmse": rmse,
    "mae":  mae,
    "mape": mape,
    "smape": smape,
    "r_squared": r_squared,
}


def get_metric(name: str):
    """
    Get a metric function by name.

    Parameters
    ----------
    name : str
        One of: mse, rmse, mae, mape, smape, r_squared

    Returns
    -------
    callable  (actual, predicted) → float
    """
    name = name.lower().strip()
    if name not in METRIC_REGISTRY:
        raise ValueError(
            f"Unknown metric '{name}'. "
            f"Available: {list(METRIC_REGISTRY.keys())}"
        )
    return METRIC_REGISTRY[name]
