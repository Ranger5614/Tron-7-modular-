"""
Parameter Optimization Engine for ENCOM Backtesting

Implements multiple optimization algorithms:
- Grid Search: Exhaustive search over parameter space
- Genetic Algorithm: Evolutionary optimization
- Random Search: Random sampling for baseline

Author: ENCOM Development Team
License: MIT
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Callable, Any, Optional
from itertools import product
from dataclasses import dataclass
import random
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm


@dataclass
class OptimizationResult:
    """Container for optimization results"""
    best_params: Dict[str, Any]
    best_score: float
    all_results: List[Dict]
    optimization_time: float
    iterations: int


class ParameterOptimizer:
    """
    Optimize strategy parameters using various algorithms

    Supports:
    - Grid Search: Test all combinations
    - Genetic Algorithm: Evolve best parameters
    - Random Search: Sample random combinations
    """

    def __init__(self, objective_function: Callable, maximize: bool = True):
        """
        Args:
            objective_function: Function that takes params dict and returns score
            maximize: True to maximize score, False to minimize
        """
        self.objective_function = objective_function
        self.maximize = maximize
        self.results = []

    def grid_search(
        self,
        param_grid: Dict[str, List[Any]],
        n_jobs: int = 1,
        verbose: bool = True
    ) -> OptimizationResult:
        """
        Exhaustive grid search over all parameter combinations

        Args:
            param_grid: Dict of parameter names to lists of values
                Example: {'rsi_period': [10, 14, 20], 'threshold': [30, 40]}
            n_jobs: Number of parallel jobs (1 = sequential)
            verbose: Show progress bar

        Returns:
            OptimizationResult with best parameters and scores
        """
        import time
        start_time = time.time()

        # Generate all combinations
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        combinations = list(product(*param_values))

        total_combinations = len(combinations)
        if verbose:
            print(f"🔍 Grid Search: Testing {total_combinations} combinations...")
            print(f"   Parameters: {param_names}")
            print(f"   Parallel jobs: {n_jobs}")
            print()

        # Run evaluations
        all_results = []

        if n_jobs == 1:
            # Sequential execution
            iterator = tqdm(combinations, desc="Grid Search") if verbose else combinations

            for values in iterator:
                params = dict(zip(param_names, values))
                score = self._safe_evaluate(params)
                all_results.append({
                    'params': params,
                    'score': score
                })

        else:
            # Parallel execution
            with ProcessPoolExecutor(max_workers=n_jobs) as executor:
                futures = []
                for values in combinations:
                    params = dict(zip(param_names, values))
                    future = executor.submit(self._safe_evaluate, params)
                    futures.append((params, future))

                # Collect results
                iterator = tqdm(as_completed([f[1] for f in futures]),
                              total=total_combinations,
                              desc="Grid Search") if verbose else as_completed([f[1] for f in futures])

                for future in iterator:
                    # Find corresponding params
                    for params, fut in futures:
                        if fut == future:
                            score = future.result()
                            all_results.append({
                                'params': params,
                                'score': score
                            })
                            break

        # Find best result
        if self.maximize:
            best_result = max(all_results, key=lambda x: x['score'])
        else:
            best_result = min(all_results, key=lambda x: x['score'])

        optimization_time = time.time() - start_time

        if verbose:
            print()
            print(f"✅ Grid Search Complete!")
            print(f"   Best Score: {best_result['score']:.4f}")
            print(f"   Best Params: {best_result['params']}")
            print(f"   Time: {optimization_time:.2f}s")
            print()

        return OptimizationResult(
            best_params=best_result['params'],
            best_score=best_result['score'],
            all_results=all_results,
            optimization_time=optimization_time,
            iterations=total_combinations
        )

    def genetic_algorithm(
        self,
        param_ranges: Dict[str, Tuple[Any, Any]],
        param_types: Dict[str, str],
        population_size: int = 50,
        generations: int = 20,
        mutation_rate: float = 0.1,
        crossover_rate: float = 0.8,
        elitism: int = 5,
        verbose: bool = True
    ) -> OptimizationResult:
        """
        Genetic algorithm optimization

        Args:
            param_ranges: Dict of parameter names to (min, max) tuples
                Example: {'rsi_period': (5, 50), 'threshold': (20, 80)}
            param_types: Dict of parameter names to types ('int' or 'float')
                Example: {'rsi_period': 'int', 'threshold': 'int'}
            population_size: Number of individuals in population
            generations: Number of generations to evolve
            mutation_rate: Probability of mutation (0-1)
            crossover_rate: Probability of crossover (0-1)
            elitism: Number of top individuals to keep unchanged
            verbose: Show progress

        Returns:
            OptimizationResult with best parameters and scores
        """
        import time
        start_time = time.time()

        if verbose:
            print(f"🧬 Genetic Algorithm")
            print(f"   Population: {population_size}")
            print(f"   Generations: {generations}")
            print(f"   Mutation Rate: {mutation_rate}")
            print(f"   Crossover Rate: {crossover_rate}")
            print(f"   Elitism: {elitism}")
            print()

        param_names = list(param_ranges.keys())

        # Initialize population
        population = self._initialize_population(
            param_ranges, param_types, population_size
        )

        # Evaluate initial population
        population = self._evaluate_population(population, verbose=False)

        all_results = []
        best_ever_score = -np.inf if self.maximize else np.inf
        best_ever_params = None

        # Evolution loop
        for generation in range(generations):
            # Sort by fitness
            if self.maximize:
                population.sort(key=lambda x: x['score'], reverse=True)
            else:
                population.sort(key=lambda x: x['score'])

            # Track best
            best_in_gen = population[0]
            all_results.append(best_in_gen)

            if self.maximize and best_in_gen['score'] > best_ever_score:
                best_ever_score = best_in_gen['score']
                best_ever_params = best_in_gen['params'].copy()
            elif not self.maximize and best_in_gen['score'] < best_ever_score:
                best_ever_score = best_in_gen['score']
                best_ever_params = best_in_gen['params'].copy()

            if verbose:
                avg_score = np.mean([ind['score'] for ind in population])
                print(f"Generation {generation + 1:3d} | "
                      f"Best: {best_in_gen['score']:8.4f} | "
                      f"Avg: {avg_score:8.4f} | "
                      f"Params: {best_in_gen['params']}")

            if generation < generations - 1:  # Don't evolve on last generation
                # Create new population
                new_population = []

                # Elitism: Keep top individuals
                new_population.extend(population[:elitism])

                # Generate offspring
                while len(new_population) < population_size:
                    # Selection
                    parent1 = self._tournament_selection(population)
                    parent2 = self._tournament_selection(population)

                    # Crossover
                    if random.random() < crossover_rate:
                        child_params = self._crossover(parent1, parent2, param_names)
                    else:
                        child_params = parent1['params'].copy()

                    # Mutation
                    if random.random() < mutation_rate:
                        child_params = self._mutate(child_params, param_ranges, param_types)

                    new_population.append({'params': child_params, 'score': None})

                # Evaluate new individuals
                to_evaluate = [ind for ind in new_population if ind['score'] is None]
                for ind in to_evaluate:
                    ind['score'] = self._safe_evaluate(ind['params'])

                population = new_population

        optimization_time = time.time() - start_time

        if verbose:
            print()
            print(f"✅ Genetic Algorithm Complete!")
            print(f"   Best Score: {best_ever_score:.4f}")
            print(f"   Best Params: {best_ever_params}")
            print(f"   Time: {optimization_time:.2f}s")
            print()

        return OptimizationResult(
            best_params=best_ever_params,
            best_score=best_ever_score,
            all_results=all_results,
            optimization_time=optimization_time,
            iterations=population_size * generations
        )

    def random_search(
        self,
        param_ranges: Dict[str, Tuple[Any, Any]],
        param_types: Dict[str, str],
        n_iter: int = 100,
        verbose: bool = True
    ) -> OptimizationResult:
        """
        Random search over parameter space

        Args:
            param_ranges: Dict of parameter names to (min, max) tuples
            param_types: Dict of parameter names to types ('int' or 'float')
            n_iter: Number of random samples
            verbose: Show progress

        Returns:
            OptimizationResult with best parameters and scores
        """
        import time
        start_time = time.time()

        if verbose:
            print(f"🎲 Random Search: {n_iter} iterations")
            print()

        all_results = []

        iterator = tqdm(range(n_iter), desc="Random Search") if verbose else range(n_iter)

        for _ in iterator:
            # Generate random parameters
            params = {}
            for param_name, (min_val, max_val) in param_ranges.items():
                param_type = param_types[param_name]

                if param_type == 'int':
                    params[param_name] = random.randint(min_val, max_val)
                else:  # float
                    params[param_name] = random.uniform(min_val, max_val)

            score = self._safe_evaluate(params)
            all_results.append({'params': params, 'score': score})

        # Find best
        if self.maximize:
            best_result = max(all_results, key=lambda x: x['score'])
        else:
            best_result = min(all_results, key=lambda x: x['score'])

        optimization_time = time.time() - start_time

        if verbose:
            print()
            print(f"✅ Random Search Complete!")
            print(f"   Best Score: {best_result['score']:.4f}")
            print(f"   Best Params: {best_result['params']}")
            print(f"   Time: {optimization_time:.2f}s")
            print()

        return OptimizationResult(
            best_params=best_result['params'],
            best_score=best_result['score'],
            all_results=all_results,
            optimization_time=optimization_time,
            iterations=n_iter
        )

    # Helper methods

    def _safe_evaluate(self, params: Dict[str, Any]) -> float:
        """Safely evaluate objective function with error handling"""
        try:
            score = self.objective_function(params)
            return float(score) if score is not None else (-np.inf if self.maximize else np.inf)
        except Exception as e:
            # Return worst possible score on error
            return -np.inf if self.maximize else np.inf

    def _initialize_population(
        self,
        param_ranges: Dict[str, Tuple],
        param_types: Dict[str, str],
        size: int
    ) -> List[Dict]:
        """Initialize random population"""
        population = []
        for _ in range(size):
            params = {}
            for param_name, (min_val, max_val) in param_ranges.items():
                param_type = param_types[param_name]

                if param_type == 'int':
                    params[param_name] = random.randint(min_val, max_val)
                else:  # float
                    params[param_name] = random.uniform(min_val, max_val)

            population.append({'params': params, 'score': None})

        return population

    def _evaluate_population(self, population: List[Dict], verbose: bool = False) -> List[Dict]:
        """Evaluate fitness of all individuals"""
        for ind in (tqdm(population, desc="Evaluating") if verbose else population):
            if ind['score'] is None:
                ind['score'] = self._safe_evaluate(ind['params'])
        return population

    def _tournament_selection(self, population: List[Dict], tournament_size: int = 3) -> Dict:
        """Select individual using tournament selection"""
        tournament = random.sample(population, min(tournament_size, len(population)))
        if self.maximize:
            return max(tournament, key=lambda x: x['score'])
        else:
            return min(tournament, key=lambda x: x['score'])

    def _crossover(self, parent1: Dict, parent2: Dict, param_names: List[str]) -> Dict:
        """Single-point crossover"""
        child = {}
        crossover_point = random.randint(0, len(param_names))

        for i, param_name in enumerate(param_names):
            if i < crossover_point:
                child[param_name] = parent1['params'][param_name]
            else:
                child[param_name] = parent2['params'][param_name]

        return child

    def _mutate(
        self,
        params: Dict[str, Any],
        param_ranges: Dict[str, Tuple],
        param_types: Dict[str, str]
    ) -> Dict:
        """Mutate parameters"""
        mutated = params.copy()

        # Mutate one random parameter
        param_name = random.choice(list(param_ranges.keys()))
        min_val, max_val = param_ranges[param_name]
        param_type = param_types[param_name]

        if param_type == 'int':
            mutated[param_name] = random.randint(min_val, max_val)
        else:  # float
            mutated[param_name] = random.uniform(min_val, max_val)

        return mutated


def optimize_strategy(
    strategy_class,
    data,
    param_grid: Dict[str, List[Any]],
    metric: str = 'sharpe_ratio',
    method: str = 'grid',
    **kwargs
) -> OptimizationResult:
    """
    Convenience function to optimize a strategy

    Args:
        strategy_class: Strategy class to optimize
        data: Market data
        param_grid: Parameter grid for optimization
        metric: Metric to optimize ('sharpe_ratio', 'total_return', etc.)
        method: 'grid', 'genetic', or 'random'
        **kwargs: Additional arguments for optimizer

    Returns:
        OptimizationResult
    """
    from encom.engine.backtest_engine import BacktestRunner

    def objective_function(params):
        """Run backtest with parameters and return metric"""
        try:
            # Create strategy with parameters
            strategy = strategy_class(**params)

            # Run backtest
            runner = BacktestRunner(strategy, data)
            result = runner.run()

            # Return metric
            return result['metrics'].get(metric, 0)
        except Exception as e:
            return -np.inf  # Return worst score on error

    # Create optimizer
    optimizer = ParameterOptimizer(objective_function, maximize=True)

    # Run optimization
    if method == 'grid':
        return optimizer.grid_search(param_grid, **kwargs)
    elif method == 'genetic':
        # Convert grid to ranges for genetic algorithm
        param_ranges = {k: (min(v), max(v)) for k, v in param_grid.items()}
        param_types = {k: ('int' if isinstance(v[0], int) else 'float')
                      for k, v in param_grid.items()}
        return optimizer.genetic_algorithm(param_ranges, param_types, **kwargs)
    elif method == 'random':
        param_ranges = {k: (min(v), max(v)) for k, v in param_grid.items()}
        param_types = {k: ('int' if isinstance(v[0], int) else 'float')
                      for k, v in param_grid.items()}
        return optimizer.random_search(param_ranges, param_types, **kwargs)
    else:
        raise ValueError(f"Unknown method: {method}")
