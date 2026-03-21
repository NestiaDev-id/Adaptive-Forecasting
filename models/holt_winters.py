import numpy as np
from models.base_model import BaseModel


class HoltWinters(BaseModel):
    """
    Triple Exponential Smoothing (Holt-Winters).
    Supports additive and multiplicative seasonal modes.
    Parameters (alpha, beta, gamma, season_length, mode) are set directly
    or injected by the GA through set_params().
    """

    def __init__(self,
                 alpha: float = 0.3,
                 beta: float = 0.1,
                 gamma: float = 0.1,
                 season_length: int = 12,
                 mode: str = "additive"):
        super().__init__(name="holt_winters")
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.season_length = max(2, int(season_length))
        self.mode = mode  # "additive" or "multiplicative"

        # internal state (populated by fit)
        self._level = 0.0
        self._trend = 0.0
        self._seasons: np.ndarray = np.zeros(self.season_length)
        self._train_data: np.ndarray = np.array([])

    # ── BaseModel interface ──────────────────────────────────────────────

    def get_params(self) -> dict:
        return {
            "alpha": self.alpha,
            "beta": self.beta,
            "gamma": self.gamma,
            "season_length": self.season_length,
            "mode": self.mode,
        }

    def set_params(self, params: dict) -> None:
        if "alpha" in params:
            self.alpha = float(np.clip(params["alpha"], 0.01, 0.99))
        if "beta" in params:
            self.beta = float(np.clip(params["beta"], 0.001, 0.50))
        if "gamma" in params:
            self.gamma = float(np.clip(params["gamma"], 0.001, 0.99))
        if "season_length" in params:
            self.season_length = max(2, int(params["season_length"]))
        if "mode" in params:
            self.mode = params["mode"]
        self._fitted = False

    def fit(self, train_data: np.ndarray) -> "HoltWinters":
        data = np.asarray(train_data, dtype=np.float64)
        n = len(data)
        m = self.season_length

        if n < 2 * m:
            # not enough data for full seasonal init → fall back
            self._level = data[-1] if n > 0 else 0.0
            self._trend = 0.0
            self._seasons = np.zeros(m)
            self._train_data = data
            self._fitted = True
            return self

        # ── Initialisation ───────────────────────────────────────────
        if self.mode == "multiplicative":
            self._fit_multiplicative(data, n, m)
        else:
            self._fit_additive(data, n, m)

        self._train_data = data
        self._fitted = True
        return self

    def forecast(self, horizon: int) -> np.ndarray:
        if not self._fitted:
            raise RuntimeError("Model not fitted. Call fit() first.")

        m = self.season_length
        preds = np.empty(horizon, dtype=np.float64)

        for h in range(1, horizon + 1):
            season_idx = (h - 1) % m
            if self.mode == "multiplicative":
                preds[h - 1] = (self._level + h * self._trend) * self._seasons[season_idx]
            else:
                preds[h - 1] = self._level + h * self._trend + self._seasons[season_idx]

        return preds

    # ── Additive fitting ─────────────────────────────────────────────────

    def _fit_additive(self, data: np.ndarray, n: int, m: int):
        # initial level: mean of first season
        level = np.mean(data[:m])

        # initial trend: average difference between first two seasons
        trend = 0.0
        if n >= 2 * m:
            trend = np.mean((data[m:2 * m] - data[:m]) / m)

        # initial seasonal components
        seasons = np.zeros(m)
        for i in range(m):
            seasons[i] = data[i] - level

        # ── Smoothing pass ───────────────────────────────────────────
        for t in range(m, n):
            s_idx = t % m
            val = data[t]

            new_level = self.alpha * (val - seasons[s_idx]) + (1 - self.alpha) * (level + trend)
            new_trend = self.beta * (new_level - level) + (1 - self.beta) * trend
            seasons[s_idx] = self.gamma * (val - new_level) + (1 - self.gamma) * seasons[s_idx]

            level = new_level
            trend = new_trend

        self._level = level
        self._trend = trend
        self._seasons = seasons

    # ── Multiplicative fitting ───────────────────────────────────────────

    def _fit_multiplicative(self, data: np.ndarray, n: int, m: int):
        # guard against zeros / negatives
        data_safe = np.where(np.abs(data) < 1e-10, 1e-10, data)

        level = np.mean(data_safe[:m])
        trend = 0.0
        if n >= 2 * m:
            trend = np.mean((data_safe[m:2 * m] - data_safe[:m]) / m)

        seasons = np.ones(m)
        for i in range(m):
            seasons[i] = data_safe[i] / level if abs(level) > 1e-10 else 1.0

        for t in range(m, n):
            s_idx = t % m
            val = data_safe[t]

            new_level = (self.alpha * (val / seasons[s_idx])
                         + (1 - self.alpha) * (level + trend))
            new_trend = self.beta * (new_level - level) + (1 - self.beta) * trend

            if abs(new_level) > 1e-10:
                seasons[s_idx] = self.gamma * (val / new_level) + (1 - self.gamma) * seasons[s_idx]

            level = new_level
            trend = new_trend

        self._level = level
        self._trend = trend
        self._seasons = seasons
