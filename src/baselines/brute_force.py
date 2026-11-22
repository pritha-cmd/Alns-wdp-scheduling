"""
Brute-force permutation enumeration for small instances (n <= 10).
Guarantees globally optimal solution for verification and benchmarking.
"""

import itertools
import time
from typing import List, Tuple, Dict, Any
from src.evaluator import compute_makespan, evaluate_schedule, EvaluationResult


def solve_brute_force(
    p: List[int],
    r: List[int],
    s: List[List[int]],
    s0: List[int],
    d: List[int] = None,
    w: List[int] = None,
) -> Tuple[List[int], int, float, int]:
    """
    Exhaustively searches all n! permutations.
    
    Returns:
    - best_perm: optimal job permutation
    - best_cmax: optimal makespan
    - elapsed_time: runtime in seconds
    - eval_count: number of evaluated permutations
    """
    n = len(p)
    if n > 11:
        raise ValueError(f"Instance size n={n} too large for brute force (n <= 11 required).")
        
    start_time = time.perf_counter()
    best_perm = None
    best_cmax = float("inf")
    eval_count = 0
    
    for perm in itertools.permutations(range(n)):
        eval_count += 1
        perm_list = list(perm)
        cmax = compute_makespan(perm_list, p, r, s, s0)
        if cmax < best_cmax:
            best_cmax = cmax
            best_perm = perm_list
            
    elapsed = time.perf_counter() - start_time
    return best_perm, int(best_cmax), elapsed, eval_count

