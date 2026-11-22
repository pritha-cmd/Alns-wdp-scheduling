"""
Exact Window Dynamic Programming (Window-DP) Polisher for 1 | r_j, s_ij | C_max:
Re-optimizes sub-permutations of size k in [6, 10] using Held-Karp bitmask DP.

Mathematical Monotonicity Guarantee:
For any job m, completion time is C_m = max(r_m, C_prev + s_prev,m) + p_m.
Since g(C_prev) = max(r_m, C_prev + s) + p is monotonically non-decreasing in C_prev,
minimizing C_prev at every prefix state strictly minimizes or preserves the completion
time of all subsequent jobs. Hence, DP(mask, j) satisfies Bellman's optimality principle,
and the polisher is guaranteed to never worsen the current sequence makespan.
"""

import random
import time
from typing import List, Tuple, Optional
import numpy as np
from src.evaluator import compute_makespan


def optimize_window_dp(
    perm: List[int],
    start_idx: int,
    k: int,
    p: List[int],
    r: List[int],
    s: List[List[int]],
    s0: List[int],
    deadline: Optional[float] = None,
) -> Tuple[List[int], bool]:
    """
    Re-optimizes the subsegment perm[start_idx : start_idx + k] to exact mathematical optimality.
    If a wall-clock `deadline` is given and passes mid-DP, the permutation is returned
    unchanged (so monotonicity is preserved and large k cannot overrun the budget).
    
    Parameters:
    - perm: full permutation
    - start_idx: window start index
    - k: window size (typically 6 to 10)
    - p, r, s, s0: instance parameters
    
    Returns:
    - new_perm: updated permutation
    - improved: bool indicating whether makespan strictly improved
    """
    n = len(perm)
    end_idx = min(start_idx + k, n)
    actual_k = end_idx - start_idx
    if actual_k <= 1:
        return list(perm), False
        
    window_jobs = perm[start_idx:end_idx]
    
    # 1. Evaluate prefix completion time
    if start_idx == 0:
        pred_job = None
        pred_completion = 0
    else:
        pred_completion = compute_makespan(perm[:start_idx], p, r, s, s0)
        pred_job = perm[start_idx - 1]
        
    succ_job = perm[end_idx] if end_idx < n else None
    
    # 2. Local Held-Karp DP over actual_k jobs
    num_states = 1 << actual_k
    INF = 10**9
    dp = np.full((num_states, actual_k), INF, dtype=np.int32)
    parent = np.full((num_states, actual_k), -1, dtype=np.int8)
    
    # Base cases: first job in window
    for j_idx, job in enumerate(window_jobs):
        mask = 1 << j_idx
        if pred_job is None:
            arr_t = s0[job]
        else:
            arr_t = pred_completion + s[pred_job][job]
        start_t = max(r[job], arr_t)
        dp[mask, j_idx] = start_t + p[job]
        
    # Transitions
    for mask in range(1, num_states):
        if deadline is not None and (mask & 63) == 0 and time.perf_counter() >= deadline:
            return list(perm), False
        for last_idx, last_job in enumerate(window_jobs):
            curr_c = dp[mask, last_idx]
            if curr_c >= INF:
                continue
                
            for next_idx, next_job in enumerate(window_jobs):
                if not (mask & (1 << next_idx)):
                    next_mask = mask | (1 << next_idx)
                    arr_t = curr_c + s[last_job][next_job]
                    start_next = max(r[next_job], arr_t)
                    comp_next = start_next + p[next_job]
                    
                    if comp_next < dp[next_mask, next_idx]:
                        dp[next_mask, next_idx] = comp_next
                        parent[next_mask, next_idx] = last_idx
                        
    # Evaluate best last job in window
    full_mask = num_states - 1
    best_last_idx = -1
    best_objective = INF
    
    for last_idx, last_job in enumerate(window_jobs):
        comp = dp[full_mask, last_idx]
        if comp >= INF:
            continue
            
        if succ_job is not None:
            suffix_arrival = comp + s[last_job][succ_job]
            cost = max(r[succ_job], suffix_arrival)
        else:
            cost = comp
            
        if cost < best_objective:
            best_objective = cost
            best_last_idx = last_idx
            
    if best_last_idx == -1:
        return list(perm), False
        
    # Reconstruct optimal window ordering
    opt_window = []
    curr_mask = full_mask
    curr_idx = best_last_idx
    while curr_idx != -1:
        opt_window.append(window_jobs[curr_idx])
        prev_idx = int(parent[curr_mask, curr_idx])
        curr_mask = curr_mask ^ (1 << curr_idx)
        curr_idx = prev_idx
        
    opt_window.reverse()
    
    new_perm = perm[:start_idx] + opt_window + perm[end_idx:]
    old_cmax = compute_makespan(perm, p, r, s, s0)
    new_cmax = compute_makespan(new_perm, p, r, s, s0)
    
    return new_perm, (new_cmax < old_cmax)


def sliding_window_dp_sweep(
    perm: List[int],
    k: int,
    p: List[int],
    r: List[int],
    s: List[List[int]],
    s0: List[int],
    step_size: Optional[int] = None,
    deadline: Optional[float] = None,
) -> Tuple[List[int], int, bool]:
    """
    Slides a window of size k across the entire sequence.
    Iteratively replaces sub-permutations with exact DP solutions.
    Respects optional wall-clock deadline.
    """
    n = len(perm)
    if n <= 1:
        return list(perm), compute_makespan(perm, p, r, s, s0), False
        
    step = step_size if step_size is not None else max(1, k // 2)
    current_perm = list(perm)
    any_improvement = False
    
    start_indices = list(range(0, max(1, n - k + 1), step))
    if n > k and start_indices[-1] != n - k:
        start_indices.append(n - k)
        
    for start_idx in start_indices:
        if deadline is not None and time.perf_counter() >= deadline:
            break
        current_perm, imp = optimize_window_dp(current_perm, start_idx, k, p, r, s, s0, deadline=deadline)
        if imp:
            any_improvement = True
            
    final_cmax = compute_makespan(current_perm, p, r, s, s0)
    return current_perm, final_cmax, any_improvement


def targeted_window_dp_polish(
    perm: List[int],
    k: int,
    strategy: str,
    p: List[int],
    r: List[int],
    s: List[List[int]],
    s0: List[int],
    rng: Optional[random.Random] = None,
    deadline: Optional[float] = None,
) -> Tuple[List[int], int, bool]:
    """
    Applies window DP polish with configurable placement strategy:
    - 'sliding': full sliding window sweep across all positions
    - 'worst_setup': centers window around the job with maximum transition setup
    - 'random': randomly selects a single window position
    Respects optional wall-clock deadline.
    """
    n = len(perm)
    if n <= k:
        new_perm, imp = optimize_window_dp(perm, 0, n, p, r, s, s0, deadline=deadline)
        return new_perm, compute_makespan(new_perm, p, r, s, s0), imp
        
    if deadline is not None and time.perf_counter() >= deadline:
        return list(perm), compute_makespan(perm, p, r, s, s0), False

    if strategy == "sliding":
        return sliding_window_dp_sweep(perm, k, p, r, s, s0, deadline=deadline)
    elif strategy == "worst_setup":
        # Identify worst transition index
        worst_pos = 0
        worst_cost = -1
        for idx in range(n):
            prev_j = perm[idx - 1] if idx > 0 else None
            curr_j = perm[idx]
            cost = s0[curr_j] if prev_j is None else s[prev_j][curr_j]
            if cost > worst_cost:
                worst_cost = cost
                worst_pos = idx
                
        start_idx = max(0, min(worst_pos - k // 2, n - k))
        new_perm, imp = optimize_window_dp(perm, start_idx, k, p, r, s, s0, deadline=deadline)
        return new_perm, compute_makespan(new_perm, p, r, s, s0), imp
    elif strategy == "random":
        r_gen = rng if rng is not None else random.Random()
        start_idx = r_gen.randint(0, n - k)
        new_perm, imp = optimize_window_dp(perm, start_idx, k, p, r, s, s0, deadline=deadline)
        return new_perm, compute_makespan(new_perm, p, r, s, s0), imp
    else:
        return sliding_window_dp_sweep(perm, k, p, r, s, s0, deadline=deadline)
