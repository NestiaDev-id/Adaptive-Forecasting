import numpy as np
from genetic.individual import Individual
from genetic.chromosome import clamp_gene, GENE_DEFS
from config.settings import (
    TOURNAMENT_SIZE,
    MUTATION_RATE_BOUNDS, CROSSOVER_RATE_BOUNDS, MUTATION_STEP_BOUNDS,
    STRATEGY_MUTATION_RATE, TAU,
)


# ── Selection ────────────────────────────────────────────────────────────

def tournament_select(population: list[Individual],
                      k: int = TOURNAMENT_SIZE) -> Individual:
    """Tournament selection: pick k random individuals, return the best."""
    k = min(k, len(population))
    contestants = np.random.choice(len(population), size=k, replace=False)
    best = min(contestants, key=lambda i: population[i].fitness)
    return population[best].clone()


# ── Crossover ────────────────────────────────────────────────────────────

def crossover(parent1: Individual, parent2: Individual,
              generation: int = 0) -> tuple[Individual, Individual]:
    """
    Blend crossover on ALL three DNA layers.
    The crossover rate used is the AVERAGE of both parents'
    strategy DNA (meta-evolution in action).
    """
    cx_rate = (parent1.crossover_rate + parent2.crossover_rate) / 2.0

    child1 = parent1.clone()
    child2 = parent2.clone()
    child1.generation_born = generation
    child2.generation_born = generation
    child1.fitness = float("inf")
    child2.fitness = float("inf")

    if np.random.random() > cx_rate:
        return child1, child2

    alpha = np.random.uniform(0.0, 1.0)

    # ── Solution DNA blend ───────────────────────────────────────────
    for gene in parent1.solution_genes:
        if gene in parent2.solution_genes:
            v1 = parent1.solution_genes[gene]
            v2 = parent2.solution_genes[gene]
            child1.solution_genes[gene] = alpha * v1 + (1 - alpha) * v2
            child2.solution_genes[gene] = (1 - alpha) * v1 + alpha * v2

            # clamp to valid range
            if gene in GENE_DEFS:
                child1.solution_genes[gene] = clamp_gene(gene, child1.solution_genes[gene])
                child2.solution_genes[gene] = clamp_gene(gene, child2.solution_genes[gene])

    # ── Strategy DNA blend ───────────────────────────────────────────
    child1.mutation_rate = alpha * parent1.mutation_rate + (1 - alpha) * parent2.mutation_rate
    child2.mutation_rate = (1 - alpha) * parent1.mutation_rate + alpha * parent2.mutation_rate
    child1.crossover_rate = alpha * parent1.crossover_rate + (1 - alpha) * parent2.crossover_rate
    child2.crossover_rate = (1 - alpha) * parent1.crossover_rate + alpha * parent2.crossover_rate
    child1.mutation_step = alpha * parent1.mutation_step + (1 - alpha) * parent2.mutation_step
    child2.mutation_step = (1 - alpha) * parent1.mutation_step + alpha * parent2.mutation_step

    # ── Model DNA blend ──────────────────────────────────────────────
    for model in parent1.model_weights:
        if model in parent2.model_weights:
            w1 = parent1.model_weights[model]
            w2 = parent2.model_weights[model]
            child1.model_weights[model] = alpha * w1 + (1 - alpha) * w2
            child2.model_weights[model] = (1 - alpha) * w1 + alpha * w2

    return child1, child2


# ── Mutation ─────────────────────────────────────────────────────────────

def mutate(individual: Individual, generation: int = 0) -> Individual:
    """
    Mutate an individual using ITS OWN mutation rate and step size.
    This is the core of meta-evolution: the strategy evolves itself.

    Mutation order:
    1. Strategy DNA first (so the updated strategy applies to solution mutation)
    2. Solution DNA
    3. Model DNA
    """
    ind = individual

    # ── 1. Mutate Strategy DNA (self-adaptation) ─────────────────────
    if np.random.random() < STRATEGY_MUTATION_RATE:
        # "1/5th rule" inspired: strategy genes mutate by log-normal
        tau_local = TAU / np.sqrt(2.0 * len(GENE_DEFS))

        ind.mutation_rate *= np.exp(tau_local * np.random.randn())
        ind.mutation_rate = float(np.clip(ind.mutation_rate, *MUTATION_RATE_BOUNDS))

        ind.crossover_rate *= np.exp(tau_local * np.random.randn())
        ind.crossover_rate = float(np.clip(ind.crossover_rate, *CROSSOVER_RATE_BOUNDS))

        ind.mutation_step *= np.exp(tau_local * np.random.randn())
        ind.mutation_step = float(np.clip(ind.mutation_step, *MUTATION_STEP_BOUNDS))

    # ── 2. Mutate Solution DNA (using this individual's strategy) ────
    for gene_name, value in ind.solution_genes.items():
        if np.random.random() < ind.mutation_rate:
            gdef = GENE_DEFS.get(gene_name)
            if gdef is None:
                continue

            if gdef["type"] == "categorical":
                # flip to another option
                n_options = len(gdef["options"])
                ind.solution_genes[gene_name] = float(
                    np.random.randint(0, n_options))
            else:
                # Gaussian perturbation scaled by individual's step size
                gene_range = gdef["max"] - gdef["min"]
                delta = np.random.randn() * ind.mutation_step * gene_range
                new_val = value + delta
                ind.solution_genes[gene_name] = clamp_gene(gene_name, new_val)

    # ── 3. Mutate Model DNA (ensemble weights) ──────────────────────
    if np.random.random() < ind.mutation_rate:
        models = list(ind.model_weights.keys())
        target = np.random.choice(models)
        delta = np.random.randn() * ind.mutation_step
        ind.model_weights[target] = max(0.01, ind.model_weights[target] + delta)

        # renormalise
        total = sum(ind.model_weights.values())
        if total > 0:
            ind.model_weights = {k: v / total
                                 for k, v in ind.model_weights.items()}

    return ind