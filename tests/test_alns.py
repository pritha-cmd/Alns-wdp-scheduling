"""
Unit tests for ALNS-WDP solver and Window DP polishers (src/alns/).
"""
import pytest
from src.instances import get_base_4job_instance, generate_instance
from src.alns.solver import solve_alns_wdp, ALNSConfig
from src.alns.window_dp import optimize_window_dp, sliding_window_dp_sweep
from src.evaluator import compute_makespan


def test_alns_base_4job():
    """Verify ALNS-WDP on base 4-job instance finds optimal makespan 14."""
    inst = get_base_4job_instance()
    cfg = ALNSConfig(time_limit=1.0, max_iterations=50, window_size_k=4, seed=42)
    res = solve_alns_wdp(inst.p, inst.r, inst.s, inst.s0, config=cfg)
    assert res.best_cmax == 14
    assert sorted(res.best_perm) == list(range(4))


def test_window_dp_monotonicity():
    """Verify Window DP never worsens the makespan of any valid schedule."""
    inst = generate_instance(n=12, alpha=0.3, setup_type="asymmetric", seed=101)
    # Start with a reverse order schedule
    perm = list(reversed(range(12)))
    initial_cmax = compute_makespan(perm, inst.p, inst.r, inst.s, inst.s0)
    
    # Run sliding window DP with k=6
    polished_perm, polished_cmax, imp = sliding_window_dp_sweep(
        perm, k=6, p=inst.p, r=inst.r, s=inst.s, s0=inst.s0
    )
    assert polished_cmax <= initial_cmax
    assert sorted(polished_perm) == list(range(12))


def test_alns_ablations_runnable():
    """Verify that ALNS configurations (full, without window-DP, without adaptive weights) execute correctly."""
    inst = generate_instance(n=10, alpha=0.3, setup_type="asymmetric", seed=202)
    
    # 1. Full ALNS-WDP
    cfg_full = ALNSConfig(time_limit=1.0, max_iterations=100, enable_window_dp=True, enable_adaptive_weights=True)
    res_full = solve_alns_wdp(inst.p, inst.r, inst.s, inst.s0, cfg_full)
    assert len(res_full.best_perm) == 10
    
    # 2. Without Window DP
    cfg_no_dp = ALNSConfig(time_limit=1.0, max_iterations=100, enable_window_dp=False, enable_adaptive_weights=True)
    res_no_dp = solve_alns_wdp(inst.p, inst.r, inst.s, inst.s0, cfg_no_dp)
    assert len(res_no_dp.best_perm) == 10
    
    # 3. Without Adaptive Weights
    cfg_no_adapt = ALNSConfig(time_limit=1.0, max_iterations=100, enable_window_dp=True, enable_adaptive_weights=False)
    res_no_adapt = solve_alns_wdp(inst.p, inst.r, inst.s, inst.s0, cfg_no_adapt)
    assert len(res_no_adapt.best_perm) == 10


def test_alns_budget_enforcement_max_overrun():
    """Verify that ALNS-WDP never exceeds the allotted wall-clock budget by more than 5%."""
    for n in [20, 50, 100]:
        inst = generate_instance(n=n, alpha=0.3, setup_type="asymmetric", seed=303 + n)
        budget = 0.5
        cfg = ALNSConfig(time_limit=budget, window_size_k=8, seed=42)
        res = solve_alns_wdp(inst.p, inst.r, inst.s, inst.s0, config=cfg)
        max_allowed = budget * 1.05
        assert res.elapsed_time <= max_allowed, (
            f"Overrun violation for n={n}: elapsed={res.elapsed_time:.4f}s > max_allowed={max_allowed:.4f}s "
            f"({(res.elapsed_time - budget)/budget * 100:.2f}% overrun)"
        )

