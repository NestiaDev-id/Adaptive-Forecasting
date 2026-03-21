import numpy as np
from collections import deque
from genetic.individual import Individual
from patterns.profile import DataProfile
from config.settings import (
    FAILURE_MEMORY_SIZE, SUCCESS_MEMORY_SIZE, PATTERN_MEMORY_SIZE,
)
from utils.logger import EvolutionLogger


class MemoryBank:
    """
    The Mahoraga memory system — three banks that let the GA learn from history:

    1. Failure Bank  — parameter regions that consistently fail → avoid
    2. Success Bank  — elite solutions from past runs → reintroduce when needed
    3. Pattern Bank  — DataProfile → Strategy DNA mapping → warm-start future runs
    """

    def __init__(self, logger: EvolutionLogger = None):
        self._failure_bank: deque[np.ndarray] = deque(maxlen=FAILURE_MEMORY_SIZE)
        self._failure_fitness: deque[float] = deque(maxlen=FAILURE_MEMORY_SIZE)

        self._success_bank: deque[Individual] = deque(maxlen=SUCCESS_MEMORY_SIZE)

        self._pattern_bank: list[tuple[DataProfile, dict]] = []
        self._pattern_max = PATTERN_MEMORY_SIZE

        self._log = logger

    # ── Failure Bank ─────────────────────────────────────────────────────

    def record_failure(self, individual: Individual, threshold: float = None):
        """
        Record a bad parameter region.
        Called when an individual's fitness is among the worst.
        """
        vec = individual.to_vector()
        self._failure_bank.append(vec)
        self._failure_fitness.append(individual.fitness)

        if self._log:
            self._log.memory_store(
                "failure",
                f"fit={individual.fitness:.6f} (bank size={len(self._failure_bank)})")

    def failure_penalty(self, individual: Individual,
                        radius: float = 0.5) -> float:
        """
        Compute penalty if individual is close to known failure regions.
        The GA uses this to steer away from bad areas.
        """
        if not self._failure_bank:
            return 0.0

        vec = individual.to_vector()
        penalty = 0.0
        for fail_vec in self._failure_bank:
            dist = float(np.linalg.norm(vec - fail_vec))
            if dist < radius:
                penalty += (radius - dist) / radius * 0.1

        return penalty

    # ── Success Bank ─────────────────────────────────────────────────────

    def record_success(self, individual: Individual):
        """Store an elite individual for potential future reintroduction."""
        clone = individual.clone()
        self._success_bank.append(clone)

        if self._log:
            self._log.memory_store(
                "success",
                f"fit={individual.fitness:.6f} (bank size={len(self._success_bank)})")

    def recall_elites(self, n: int = 3) -> list[Individual]:
        """
        Recall top-N elite solutions from success bank.
        Used when diversity drops — inject proven solutions back.
        """
        if not self._success_bank:
            return []

        elites = sorted(self._success_bank, key=lambda i: i.fitness)[:n]

        if self._log and elites:
            self._log.memory_recall(
                "success",
                f"recalled {len(elites)} elites "
                f"(best fit={elites[0].fitness:.6f})")

        return [e.clone() for e in elites]

    # ── Pattern Bank ─────────────────────────────────────────────────────

    def record_pattern(self, profile: DataProfile,
                       best_individual: Individual):
        """
        Map a data profile to the strategy DNA that worked best.
        Enables warm-starting on similar future data.
        """
        strategy = best_individual.get_strategy()

        # check if similar profile exists (update if closer)
        for i, (saved_profile, _) in enumerate(self._pattern_bank):
            if saved_profile.distance(profile) < 0.1:
                self._pattern_bank[i] = (profile, strategy)
                if self._log:
                    self._log.memory_store(
                        "pattern", f"updated existing pattern entry")
                return

        if len(self._pattern_bank) < self._pattern_max:
            self._pattern_bank.append((profile, strategy))
            if self._log:
                self._log.memory_store(
                    "pattern",
                    f"new pattern (bank size={len(self._pattern_bank)})")

    def recall_strategy(self, profile: DataProfile,
                        max_distance: float = 0.5) -> dict | None:
        """
        Find the best matching strategy DNA for a given data profile.
        Returns None if no close match is found.
        """
        best_match = None
        best_dist = max_distance

        for saved_profile, strategy in self._pattern_bank:
            dist = saved_profile.distance(profile)
            if dist < best_dist:
                best_dist = dist
                best_match = strategy

        if best_match and self._log:
            self._log.memory_recall(
                "pattern",
                f"found match (dist={best_dist:.3f})")

        return best_match

    # ── Batch operations ─────────────────────────────────────────────────

    def update_from_generation(self, population_sorted: list[Individual],
                               top_n: int = 3, bottom_n: int = 5):
        """Called after each generation: store best & worst."""
        for ind in population_sorted[:top_n]:
            self.record_success(ind)
        for ind in population_sorted[-bottom_n:]:
            self.record_failure(ind)

    # ── State ────────────────────────────────────────────────────────────

    def summary(self) -> dict:
        return {
            "failure_bank_size": len(self._failure_bank),
            "success_bank_size": len(self._success_bank),
            "pattern_bank_size": len(self._pattern_bank),
        }
