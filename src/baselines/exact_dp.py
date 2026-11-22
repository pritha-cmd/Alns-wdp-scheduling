"""
Exact Held-Karp Subset Dynamic Programming for 1 | r_j, s_ij | C_max.
Solves instances to proven global mathematical optimality for n <= 20.
Complexity: O(n^2 * 2^n) time, O(n * 2^n) memory.
"""

import time
from typing import List, Tuple, Optional
import numpy as np


def solve_exact_dp(
    p: List[int],
    r: List[int],
    s: List[List[int]],
    s0: List[int],
    timeout: float = 60.0,
) -> Tuple[Optional[List[int]], int, float, int]:
    """
    Solves 1 | r_j, s_ij | C_max exactly using Held-Karp subset DP.
    
    Returns:
    - best_perm: optimal permutation
    - best_cmax: optimal makespan (or -1 if timed out)
    - elapsed_time: runtime in seconds
    - transitions: total state transitions evaluated
    """
    n = len(p)
    if n > 20:
        raise ValueError(f"Instance size n={n} exceeds exact DP capability (n <= 20).")
        
    start_time = time.perf_counter()
    num_states = 1 << n
    INF = 10**9
    
    # 32-bit integer array for min completion times
    dp = np.full((num_states, n), INF, dtype=np.int32)
    parent = np.full((num_states, n), -1, dtype=np.int8)
    
    # Base cases: subsets of size 1
    for j in range(n):
        mask = 1 << j
        start_t = max(r[j], s0[j])
        dp[mask, j] = start_t + p[j]
        
    transitions = 0
    
    # Iterate topologically through mask values
    for mask in range(1, num_states):
        if time.perf_counter() - start_time > timeout:
            return None, -1, time.perf_counter() - start_time, transitions
            
        for last in range(n):
            curr_c = dp[mask, last]
            if curr_c >= INF:
                continue
                
            # Iterate through unvisited jobs
            for next_job in range(n):
                if not (mask & (1 << next_job)):
                    transitions += 1
                    next_mask = mask | (1 << next_job)
                    arr_t = curr_c + s[last][next_job]
                    start_next = max(r[next_job], arr_t)
                    comp_next = start_next + p[next_job]
                    
                    if comp_next < dp[next_mask, next_job]:
                        dp[next_mask, next_job] = comp_next
                        parent[next_mask, next_job] = last
                        
    full_mask = num_states - 1
    best_last = int(np.argmin(dp[full_mask, :]))
    best_cmax = int(dp[full_mask, best_last])
    
    # Reconstruct optimal sequence
    perm = []
    curr_mask = full_mask
    curr_job = best_last
    while curr_job != -1:
        perm.append(curr_job)
        prev_job = int(parent[curr_mask, curr_job])
        curr_mask = curr_mask ^ (1 << curr_job)
        curr_job = prev_job
        
    perm.reverse()
    elapsed = time.perf_counter() - start_time
    return perm, best_cmax, elapsed, transitions
