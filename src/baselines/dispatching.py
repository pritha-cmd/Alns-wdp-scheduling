"""
Heuristic Priority Dispatching Rules for 1 | r_j, s_ij | C_max:
- SPT (Shortest Processing Time)
- ERD (Earliest Release Date)
- Nearest-Setup Greedy
- Earliest-Completion-Time Greedy (ECT)
"""

import time
from typing import List, Tuple
from src.evaluator import compute_makespan


def rule_spt(
    p: List[int],
    r: List[int],
    s: List[List[int]],
    s0: List[int],
) -> Tuple[List[int], int, float]:
    """Shortest Processing Time: sorts jobs ascending by p_j."""
    start_time = time.perf_counter()
    n = len(p)
    perm = sorted(range(n), key=lambda j: p[j])
    cmax = compute_makespan(perm, p, r, s, s0)
    elapsed = time.perf_counter() - start_time
    return perm, cmax, elapsed


def rule_erd(
    p: List[int],
    r: List[int],
    s: List[List[int]],
    s0: List[int],
) -> Tuple[List[int], int, float]:
    """Earliest Release Date: sorts jobs ascending by r_j (ties broken by p_j)."""
    start_time = time.perf_counter()
    n = len(p)
    perm = sorted(range(n), key=lambda j: (r[j], p[j]))
    cmax = compute_makespan(perm, p, r, s, s0)
    elapsed = time.perf_counter() - start_time
    return perm, cmax, elapsed


def rule_nearest_setup(
    p: List[int],
    r: List[int],
    s: List[List[int]],
    s0: List[int],
) -> Tuple[List[int], int, float]:
    """
    Nearest-Setup Greedy: iteratively selects unvisited job with minimum setup time.
    """
    start_time = time.perf_counter()
    n = len(p)
    unvisited = set(range(n))
    
    # First job: min s0[j]
    first = min(unvisited, key=lambda j: (s0[j], r[j]))
    perm = [first]
    unvisited.remove(first)
    
    curr = first
    while unvisited:
        nxt = min(unvisited, key=lambda j: (s[curr][j], r[j]))
        perm.append(nxt)
        unvisited.remove(nxt)
        curr = nxt
        
    cmax = compute_makespan(perm, p, r, s, s0)
    elapsed = time.perf_counter() - start_time
    return perm, cmax, elapsed


def rule_earliest_completion(
    p: List[int],
    r: List[int],
    s: List[List[int]],
    s0: List[int],
) -> Tuple[List[int], int, float]:
    """
    Earliest Completion Time (ECT) Greedy:
    Greedily selects the unvisited job that completes earliest from the current state.
    """
    start_time = time.perf_counter()
    n = len(p)
    unvisited = set(range(n))
    
    # First job: earliest completion
    first = min(unvisited, key=lambda j: max(r[j], s0[j]) + p[j])
    perm = [first]
    unvisited.remove(first)
    curr_t = max(r[first], s0[first]) + p[first]
    curr_job = first
    
    while unvisited:
        best_j = None
        best_comp = float("inf")
        for j in unvisited:
            st = max(r[j], curr_t + s[curr_job][j])
            comp = st + p[j]
            if comp < best_comp:
                best_comp = comp
                best_j = j
                
        perm.append(best_j)
        unvisited.remove(best_j)
        curr_t = best_comp
        curr_job = best_j
        
    cmax = curr_t
    elapsed = time.perf_counter() - start_time
    return perm, cmax, elapsed

