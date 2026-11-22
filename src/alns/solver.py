"""
ALNS-WDP: Adaptive Large Neighborhood Search with Exact Window Dynamic Programming
and Reinforcement-Style Operator Selection for 1 | r_j, s_ij | C_max
and Bi-Objective Scalarized Scheduling (C_max, sum w_j T_j).
"""

import time
import math
import random
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any, Optional
import numpy as np

from src.evaluator import (
    compute_makespan,
    evaluate_schedule,
    compute_bi_objective,
    compute_scalarized_objective,
)
from src.alns.operators import (
    destroy_random,
    destroy_worst_setup,
    destroy_release_cluster,
    destroy_relatedness,
    repair_greedy_best_insertion,
    repair_regret2_insertion,
)
from src.alns.window_dp import (
    sliding_window_dp_sweep,
    optimize_window_dp,
    targeted_window_dp_polish,
)
from src.baselines.dispatching import rule_erd, rule_nearest_setup, rule_earliest_completion


@dataclass
class ALNSConfig:
    time_limit: float = 2.0
    max_iterations: Optional[int] = None
    window_size_k: int = 8
    enable_adaptive_k: bool = False
    k_min: int = 6
    k_max: int = 10
    enable_window_dp: bool = True
    dp_placement_strategy: str = "sliding"  # 'sliding', 'worst_setup', 'random'
    dp_interval: int = 25
    enable_adaptive_weights: bool = True
    enable_contextual_bandit: bool = False
    learning_rate_rho: float = 0.2
    weight_floor_ratio: float = 0.1
    temp_ratio: float = 0.05
    t_min_ratio: float = 0.001
    reheat_threshold: int = 200
    q_min_ratio: float = 0.1
    q_max_ratio: float = 0.3
    seed: int = 42
    # Bi-objective scalarization parameters
    scalar_lambda: float = 1.0  # 1.0 = makespan only; <1.0 = scalarized (C_max, TWT)
    norm_cmax: float = 1.0
    norm_twt: float = 1.0


@dataclass
class ALNSResult:
    best_perm: List[int]
    best_cmax: int
    best_scalar_cost: float
    elapsed_time: float
    total_iterations: int
    total_evals: int
    convergence_history: List[Tuple[float, float]]
    operator_scores: Dict[str, float]
    window_dp_improvements: int


def construct_initial_solution(
    p: List[int],
    r: List[int],
    s: List[List[int]],
    s0: List[int],
    rng: random.Random,
    d: Optional[List[int]] = None,
    w: Optional[List[int]] = None,
    lam: float = 1.0,
    norm_cmax: float = 1.0,
    norm_twt: float = 1.0,
) -> Tuple[List[int], int, float]:
    """
    Constructs the strongest starting permutation among ERD, Nearest-Setup, and ECT.
    """
    candidates = []
    
    # 1. ERD
    p_erd, c_erd, _ = rule_erd(p, r, s, s0)
    score_erd = compute_scalarized_objective(p_erd, p, r, s, s0, d, w, lam, norm_cmax, norm_twt)
    candidates.append((p_erd, c_erd, score_erd))
    
    # 2. Nearest-Setup
    p_ns, c_ns, _ = rule_nearest_setup(p, r, s, s0)
    score_ns = compute_scalarized_objective(p_ns, p, r, s, s0, d, w, lam, norm_cmax, norm_twt)
    candidates.append((p_ns, c_ns, score_ns))
    
    # 3. ECT
    p_ect, c_ect, _ = rule_earliest_completion(p, r, s, s0)
    score_ect = compute_scalarized_objective(p_ect, p, r, s, s0, d, w, lam, norm_cmax, norm_twt)
    candidates.append((p_ect, c_ect, score_ect))
    
    # Sort by scalarized objective
    candidates.sort(key=lambda x: x[2])
    return list(candidates[0][0]), candidates[0][1], candidates[0][2]


def solve_alns_wdp(
    p: List[int],
    r: List[int],
    s: List[List[int]],
    s0: List[int],
    d: Optional[List[int]] = None,
    w: Optional[List[int]] = None,
    config: Optional[ALNSConfig] = None,
) -> ALNSResult:
    """
    Executes ALNS-WDP under strict wall-clock time limit.
    """
    if config is None:
        config = ALNSConfig()
        
    start_time = time.perf_counter()
    deadline = start_time + config.time_limit
    search_deadline = start_time + config.time_limit * 0.98
    rng = random.Random(config.seed)
    n = len(p)
    
    # Operator definitions
    destroy_ops = [
        ("random", destroy_random),
        ("worst_setup", destroy_worst_setup),
        ("release_cluster", destroy_release_cluster),
        ("relatedness", destroy_relatedness),
    ]
    repair_ops = [
        ("greedy", repair_greedy_best_insertion),
        ("regret2", repair_regret2_insertion),
    ]
    
    num_d = len(destroy_ops)
    num_r = len(repair_ops)
    
    # Action-value weights (Context 0: low stagnation, Context 1: high stagnation)
    num_contexts = 2 if config.enable_contextual_bandit else 1
    w_destroy = np.ones((num_contexts, num_d), dtype=float)
    w_repair = np.ones((num_contexts, num_r), dtype=float)
    
    # Base reward constants
    R_BEST_BASE = 30.0
    R_IMP_BASE = 15.0
    R_ACC = 5.0
    R_REJ = 0.0
    
    # Estimate normalization scales if in bi-objective mode
    lam = config.scalar_lambda
    is_scalarized = (lam < 0.999 and d is not None and w is not None)
    norm_c = config.norm_cmax if config.norm_cmax > 1.0 else float(sum(p) + 10 * n)
    norm_t = config.norm_twt if config.norm_twt > 1.0 else float(sum(w) * sum(p) if w else 100.0)
    
    # 1. Initial construction
    curr_perm, curr_cmax, curr_cost = construct_initial_solution(
        p, r, s, s0, rng, d, w, lam, norm_c, norm_t
    )
    best_perm = list(curr_perm)
    best_cmax = curr_cmax
    best_cost = curr_cost
    
    convergence = [(0.0, best_cost)]
    total_evals = 3
    dp_improvements = 0
    stagnant_steps = 0
    
    # Scale-normalized initial temperature
    T0 = max(1.0, config.temp_ratio * curr_cmax)
    T_min = max(0.001, config.t_min_ratio * T0)
    
    # Initial Window DP Polish
    curr_k = config.k_min if config.enable_adaptive_k else config.window_size_k
    if config.enable_window_dp and n >= curr_k and (time.perf_counter() < deadline - 0.05):
        dp_perm, dp_c, imp = sliding_window_dp_sweep(curr_perm, min(curr_k, n), p, r, s, s0, deadline=deadline)
        total_evals += n
        dp_cost = compute_scalarized_objective(dp_perm, p, r, s, s0, d, w, lam, norm_c, norm_t)
        if dp_cost < curr_cost:
            curr_perm = dp_perm
            curr_cmax = dp_c
            curr_cost = dp_cost
            best_perm = list(dp_perm)
            best_cmax = dp_c
            best_cost = dp_cost
            dp_improvements += 1
            convergence.append((time.perf_counter() - start_time, best_cost))
            
    iteration = 0
    
    # Main search loop strictly budgeted by wall-clock time
    while time.perf_counter() < search_deadline:
        iteration += 1
        elapsed = time.perf_counter() - start_time
        time_frac = min(1.0, elapsed / config.time_limit)
        
        # Continuous time-based geometric cooling
        temp = T0 * ((T_min / T0) ** time_frac)
        
        # Context determination: 0 = normal, 1 = stagnant
        ctx = 1 if (config.enable_contextual_bandit and stagnant_steps >= config.reheat_threshold // 2) else 0
        
        # Adaptive window size k adjustment
        if config.enable_adaptive_k:
            if stagnant_steps >= config.reheat_threshold:
                curr_k = min(config.k_max, n)
            elif stagnant_steps >= config.reheat_threshold // 2:
                curr_k = min((config.k_min + config.k_max) // 2, n)
            else:
                curr_k = min(config.k_min, n)
        else:
            curr_k = min(config.window_size_k, n)
            
        # 1. Operator Selection (Bandit with weight floor)
        if config.enable_adaptive_weights:
            # Enforce weight floor to prevent starvation
            mean_wd = float(np.mean(w_destroy[ctx]))
            floor_wd = max(0.01, config.weight_floor_ratio * mean_wd)
            eff_wd = np.maximum(w_destroy[ctx], floor_wd)
            prob_d = eff_wd / eff_wd.sum()
            
            mean_wr = float(np.mean(w_repair[ctx]))
            floor_wr = max(0.01, config.weight_floor_ratio * mean_wr)
            eff_wr = np.maximum(w_repair[ctx], floor_wr)
            prob_r = eff_wr / eff_wr.sum()
            
            d_idx = rng.choices(range(num_d), weights=prob_d, k=1)[0]
            r_idx = rng.choices(range(num_r), weights=prob_r, k=1)[0]
        else:
            d_idx = rng.randrange(num_d)
            r_idx = rng.randrange(num_r)
            
        d_name, d_func = destroy_ops[d_idx]
        r_name, r_func = repair_ops[r_idx]
        
        # 2. Destroy
        q_min = max(2, int(config.q_min_ratio * n))
        q_max = max(q_min + 1, int(config.q_max_ratio * n))
        q = rng.randint(q_min, min(q_max, n - 1))
        
        partial, removed = d_func(
            perm=curr_perm,
            q=q,
            rng=rng,
            p=p,
            r=r,
            s=s,
            s0=s0,
        )
        
        # 3. Repair (using accelerated incremental insertion with strict deadline)
        cand_perm = r_func(
            partial=partial,
            removed=removed,
            p=p,
            r=r,
            s=s,
            s0=s0,
            rng=rng,
            deadline=deadline,
        )
        cand_cmax = compute_makespan(cand_perm, p, r, s, s0)
        cand_cost = compute_scalarized_objective(cand_perm, p, r, s, s0, d, w, lam, norm_c, norm_t)
        total_evals += q * len(partial)
        
        # 4. Window DP Polishing during search (strictly bounded to prevent overrun)
        if config.enable_window_dp and n >= curr_k and (time.perf_counter() < deadline - 0.05):
            if iteration % config.dp_interval == 0 or cand_cost < best_cost:
                polished_perm, polished_c, imp = targeted_window_dp_polish(
                    cand_perm, curr_k, config.dp_placement_strategy, p, r, s, s0, rng=rng, deadline=deadline
                )
                total_evals += n
                if imp:
                    polished_cost = compute_scalarized_objective(
                        polished_perm, p, r, s, s0, d, w, lam, norm_c, norm_t
                    )
                    if polished_cost < cand_cost:
                        cand_perm = polished_perm
                        cand_cmax = polished_c
                        cand_cost = polished_cost
                        dp_improvements += 1
                        
        # 5. Acceptance Evaluation
        delta = cand_cost - curr_cost
        accepted = False
        reward = R_REJ
        
        if cand_cost < best_cost:
            # New global best
            rel_imp = max(0.0, (best_cost - cand_cost) / max(1.0, best_cost))
            reward = R_BEST_BASE + 100.0 * rel_imp
            best_cost = cand_cost
            best_cmax = cand_cmax
            best_perm = list(cand_perm)
            curr_perm = cand_perm
            curr_cmax = cand_cmax
            curr_cost = cand_cost
            accepted = True
            stagnant_steps = 0
            convergence.append((time.perf_counter() - start_time, best_cost))
        elif delta < 0:
            # Improving current
            rel_imp = max(0.0, (curr_cost - cand_cost) / max(1.0, curr_cost))
            reward = R_IMP_BASE + 50.0 * rel_imp
            curr_perm = cand_perm
            curr_cmax = cand_cmax
            curr_cost = cand_cost
            accepted = True
            stagnant_steps = 0
        elif temp > 1e-4 and rng.random() < math.exp(-delta / temp):
            # Accepted via Metropolis criterion
            reward = R_ACC
            curr_perm = cand_perm
            curr_cmax = cand_cmax
            curr_cost = cand_cost
            accepted = True
            stagnant_steps += 1
        else:
            reward = R_REJ
            stagnant_steps += 1
            
        # 6. Action-Value Weight Update (Exponential-Recency Bandit)
        if config.enable_adaptive_weights:
            rho = config.learning_rate_rho
            w_destroy[ctx, d_idx] = (1.0 - rho) * w_destroy[ctx, d_idx] + rho * reward
            w_repair[ctx, r_idx] = (1.0 - rho) * w_repair[ctx, r_idx] + rho * reward
            
        # 7. Stagnation Reheating
        if stagnant_steps >= config.reheat_threshold:
            T0 = T0 * 0.5  # Soft reheat
            stagnant_steps = 0
            
    # Final sweep with window DP to ensure local mathematical optimality
    if config.enable_window_dp and n >= curr_k and (time.perf_counter() < deadline - 0.02):
        final_perm, final_c, imp = sliding_window_dp_sweep(
            best_perm, curr_k, p, r, s, s0, step_size=1, deadline=deadline
        )
        final_cost = compute_scalarized_objective(final_perm, p, r, s, s0, d, w, lam, norm_c, norm_t)
        if final_cost < best_cost:
            best_perm = final_perm
            best_cmax = final_c
            best_cost = final_cost
            dp_improvements += 1
            
    elapsed = time.perf_counter() - start_time
    convergence.append((elapsed, best_cost))
    
    # Aggregate operator scores for logging
    op_scores = {}
    for i, (name, _) in enumerate(destroy_ops):
        op_scores[f"destroy_{name}"] = float(np.mean(w_destroy[:, i]))
    for j, (name, _) in enumerate(repair_ops):
        op_scores[f"repair_{name}"] = float(np.mean(w_repair[:, j]))
        
    return ALNSResult(
        best_perm=best_perm,
        best_cmax=best_cmax,
        best_scalar_cost=best_cost,
        elapsed_time=elapsed,
        total_iterations=iteration,
        total_evals=total_evals,
        convergence_history=convergence,
        operator_scores=op_scores,
        window_dp_improvements=dp_improvements,
    )
