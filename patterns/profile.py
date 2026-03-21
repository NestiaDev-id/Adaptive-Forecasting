from dataclasses import dataclass, field
import numpy as np


@dataclass
class DataProfile:
    """
    Characterisation of a time series — used as *input signal*
    to the GA and adaptation layers (not as IF-ELSE rules).

    Attributes
    ----------
    trend_strength      : float  0..1 — how strongly data trends
    seasonal_strength   : float  0..1 — how strongly data is seasonal
    noise_level         : float  ≥ 0 — residual variance after decomposition
    seasonal_period     : int    detected dominant period (0 if none)
    data_length         : int    total number of observations
    stationarity        : float  0..1 — rough stationarity score
    """

    trend_strength: float = 0.0
    seasonal_strength: float = 0.0
    noise_level: float = 0.0
    seasonal_period: int = 0
    data_length: int = 0
    stationarity: float = 0.5

    # ── Convenience helpers ──────────────────────────────────────────────

    @property
    def is_seasonal(self) -> bool:
        return self.seasonal_strength > 0.3 and self.seasonal_period > 1

    @property
    def is_trending(self) -> bool:
        return self.trend_strength > 0.3

    @property
    def is_noisy(self) -> bool:
        return self.noise_level > 0.5

    def to_vector(self) -> np.ndarray:
        """Encode profile as a fixed-length feature vector (for memory bank)."""
        return np.array([
            self.trend_strength,
            self.seasonal_strength,
            self.noise_level,
            self.seasonal_period / 52.0,   # normalise
            self.stationarity,
        ], dtype=np.float64)

    def distance(self, other: "DataProfile") -> float:
        """Euclidean distance between two profiles (for pattern matching)."""
        return float(np.linalg.norm(self.to_vector() - other.to_vector()))

    def summary(self) -> str:
        """One-line human-readable summary."""
        flags = []
        if self.is_trending:
            flags.append(f"trend={self.trend_strength:.2f}")
        if self.is_seasonal:
            flags.append(f"season(T={self.seasonal_period})={self.seasonal_strength:.2f}")
        if self.is_noisy:
            flags.append(f"noisy={self.noise_level:.2f}")
        if not flags:
            flags.append("stable")
        return " | ".join(flags)

    def __repr__(self) -> str:
        return (f"DataProfile(trend={self.trend_strength:.2f}, "
                f"season={self.seasonal_strength:.2f}, "
                f"noise={self.noise_level:.2f}, "
                f"period={self.seasonal_period}, "
                f"n={self.data_length})")
