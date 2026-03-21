import numpy as np
from dataclasses import dataclass
from adaptation.drift_detection import DriftSignal
from utils.logger import EvolutionLogger


@dataclass
class AdaptationAction:
    """Decision from the policy engine."""
    action: str          # INCREASE_MUTATION, PARTIAL_RESET, FULL_RESET, SWITCH_FITNESS, INJECT_DIVERSITY
    confidence: float    # 0..1 how confident the policy is
    reason: str = ""
    params: dict = None  # extra parameters (e.g. reset_fraction)

    def __post_init__(self):
        if self.params is None:
            self.params = {}


class AdaptationPolicy:
    """
    Decision engine — takes drift signal + drift type → decides response.
    NOT IF-ELSE statis. Uses scoring-based approach: each possible action
    gets a score based on context, highest score wins.
    """

    # possible actions and their base applicability per drift type
    ACTION_SCORES = {
        "sudden": {
            "FULL_RESET": 0.7,
            "PARTIAL_RESET": 0.5,
            "INCREASE_MUTATION": 0.3,
            "SWITCH_FITNESS": 0.2,
            "INJECT_DIVERSITY": 0.4,
        },
        "gradual": {
            "FULL_RESET": 0.1,
            "PARTIAL_RESET": 0.3,
            "INCREASE_MUTATION": 0.7,
            "SWITCH_FITNESS": 0.4,
            "INJECT_DIVERSITY": 0.3,
        },
        "recurring": {
            "FULL_RESET": 0.1,
            "PARTIAL_RESET": 0.2,
            "INCREASE_MUTATION": 0.3,
            "SWITCH_FITNESS": 0.2,
            "INJECT_DIVERSITY": 0.6,  # recall from memory
        },
        "incremental": {
            "FULL_RESET": 0.05,
            "PARTIAL_RESET": 0.2,
            "INCREASE_MUTATION": 0.5,
            "SWITCH_FITNESS": 0.3,
            "INJECT_DIVERSITY": 0.2,
        },
    }

    def __init__(self, logger: EvolutionLogger = None):
        self._log = logger
        self._action_history: list[AdaptationAction] = []
        self._drift_count: int = 0

    def decide(self, drift_type: str,
               signal: DriftSignal,
               current_diversity: float = 0.5,
               stagnation_count: int = 0) -> AdaptationAction:
        """
        Score all possible actions and return the best one.

        Context factors that modify scores:
        - drift magnitude → favour stronger resets
        - low diversity → favour INJECT_DIVERSITY
        - high stagnation → favour SWITCH_FITNESS
        - recurring pattern → favour INJECT_DIVERSITY (recall from memory)
        """
        self._drift_count += 1

        base_scores = self.ACTION_SCORES.get(
            drift_type, self.ACTION_SCORES["incremental"]).copy()

        # ── Context modifiers ────────────────────────────────────────
        scores = {}
        for action, base in base_scores.items():
            score = base

            # magnitude boost
            if signal.magnitude > 10:
                if action in ("FULL_RESET", "PARTIAL_RESET"):
                    score += 0.2
            elif signal.magnitude > 5:
                if action == "INCREASE_MUTATION":
                    score += 0.15

            # diversity context
            if current_diversity < 0.1:
                if action == "INJECT_DIVERSITY":
                    score += 0.3
                if action == "FULL_RESET":
                    score += 0.1

            # stagnation context
            if stagnation_count > 10:
                if action == "SWITCH_FITNESS":
                    score += 0.25
                if action == "INCREASE_MUTATION":
                    score += 0.1

            # repeated drifts → escalate response
            if self._drift_count > 3:
                if action in ("FULL_RESET", "PARTIAL_RESET"):
                    score += 0.15

            scores[action] = float(np.clip(score, 0.0, 1.0))

        # ── Pick best action ─────────────────────────────────────────
        best_action = max(scores, key=scores.get)
        best_score = scores[best_action]

        # determine action parameters
        params = {}
        if best_action == "PARTIAL_RESET":
            # reset fraction scales with magnitude
            params["reset_fraction"] = float(
                np.clip(signal.magnitude / 20.0, 0.2, 0.6))

        result = AdaptationAction(
            action=best_action,
            confidence=best_score,
            reason=f"{drift_type} drift (mag={signal.magnitude:.2f})",
            params=params,
        )

        self._action_history.append(result)

        if self._log:
            self._log.adaptation(
                result.action,
                reason=result.reason,
                confidence=result.confidence)

        return result

    @property
    def history(self) -> list[AdaptationAction]:
        return list(self._action_history)

    def reset(self):
        self._drift_count = 0
        self._action_history.clear()
