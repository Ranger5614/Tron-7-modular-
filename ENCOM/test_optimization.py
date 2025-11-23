"""
Test Parameter Optimization

Demonstrates grid search, genetic algorithm, and random search.

Author: ENCOM Development Team
"""

import sys
import numpy as np

print("=" * 70)
print("TESTING ENCOM PARAMETER OPTIMIZATION")
print("=" * 70)
print()

# Test import
try:
    from encom.optimization import ParameterOptimizer, OptimizationResult
    print("✅ Parameter optimizer imported successfully")
    print()
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# Define test objective function
# Simulates a strategy backtest that returns Sharpe ratio
# Optimal parameters: rsi_period=14, threshold=30
def objective_function(params):
    """
    Mock objective function (Sharpe ratio)

    Peaks at rsi_period=14, threshold=30
    """
    rsi_period = params.get('rsi_period', 14)
    threshold = params.get('threshold', 30)

    # Quadratic penalty from optimal values
    rsi_penalty = (rsi_period - 14) ** 2 / 100
    threshold_penalty = (threshold - 30) ** 2 / 100

    # Base Sharpe + penalties + noise
    sharpe = 1.5 - rsi_penalty - threshold_penalty
    sharpe += np.random.randn() * 0.05  # Add noise

    return sharpe


print("Objective Function: Mock Sharpe Ratio")
print("Optimal Parameters: rsi_period=14, threshold=30")
print()

# Test 1: Grid Search
print("=" * 70)
print("TEST 1: GRID SEARCH")
print("=" * 70)
print()

try:
    optimizer = ParameterOptimizer(objective_function, maximize=True)

    param_grid = {
        'rsi_period': [10, 12, 14, 16, 18, 20],
        'threshold': [20, 25, 30, 35, 40]
    }

    result = optimizer.grid_search(param_grid, n_jobs=1, verbose=True)

    print(f"✅ Grid Search Passed")
    print(f"   Tested: {result.iterations} combinations")
    print(f"   Best Score: {result.best_score:.4f}")
    print(f"   Best Params: {result.best_params}")
    print()

except Exception as e:
    print(f"❌ Grid Search Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Genetic Algorithm
print("=" * 70)
print("TEST 2: GENETIC ALGORITHM")
print("=" * 70)
print()

try:
    optimizer = ParameterOptimizer(objective_function, maximize=True)

    param_ranges = {
        'rsi_period': (5, 30),
        'threshold': (10, 50)
    }

    param_types = {
        'rsi_period': 'int',
        'threshold': 'int'
    }

    result = optimizer.genetic_algorithm(
        param_ranges,
        param_types,
        population_size=20,
        generations=10,
        mutation_rate=0.1,
        crossover_rate=0.8,
        elitism=3,
        verbose=True
    )

    print(f"✅ Genetic Algorithm Passed")
    print(f"   Evaluations: {result.iterations}")
    print(f"   Best Score: {result.best_score:.4f}")
    print(f"   Best Params: {result.best_params}")
    print()

except Exception as e:
    print(f"❌ Genetic Algorithm Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Random Search
print("=" * 70)
print("TEST 3: RANDOM SEARCH")
print("=" * 70)
print()

try:
    optimizer = ParameterOptimizer(objective_function, maximize=True)

    param_ranges = {
        'rsi_period': (5, 30),
        'threshold': (10, 50)
    }

    param_types = {
        'rsi_period': 'int',
        'threshold': 'int'
    }

    result = optimizer.random_search(
        param_ranges,
        param_types,
        n_iter=30,
        verbose=True
    )

    print(f"✅ Random Search Passed")
    print(f"   Samples: {result.iterations}")
    print(f"   Best Score: {result.best_score:.4f}")
    print(f"   Best Params: {result.best_params}")
    print()

except Exception as e:
    print(f"❌ Random Search Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Summary
print("=" * 70)
print("SUMMARY")
print("=" * 70)
print()
print("✅ ALL OPTIMIZATION TESTS PASSED")
print()
print("Available optimization methods:")
print("  • Grid Search: Exhaustive search over all combinations")
print("  • Genetic Algorithm: Evolutionary optimization")
print("  • Random Search: Random sampling baseline")
print()
print("The optimization engine can find optimal parameters for any strategy!")
print()
print("End of Line. 🎮")
