import numpy as np
from patterns.profile import DataProfile


def detect(data: np.ndarray) -> DataProfile:
    """
    Analyse a time series and produce a DataProfile.
    The profile is used as *input signal* to the GA and adaptation layers.
    """
    data = np.asarray(data, dtype=np.float64)
    n = len(data)

    if n < 4:
        return DataProfile(data_length=n)

    trend_str = _trend_strength(data)
    seasonal_str, period = _seasonal_strength(data)
    noise = _noise_level(data, period)
    stationarity = _stationarity_score(data)

    return DataProfile(
        trend_strength=trend_str,
        seasonal_strength=seasonal_str,
        noise_level=noise,
        seasonal_period=period,
        data_length=n,
        stationarity=stationarity,
    )


# ── Trend detection ─────────────────────────────────────────────────────

def _trend_strength(data: np.ndarray) -> float:
    """
    Measure trend strength via linear regression R².
    Returns 0..1 (0 = no trend, 1 = perfect linear trend).
    """
    n = len(data)
    t = np.arange(n, dtype=np.float64)

    # least-squares linear fit
    t_mean = t.mean()
    d_mean = data.mean()

    ss_tt = np.sum((t - t_mean) ** 2)
    if ss_tt < 1e-12:
        return 0.0

    slope = np.sum((t - t_mean) * (data - d_mean)) / ss_tt
    intercept = d_mean - slope * t_mean
    fitted = slope * t + intercept
    residuals = data - fitted

    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((data - d_mean) ** 2)

    if ss_tot < 1e-12:
        return 0.0

    r_squared = 1.0 - ss_res / ss_tot
    return float(np.clip(r_squared, 0.0, 1.0))


# ── Seasonal detection ───────────────────────────────────────────────────

def _seasonal_strength(data: np.ndarray) -> tuple[float, int]:
    """
    Detect dominant seasonal period via autocorrelation peaks.
    Returns (strength 0..1, period).
    """
    n = len(data)
    if n < 6:
        return 0.0, 0

    # detrend first (remove linear trend)
    t = np.arange(n, dtype=np.float64)
    t_mean = t.mean()
    d_mean = data.mean()
    ss_tt = np.sum((t - t_mean) ** 2)
    if ss_tt > 1e-12:
        slope = np.sum((t - t_mean) * (data - d_mean)) / ss_tt
        detrended = data - (slope * t + (d_mean - slope * t_mean))
    else:
        detrended = data - d_mean

    # compute autocorrelation
    max_lag = min(n // 2, 60)
    if max_lag < 3:
        return 0.0, 0

    acf = _autocorrelation(detrended, max_lag)

    # find peaks in ACF (skip lag 0)
    best_lag = 0
    best_val = 0.0

    for lag in range(2, max_lag):
        if (acf[lag] > acf[lag - 1] and
                acf[lag] > acf[lag + 1] if lag + 1 < len(acf) else True):
            if acf[lag] > best_val:
                best_val = acf[lag]
                best_lag = lag

    strength = float(np.clip(best_val, 0.0, 1.0))

    return strength, best_lag


def _autocorrelation(data: np.ndarray, max_lag: int) -> np.ndarray:
    """Compute normalised autocorrelation for lags 0..max_lag."""
    n = len(data)
    mean = data.mean()
    var = np.sum((data - mean) ** 2)

    if var < 1e-12:
        return np.zeros(max_lag + 1)

    acf = np.zeros(max_lag + 1)
    for lag in range(max_lag + 1):
        acf[lag] = np.sum((data[:n - lag] - mean) * (data[lag:] - mean)) / var

    return acf


# ── Noise level ──────────────────────────────────────────────────────────

def _noise_level(data: np.ndarray, seasonal_period: int) -> float:
    """
    Estimate noise as ratio of residual variance to total variance.
    Returns 0..1 (0 = clean, 1 = pure noise).
    """
    n = len(data)

    # remove trend
    t = np.arange(n, dtype=np.float64)
    t_mean = t.mean()
    d_mean = data.mean()
    ss_tt = np.sum((t - t_mean) ** 2)

    if ss_tt > 1e-12:
        slope = np.sum((t - t_mean) * (data - d_mean)) / ss_tt
        residuals = data - (slope * t + (d_mean - slope * t_mean))
    else:
        residuals = data - d_mean

    # remove seasonal (if detected)
    if seasonal_period > 1 and n >= 2 * seasonal_period:
        seasonal_avg = np.zeros(seasonal_period)
        counts = np.zeros(seasonal_period)
        for i in range(n):
            idx = i % seasonal_period
            seasonal_avg[idx] += residuals[i]
            counts[idx] += 1
        seasonal_avg /= np.maximum(counts, 1)

        for i in range(n):
            residuals[i] -= seasonal_avg[i % seasonal_period]

    total_var = np.var(data)
    if total_var < 1e-12:
        return 0.0

    noise_var = np.var(residuals)
    ratio = noise_var / total_var

    return float(np.clip(ratio, 0.0, 1.0))


# ── Stationarity ─────────────────────────────────────────────────────────

def _stationarity_score(data: np.ndarray) -> float:
    """
    Simple stationarity heuristic based on comparing statistics
    of the first half vs second half of the data.
    Returns 0..1 (1 = very stationary, 0 = clearly non-stationary).
    """
    n = len(data)
    if n < 10:
        return 0.5

    mid = n // 2
    first_half = data[:mid]
    second_half = data[mid:]

    # compare means
    mean_diff = abs(first_half.mean() - second_half.mean())
    mean_scale = max(abs(data.mean()), 1e-10)
    mean_ratio = mean_diff / mean_scale

    # compare variances
    var1 = first_half.var()
    var2 = second_half.var()
    var_scale = max(data.var(), 1e-10)
    var_diff = abs(var1 - var2) / var_scale

    # combine
    score = 1.0 - np.clip(0.5 * mean_ratio + 0.5 * var_diff, 0.0, 1.0)
    return float(score)
