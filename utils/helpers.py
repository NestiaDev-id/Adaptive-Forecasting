import numpy as np
import time
from functools import wraps


# ---------------------------------------------------------------------------
# Array / Math helpers
# ---------------------------------------------------------------------------

def normalize(arr: np.ndarray) -> np.ndarray:
    """Min-max normalize an array to [0, 1]."""
    arr = np.asarray(arr, dtype=np.float64)
    mn, mx = arr.min(), arr.max()
    if mx - mn < 1e-12:
        return np.zeros_like(arr)
    return (arr - mn) / (mx - mn)


def standardize(arr: np.ndarray) -> np.ndarray:
    """Z-score standardize (mean=0, std=1)."""
    arr = np.asarray(arr, dtype=np.float64)
    std = arr.std()
    if std < 1e-12:
        return np.zeros_like(arr)
    return (arr - arr.mean()) / std


def softmax(arr: np.ndarray) -> np.ndarray:
    """Numerically stable softmax."""
    arr = np.asarray(arr, dtype=np.float64)
    shifted = arr - arr.max()
    exp_vals = np.exp(shifted)
    return exp_vals / exp_vals.sum()


def clip(value: float, lo: float, hi: float) -> float:
    """Clip a scalar to [lo, hi]."""
    return max(lo, min(hi, value))


def weighted_average(values: np.ndarray, weights: np.ndarray) -> float:
    """Compute weighted average. Weights are normalized internally."""
    values = np.asarray(values, dtype=np.float64)
    weights = np.asarray(weights, dtype=np.float64)
    w_sum = weights.sum()
    if w_sum < 1e-12:
        return float(np.mean(values))
    return float(np.dot(values, weights) / w_sum)


def moving_average(arr: np.ndarray, window: int) -> np.ndarray:
    """Simple moving average with given window size."""
    arr = np.asarray(arr, dtype=np.float64)
    if window < 1 or window > len(arr):
        return arr.copy()
    cumsum = np.cumsum(arr)
    cumsum[window:] = cumsum[window:] - cumsum[:-window]
    result = np.full_like(arr, np.nan)
    result[window - 1:] = cumsum[window - 1:] / window
    return result


def exponential_weights(n: int, decay: float = 0.95) -> np.ndarray:
    """Generate exponentially decaying weights (most recent = highest)."""
    weights = np.array([decay ** i for i in range(n - 1, -1, -1)],
                       dtype=np.float64)
    return weights / weights.sum()


# ---------------------------------------------------------------------------
# Train / Validation split for time series
# ---------------------------------------------------------------------------

def train_val_split(data: np.ndarray,
                    val_ratio: float = 0.2) -> tuple:
    """
    Split time series into train and validation sets.
    Keeps temporal order (no shuffling).

    Returns
    -------
    (train, val) : tuple of np.ndarray
    """
    data = np.asarray(data, dtype=np.float64)
    split_idx = int(len(data) * (1.0 - val_ratio))
    split_idx = max(1, min(split_idx, len(data) - 1))
    return data[:split_idx], data[split_idx:]


# ---------------------------------------------------------------------------
# Timing decorator
# ---------------------------------------------------------------------------

def timed(func):
    """Decorator that logs execution time."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        return result, elapsed
    return wrapper


# ---------------------------------------------------------------------------
# Random reproducibility
# ---------------------------------------------------------------------------

def set_seed(seed: int = 42):
    """Set numpy random seed for reproducibility."""
    np.random.seed(seed)


# ---------------------------------------------------------------------------
# Safe division
# ---------------------------------------------------------------------------

def safe_div(a: float, b: float, default: float = 0.0) -> float:
    """Division that returns *default* when divisor is near zero."""
    if abs(b) < 1e-12:
        return default
    return a / b
