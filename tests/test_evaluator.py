"""
Unit tests for Schedule Evaluator (src/evaluator.py).
"""
import itertools
import pytest
from src.instances import get_base_4job_instance, generate_instance
from src.evaluator import evaluate_schedule, compute_makespan, compute_bi_objective


def test_base_4job_evaluator_all_permutations():
    """Verify that the base 4-job instance yields c_max=14 for all 24 permutations."""
    inst = get_base_4job_instance()
    perms = list(itertools.permutations(range(inst.n)))
    assert len(perms) == 24
    
    for p in perms:
        res = evaluate_schedule(
            perm=list(p),
            p=inst.p,
            r=inst.r,
            s=inst.s,
            s0=inst.s0,
            d=inst.d,
            w=inst.w,
        )
        assert res.c_max == 14
        assert res.idle_time == 0
        assert res.total_setup_time == 0
        assert res.total_weighted_tardiness == 0.0
        
        # Test fast makespan calculation
        fast_cmax = compute_makespan(list(p), inst.p, inst.r, inst.s, inst.s0)
        assert fast_cmax == 14
        
        fast_cmax_bi, fast_twt = compute_bi_objective(
            list(p), inst.p, inst.r, inst.s, inst.s0, inst.d, inst.w
        )
        assert fast_cmax_bi == 14
        assert fast_twt == 0.0


def test_evaluator_consistency_random_instance():
    """Verify consistency between detailed evaluator and fast evaluation functions."""
    inst = generate_instance(n=8, alpha=0.3, setup_type="asymmetric", seed=123)
    rng_perm = [3, 0, 7, 2, 5, 1, 4, 6]
    
    res = evaluate_schedule(
        perm=rng_perm,
        p=inst.p,
        r=inst.r,
        s=inst.s,
        s0=inst.s0,
        d=inst.d,
        w=inst.w,
    )
    
    fast_cmax = compute_makespan(rng_perm, inst.p, inst.r, inst.s, inst.s0)
    fast_cmax_bi, fast_twt = compute_bi_objective(
        rng_perm, inst.p, inst.r, inst.s, inst.s0, inst.d, inst.w
    )
    
    assert res.c_max == fast_cmax
    assert res.c_max == fast_cmax_bi
    assert abs(res.total_weighted_tardiness - fast_twt) < 1e-6
    
    # Check start and completion times consistency
    for idx, job in enumerate(rng_perm):
        assert res.completion_times[job] == res.start_times[job] + inst.p[job]
        assert res.start_times[job] >= inst.r[job]
        if idx > 0:
            prev_job = rng_perm[idx - 1]
            assert res.start_times[job] >= res.completion_times[prev_job] + inst.s[prev_job][job]
        else:
            assert res.start_times[job] >= inst.s0[job]


def test_evaluator_idle_time_verification():
    """Manual trace test to check idle time computation."""
    # 2 jobs:
    # Job 0: p=5, r=0, s0=2
    # Job 1: p=10, r=25, s0=1, s[0][1]=3
    # Schedule [0, 1]:
    # Job 0 starts at max(0, 2) = 2, ends at 2+5=7.
    # Job 1 earliest after setup = 7+3 = 10.
    # Job 1 release date = 25.
    # Start of Job 1 = max(25, 10) = 25. Idle time = 25 - 10 = 15.
    # Job 1 ends at 25+10 = 35. Makespan = 35. Total setup = 2 + 3 = 5.
    p = [5, 10]
    r = [0, 25]
    s = [[0, 3], [3, 0]]
    s0 = [2, 1]
    
    res = evaluate_schedule([0, 1], p, r, s, s0)
    assert res.start_times[0] == 2
    assert res.completion_times[0] == 7
    assert res.start_times[1] == 25
    assert res.completion_times[1] == 35
    assert res.c_max == 35
    assert res.idle_time == 15
    assert res.total_setup_time == 5

