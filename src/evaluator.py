"""
High-Performance Schedule Evaluator for Single-Machine Scheduling:
1 | r_j, s_ij | C_max and Bi-objective (C_max, sum w_j T_j).
Includes incremental prefix-suffix evaluation primitives for O(n) insertions.
"""

from dataclasses import dataclass
from typing import List, Tuple, Dict, Any, Optional
import numpy as np


@dataclass(slots=True)
class EvaluationResult:
    c_max: int
    total_weighted_tardiness: float
    start_times: List[int]
    completion_times: List[int]
    idle_time: int
    total_setup_time: int
    tardiness_per_job: List[int]


def evaluate_schedule(
    perm: List[int],
    p: List[int],
    r: List[int],
    s: List[List[int]],
    s0: List[int],
    d: List[int] = None,
    w: List[int] = None,
) -> EvaluationResult:
    """Detailed evaluator returning all schedule metrics."""
    total_n = len(p)
    n = len(perm)
    start_times = [0] * total_n
    completion_times = [0] * total_n
    tardiness_per_job = [0] * total_n
    
    current_time = 0
    total_idle = 0
    total_setup = 0
    
    for idx, job in enumerate(perm):
        if idx == 0:
            setup = s0[job]
            total_setup += setup
            earliest_start = setup
        else:
            prev_job = perm[idx - 1]
            setup = s[prev_job][job]
            total_setup += setup
            earliest_start = current_time + setup
            
        start = max(r[job], earliest_start)
        idle = start - (earliest_start if idx > 0 else setup)
        if idle > 0:
            total_idle += idle
            
        start_times[job] = start
        current_time = start + p[job]
        completion_times[job] = current_time
        
        if d is not None:
            tardiness_per_job[job] = max(0, current_time - d[job])
            
    c_max = current_time
    if w is not None and d is not None:
        twt = float(sum(w[j] * tardiness_per_job[j] for j in range(total_n)))
    else:
        twt = 0.0
        
    return EvaluationResult(
        c_max=c_max,
        total_weighted_tardiness=twt,
        start_times=start_times,
        completion_times=completion_times,
        idle_time=total_idle,
        total_setup_time=total_setup,
        tardiness_per_job=tardiness_per_job,
    )


def compute_makespan(
    perm: List[int],
    p: List[int],
    r: List[int],
    s: List[List[int]],
    s0: List[int],
) -> int:
    """Ultra-fast makespan calculation for inner loops of metaheuristics."""
    n = len(perm)
    if n == 0:
        return 0
    
    first = perm[0]
    t = s0[first]
    if r[first] > t:
        t = r[first]
    t += p[first]
    
    prev = first
    for i in range(1, n):
        curr = perm[i]
        t_arr = t + s[prev][curr]
        r_curr = r[curr]
        if r_curr > t_arr:
            t = r_curr + p[curr]
        else:
            t = t_arr + p[curr]
        prev = curr
        
    return t


def compute_prefix_completions(
    perm: List[int],
    p: List[int],
    r: List[int],
    s: List[List[int]],
    s0: List[int],
) -> List[int]:
    """
    Computes prefix completion times [C_0, C_1, ..., C_{n-1}] for a sequence.
    Allows O(1) prefix lookup during insertion evaluations.
    """
    n = len(perm)
    if n == 0:
        return []
        
    completions = [0] * n
    first = perm[0]
    t = s0[first]
    if r[first] > t:
        t = r[first]
    t += p[first]
    completions[0] = t
    
    prev = first
    for i in range(1, n):
        curr = perm[i]
        arr = t + s[prev][curr]
        r_curr = r[curr]
        t = (r_curr if r_curr > arr else arr) + p[curr]
        completions[i] = t
        prev = curr
        
    return completions


def evaluate_incremental_insertion_makespan(
    partial: List[int],
    prefix_completions: List[int],
    job: int,
    pos: int,
    p: List[int],
    r: List[int],
    s: List[List[int]],
    s0: List[int],
) -> int:
    """
    Evaluates makespan of inserting job into partial at pos in O(n - pos) time
    leveraging precomputed prefix completions instead of full O(n) re-evaluation.
    """
    n = len(partial)
    
    # 1. Compute completion time of inserted job
    if pos == 0:
        arr = s0[job]
    else:
        prev_job = partial[pos - 1]
        arr = prefix_completions[pos - 1] + s[prev_job][job]
        
    start_job = max(r[job], arr)
    curr_t = start_job + p[job]
    curr_job = job
    
    # 2. Propagate forward through suffix partial[pos:]
    for idx in range(pos, n):
        nxt_job = partial[idx]
        arr_nxt = curr_t + s[curr_job][nxt_job]
        start_nxt = max(r[nxt_job], arr_nxt)
        curr_t = start_nxt + p[nxt_job]
        curr_job = nxt_job
        
    return curr_t


def compute_bi_objective(
    perm: List[int],
    p: List[int],
    r: List[int],
    s: List[List[int]],
    s0: List[int],
    d: List[int],
    w: List[int],
) -> Tuple[int, float]:
    """Fast computation of both makespan and total weighted tardiness."""
    n = len(perm)
    if n == 0:
        return 0, 0.0
        
    first = perm[0]
    t = s0[first]
    if r[first] > t:
        t = r[first]
    t += p[first]
    
    twt = w[first] * (t - d[first]) if t > d[first] else 0.0
    prev = first
    
    for i in range(1, n):
        curr = perm[i]
        t_arr = t + s[prev][curr]
        r_curr = r[curr]
        t = (r_curr if r_curr > t_arr else t_arr) + p[curr]
        if t > d[curr]:
            twt += w[curr] * (t - d[curr])
        prev = curr
        
    return t, float(twt)


def compute_scalarized_objective(
    perm: List[int],
    p: List[int],
    r: List[int],
    s: List[List[int]],
    s0: List[int],
    d: Optional[List[int]],
    w: Optional[List[int]],
    lam: float = 1.0,
    norm_cmax: float = 1.0,
    norm_twt: float = 1.0,
) -> float:
    """
    Normalized scalarized objective: lambda * (C_max / norm_cmax) + (1 - lambda) * (TWT / norm_twt).
    If lam == 1.0 or d/w is None, returns raw makespan.
    """
    if lam >= 0.999 or d is None or w is None:
        return float(compute_makespan(perm, p, r, s, s0))
        
    cmax, twt = compute_bi_objective(perm, p, r, s, s0, d, w)
    val = lam * (cmax / max(1.0, norm_cmax)) + (1.0 - lam) * (twt / max(1.0, norm_twt))
    return float(val)
