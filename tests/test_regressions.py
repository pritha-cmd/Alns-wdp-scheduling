"""
Regression tests for bugs found in the repository audit:
1. ALNS-WDP crashed for n <= 2 (empty randint range).
2. SA/GA mutation was a no-op for n == 2, so SA could not find the optimum.
3. Window DP ignored the wall-clock deadline, so large k overran the budget.
4. ALNSConfig.max_iterations was silently ignored.
"""
import time
import pytest

from src.instances import generate_instance
from src.alns.solver import solve_alns_wdp, ALNSConfig
from src.alns.window_dp import optimize_window_dp
from src.baselines.exact_dp import solve_exact_dp
from src.baselines.ga_sa import solve_sa, mutate_perm
import random


@pytest.mark.parametrize("n", [1, 2, 3])
def test_alns_tiny_instances_do_not_crash_and_are_optimal(n):
    inst = generate_instance(n=n, alpha=0.3, setup_type="asymmetric", seed=5)
    res = solve_alns_wdp(inst.p, inst.r, inst.s, inst.s0, inst.d, inst.w, ALNSConfig(time_limit=0.2))
    _, opt, _, _ = solve_exact_dp(inst.p, inst.r, inst.s, inst.s0)
    assert sorted(res.best_perm) == list(range(n))
    assert res.best_cmax == opt


def test_mutate_perm_changes_two_job_permutation():
    rng = random.Random(0)
    outs = {tuple(mutate_perm([0, 1], rng)) for _ in range(50)}
    assert (1, 0) in outs


def test_sa_finds_optimum_for_two_jobs():
    inst = generate_instance(n=2, alpha=0.3, setup_type="asymmetric", seed=5)
    _, sa_c, _, _, _ = solve_sa(inst.p, inst.r, inst.s, inst.s0, time_limit=0.2, seed=1)
    _, opt, _, _ = solve_exact_dp(inst.p, inst.r, inst.s, inst.s0)
    assert sa_c == opt


def test_max_iterations_is_honoured():
    inst = generate_instance(n=10, alpha=0.3, setup_type="asymmetric", seed=3)
    cfg = ALNSConfig(time_limit=5.0, max_iterations=5, seed=1)
    t0 = time.perf_counter()
    res = solve_alns_wdp(inst.p, inst.r, inst.s, inst.s0, config=cfg)
    assert res.total_iterations == 5
    assert time.perf_counter() - t0 < 2.0


def test_window_dp_respects_expired_deadline_and_leaves_perm_unchanged():
    inst = generate_instance(n=14, alpha=0.3, setup_type="asymmetric", seed=9)
    perm = list(reversed(range(14)))
    new_perm, improved = optimize_window_dp(
        perm, 0, 12, inst.p, inst.r, inst.s, inst.s0, deadline=time.perf_counter() - 1.0
    )
    assert new_perm == perm and improved is False


def test_alns_budget_with_large_window_k12():
    """k=12 previously overran the budget by 12-21%; allow 10% here."""
    for n in [30, 100]:
        inst = generate_instance(n=n, alpha=0.3, setup_type="asymmetric", seed=7)
        budget = 0.3
        res = solve_alns_wdp(
            inst.p, inst.r, inst.s, inst.s0, config=ALNSConfig(time_limit=budget, window_size_k=12, seed=1)
        )
        assert res.elapsed_time <= budget * 1.10, f"n={n}: {res.elapsed_time:.3f}s"
