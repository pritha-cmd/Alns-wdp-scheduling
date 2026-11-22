"""
Unit tests for Dual Lower Bound (src/lower_bound.py).
Includes explicit regression tests for interleaving counterexample and non-metric setups.
"""
import pytest
from src.instances import get_base_4job_instance, generate_instance
from src.lower_bound import compute_lower_bound, compute_assignment_setup_bound
from src.baselines.exact_dp import solve_exact_dp
from src.evaluator import compute_makespan


def test_lower_bound_base_4job():
    """Verify lower bound on base 4-job instance equals exact optimum 14."""
    inst = get_base_4job_instance()
    lb = compute_lower_bound(inst.p, inst.r, inst.s, inst.s0)
    assert lb == 14


def test_lower_bound_interleaving_counterexample():
    """
    Regression test for the interleaving counterexample:
    p = [1, 1, 1], r = [0, 1, 1], s0 = [0, 0, 0]
    s = [[0, 0, 0], [0, 0, 100], [0, 100, 0]]
    Schedule [B, A, C] (indices [1, 0, 2]) achieves makespan 4:
      t=0 -> start B at r_1=1 -> finish 2
      t=2 -> start A (r_0=0, setup=0) -> finish 3
      t=3 -> start C at r_2=1 (setup=0) -> finish 4
    The previous invalid anchor bound computed 1 + (1+1) + 100 = 103 > 4.
    The corrected bound returns 3 <= 4.
    """
    p = [1, 1, 1]
    r = [0, 1, 1]
    s = [[0, 0, 0], [0, 0, 100], [0, 100, 0]]
    s0 = [0, 0, 0]

    # Verify feasible schedule makespan is 4
    cmax_perm = compute_makespan([1, 0, 2], p, r, s, s0)
    assert cmax_perm == 4, f"Permutation [1, 0, 2] makespan must be 4, got {cmax_perm}"

    # Verify exact DP finds optimum 4
    _, exact_opt, _, _ = solve_exact_dp(p, r, s, s0)
    assert exact_opt == 4, f"Exact DP optimum must be 4, got {exact_opt}"

    # Verify lower bound is valid (<= 4) and non-negative
    lb = compute_lower_bound(p, r, s, s0)
    assert lb <= exact_opt, f"LB ({lb}) must be <= exact optimum ({exact_opt})"
    assert lb == 3, f"Expected LB=3, got {lb}"


def test_lower_bound_non_metric_asymmetric_setups():
    """Verify LB validity on non-metric setup matrices with severe triangle inequality violations."""
    # Job 0 -> Job 1 is 50, but Job 0 -> Job 2 -> Job 1 is 1 + 1 = 2
    p = [3, 4, 2]
    r = [0, 5, 2]
    s = [
        [0, 50, 1],
        [10, 0, 30],
        [20, 1, 0]
    ]
    s0 = [0, 5, 2]

    _, exact_opt, _, _ = solve_exact_dp(p, r, s, s0)
    lb = compute_lower_bound(p, r, s, s0)
    assert lb <= exact_opt, f"LB ({lb}) must be <= exact optimum ({exact_opt}) on non-metric instance"


def test_lower_bound_validity_against_exact_optimum():
    """Verify that LB <= exact_optimum for random instances across alphas and setup structures."""
    for n in [6, 8]:
        for alpha in [0.0, 0.3, 0.6]:
            for s_type in ["asymmetric", "symmetric"]:
                inst = generate_instance(n=n, alpha=alpha, setup_type=s_type, seed=n*10 + int(alpha*10))
                lb = compute_lower_bound(inst.p, inst.r, inst.s, inst.s0)
                _, exact_opt, _, _ = solve_exact_dp(inst.p, inst.r, inst.s, inst.s0)
                assert lb <= exact_opt, f"LB ({lb}) violated optimality bound ({exact_opt}) for {inst.name}"
