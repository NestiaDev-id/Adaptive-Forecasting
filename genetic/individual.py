import numpy as np
from genetic.chromosome import (
    random_gene, clamp_gene, encode_params, decode_params, GENE_DEFS,
)
from config.settings import (
    MUTATION_RATE_BOUNDS, CROSSOVER_RATE_BOUNDS, MUTATION_STEP_BOUNDS,
)


class Individual:
    """
    A single entity in the Mahoraga GA population.
    Carries THREE layers of DNA that co-evolve:

    1. Solution DNA  — model parameters (alpha, beta, gamma, p, d, q, …)
    2. Strategy DNA   — HOW this individual evolves (mutation rate, crossover rate, step size)
    3. Model DNA      — WHICH model(s) to use + ensemble weights
    """

    def __init__(self):
        # ── Solution DNA (model parameters, keyed by gene name) ──────
        self.solution_genes: dict[str, float] = {}

        # ── Strategy DNA (self-adaptive evolution parameters) ────────
        self.mutation_rate: float = 0.1
        self.crossover_rate: float = 0.7
        self.mutation_step: float = 0.05

        # ── Model DNA (which models & their ensemble weights) ────────
        self.model_weights: dict[str, float] = {
            "holt_winters": 0.5,
            "arima": 0.3,
            "lstm": 0.2,
        }

        # ── Fitness ──────────────────────────────────────────────────
        self.fitness: float = float("inf")  # lower = better (error metric)
        self.fitness_components: dict[str, float] = {}
        self.generation_born: int = 0

    # ── Factory methods ──────────────────────────────────────────────────

    @classmethod
    def random(cls, generation: int = 0) -> "Individual":
        """Create a fully randomised individual."""
        ind = cls()
        ind.generation_born = generation

        # Randomise solution genes for all models
        for gene_name in GENE_DEFS:
            ind.solution_genes[gene_name] = random_gene(gene_name)

        # Randomise strategy DNA
        ind.mutation_rate = np.random.uniform(*MUTATION_RATE_BOUNDS)
        ind.crossover_rate = np.random.uniform(*CROSSOVER_RATE_BOUNDS)
        ind.mutation_step = np.random.uniform(*MUTATION_STEP_BOUNDS)

        # Randomise model weights (normalised)
        raw_w = np.random.dirichlet(np.ones(3))
        ind.model_weights = {
            "holt_winters": float(raw_w[0]),
            "arima": float(raw_w[1]),
            "lstm": float(raw_w[2]),
        }

        return ind

    @classmethod
    def from_params(cls, model_name: str, params: dict,
                    generation: int = 0) -> "Individual":
        """Create an individual from known model parameters."""
        ind = cls.random(generation)
        genes = encode_params(model_name, params)
        ind.solution_genes.update(genes)
        return ind

    # ── Getters for model parameters ─────────────────────────────────────

    def get_model_params(self, model_name: str) -> dict:
        """Decode solution genes into typed model parameters."""
        return decode_params(model_name, self.solution_genes)

    def get_strategy(self) -> dict:
        """Return strategy DNA as a dict."""
        return {
            "mutation_rate": self.mutation_rate,
            "crossover_rate": self.crossover_rate,
            "mutation_step": self.mutation_step,
        }

    def get_normalised_weights(self) -> dict[str, float]:
        """Return model weights normalised to sum=1."""
        total = sum(self.model_weights.values())
        if total < 1e-12:
            n = len(self.model_weights)
            return {k: 1.0 / n for k in self.model_weights}
        return {k: v / total for k, v in self.model_weights.items()}

    # ── Cloning ──────────────────────────────────────────────────────────

    def clone(self) -> "Individual":
        """Deep copy of this individual."""
        new = Individual()
        new.solution_genes = dict(self.solution_genes)
        new.mutation_rate = self.mutation_rate
        new.crossover_rate = self.crossover_rate
        new.mutation_step = self.mutation_step
        new.model_weights = dict(self.model_weights)
        new.fitness = self.fitness
        new.fitness_components = dict(self.fitness_components)
        new.generation_born = self.generation_born
        return new

    # ── Representation ───────────────────────────────────────────────────

    def to_vector(self) -> np.ndarray:
        """Flat numeric vector of all genes (for diversity measurement)."""
        vals = list(self.solution_genes.values())
        vals += [self.mutation_rate, self.crossover_rate, self.mutation_step]
        vals += list(self.model_weights.values())
        return np.array(vals, dtype=np.float64)

    def distance(self, other: "Individual") -> float:
        """Euclidean distance between two individuals."""
        return float(np.linalg.norm(self.to_vector() - other.to_vector()))

    def __repr__(self) -> str:
        w = self.get_normalised_weights()
        best_model = max(w, key=w.get)
        return (f"Individual(fit={self.fitness:.6f}, "
                f"best={best_model}({w[best_model]:.0%}), "
                f"mut={self.mutation_rate:.3f})")

    def __lt__(self, other: "Individual") -> bool:
        """Sort by fitness (lower = better)."""
        return self.fitness < other.fitness
