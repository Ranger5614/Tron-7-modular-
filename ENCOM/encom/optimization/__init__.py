"""
Parameter Optimization Module

Implements multiple optimization algorithms for finding optimal strategy parameters:
- Grid Search: Exhaustive search over parameter combinations
- Genetic Algorithm: Evolutionary optimization
- Random Search: Random sampling for baseline comparison

Author: ENCOM Development Team
License: MIT
"""

from encom.optimization.parameter_optimizer import (
    ParameterOptimizer,
    OptimizationResult,
    optimize_strategy,
)

__all__ = [
    'ParameterOptimizer',
    'OptimizationResult',
    'optimize_strategy',
]
