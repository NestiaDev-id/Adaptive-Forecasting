import numpy as np
from dataclasses import dataclass
from config.settings import (
    DRIFT_CUSUM_THRESHOLD, DRIFT_CUSUM_DRIFT_RATE,
    DRIFT_MIN_WINDOW, DRIFT_COOLDOWN,
)


@dataclass
class DriftSignal:
    """Output from drift detection."""
    detected: bool = False
    magnitude: float = 0.0
    location: int = -1
    method: str = ""


class CUSUMDetector:
    """
    CUSUM (Cumulative Sum) drift detector.
    Detects mean shifts by tracking cumulative deviations
    from the expected error level.
    """

    def __init__(self,
                 threshold: float = DRIFT_CUSUM_THRESHOLD,
                 drift_rate: float = DRIFT_CUSUM_DRIFT_RATE,
                 min_window: int = DRIFT_MIN_WINDOW,
                 cooldown: int = DRIFT_COOLDOWN):
        self.threshold = threshold
        self.drift_rate = drift_rate
        self.min_window = min_window
        self.cooldown = cooldown

        self._s_pos: float = 0.0
        self._s_neg: float = 0.0
        self._mean: float = 0.0
        self._count: int = 0
        self._last_alarm: int = -cooldown

    def update(self, error: float) -> DriftSignal:
        """
        Feed one new error observation.
        Returns DriftSignal with detected=True if drift is found.
        """
        self._count += 1

        # running mean (incremental)
        self._mean += (error - self._mean) / self._count

        if self._count < self.min_window:
            return DriftSignal()

        # CUSUM statistics
        self._s_pos = max(0, self._s_pos + error - self._mean - self.drift_rate)
        self._s_neg = max(0, self._s_neg - error + self._mean - self.drift_rate)

        magnitude = max(self._s_pos, self._s_neg)

        # check alarm
        if (magnitude > self.threshold and
                self._count - self._last_alarm >= self.cooldown):
            self._last_alarm = self._count
            self._s_pos = 0.0
            self._s_neg = 0.0
            return DriftSignal(
                detected=True,
                magnitude=magnitude,
                location=self._count,
                method="cusum",
            )

        return DriftSignal()

    def reset(self):
        self._s_pos = 0.0
        self._s_neg = 0.0
        self._mean = 0.0
        self._count = 0
        self._last_alarm = -self.cooldown


class PageHinkleyDetector:
    """
    Page-Hinkley test — a secondary drift detector.
    More sensitive to gradual drifts than CUSUM.
    """

    def __init__(self, threshold: float = 50.0,
                 delta: float = 0.005,
                 min_window: int = DRIFT_MIN_WINDOW):
        self.threshold = threshold
        self.delta = delta
        self.min_window = min_window

        self._sum: float = 0.0
        self._mean: float = 0.0
        self._count: int = 0

    def update(self, error: float) -> DriftSignal:
        self._count += 1
        self._mean += (error - self._mean) / self._count

        self._sum += error - self._mean - self.delta

        if self._count < self.min_window:
            return DriftSignal()

        if abs(self._sum) > self.threshold:
            magnitude = abs(self._sum)
            self._sum = 0.0
            return DriftSignal(
                detected=True,
                magnitude=magnitude,
                location=self._count,
                method="page_hinkley",
            )

        return DriftSignal()

    def reset(self):
        self._sum = 0.0
        self._mean = 0.0
        self._count = 0


class DriftDetector:
    """
    Combined drift detection using CUSUM + Page-Hinkley.
    Fires alarm when EITHER detector triggers.
    """

    def __init__(self):
        self.cusum = CUSUMDetector()
        self.page_hinkley = PageHinkleyDetector()
        self._history: list[DriftSignal] = []

    def update(self, error: float) -> DriftSignal:
        sig_cusum = self.cusum.update(error)
        sig_ph = self.page_hinkley.update(error)

        # prioritise CUSUM, fallback to Page-Hinkley
        if sig_cusum.detected:
            self._history.append(sig_cusum)
            return sig_cusum
        if sig_ph.detected:
            self._history.append(sig_ph)
            return sig_ph

        return DriftSignal()

    def reset(self):
        self.cusum.reset()
        self.page_hinkley.reset()

    @property
    def drift_count(self) -> int:
        return len(self._history)

    @property
    def history(self) -> list[DriftSignal]:
        return list(self._history)
