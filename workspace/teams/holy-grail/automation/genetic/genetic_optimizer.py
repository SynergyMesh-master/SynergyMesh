#!/usr/bin/env python3
"""
L10: System Optimization - Genetic Optimizer
AXIOM Layer 10: 系統優化 - 遺傳算法優化器

Responsibilities:
- Genetic algorithm-based optimization
- Parameter tuning via evolution
- Multi-objective optimization
"""

from typing import Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass
from enum import Enum
import random
import copy


class SelectionMethod(Enum):
    """Selection methods for genetic algorithm."""
    TOURNAMENT = "tournament"
    ROULETTE = "roulette"
    RANK = "rank"
    ELITISM = "elitism"


@dataclass
class Individual:
    """Individual in the population."""
    genes: Dict[str, float]
    fitness: float = 0.0
    age: int = 0


@dataclass
class OptimizationConfig:
    """Genetic optimizer configuration."""
    population_size: int = 100
    generations: int = 50
    mutation_rate: float = 0.1
    crossover_rate: float = 0.8
    elitism_count: int = 2
    selection_method: SelectionMethod = SelectionMethod.TOURNAMENT
    tournament_size: int = 3


@dataclass
class OptimizationResult:
    """Result of genetic optimization."""
    best_individual: Individual
    best_fitness: float
    generations_run: int
    fitness_history: List[float]
    final_population: List[Individual]


class GeneticOptimizer:
    """
    Genetic algorithm optimizer for L10 System Optimization layer.

    Uses evolutionary algorithms to find optimal configurations.
    """

    VERSION = "2.0.0"
    LAYER = "L10_system_optimization"

    def __init__(self, config: Optional[OptimizationConfig] = None):
        self.config = config or OptimizationConfig()
        self._fitness_func: Optional[Callable[[Dict[str, float]], float]] = None
        self._gene_ranges: Dict[str, Tuple[float, float]] = {}
        self._population: List[Individual] = []

    def set_fitness_function(self, func: Callable[[Dict[str, float]], float]) -> None:
        """Set the fitness evaluation function."""
        self._fitness_func = func

    def set_gene_ranges(self, ranges: Dict[str, Tuple[float, float]]) -> None:
        """Set the valid ranges for each gene."""
        self._gene_ranges = ranges

    async def optimize(self) -> OptimizationResult:
        """Run genetic optimization."""
        if not self._fitness_func or not self._gene_ranges:
            raise ValueError("Fitness function and gene ranges must be set")

        # Initialize population
        self._initialize_population()

        fitness_history = []
        generations_completed = 0

        for generation in range(self.config.generations):
            # Evaluate fitness
            await self._evaluate_population()

            # Record best fitness
            best = max(self._population, key=lambda i: i.fitness)
            fitness_history.append(best.fitness)

            generations_completed = generation + 1

            # Check for convergence
            if generation > 10 and self._check_convergence(fitness_history[-10:]):
                break

            # Create next generation
            self._evolve()

        # Final evaluation
        await self._evaluate_population()
        best = max(self._population, key=lambda i: i.fitness)

        return OptimizationResult(
            best_individual=best,
            best_fitness=best.fitness,
            generations_run=generations_completed,
            fitness_history=fitness_history,
            final_population=self._population,
        )

    def _initialize_population(self) -> None:
        """Initialize random population."""
        self._population = []
        for _ in range(self.config.population_size):
            genes = {}
            for gene, (min_val, max_val) in self._gene_ranges.items():
                genes[gene] = random.uniform(min_val, max_val)
            self._population.append(Individual(genes=genes))

    async def _evaluate_population(self) -> None:
        """Evaluate fitness of all individuals."""
        for individual in self._population:
            individual.fitness = self._fitness_func(individual.genes)

    def _evolve(self) -> None:
        """Create next generation through evolution."""
        # Sort by fitness
        self._population.sort(key=lambda i: i.fitness, reverse=True)

        new_population = []

        # Elitism: keep best individuals
        for i in range(self.config.elitism_count):
            elite = copy.deepcopy(self._population[i])
            elite.age += 1
            new_population.append(elite)

        # Fill rest with offspring
        while len(new_population) < self.config.population_size:
            # Selection
            parent1 = self._select()
            parent2 = self._select()

            # Crossover
            if random.random() < self.config.crossover_rate:
                child1, child2 = self._crossover(parent1, parent2)
            else:
                child1, child2 = copy.deepcopy(parent1), copy.deepcopy(parent2)

            # Mutation
            self._mutate(child1)
            self._mutate(child2)

            new_population.append(child1)
            if len(new_population) < self.config.population_size:
                new_population.append(child2)

        self._population = new_population

    def _select(self) -> Individual:
        """Select an individual based on selection method."""
        if self.config.selection_method == SelectionMethod.TOURNAMENT:
            return self._tournament_selection()
        elif self.config.selection_method == SelectionMethod.ROULETTE:
            return self._roulette_selection()
        elif self.config.selection_method == SelectionMethod.RANK:
            return self._rank_selection()
        else:
            return self._tournament_selection()

    def _tournament_selection(self) -> Individual:
        """Tournament selection."""
        tournament = random.sample(self._population, self.config.tournament_size)
        return max(tournament, key=lambda i: i.fitness)

    def _roulette_selection(self) -> Individual:
        """Roulette wheel selection."""
        total_fitness = sum(i.fitness for i in self._population)
        if total_fitness == 0:
            return random.choice(self._population)

        pick = random.uniform(0, total_fitness)
        current = 0
        for individual in self._population:
            current += individual.fitness
            if current >= pick:
                return individual
        return self._population[-1]

    def _rank_selection(self) -> Individual:
        """Rank-based selection."""
        sorted_pop = sorted(self._population, key=lambda i: i.fitness)
        ranks = list(range(1, len(sorted_pop) + 1))
        total = sum(ranks)
        pick = random.uniform(0, total)
        current = 0
        for rank, individual in zip(ranks, sorted_pop):
            current += rank
            if current >= pick:
                return individual
        return sorted_pop[-1]

    def _crossover(self, parent1: Individual,
                   parent2: Individual) -> Tuple[Individual, Individual]:
        """Perform crossover between two parents."""
        child1_genes = {}
        child2_genes = {}

        for gene in self._gene_ranges.keys():
            if random.random() < 0.5:
                child1_genes[gene] = parent1.genes[gene]
                child2_genes[gene] = parent2.genes[gene]
            else:
                child1_genes[gene] = parent2.genes[gene]
                child2_genes[gene] = parent1.genes[gene]

        return Individual(genes=child1_genes), Individual(genes=child2_genes)

    def _mutate(self, individual: Individual) -> None:
        """Apply mutation to an individual."""
        for gene, (min_val, max_val) in self._gene_ranges.items():
            if random.random() < self.config.mutation_rate:
                # Gaussian mutation
                current = individual.genes[gene]
                range_size = max_val - min_val
                mutation = random.gauss(0, range_size * 0.1)
                new_value = current + mutation
                individual.genes[gene] = max(min_val, min(max_val, new_value))

    def _check_convergence(self, recent_fitness: List[float]) -> bool:
        """Check if optimization has converged.
        
        Args:
            recent_fitness: List of recent fitness values
            
        Returns:
            True if variance is below threshold, False otherwise
        """
        # Ensure we have sufficient data points for meaningful variance calculation
        if not recent_fitness or len(recent_fitness) < 2:
            return False
        
        # Calculate mean once for efficiency
        mean = sum(recent_fitness) / len(recent_fitness)
        
        # Calculate variance
        variance = sum((f - mean) ** 2 for f in recent_fitness) / len(recent_fitness)
        
        return variance < 1e-6


# Module exports
__all__ = [
    "GeneticOptimizer",
    "OptimizationConfig",
    "OptimizationResult",
    "Individual",
    "SelectionMethod",
]
