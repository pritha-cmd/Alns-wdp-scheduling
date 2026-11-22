"""
Local Search and Multi-Start Local Search for 1 | r_j, s_ij | C_max:
- 2-opt neighborhood (sub-permutation inversion)
- Relocate neighborhood (insertion)
- Multi-start descent
"""

import time
import random
from typing import List, Tuple, Optional
from src.evaluator import compute_makespan


def local_search_first_improvement(
    init_perm: List[int],
    p: List[int],
    r: List[int],
    s: List[List[int]],
    s0: List[int],
    max_evals: int = 10000,
) -> Tuple[List[int], int, int]:
    """
    First-improvement local search combining 2-opt and relocate neighborhoods.
    """
    n = len(init_perm)
    current_perm = list(init_perm)
    current_cmax = compute_makespan(current_perm, p, r, s, s0)
    evals = 1
    
    improved = True
    while improved and evals < max_evals:
        improved = False
        
        # 1. 2-opt neighborhood
        for i in range(n - 1):
            if improved or evals >= max_evals:
                break
            for j in range(i + 1, n):
                if evals >= max_evals:
                    break
                # Invert slice [i:j+1]
                cand = current_perm[:i] + current_perm[i : j + 1][::-1] + current_perm[j + 1 :]
                evals += 1
                cand_cmax = compute_makespan(cand, p, r, s, s0)
                if cand_cmax < current_cmax:
                    current_cmax = cand_cmax
                    current_perm = cand
                    improved = True
                    break
                    
        if improved:
            continue
            
        # 2. Relocate neighborhood
        for i in range(n):
            if improved or evals >= max_evals:
                break
            for j in range(n):
                if i == j or evals >= max_evals:
                    continue
                cand = list(current_perm)
                job = cand.pop(i)
                cand.insert(j, job)
                evals += 1
                cand_cmax = compute_makespan(cand, p, r, s, s0)
                if cand_cmax < current_cmax:
                    current_cmax = cand_cmax
                    current_perm = cand
                    improved = True
                    break
                    
    return current_perm, current_cmax, evals


def multi_start_local_search(
    p: List[int],
    r: List[int],
    s: List[List[int]],
    s0: List[int],
    num_starts: int = 10,
    time_limit: float = 10.0,
    seed: int = 42,
) -> Tuple[List[int], int, float, int]:
    """
    Multi-start local search from randomized and heuristic starting permutations.
    Restarts continue until `time_limit` is exhausted; `num_starts` is accepted for
    backward compatibility but is not used.
    """
    start_time = time.perf_counter()
    rng = random.Random(seed)
    n = len(p)
    
    best_perm = None
    best_cmax = float("inf")
    total_evals = 0
    
    # Start 0: ERD order
    erd_start = sorted(range(n), key=lambda j: (r[j], p[j]))
    p_opt, c_opt, ev = local_search_first_improvement(erd_start, p, r, s, s0)
    total_evals += ev
    if c_opt < best_cmax:
        best_cmax = c_opt
        best_perm = p_opt
        
    # Continuous restarts until wall-clock budget is exhausted
    start_count = 1
    while time.perf_counter() - start_time < time_limit:
        start_count += 1
        # Random start
        cand = list(range(n))
        rng.shuffle(cand)
        p_opt, c_opt, ev = local_search_first_improvement(cand, p, r, s, s0)
        total_evals += ev
        if c_opt < best_cmax:
            best_cmax = c_opt
            best_perm = p_opt
            
    elapsed = time.perf_counter() - start_time
    return best_perm, best_cmax, elapsed, total_evals

