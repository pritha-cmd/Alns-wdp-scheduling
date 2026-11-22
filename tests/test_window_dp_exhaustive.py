"""
Exhaustive verification of Window DP against Brute Force on sub-windows.
Tests that Window DP achieves the exact mathematical minimum over all k! window orderings
given fixed prefix and suffix constraints.
"""

import itertools
import pytest
from src.instances import generate_instance
from src.alns.window_dp import optimize_window_dp
from src.evaluator import compute_makespan


def test_window_dp_exact_match_against_brute_force():
    """Verify optimize_window_dp produces the exact same optimal order as brute-force enumeration of the window."""
    inst = generate_instance(n=10, alpha=0.3, setup_type="asymmetric", seed=505)
    perm = list(range(10))
    
    # Test windows of size k=4 at various positions: start (idx=0), middle (idx=3), end (idx=6)
    for start_idx in [0, 3, 6]:
        k = 4
        end_idx = start_idx + k
        window_jobs = perm[start_idx:end_idx]
        
        # 1. DP solution
        dp_perm, _ = optimize_window_dp(perm, start_idx, k, inst.p, inst.r, inst.s, inst.s0)
        dp_cmax = compute_makespan(dp_perm, inst.p, inst.r, inst.s, inst.s0)
        
        # 2. Brute Force enumeration over all k! orderings of window_jobs
        bf_best_cmax = float("inf")
        for sub_perm in itertools.permutations(window_jobs):
            cand = perm[:start_idx] + list(sub_perm) + perm[end_idx:]
            c = compute_makespan(cand, inst.p, inst.r, inst.s, inst.s0)
            if c < bf_best_cmax:
                bf_best_cmax = c
                
        assert dp_cmax == bf_best_cmax, (
            f"Window DP ({dp_cmax}) failed to match Brute Force ({bf_best_cmax}) at start_idx={start_idx}"
        )


def test_window_dp_monotonicity_property():
    """Verify optimize_window_dp NEVER increases the makespan of any schedule."""
    inst = generate_instance(n=12, alpha=0.6, setup_type="symmetric", seed=808)
    # Scramble permutation
    rng_perm = [11, 2, 7, 4, 0, 9, 3, 8, 1, 10, 5, 6]
    orig_cmax = compute_makespan(rng_perm, inst.p, inst.r, inst.s, inst.s0)
    
    for start_idx in range(0, 7):
        new_perm, _ = optimize_window_dp(rng_perm, start_idx, k=6, p=inst.p, r=inst.r, s=inst.s, s0=inst.s0)
        new_cmax = compute_makespan(new_perm, inst.p, inst.r, inst.s, inst.s0)
        assert new_cmax <= orig_cmax, f"Monotonicity violated: {new_cmax} > {orig_cmax}"

