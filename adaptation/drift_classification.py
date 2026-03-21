import numpy as np
from adaptation.drift_detection import DriftSignal
from patterns.profile import DataProfile
from patterns.detector import detect


class DriftClassifier:
    """
    Classify the TYPE of drift detected.
    Different drift types require different adaptation responses:

    - sudden     : abrupt change in data distribution
    - gradual    : slow shift over time
    - recurring  : pattern that repeats (e.g. seasonal regime change)
    - incremental: continuous small changes adding up
    """

    def __init__(self, window_size: int = 30):
        self._error_history: list[float] = []
        self._drift_times: list[int] = []
        self._window = window_size
        self._step: int = 0

    def record_error(self, error: float):
        """Feed each step's error (call before or after drift detection)."""
        self._error_history.append(error)
        self._step += 1

    def classify(self, signal: DriftSignal,
                 data_before: np.ndarray = None,
                 data_after: np.ndarray = None) -> str:
        """
        Given a DriftSignal + recent data, classify the drift type.
        Returns one of: 'sudden', 'gradual', 'recurring', 'incremental'
        """
        self._drift_times.append(self._step)

        # Check if this is a recurring drift
        if len(self._drift_times) >= 3:
            intervals = [
                self._drift_times[i] - self._drift_times[i - 1]
                for i in range(1, len(self._drift_times))
            ]
            interval_std = np.std(intervals)
            interval_mean = np.mean(intervals)

            if interval_mean > 0 and interval_std / interval_mean < 0.3:
                return "recurring"

        # Analyse the error pattern to distinguish sudden vs gradual
        if len(self._error_history) >= self._window:
            recent = self._error_history[-self._window:]
            first_half = recent[:len(recent) // 2]
            second_half = recent[len(recent) // 2:]

            mean_change = abs(np.mean(second_half) - np.mean(first_half))
            var_change = abs(np.var(second_half) - np.var(first_half))

            # sudden: big mean jump with low variance change
            if mean_change > 2 * np.std(first_half) and var_change < np.var(first_half):
                return "sudden"

            # gradual: error increasing steadily
            if len(recent) > 5:
                slope = np.polyfit(range(len(recent)), recent, 1)[0]
                if slope > 0.01:
                    return "gradual"

        # Compare data profiles if available
        if data_before is not None and data_after is not None:
            profile_before = detect(data_before)
            profile_after = detect(data_after)
            dist = profile_before.distance(profile_after)

            if dist > 0.5:
                return "sudden"
            elif dist > 0.2:
                return "gradual"

        # Default: high magnitude = sudden, low = incremental
        if signal.magnitude > 10.0:
            return "sudden"

        return "incremental"

    def reset(self):
        self._error_history.clear()
        self._drift_times.clear()
        self._step = 0
