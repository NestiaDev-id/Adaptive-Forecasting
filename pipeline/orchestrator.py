import numpy as np
from patterns.detector import detect
from patterns.profile import DataProfile
from models.registry import build_default_registry
from adaptation.reflex import ReflexLayer
from adaptation.drift_detection import DriftDetector
from adaptation.drift_classification import DriftClassifier
from adaptation.weighting import WeightManager
from adaptation.policy import AdaptationPolicy
from genetic.ga_engine import GAEngine
from genetic.population import Population
from evaluation.metrics import mse
from evaluation.uncertainty import UncertaintyEstimator
from utils.helpers import train_val_split
from utils.logger import EvolutionLogger, get_logger
from config.settings import DEFAULT_FORECAST_HORIZON, DEFAULT_VAL_RATIO


class Orchestrator:
    """
    The Mahoraga Brain — ties all 3 layers together:

    1. Reflex (instant)     : error-based weight update every step
    2. Drift Detector (mid) : detect environment changes → classify → decide
    3. GA Strategist (slow) : evolve model params + strategy in background

    Main loop:
        detect pattern → init models → for each batch:
            all models predict → errors
            reflex updates weights
            drift detector checks for change
            if drift → policy decides action → GA responds
            GA evolves in background
            output: weighted prediction + confidence

    It also does an initial 'training' GA run to find good starting params.
    """

    def __init__(self,
                 ga_generations: int = 80,
                 ga_population: int = 40,
                 forecast_horizon: int = DEFAULT_FORECAST_HORIZON,
                 logger: EvolutionLogger = None):
        self._log = logger or EvolutionLogger("orchestrator")
        self._info = get_logger("orchestrator")

        self._registry = build_default_registry()
        self._model_names = self._registry.list_models()

        # layers
        self._reflex = ReflexLayer(self._model_names)
        self._drift_detector = DriftDetector()
        self._drift_classifier = DriftClassifier()
        self._weight_manager = WeightManager(self._model_names)
        self._policy = AdaptationPolicy(logger=self._log)
        self._uncertainty = UncertaintyEstimator()

        # GA
        self._ga = GAEngine(
            population_size=ga_population,
            max_generations=ga_generations,
            logger=self._log,
        )

        # state
        self._profile: DataProfile = None
        self._models: dict = {}
        self._forecast_horizon = forecast_horizon
        self._history: list[dict] = []

    def run(self, data: np.ndarray,
            val_ratio: float = DEFAULT_VAL_RATIO) -> dict:
        """
        Full pipeline execution.

        Returns
        -------
        dict with:
            predictions, confidence, profile, best_individual,
            drift_events, adaptation_history, fitness_history
        """
        data = np.asarray(data, dtype=np.float64)
        train, val = train_val_split(data, val_ratio)

        # ── Step 1: Detect patterns ──────────────────────────────────
        self._profile = detect(data)
        self._info.info(f"Data profile: {self._profile.summary()}")

        # ── Step 2: Initial GA training ──────────────────────────────
        self._info.info("Starting GA training...")
        population = Population.from_profile(
            self._profile,
            size=self._ga.population_size,
        )
        best = self._ga.run(data, population=population, val_ratio=val_ratio)
        self._info.info(f"GA complete: {best}")

        # ── Step 3: Set up models with best params ───────────────────
        self._setup_models(best, train)

        # ── Step 4: Update weights from GA individual ────────────────
        self._weight_manager.update_ga(best.get_normalised_weights())

        # ── Step 5: Adaptive evaluation loop over validation ─────────
        predictions = np.zeros(len(val))
        confidences = []

        for t in range(len(val)):
            step_result = self._adaptive_step(train, val, t)
            predictions[t] = step_result["prediction"]
            confidences.append(step_result["confidence"])

        # ── Step 6: Final forecast beyond data ───────────────────────
        final_models_pred = self._get_all_predictions(
            data, self._forecast_horizon)
        final_weights = self._weight_manager.get_final_weights()
        forecast = self._weight_manager.weighted_prediction(final_models_pred)

        # confidence & intervals
        final_confidence = self._uncertainty.confidence_score(
            final_models_pred, final_weights)
        lower, upper = self._uncertainty.prediction_interval(forecast)

        return {
            "forecast": forecast,
            "forecast_lower": lower,
            "forecast_upper": upper,
            "confidence": final_confidence,
            "val_predictions": predictions,
            "val_actual": val,
            "val_mse": float(mse(val, predictions)),
            "profile": self._profile,
            "best_individual": best,
            "drift_events": self._drift_detector.history,
            "adaptation_history": self._policy.history,
            "fitness_history": self._ga.fitness_history,
            "final_weights": final_weights,
        }

    # ── Adaptive step (one time-step of the evaluation loop) ─────────────

    def _adaptive_step(self, train, val, t) -> dict:
        # expand training window
        expanded_train = np.concatenate([train, val[:t]]) if t > 0 else train
        actual = val[t]

        # all models predict next step
        model_preds = {}
        model_errors = {}
        for name in self._model_names:
            try:
                self._models[name].fit(expanded_train)
                pred = self._models[name].forecast(1)
                model_preds[name] = pred
                model_errors[name] = abs(pred[0] - actual)
            except Exception:
                model_preds[name] = np.array([np.mean(expanded_train)])
                model_errors[name] = abs(model_preds[name][0] - actual)

        # ── Layer 1: Reflex ──────────────────────────────────────────
        self._reflex.update(model_errors)
        self._weight_manager.update_reflex(self._reflex.get_weights())

        for name, err in model_errors.items():
            self._weight_manager.record_error(name, err)

        # ── Layer 2: Drift Detection ────────────────────────────────
        ensemble_error = abs(
            self._weight_manager.weighted_prediction(model_preds)[0] - actual)
        self._drift_classifier.record_error(ensemble_error)
        self._uncertainty.record_error(ensemble_error)

        drift_signal = self._drift_detector.update(ensemble_error)

        if drift_signal.detected:
            drift_type = self._drift_classifier.classify(drift_signal)
            self._log.drift_detected(
                drift_type, drift_signal.magnitude, drift_signal.location)

            # ── Policy decision ──────────────────────────────────────
            diversity = self._ga.population.diversity() if self._ga.population else 0.5
            stag = self._ga._fitness.stagnation_count

            action = self._policy.decide(
                drift_type, drift_signal,
                current_diversity=diversity,
                stagnation_count=stag,
            )

            # ── Execute adaptation on GA ─────────────────────────────
            self._ga.on_drift(
                action.action,
                reset_fraction=action.params.get("reset_fraction", 0.3))

        # ── Produce prediction ───────────────────────────────────────
        final_weights = self._weight_manager.get_final_weights()
        prediction = sum(
            final_weights.get(name, 0) * model_preds[name][0]
            for name in self._model_names
        )

        confidence = self._uncertainty.confidence_score(model_preds, final_weights)

        return {"prediction": prediction, "confidence": confidence}

    # ── Helpers ──────────────────────────────────────────────────────────

    def _setup_models(self, best_individual, train):
        """Instantiate all models with GA-optimised params."""
        for name in self._model_names:
            model = self._registry.get(name)
            params = best_individual.get_model_params(name)
            model.set_params(params)
            try:
                model.fit(train)
            except Exception:
                pass
            self._models[name] = model

    def _get_all_predictions(self, data, horizon) -> dict[str, np.ndarray]:
        preds = {}
        for name, model in self._models.items():
            try:
                model.fit(data)
                pred = model.forecast(horizon)
                if not np.all(np.isfinite(pred)):
                    pred = np.full(horizon, np.mean(data))
                preds[name] = pred
            except Exception:
                preds[name] = np.full(horizon, np.mean(data))
        return preds
