import numpy as np
from genetic.individual import Individual
from genetic.population import Population
from genetic.operators import tournament_select, crossover, mutate
from genetic.fitness import AdaptiveFitness
from genetic.memory import MemoryBank
from models.registry import build_default_registry
from evaluation.metrics import mse
from utils.helpers import train_val_split
from utils.logger import EvolutionLogger
from config.settings import (
    POPULATION_SIZE, MAX_GENERATIONS, ELITISM_COUNT,
    DIVERSITY_THRESHOLD, DEFAULT_VAL_RATIO,
)


class GAEngine:
    """
    Mahoraga GA — the Layer 3 strategist.

    Runs an evolutionary loop where:
    - Solution DNA (model params) evolves to minimise forecast error
    - Strategy DNA (mutation/crossover rates) co-evolves
    - Model DNA (ensemble weights) co-evolves
    - Fitness function adapts (switches metrics on stagnation)
    - Memory system avoids past failures and reuses successes
    """

    def __init__(self,
                 population_size: int = POPULATION_SIZE,
                 max_generations: int = MAX_GENERATIONS,
                 elitism: int = ELITISM_COUNT,
                 logger: EvolutionLogger = None):
        self.population_size = population_size
        self.max_generations = max_generations
        self.elitism = elitism

        self._log = logger or EvolutionLogger()
        self._fitness = AdaptiveFitness(logger=self._log)
        self._memory = MemoryBank(logger=self._log)
        self._registry = build_default_registry()

        self._population: Population = None
        self._best_individual: Individual = None
        self._generation: int = 0

        # tracking
        self._fitness_history: list[dict] = []

    # ── Public API ───────────────────────────────────────────────────────

    def run(self, data: np.ndarray,
            population: Population = None,
            val_ratio: float = DEFAULT_VAL_RATIO,
            early_stop_gens: int = 30,
            target_fitness: float = None) -> Individual:
        """
        Run the full GA evolution loop.

        Parameters
        ----------
        data : np.ndarray
            Time series training data.
        population : Population, optional
            Pre-initialised population. If None, creates random.
        val_ratio : float
            Fraction of data used for validation.
        early_stop_gens : int
            Stop if no improvement for this many generations.
        target_fitness : float, optional
            Stop if fitness drops below this.

        Returns
        -------
        Individual — the best solution found.
        """
        train, val = train_val_split(data, val_ratio)

        if population is not None:
            self._population = population
        elif self._population is None:
            self._population = Population.random(
                self.population_size, generation=0)

        # ── Initial evaluation ───────────────────────────────────────
        self._evaluate_population(train, val)
        no_improve_count = 0

        # ── Evolution loop ───────────────────────────────────────────
        for gen in range(self.max_generations):
            self._generation = gen

            # Create next generation
            new_individuals = self._evolve_one_generation(train, val, gen)
            self._population.replace(new_individuals)

            # Evaluate
            self._evaluate_population(train, val)

            # Stats
            pop_sorted = self._population.sorted()
            best = pop_sorted[0]
            avg = self._population.avg_fitness()
            diversity = self._population.diversity()

            # Update fitness controller
            train_err = self._compute_model_error(best, train, train)
            val_err = best.fitness
            self._fitness.update(
                gen, best.fitness, avg, diversity,
                train_error=train_err, val_error=val_err)

            # Update memory
            self._memory.update_from_generation(pop_sorted)

            # Log
            self._log.generation(
                gen=gen, best_fit=best.fitness, avg_fit=avg,
                mutation_rate=self._population.avg_mutation_rate())

            self._fitness_history.append({
                "gen": gen,
                "best": best.fitness,
                "avg": avg,
                "diversity": diversity,
                "metric": self._fitness.current_metric_name,
                "avg_mutation": self._population.avg_mutation_rate(),
            })

            # Track best overall
            if (self._best_individual is None or
                    best.fitness < self._best_individual.fitness):
                self._best_individual = best.clone()
                no_improve_count = 0
            else:
                no_improve_count += 1

            # Diversity rescue
            if diversity < DIVERSITY_THRESHOLD:
                elites = self._memory.recall_elites(n=3)
                if elites:
                    self._population.inject(elites)

            # Early stopping
            if no_improve_count >= early_stop_gens:
                self._log.stagnation(gen, no_improve_count)
                break

            if target_fitness is not None and best.fitness <= target_fitness:
                break

        return self._best_individual

    # ── Trigger adaptive reset (called by drift detector) ────────────────

    def on_drift(self, action: str = "PARTIAL_RESET",
                 reset_fraction: float = 0.3):
        """
        External signal from the drift detector / policy engine.
        Adjusts GA behaviour in response to environment changes.
        """
        if self._population is None:
            return

        if action == "FULL_RESET":
            self._population = Population.random(
                self.population_size, generation=self._generation)
            self._log.adaptation("FULL_RESET",
                                 reason="drift detected")

        elif action == "PARTIAL_RESET":
            self._population.partial_reset(
                fraction=reset_fraction,
                generation=self._generation)
            self._log.adaptation("PARTIAL_RESET",
                                 reason=f"drift detected (reset {reset_fraction:.0%})")

        elif action == "INCREASE_MUTATION":
            for ind in self._population:
                ind.mutation_rate = min(ind.mutation_rate * 2.0, 0.5)
                ind.mutation_step = min(ind.mutation_step * 1.5, 0.2)
            self._log.adaptation("INCREASE_MUTATION",
                                 reason="drift detected")

        elif action == "SWITCH_FITNESS":
            old = self._fitness.current_metric_name
            self._fitness.update(
                self._generation, float("inf"), float("inf"), 0.0)
            self._log.adaptation("SWITCH_FITNESS",
                                 reason=f"forced switch from {old}")

        elif action == "INJECT_DIVERSITY":
            elites = self._memory.recall_elites(n=5)
            randoms = [Individual.random(self._generation)
                       for _ in range(5)]
            self._population.inject(elites + randoms)
            self._log.adaptation("INJECT_DIVERSITY",
                                 reason="drift detected")

    # ── Private ──────────────────────────────────────────────────────────

    def _evolve_one_generation(self, train: np.ndarray,
                               val: np.ndarray,
                               gen: int) -> list[Individual]:
        pop = self._population.individuals
        pop_sorted = sorted(pop, key=lambda i: i.fitness)

        # Elitism
        new_pop = [ind.clone() for ind in pop_sorted[:self.elitism]]

        # Fill rest via selection + crossover + mutation
        while len(new_pop) < self.population_size:
            p1 = tournament_select(pop)
            p2 = tournament_select(pop)
            c1, c2 = crossover(p1, p2, generation=gen)
            c1 = mutate(c1, generation=gen)
            c2 = mutate(c2, generation=gen)
            new_pop.append(c1)
            if len(new_pop) < self.population_size:
                new_pop.append(c2)

        return new_pop[:self.population_size]

    def _evaluate_population(self, train: np.ndarray, val: np.ndarray):
        pop_vectors = [ind.to_vector() for ind in self._population]
        mean_vector = np.mean(pop_vectors, axis=0)

        for ind in self._population:
            fitness = self._evaluate_individual(
                ind, train, val,
                population_mean_vector=mean_vector)
            ind.fitness = fitness

    def _evaluate_individual(self, individual: Individual,
                             train: np.ndarray, val: np.ndarray,
                             population_mean_vector: np.ndarray = None) -> float:
        """
        Evaluate one individual across all models with ensemble weighting.
        """
        weights = individual.get_normalised_weights()
        horizon = len(val)
        ensemble_pred = np.zeros(horizon)
        train_error_total = 0.0

        for model_name, weight in weights.items():
            if weight < 0.01:
                continue

            try:
                model = self._registry.get(model_name)
                params = individual.get_model_params(model_name)
                model.set_params(params)
                model.fit(train)
                pred = model.forecast(horizon)

                if len(pred) != horizon:
                    pred = np.resize(pred, horizon)

                # check for NaN / Inf
                if not np.all(np.isfinite(pred)):
                    pred = np.full(horizon, np.mean(train))

                ensemble_pred += weight * pred

                # train error for overfitting detection
                train_pred = model.forecast(len(train))
                if len(train_pred) >= len(train):
                    train_pred = train_pred[:len(train)]
                    tr_err = mse(train, train_pred)
                else:
                    tr_err = float("inf")
                train_error_total += weight * tr_err

            except Exception:
                ensemble_pred += weight * np.mean(train)

        # Memory penalty
        memory_penalty = self._memory.failure_penalty(individual)

        # Adaptive fitness evaluation
        fitness = self._fitness.evaluate(
            val, ensemble_pred,
            train_error=train_error_total,
            individual_vector=individual.to_vector(),
            population_mean_vector=population_mean_vector,
        )

        return fitness + memory_penalty

    def _compute_model_error(self, individual: Individual,
                             train: np.ndarray,
                             target: np.ndarray) -> float:
        weights = individual.get_normalised_weights()
        horizon = len(target)
        ensemble_pred = np.zeros(horizon)

        for model_name, weight in weights.items():
            if weight < 0.01:
                continue
            try:
                model = self._registry.get(model_name)
                params = individual.get_model_params(model_name)
                model.set_params(params)
                model.fit(train)
                pred = model.forecast(horizon)
                if len(pred) != horizon:
                    pred = np.resize(pred, horizon)
                if not np.all(np.isfinite(pred)):
                    pred = np.full(horizon, np.mean(train))
                ensemble_pred += weight * pred
            except Exception:
                ensemble_pred += weight * np.mean(train)

        return mse(target, ensemble_pred)

    # ── Getters ──────────────────────────────────────────────────────────

    @property
    def best_individual(self) -> Individual:
        return self._best_individual

    @property
    def fitness_history(self) -> list[dict]:
        return self._fitness_history

    @property
    def memory(self) -> MemoryBank:
        return self._memory

    @property
    def population(self) -> Population:
        return self._population
