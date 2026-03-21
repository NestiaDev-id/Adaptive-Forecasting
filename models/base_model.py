from abc import ABC, abstractmethod
import numpy as np


class BaseModel(ABC):
    """
    Abstract base for all forecasting models.
    Every model (Holt-Winters, ARIMA, LSTM, …) must implement this interface
    so the GA and ensemble layer can treat them uniformly.
    """

    def __init__(self, name: str = "base"):
        self.name = name
        self._fitted = False

    # ── Core interface ───────────────────────────────────────────────────

    @abstractmethod
    def fit(self, train_data: np.ndarray) -> "BaseModel":
        """Fit the model on training data. Returns self for chaining."""
        ...

    @abstractmethod
    def forecast(self, horizon: int) -> np.ndarray:
        """Produce *horizon* future predictions. Must call fit() first."""
        ...

    @abstractmethod
    def get_params(self) -> dict:
        """Return current model parameters as a flat dict."""
        ...

    @abstractmethod
    def set_params(self, params: dict) -> None:
        """Set model parameters from a flat dict (used by GA)."""
        ...

    # ── Shared helpers ───────────────────────────────────────────────────

    @property
    def is_fitted(self) -> bool:
        return self._fitted

    def fit_predict(self, train_data: np.ndarray, horizon: int) -> np.ndarray:
        """Convenience: fit + forecast in one call."""
        self.fit(train_data)
        return self.forecast(horizon)

    def clone(self) -> "BaseModel":
        """Create a fresh instance with the same parameters."""
        new = self.__class__.__new__(self.__class__)
        new.__init__()
        new.set_params(self.get_params())
        return new

    def __repr__(self) -> str:
        params = self.get_params()
        param_str = ", ".join(f"{k}={v}" for k, v in params.items())
        return f"{self.__class__.__name__}({param_str})"
