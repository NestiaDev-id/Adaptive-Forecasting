import numpy as np
from genetic.individual import Individual
from patterns.profile import DataProfile
from config.settings import POPULATION_SIZE


class Population:
    """
    Collection of Individuals with diversity tracking and statistics.
    Supports profile-aware initialisation (seed population based on DataProfile).
    """

    def __init__(self, individuals: list[Individual] = None):
        self.individuals: list[Individual] = individuals or []

    # ── Factory ──────────────────────────────────────────────────────────

    @classmethod
    def random(cls, size: int = POPULATION_SIZE,
               generation: int = 0) -> "Population":
        """Create a random population."""
        inds = [Individual.random(generation) for _ in range(size)]
        return cls(inds)

    @classmethod
    def from_profile(cls, profile: DataProfile,
                     size: int = POPULATION_SIZE,
                     generation: int = 0) -> "Population":
        """
        Create a population seeded with profile-aware bias.
        Individuals are not hard-coded — just nudged toward
        sensible starting regions based on the data characteristics.
        """
        inds = []
        for _ in range(size):
            ind = Individual.random(generation)

            # Bias model weights based on detected patterns
            if profile.is_seasonal:
                ind.model_weights["holt_winters"] += 0.3
                ind.solution_genes["hw_season_length"] = float(
                    max(2, profile.seasonal_period) if profile.seasonal_period > 0 else 12
                )
            if profile.is_trending and not profile.is_seasonal:
                ind.model_weights["arima"] += 0.2
            if profile.is_noisy:
                ind.model_weights["lstm"] += 0.1
                ind.mutation_rate = min(ind.mutation_rate * 1.5, 0.5)

            # Renormalise model weights
            total = sum(ind.model_weights.values())
            if total > 0:
                ind.model_weights = {k: v / total
                                     for k, v in ind.model_weights.items()}

            inds.append(ind)

        return cls(inds)

    # ── Access ───────────────────────────────────────────────────────────

    @property
    def size(self) -> int:
        return len(self.individuals)

    @property
    def best(self) -> Individual:
        return min(self.individuals, key=lambda i: i.fitness)

    @property
    def worst(self) -> Individual:
        return max(self.individuals, key=lambda i: i.fitness)

    def sorted(self) -> list[Individual]:
        return sorted(self.individuals, key=lambda i: i.fitness)

    def top_n(self, n: int) -> list[Individual]:
        return self.sorted()[:n]

    # ── Statistics ───────────────────────────────────────────────────────

    def avg_fitness(self) -> float:
        fits = [i.fitness for i in self.individuals if np.isfinite(i.fitness)]
        return float(np.mean(fits)) if fits else float("inf")

    def best_fitness(self) -> float:
        fits = [i.fitness for i in self.individuals if np.isfinite(i.fitness)]
        return float(min(fits)) if fits else float("inf")

    def avg_mutation_rate(self) -> float:
        return float(np.mean([i.mutation_rate for i in self.individuals]))

    def avg_crossover_rate(self) -> float:
        return float(np.mean([i.crossover_rate for i in self.individuals]))

    # ── Diversity ────────────────────────────────────────────────────────

    def diversity(self) -> float:
        """
        Average pairwise distance (sampled for efficiency).
        0 = all identical, higher = more diverse.
        """
        n = self.size
        if n < 2:
            return 0.0

        # sample up to 100 random pairs
        n_pairs = min(100, n * (n - 1) // 2)
        distances = []
        for _ in range(n_pairs):
            i, j = np.random.choice(n, size=2, replace=False)
            distances.append(
                self.individuals[i].distance(self.individuals[j])
            )
        return float(np.mean(distances))

    # ── Manipulation ─────────────────────────────────────────────────────

    def replace(self, new_individuals: list[Individual]):
        """Replace entire population."""
        self.individuals = new_individuals

    def inject(self, immigrants: list[Individual]):
        """Add immigrants (sorted by fitness, worst individuals replaced)."""
        combined = self.individuals + immigrants
        combined.sort(key=lambda i: i.fitness)
        self.individuals = combined[:self.size]

    def partial_reset(self, fraction: float = 0.3,
                      generation: int = 0):
        """
        Replace the worst `fraction` of the population with fresh randoms.
        Used when drift is detected — like Mahoraga adapting to a new attack.
        """
        n_keep = int(self.size * (1 - fraction))
        kept = self.sorted()[:n_keep]
        n_new = self.size - n_keep
        new = [Individual.random(generation) for _ in range(n_new)]
        self.individuals = kept + new

    def __len__(self) -> int:
        return self.size

    def __iter__(self):
        return iter(self.individuals)

    def __getitem__(self, idx) -> Individual:
        return self.individuals[idx]
