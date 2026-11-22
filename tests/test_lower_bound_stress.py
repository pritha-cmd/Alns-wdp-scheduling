"""
Stress test for Dual Lower Bound:
Validates that LB <= C_max* across 1,000 diverse random instances (n in [3, 8],
alpha in [0, 0.6], symmetric & asymmetric setups) against exact Held-Karp DP.
"""

import pytest
import numpy as np
from src.instances import generate_instance
from src.lower_bound import compute_lower_bound
from src.baselines.exact_dp import solve_exact_dp


def test_lower_bound_stress_1000_instances():
    """Verify LB <= exact_opt across 1,000 random instances."""
    rng = np.random.default_rng(2026)
    
    total_tested = 0
    tight_matches = 0
    
    # 1,000 instances across various sizes, alphas, and setup families
    for i in range(1000):
        n = int(rng.integers(3, 8))
        alpha = float(rng.choice([0.0, 0.2, 0.4, 0.6]))
        s_type = str(rng.choice(["asymmetric", "symmetric"]))
        seed = int(rng.integers(1, 1000000))
        
        inst = generate_instance(n=n, alpha=alpha, setup_type=s_type, seed=seed)
        lb = compute_lower_bound(inst.p, inst.r, inst.s, inst.s0)
        _, exact_opt, _, _ = solve_exact_dp(inst.p, inst.r, inst.s, inst.s0)
        
        assert lb <= exact_opt, (
            f"VIOLATION at instance {i}: n={n}, alpha={alpha}, s_type={s_type}, seed={seed} | "
            f"LB={lb} > Opt={exact_opt}"
        )
        if lb == exact_opt:
            tight_matches += 1
        total_tested += 1
        
    print(f"\n[Stress Test Passed] 1,000 / 1,000 instances verified: LB <= Opt.")
    print(f"Exact match rate (LB == Opt): {tight_matches / total_tested * 100:.1f}%.")


if __name__ == "__main__":
    test_lower_bound_stress_1000_instances()

