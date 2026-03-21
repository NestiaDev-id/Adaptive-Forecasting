import numpy as np
from models.base_model import BaseModel


class ARIMA(BaseModel):
    """
    Lightweight ARIMA(p,d,q) implementation using pure numpy.
    AR coefficients are estimated via least-squares (Yule-Walker approx).
    MA part is approximated through residual feedback.
    """

    def __init__(self, p: int = 2, d: int = 1, q: int = 1):
        super().__init__(name="arima")
        self.p = max(0, int(p))  # AR order
        self.d = max(0, int(d))  # differencing order
        self.q = max(0, int(q))  # MA order

        self._ar_coeffs: np.ndarray = np.zeros(max(1, self.p))
        self._ma_coeffs: np.ndarray = np.zeros(max(1, self.q))
        self._residuals: np.ndarray = np.array([])
        self._diff_data: np.ndarray = np.array([])
        self._original_tail: list[float] = []
        self._train_data: np.ndarray = np.array([])

    # ── BaseModel interface ──────────────────────────────────────────────

    def get_params(self) -> dict:
        return {"p": self.p, "d": self.d, "q": self.q}

    def set_params(self, params: dict) -> None:
        if "p" in params:
            self.p = max(0, int(params["p"]))
        if "d" in params:
            self.d = max(0, min(2, int(params["d"])))
        if "q" in params:
            self.q = max(0, int(params["q"]))
        self._fitted = False

    def fit(self, train_data: np.ndarray) -> "ARIMA":
        data = np.asarray(train_data, dtype=np.float64).copy()
        self._train_data = data.copy()

        # ── Differencing ─────────────────────────────────────────────
        self._original_tail = []
        diff = data.copy()
        for _ in range(self.d):
            self._original_tail.append(diff[-1])
            diff = np.diff(diff)

        self._diff_data = diff

        # ── Estimate AR coefficients (Yule-Walker via least-squares) ─
        if self.p > 0 and len(diff) > self.p + 1:
            self._ar_coeffs = self._estimate_ar(diff, self.p)
        else:
            self._ar_coeffs = np.zeros(max(1, self.p))

        # ── Estimate MA coefficients from residuals ──────────────────
        self._residuals = self._compute_residuals(diff)
        if self.q > 0 and len(self._residuals) > self.q + 1:
            self._ma_coeffs = self._estimate_ma(self._residuals, self.q)
        else:
            self._ma_coeffs = np.zeros(max(1, self.q))

        self._fitted = True
        return self

    def forecast(self, horizon: int) -> np.ndarray:
        if not self._fitted:
            raise RuntimeError("Model not fitted. Call fit() first.")

        diff = self._diff_data.copy().tolist()
        residuals = self._residuals.copy().tolist()

        preds_diff = []
        for _ in range(horizon):
            # AR component
            ar_val = 0.0
            if self.p > 0:
                for j in range(min(self.p, len(diff))):
                    ar_val += self._ar_coeffs[j] * diff[-(j + 1)]

            # MA component
            ma_val = 0.0
            if self.q > 0:
                for j in range(min(self.q, len(residuals))):
                    ma_val += self._ma_coeffs[j] * residuals[-(j + 1)]

            pred = ar_val + ma_val
            preds_diff.append(pred)
            diff.append(pred)
            residuals.append(0.0)  # future residuals unknown

        # ── Invert differencing ──────────────────────────────────────
        preds = np.array(preds_diff, dtype=np.float64)
        preds = self._invert_diff(preds)
        return preds

    # ── Private helpers ──────────────────────────────────────────────────

    @staticmethod
    def _estimate_ar(data: np.ndarray, p: int) -> np.ndarray:
        n = len(data)
        if n <= p:
            return np.zeros(p)

        # build Toeplitz-style matrix for least-squares
        X = np.zeros((n - p, p))
        y = data[p:]
        for i in range(n - p):
            for j in range(p):
                X[i, j] = data[p + i - j - 1]

        try:
            coeffs, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
        except np.linalg.LinAlgError:
            coeffs = np.zeros(p)

        return coeffs

    def _compute_residuals(self, data: np.ndarray) -> np.ndarray:
        n = len(data)
        residuals = np.zeros(n)
        p = min(self.p, n - 1)

        for t in range(p, n):
            pred = 0.0
            for j in range(p):
                pred += self._ar_coeffs[j] * data[t - j - 1]
            residuals[t] = data[t] - pred

        return residuals

    @staticmethod
    def _estimate_ma(residuals: np.ndarray, q: int) -> np.ndarray:
        n = len(residuals)
        if n <= q:
            return np.zeros(q)

        X = np.zeros((n - q, q))
        y = residuals[q:]
        for i in range(n - q):
            for j in range(q):
                X[i, j] = residuals[q + i - j - 1]

        try:
            coeffs, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
        except np.linalg.LinAlgError:
            coeffs = np.zeros(q)

        return coeffs

    def _invert_diff(self, preds_diff: np.ndarray) -> np.ndarray:
        result = preds_diff.copy()
        for d_level in range(self.d):
            if d_level < len(self._original_tail):
                last_val = self._original_tail[-(d_level + 1)]
            else:
                last_val = self._train_data[-1]
            cumulative = np.empty_like(result)
            cumulative[0] = last_val + result[0]
            for i in range(1, len(result)):
                cumulative[i] = cumulative[i - 1] + result[i]
            result = cumulative
        return result
