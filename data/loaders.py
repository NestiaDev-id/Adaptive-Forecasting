import numpy as np
import os


# ============================================================================
# CSV Loading
# ============================================================================

def load_csv(path: str, column: int = 0,
             skip_header: bool = True) -> np.ndarray:
    """
    Load a single column from a CSV file as a numpy array.

    Parameters
    ----------
    path : str
        Path to the CSV file.
    column : int
        Column index to extract (0-based).
    skip_header : bool
        Whether to skip the first row.

    Returns
    -------
    np.ndarray of float64
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Data file not found: {path}")

    data = []
    with open(path, "r") as f:
        for i, line in enumerate(f):
            if skip_header and i == 0:
                continue
            parts = line.strip().split(",")
            if column < len(parts):
                try:
                    data.append(float(parts[column]))
                except ValueError:
                    continue
    if not data:
        raise ValueError(f"No numeric data found in column {column} of {path}")
    return np.array(data, dtype=np.float64)


# ============================================================================
# Synthetic Data Generators
# ============================================================================

def generate_synthetic(pattern_type: str = "seasonal",
                       length: int = 200,
                       noise_level: float = 0.1,
                       seed: int = None) -> np.ndarray:
    """
    Generate synthetic time series with a known pattern.

    Parameters
    ----------
    pattern_type : str
        One of: 'stable', 'trending', 'seasonal', 'chaotic', 'regime_change'
    length : int
        Number of data points.
    noise_level : float
        Standard deviation of Gaussian noise (relative to signal amplitude).
    seed : int, optional
        Random seed for reproducibility.

    Returns
    -------
    np.ndarray of float64
    """
    if seed is not None:
        np.random.seed(seed)

    t = np.arange(length, dtype=np.float64)
    noise = np.random.normal(0, noise_level, length)

    generators = {
        "stable":        _gen_stable,
        "trending":      _gen_trending,
        "seasonal":      _gen_seasonal,
        "chaotic":       _gen_chaotic,
        "regime_change": _gen_regime_change,
    }

    gen_func = generators.get(pattern_type.lower())
    if gen_func is None:
        raise ValueError(
            f"Unknown pattern_type '{pattern_type}'. "
            f"Available: {list(generators.keys())}"
        )

    return gen_func(t, noise)


# ---------------------------------------------------------------------------
# Individual generators
# ---------------------------------------------------------------------------

def _gen_stable(t: np.ndarray, noise: np.ndarray) -> np.ndarray:
    """Flat signal around a constant + noise."""
    base = 50.0
    return base + noise * 5


def _gen_trending(t: np.ndarray, noise: np.ndarray) -> np.ndarray:
    """Linear upward trend + slight curvature + noise."""
    trend = 10 + 0.5 * t + 0.001 * t ** 2
    return trend + noise * 5


def _gen_seasonal(t: np.ndarray, noise: np.ndarray) -> np.ndarray:
    """
    Clear seasonal pattern (period=12) with a mild upward trend.
    This is the "classic" case for Holt-Winters.
    """
    period = 12
    trend = 50 + 0.3 * t
    seasonal = 15 * np.sin(2 * np.pi * t / period)
    return trend + seasonal + noise * 3


def _gen_chaotic(t: np.ndarray, noise: np.ndarray) -> np.ndarray:
    """
    High noise, multiple overlapping frequencies, non-stationary variance.
    This is the hardest case — tests how well the system adapts to
    unpredictable data.
    """
    sig1 = 10 * np.sin(2 * np.pi * t / 7)
    sig2 = 5 * np.sin(2 * np.pi * t / 23)
    sig3 = 3 * np.cos(2 * np.pi * t / 3)
    variance_ramp = 1 + 0.02 * t
    return 50 + sig1 + sig2 + sig3 + noise * 10 * variance_ramp


def _gen_regime_change(t: np.ndarray, noise: np.ndarray) -> np.ndarray:
    """
    Data that suddenly changes character midway.
    First half: stable seasonal.  Second half: strong upward trend + chaos.
    This tests the drift detection system.
    """
    n = len(t)
    mid = n // 2
    data = np.zeros(n, dtype=np.float64)

    # Regime 1: calm seasonal
    period = 12
    data[:mid] = (50
                  + 10 * np.sin(2 * np.pi * t[:mid] / period)
                  + noise[:mid] * 2)

    # Regime 2: aggressive trend + high noise
    t2 = t[mid:] - t[mid]
    data[mid:] = (50
                  + 2.0 * t2
                  + 5 * np.sin(2 * np.pi * t2 / 5)
                  + noise[mid:] * 15)

    return data


# ============================================================================
# Multi-environment data (for GA multi-environment training)
# ============================================================================

def generate_multi_environment(length: int = 200,
                               noise_level: float = 0.1,
                               seed: int = 42) -> dict[str, np.ndarray]:
    """
    Generate a full set of environments for multi-environment GA training.

    Returns
    -------
    dict  mapping environment name → time series array
    """
    envs = {}
    for ptype in ("stable", "trending", "seasonal", "chaotic"):
        envs[ptype] = generate_synthetic(
            pattern_type=ptype,
            length=length,
            noise_level=noise_level,
            seed=seed,
        )
    return envs
