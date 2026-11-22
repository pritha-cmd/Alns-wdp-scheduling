"""
Valid Dual Lower Bounds for 1 | r_j, s_ij | C_max:
Combines Linear Sum Assignment Problem (Hungarian) relaxation on global setups
with processing-only release-date anchor bounds.
Guaranteed: LB <= C_max* for all valid instances.
"""

from typing import List, Tuple, Set
import numpy as np
from scipy.optimize import linear_sum_assignment


def compute_assignment_setup_bound(
    n: int,
    s: List[List[int]],
    s0: List[int],
    subset: List[int] = None,
    include_initial_depot: bool = True,
) -> int:
    """
    Computes minimum setup transition lower bound via Linear Sum Assignment Problem.
    
    CRITICAL VALIDITY WARNING:
    Computing an assignment relaxation strictly on a proper subset of jobs S_a subset V
    does NOT yield a valid lower bound when combined with release dates
    (e.g., r_a + sum_{k in S_a} p_k + C_AP(S_a) is INADMISSIBLE for arbitrary setups).
    Earlier-released jobs outside S_a can interleave between subset jobs, bypassing
    internal transitions of S_a.
    For valid global scheduling lower bounds, this function must be evaluated over the
    complete job set V (subset=None) with include_initial_depot=True.
    The subset parameter is retained only for sub-graph analysis where interleaving is
    prohibited by external constraints.
    """
    if subset is None:
        subset = list(range(n))
        
    m = len(subset)
    if m <= 1:
        return 0
        
    INF = 10**8
    # Cost matrix of size (m + 1) x (m + 1)
    # Row 0: entry node (depot or dummy source)
    # Rows 1..m: jobs in subset
    # Col 0..m-1: jobs in subset
    # Col m: dummy sink
    cost_matrix = np.full((m + 1, m + 1), INF, dtype=int)
    
    # Entry node (row 0) to subset jobs
    for j_idx, job in enumerate(subset):
        if include_initial_depot:
            cost_matrix[0, j_idx] = s0[job]
        else:
            cost_matrix[0, j_idx] = 0  # free entry from prior schedule
            
    # Transition arcs between subset jobs
    for i_idx, u in enumerate(subset):
        for j_idx, v in enumerate(subset):
            if i_idx != j_idx:
                cost_matrix[i_idx + 1, j_idx] = s[u][v]
                
    # Free exit to sink
    for i_idx in range(m):
        cost_matrix[i_idx + 1, m] = 0
        
    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    min_setup = int(cost_matrix[row_ind, col_ind].sum())
    return max(0, min_setup)


def compute_lower_bound(
    p: List[int],
    r: List[int],
    s: List[List[int]],
    s0: List[int],
) -> int:
    r"""
    Computes proven valid dual lower bound for 1 | r_j, s_ij | C_max.
    
    LB = max(
        sum(p) + C_AP(V),                                       # Global flow + setup bound (Hungarian Assignment Problem)
        max_{j in V} (r_j + p_j),                               # Individual release completion bound
        max_{a in V} (r_a + sum_{k in S_a} p_k)                 # Valid processing-only release anchor bound
    )
    where S_a = {k in V : r_k >= r_a}.
    
    MATHEMATICAL VALIDITY AND CAUTION ON SUBSET SETUPS:
    An anchor subset S_a cannot validly add an internal assignment setup term C_AP(S_a)
    for arbitrary setup matrices because earlier-released jobs from V \ S_a can be interleaved
    between subset jobs in a feasible schedule, bypassing internal transitions of S_a (as proven
    by counterexample p=[1,1,1], r=[0,1,1], s_{BC}=s_{CB}=100 where makespan is 4 but subset setup bound returned 103).
    Hence, the release-anchor bound is strictly processing-only: r_a + sum_{k in S_a} p_k.
    This guarantees LB <= C_max* for all valid problem instances.
    """
    n = len(p)
    if n == 0:
        return 0
        
    # 1. Global flow + assignment setup bound (Hungarian relaxation over all jobs + depot)
    sum_p = sum(p)
    global_ap_setup = compute_assignment_setup_bound(n, s, s0, subset=None, include_initial_depot=True)
    lb_global = sum_p + global_ap_setup
    
    # 2. Individual release date completion lower bound
    lb_indiv = max(r[j] + p[j] for j in range(n))
    
    # 3. Processing-only release anchor lower bound
    # For any job a, all jobs in S_a = {k : r_k >= r_a} cannot start before r_a,
    # and require at least sum_{k in S_a} p_k processing time on the single machine.
    distinct_r = set(r)
    lb_anchor_max = max(r_val + sum(p[k] for k in range(n) if r[k] >= r_val) for r_val in distinct_r)
            
    return int(max(lb_global, lb_indiv, lb_anchor_max))
