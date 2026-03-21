import numpy as np
from models.base_model import BaseModel


class SimpleLSTM(BaseModel):
    """
    Minimal LSTM-style sequence model built on pure numpy.
    Single-layer, single-feature, trained with truncated BPTT.
    Designed to be lightweight enough for GA population evaluation.
    """

    def __init__(self,
                 hidden_size: int = 16,
                 learning_rate: float = 0.01,
                 epochs: int = 50,
                 lookback: int = 10):
        super().__init__(name="lstm")
        self.hidden_size = max(4, int(hidden_size))
        self.learning_rate = float(learning_rate)
        self.epochs = max(1, int(epochs))
        self.lookback = max(2, int(lookback))

        # weights (initialised in _init_weights)
        self._Wf = None  # forget gate
        self._Wi = None  # input gate
        self._Wc = None  # cell candidate
        self._Wo = None  # output gate
        self._Wy = None  # output projection
        self._by = None
        self._init_weights()

        self._train_data: np.ndarray = np.array([])
        self._mean = 0.0
        self._std = 1.0

    # ── BaseModel interface ──────────────────────────────────────────────

    def get_params(self) -> dict:
        return {
            "hidden_size": self.hidden_size,
            "learning_rate": self.learning_rate,
            "epochs": self.epochs,
            "lookback": self.lookback,
        }

    def set_params(self, params: dict) -> None:
        changed = False
        if "hidden_size" in params:
            new_h = max(4, int(params["hidden_size"]))
            if new_h != self.hidden_size:
                self.hidden_size = new_h
                changed = True
        if "learning_rate" in params:
            self.learning_rate = float(np.clip(params["learning_rate"], 1e-5, 0.5))
        if "epochs" in params:
            self.epochs = max(1, int(params["epochs"]))
        if "lookback" in params:
            self.lookback = max(2, int(params["lookback"]))
        if changed:
            self._init_weights()
        self._fitted = False

    def fit(self, train_data: np.ndarray) -> "SimpleLSTM":
        data = np.asarray(train_data, dtype=np.float64)
        self._train_data = data.copy()

        # Normalize
        self._mean = data.mean()
        self._std = data.std()
        if self._std < 1e-10:
            self._std = 1.0
        normed = (data - self._mean) / self._std

        # Build sequences
        X, Y = self._build_sequences(normed)
        if len(X) == 0:
            self._fitted = True
            return self

        # Training loop (simple gradient descent)
        for _ in range(self.epochs):
            total_loss = 0.0
            for i in range(len(X)):
                loss = self._train_step(X[i], Y[i])
                total_loss += loss

        self._fitted = True
        return self

    def forecast(self, horizon: int) -> np.ndarray:
        if not self._fitted:
            raise RuntimeError("Model not fitted. Call fit() first.")

        normed = (self._train_data - self._mean) / self._std
        window = normed[-self.lookback:].tolist()

        preds = []
        for _ in range(horizon):
            seq = np.array(window[-self.lookback:])
            out = self._forward(seq)
            pred = out[-1]
            preds.append(pred)
            window.append(pred)

        preds = np.array(preds) * self._std + self._mean
        return preds

    # ── Internal helpers ─────────────────────────────────────────────────

    def _init_weights(self):
        h = self.hidden_size
        scale = 0.1
        # combined input (1 feature) + hidden → 4 gates
        self._Wf = np.random.randn(1 + h, h) * scale
        self._Wi = np.random.randn(1 + h, h) * scale
        self._Wc = np.random.randn(1 + h, h) * scale
        self._Wo = np.random.randn(1 + h, h) * scale
        # output projection
        self._Wy = np.random.randn(h, 1) * scale
        self._by = np.zeros(1)

    def _build_sequences(self, data: np.ndarray):
        n = len(data)
        if n <= self.lookback:
            return np.array([]), np.array([])

        X, Y = [], []
        for i in range(n - self.lookback):
            X.append(data[i:i + self.lookback])
            Y.append(data[i + self.lookback])
        return np.array(X), np.array(Y)

    @staticmethod
    def _sigmoid(x: np.ndarray) -> np.ndarray:
        x = np.clip(x, -20, 20)
        return 1.0 / (1.0 + np.exp(-x))

    def _forward(self, sequence: np.ndarray) -> np.ndarray:
        h = np.zeros(self.hidden_size)
        c = np.zeros(self.hidden_size)
        outputs = []

        for t in range(len(sequence)):
            x_t = np.array([sequence[t]])
            combined = np.concatenate([x_t, h])

            f = self._sigmoid(combined @ self._Wf)
            i = self._sigmoid(combined @ self._Wi)
            c_cand = np.tanh(combined @ self._Wc)
            o = self._sigmoid(combined @ self._Wo)

            c = f * c + i * c_cand
            h = o * np.tanh(c)

            y = (h @ self._Wy + self._by)[0]
            outputs.append(y)

        return np.array(outputs)

    def _train_step(self, sequence: np.ndarray, target: float) -> float:
        # Forward
        outputs = self._forward(sequence)
        pred = outputs[-1]
        loss = (pred - target) ** 2

        # Simplified gradient: only adjust output projection
        h = np.zeros(self.hidden_size)
        c = np.zeros(self.hidden_size)

        for t in range(len(sequence)):
            x_t = np.array([sequence[t]])
            combined = np.concatenate([x_t, h])
            f = self._sigmoid(combined @ self._Wf)
            i = self._sigmoid(combined @ self._Wi)
            c_cand = np.tanh(combined @ self._Wc)
            o = self._sigmoid(combined @ self._Wo)
            c = f * c + i * c_cand
            h = o * np.tanh(c)

        # Gradient on output layer
        d_loss = 2.0 * (pred - target)
        d_Wy = np.outer(h, np.array([d_loss]))
        d_by = np.array([d_loss])

        # Clip gradients
        d_Wy = np.clip(d_Wy, -1.0, 1.0)
        d_by = np.clip(d_by, -1.0, 1.0)

        self._Wy -= self.learning_rate * d_Wy
        self._by -= self.learning_rate * d_by

        return loss
