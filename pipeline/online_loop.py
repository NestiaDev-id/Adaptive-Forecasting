import numpy as np
from pipeline.orchestrator import Orchestrator
from adaptation.reflex import ReflexLayer
from adaptation.drift_detection import DriftDetector
from adaptation.drift_classification import DriftClassifier
from adaptation.weighting import WeightManager
from adaptation.policy import AdaptationPolicy
from evaluation.uncertainty import UncertaintyEstimator
from models.registry import build_default_registry
from utils.logger import EvolutionLogger


class OnlineLoop:
    """
    Streaming mode — process data point-by-point.
    Maintains running state across calls.
    Useful when data arrives in real time.
    """

    def __init__(self, orchestrator: Orchestrator = None,
                 logger: EvolutionLogger = None):
        self._log = logger or EvolutionLogger("online")
        self._registry = build_default_registry()
        self._model_names = self._registry.list_models()

        self._reflex = ReflexLayer(self._model_names)
        self._drift_detector = DriftDetector()
        self._drift_classifier = DriftClassifier()
        self._weight_manager = WeightManager(self._model_names)
        self._policy = AdaptationPolicy(logger=self._log)
        self._uncertainty = UncertaintyEstimator()

        self._models = {}
        self._buffer: list[float] = []
        self._min_buffer = 30  # minimum data points before predictions start
        self._initialised = False
        self._step = 0

    def initialise(self, initial_data: np.ndarray):
        """Warm-start with historical data."""
        self._buffer = list(np.asarray(initial_data, dtype=np.float64))

        # fit models on initial data
        for name in self._model_names:
            model = self._registry.get(name)
            try:
                model.fit(np.array(self._buffer))
            except Exception:
                pass
            self._models[name] = model

        self._initialised = True

    def step(self, new_value: float) -> dict:
        """
        Process one new data point.

        Returns
        -------
        dict with: prediction (next value), confidence, weights, drift_detected
        """
        self._buffer.append(float(new_value))
        self._step += 1
        data = np.array(self._buffer, dtype=np.float64)

        if len(data) < self._min_buffer:
            return {
                "prediction": new_value,
                "confidence": 0.0,
                "weights": {},
                "drift_detected": False,
            }

        # ── Fit & predict ────────────────────────────────────────────
        model_preds = {}
        model_errors = {}
        for name in self._model_names:
            try:
                self._models[name].fit(data)
                pred = self._models[name].forecast(1)
                model_preds[name] = pred
                # error vs last actual (since we don't know future)
                if len(data) > 1:
                    model_errors[name] = abs(pred[0] - data[-1])
                else:
                    model_errors[name] = 0.0
            except Exception:
                model_preds[name] = np.array([np.mean(data)])
                model_errors[name] = 1.0

        # ── Layer 1: Reflex ──────────────────────────────────────────
        self._reflex.update(model_errors)
        self._weight_manager.update_reflex(self._reflex.get_weights())

        # ── Layer 2: Drift ───────────────────────────────────────────
        ensemble_pred = self._weight_manager.weighted_prediction(model_preds)
        ensemble_error = abs(ensemble_pred[0] - data[-1]) if len(data) > 1 else 0.0
        self._drift_classifier.record_error(ensemble_error)

        drift_signal = self._drift_detector.update(ensemble_error)
        drift_detected = drift_signal.detected

        if drift_detected:
            drift_type = self._drift_classifier.classify(drift_signal)
            self._log.drift_detected(
                drift_type, drift_signal.magnitude, drift_signal.location)

        # ── Prediction ───────────────────────────────────────────────
        final_weights = self._weight_manager.get_final_weights()
        prediction = sum(
            final_weights.get(name, 0) * model_preds[name][0]
            for name in self._model_names
        )

        confidence = self._uncertainty.confidence_score(
            model_preds, final_weights)

        return {
            "prediction": prediction,
            "confidence": confidence,
            "weights": final_weights,
            "drift_detected": drift_detected,
        }

    @property
    def buffer_size(self) -> int:
        return len(self._buffer)

    def reset(self):
        self._buffer.clear()
        self._reflex.reset()
        self._drift_detector.reset()
        self._drift_classifier.reset()
        self._weight_manager.reset()
        self._step = 0
        self._initialised = False
