"""
Unit tests for Baselines (brute_force, exact_dp, ilp, ga_sa, dispatching, local_search).
"""
import pytest
from src.instances import get_base_4job_instance, generate_instance
from src.baselines.brute_force import solve_brute_force
from src.baselines.exact_dp import solve_exact_dp
from src.baselines.ilp import solve_ilp_cpsat, solve_ilp_pulp
from src.baselines.dispatching import rule_spt, rule_erd, rule_nearest_setup, rule_earliest_completion
from src.baselines.local_search import multi_start_local_search
from src.baselines.ga_sa import solve_ga, solve_sa


def test_base_4job_exact_match_all_exact_solvers():
    """Verify all exact solvers give c_max = 14 on base 4-job instance."""
    inst = get_base_4job_instance()
    
    # 1. Brute Force
    bf_perm, bf_cmax, _, _ = solve_brute_force(inst.p, inst.r, inst.s, inst.s0)
    assert bf_cmax == 14
    
    # 2. Exact DP
    dp_perm, dp_cmax, _, _ = solve_exact_dp(inst.p, inst.r, inst.s, inst.s0)
    assert dp_cmax == 14
    
    # 3. CP-SAT
    cp_perm, cp_cmax, _, _ = solve_ilp_cpsat(inst.p, inst.r, inst.s, inst.s0, time_limit=10.0)
    assert cp_cmax == 14
    
    # 4. PuLP
    pulp_perm, pulp_cmax, _, _ = solve_ilp_pulp(inst.p, inst.r, inst.s, inst.s0, time_limit=10.0)
    assert pulp_cmax == 14


def test_exact_solvers_agreement_random_instance():
    """Verify brute force, exact DP, and CP-SAT find the EXACT same optimal makespan on n=6 instance."""
    inst = generate_instance(n=6, alpha=0.3, setup_type="asymmetric", seed=42)
    
    bf_perm, bf_cmax, _, _ = solve_brute_force(inst.p, inst.r, inst.s, inst.s0)
    dp_perm, dp_cmax, _, _ = solve_exact_dp(inst.p, inst.r, inst.s, inst.s0)
    cp_perm, cp_cmax, _, _ = solve_ilp_cpsat(inst.p, inst.r, inst.s, inst.s0, time_limit=15.0)
    
    assert bf_cmax == dp_cmax, f"BF ({bf_cmax}) != DP ({dp_cmax})"
    assert dp_cmax == cp_cmax, f"DP ({dp_cmax}) != CP-SAT ({cp_cmax})"
    assert sorted(dp_perm) == list(range(6))
    assert sorted(cp_perm) == list(range(6))


def test_metaheuristics_validity():
    """Verify dispatching rules, GA, SA, and Local Search yield valid permutations."""
    inst = generate_instance(n=10, alpha=0.3, setup_type="asymmetric", seed=101)
    
    methods = [
        ("SPT", lambda: rule_spt(inst.p, inst.r, inst.s, inst.s0)[0]),
        ("ERD", lambda: rule_erd(inst.p, inst.r, inst.s, inst.s0)[0]),
        ("Nearest", lambda: rule_nearest_setup(inst.p, inst.r, inst.s, inst.s0)[0]),
        ("ECT", lambda: rule_earliest_completion(inst.p, inst.r, inst.s, inst.s0)[0]),
        ("LocalSearch", lambda: multi_start_local_search(inst.p, inst.r, inst.s, inst.s0, num_starts=3, time_limit=1.0)[0]),
        ("GA", lambda: solve_ga(inst.p, inst.r, inst.s, inst.s0, pop_size=20, time_limit=1.0)[0]),
        ("SA", lambda: solve_sa(inst.p, inst.r, inst.s, inst.s0, time_limit=1.0)[0]),
    ]
    
    for name, method in methods:
        perm = method()
        assert len(perm) == inst.n, f"{name} produced incorrect length {len(perm)}"
        assert sorted(perm) == list(range(inst.n)), f"{name} produced invalid permutation {perm}"

