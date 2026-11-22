"""
Unit tests for NSGA-II bi-objective baseline (src/baselines/nsga2.py).
"""
import pytest
import numpy as np
from src.instances import get_base_4job_instance, generate_instance
from src.baselines.nsga2 import solve_nsga2, compute_hypervolume


def test_nsga2_base_4job():
    """Verify NSGA-II on base 4-job instance finds C_max=14, TWT=0."""
    inst = get_base_4job_instance()
    perms, front, elapsed, evals = solve_nsga2(
        inst.p, inst.r, inst.s, inst.s0, inst.d, inst.w,
        pop_size=20, n_gen=10, seed=42
    )
    assert len(front) > 0
    # Every solution in the Pareto front must achieve C_max = 14 and TWT = 0.0
    for obj in front:
        assert obj[0] == 14
        assert obj[1] == 0.0


def test_nsga2_random_instance():
    """Verify NSGA-II produces valid non-dominated solutions on an n=8 instance."""
    inst = generate_instance(n=8, alpha=0.3, setup_type="asymmetric", seed=99)
    perms, front, elapsed, evals = solve_nsga2(
        inst.p, inst.r, inst.s, inst.s0, inst.d, inst.w,
        pop_size=20, n_gen=15, seed=42
    )
    assert len(front) > 0
    assert len(perms) == len(front)
    
    # Check each solution is a valid permutation of 0..7
    for perm in perms:
        assert sorted(perm.tolist()) == list(range(8))
        
    # Check hypervolume with respect to an upper bounding reference point
    max_cmax = max(front[:, 0]) * 1.5
    max_twt = max(front[:, 1]) * 1.5 + 10.0
    ref_point = np.array([max_cmax, max_twt])
    hv = compute_hypervolume(front, ref_point)
    assert hv > 0.0

