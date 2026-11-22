"""
Comprehensive Experimental Benchmarking Suite for Single-Machine Scheduling:
Executes single-objective benchmarks across all instance families (alpha in {0, 0.3, 0.6},
symmetric and asymmetric, derived TSPLIB), exact solvers up to n<=20, CP-SAT variations,
30 independent seeds, real bi-objective scalarization with HV and IGD, and run manifest.
"""

import time
import os
import json
import platform
import psutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd

from src.instances import Instance, generate_instance, get_base_4job_instance
from src.evaluator import (
    compute_makespan,
    evaluate_schedule,
    compute_bi_objective,
    compute_scalarized_objective,
)
from src.lower_bound import compute_lower_bound
from src.baselines.brute_force import solve_brute_force
from src.baselines.exact_dp import solve_exact_dp
from src.baselines.ilp import solve_ilp_cpsat, solve_cpsat_matheuristic
from src.baselines.dispatching import rule_spt, rule_erd, rule_nearest_setup, rule_earliest_completion
from src.baselines.local_search import multi_start_local_search
from src.baselines.ga_sa import solve_ga, solve_sa
from src.baselines.nsga2 import solve_nsga2, compute_hypervolume, compute_igd_metric
from src.alns.solver import solve_alns_wdp, ALNSConfig


def generate_run_manifest(results_dir: str = "results", extra_meta: Dict[str, Any] = None) -> Path:
    """Generates run_manifest.json logging hardware, environment, packages, and seeds."""
    out_dir = Path(results_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "run_manifest.json"
    
    import ortools
    import pulp
    import pymoo
    import scipy
    
    manifest = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "cpu_count_logical": psutil.cpu_count(logical=True),
        "cpu_count_physical": psutil.cpu_count(logical=False),
        "total_ram_gb": round(psutil.virtual_memory().total / (1024**3), 2),
        "packages": {
            "ortools": ortools.__version__,
            "pulp": pulp.__version__,
            "pymoo": pymoo.__version__,
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "pandas": pd.__version__,
        },
        "random_seeds_stochastic": [42 + i * 17 for i in range(30)],
        "configuration": extra_meta or {},
    }
    
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    return manifest_path


def run_single_objective_experiments(
    instances: List[Instance],
    num_seeds: int = 30,
    base_budget_per_run: float = 1.0,
    results_dir: str = "results",
) -> pd.DataFrame:
    """
    Executes single-objective benchmarks across all instances and methods with 30 seeds.
    Guarantees strictly unique rows on (instance, method, seed).
    """
    out_dir = Path(results_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    records = []
    seen_keys = set()
    
    def _add_record(rec: Dict[str, Any]):
        key = (rec["instance"], rec["method"], rec["seed"])
        if key not in seen_keys:
            seen_keys.add(key)
            records.append(rec)
            
    for inst in instances:
        setup_type = "sym" if inst.is_symmetric else "asym"
        print(f"\n[Benchmarking] {inst.name} | n={inst.n} | alpha={inst.alpha} | setup={setup_type} | family={inst.family}")
        
        # 1. Compute Tightened Dual Lower Bound
        lb = compute_lower_bound(inst.p, inst.r, inst.s, inst.s0)
        
        # 2. Exact Solutions for Ground-Truth Reference
        exact_opt = None
        
        # (a) Brute Force for n <= 10
        if inst.n <= 10:
            bf_perm, bf_cmax, bf_time, bf_evals = solve_brute_force(inst.p, inst.r, inst.s, inst.s0)
            exact_opt = bf_cmax
            gap_lb = ((bf_cmax - lb) / lb) * 100.0
            _add_record({
                "instance": inst.name, "n": inst.n, "alpha": inst.alpha, "setup_type": setup_type,
                "family": inst.family, "method": "Brute_Force", "seed": 0, "makespan": bf_cmax,
                "lb": lb, "opt": exact_opt, "gap_lb_pct": gap_lb, "gap_opt_pct": 0.0,
                "runtime": bf_time, "eval_count": bf_evals, "is_optimal": True
            })
            
        # (b) Exact Held-Karp DP for n <= 20
        if inst.n <= 20:
            dp_timeout = 25.0 if inst.n <= 16 else 60.0
            dp_perm, dp_cmax, dp_time, dp_evals = solve_exact_dp(inst.p, inst.r, inst.s, inst.s0, timeout=dp_timeout)
            if dp_cmax != -1:
                exact_opt = dp_cmax
                gap_lb = ((dp_cmax - lb) / lb) * 100.0
                _add_record({
                    "instance": inst.name, "n": inst.n, "alpha": inst.alpha, "setup_type": setup_type,
                    "family": inst.family, "method": "Exact_DP", "seed": 0, "makespan": dp_cmax,
                    "lb": lb, "opt": exact_opt, "gap_lb_pct": gap_lb, "gap_opt_pct": 0.0,
                    "runtime": dp_time, "eval_count": dp_evals, "is_optimal": True
                })
                
        # (c) CP-SAT at equal metaheuristic budget and at 60s
        budget = max(base_budget_per_run, 0.03 * inst.n)
        
        if inst.n <= 30:
            # Equal budget CP-SAT
            cp_perm, cp_cmax, cp_time, cp_meta = solve_ilp_cpsat(
                inst.p, inst.r, inst.s, inst.s0, time_limit=budget, symmetry_breaking=True
            )
            if cp_cmax is not None:
                is_opt = (cp_meta["status"] == "OPTIMAL")
                if is_opt and exact_opt is None:
                    exact_opt = cp_cmax
                gap_lb = ((cp_cmax - lb) / lb) * 100.0
                gap_opt = ((cp_cmax - exact_opt) / exact_opt * 100.0) if exact_opt else None
                _add_record({
                    "instance": inst.name, "n": inst.n, "alpha": inst.alpha, "setup_type": setup_type,
                    "family": inst.family, "method": "CP_SAT_EqualBudget", "seed": 0, "makespan": cp_cmax,
                    "lb": lb, "opt": exact_opt, "gap_lb_pct": gap_lb, "gap_opt_pct": gap_opt,
                    "runtime": cp_time, "eval_count": cp_meta.get("branches", 0), "is_optimal": is_opt
                })
                
            # Warm-started CP-SAT with ECT dispatching
            ect_perm, _, _ = rule_earliest_completion(inst.p, inst.r, inst.s, inst.s0)
            cp_w_perm, cp_w_cmax, cp_w_time, cp_w_meta = solve_ilp_cpsat(
                inst.p, inst.r, inst.s, inst.s0, time_limit=budget, warm_start_perm=ect_perm
            )
            if cp_w_cmax is not None:
                gap_lb = ((cp_w_cmax - lb) / lb) * 100.0
                gap_opt = ((cp_w_cmax - exact_opt) / exact_opt * 100.0) if exact_opt else None
                _add_record({
                    "instance": inst.name, "n": inst.n, "alpha": inst.alpha, "setup_type": setup_type,
                    "family": inst.family, "method": "CP_SAT_WarmStart_ECT", "seed": 0, "makespan": cp_w_cmax,
                    "lb": lb, "opt": exact_opt, "gap_lb_pct": gap_lb, "gap_opt_pct": gap_opt,
                    "runtime": cp_w_time, "eval_count": cp_w_meta.get("branches", 0), "is_optimal": (cp_w_meta["status"] == "OPTIMAL")
                })
                
        # 3. Deterministic Priority Dispatching Rules
        rules = [
            ("Rule_SPT", rule_spt),
            ("Rule_ERD", rule_erd),
            ("Rule_NearestSetup", rule_nearest_setup),
            ("Rule_ECT", rule_earliest_completion),
        ]
        for r_name, r_func in rules:
            r_perm, r_cmax, r_time = r_func(inst.p, inst.r, inst.s, inst.s0)
            gap_lb = ((r_cmax - lb) / lb) * 100.0
            gap_opt = ((r_cmax - exact_opt) / exact_opt * 100.0) if exact_opt else None
            _add_record({
                "instance": inst.name, "n": inst.n, "alpha": inst.alpha, "setup_type": setup_type,
                "family": inst.family, "method": r_name, "seed": 0, "makespan": r_cmax,
                "lb": lb, "opt": exact_opt, "gap_lb_pct": gap_lb, "gap_opt_pct": gap_opt,
                "runtime": r_time, "eval_count": 1, "is_optimal": (r_cmax == exact_opt if exact_opt else False)
            })
            
        # 4. Stochastic Metaheuristics across 30 Independent Seeds
        for seed_idx in range(num_seeds):
            curr_seed = 42 + seed_idx * 17
            
            # (a) Multi-Start Local Search
            ms_perm, ms_cmax, ms_time, ms_evals = multi_start_local_search(
                inst.p, inst.r, inst.s, inst.s0, num_starts=5, time_limit=budget, seed=curr_seed
            )
            gap_lb = ((ms_cmax - lb) / lb) * 100.0
            gap_opt = ((ms_cmax - exact_opt) / exact_opt * 100.0) if exact_opt else None
            _add_record({
                "instance": inst.name, "n": inst.n, "alpha": inst.alpha, "setup_type": setup_type,
                "family": inst.family, "method": "MultiStart_LS", "seed": curr_seed, "makespan": ms_cmax,
                "lb": lb, "opt": exact_opt, "gap_lb_pct": gap_lb, "gap_opt_pct": gap_opt,
                "runtime": ms_time, "eval_count": ms_evals, "is_optimal": (ms_cmax == exact_opt if exact_opt else False)
            })
            
            # (b) Genetic Algorithm (GA)
            ga_perm, ga_cmax, ga_time, ga_evals, _ = solve_ga(
                inst.p, inst.r, inst.s, inst.s0, pop_size=40, time_limit=budget, seed=curr_seed
            )
            gap_lb = ((ga_cmax - lb) / lb) * 100.0
            gap_opt = ((ga_cmax - exact_opt) / exact_opt * 100.0) if exact_opt else None
            _add_record({
                "instance": inst.name, "n": inst.n, "alpha": inst.alpha, "setup_type": setup_type,
                "family": inst.family, "method": "GA", "seed": curr_seed, "makespan": ga_cmax,
                "lb": lb, "opt": exact_opt, "gap_lb_pct": gap_lb, "gap_opt_pct": gap_opt,
                "runtime": ga_time, "eval_count": ga_evals, "is_optimal": (ga_cmax == exact_opt if exact_opt else False)
            })
            
            # (c) Simulated Annealing (SA)
            sa_perm, sa_cmax, sa_time, sa_evals, _ = solve_sa(
                inst.p, inst.r, inst.s, inst.s0, time_limit=budget, seed=curr_seed
            )
            gap_lb = ((sa_cmax - lb) / lb) * 100.0
            gap_opt = ((sa_cmax - exact_opt) / exact_opt * 100.0) if exact_opt else None
            _add_record({
                "instance": inst.name, "n": inst.n, "alpha": inst.alpha, "setup_type": setup_type,
                "family": inst.family, "method": "SA", "seed": curr_seed, "makespan": sa_cmax,
                "lb": lb, "opt": exact_opt, "gap_lb_pct": gap_lb, "gap_opt_pct": gap_opt,
                "runtime": sa_time, "eval_count": sa_evals, "is_optimal": (sa_cmax == exact_opt if exact_opt else False)
            })
            
            # (d) Proposed ALNS-WDP
            cfg = ALNSConfig(
                time_limit=budget,
                window_size_k=min(8, inst.n),
                enable_window_dp=True,
                enable_adaptive_weights=True,
                seed=curr_seed,
            )
            alns_res = solve_alns_wdp(inst.p, inst.r, inst.s, inst.s0, config=cfg)
            gap_lb = ((alns_res.best_cmax - lb) / lb) * 100.0
            gap_opt = ((alns_res.best_cmax - exact_opt) / exact_opt * 100.0) if exact_opt else None
            _add_record({
                "instance": inst.name, "n": inst.n, "alpha": inst.alpha, "setup_type": setup_type,
                "family": inst.family, "method": "ALNS_WDP", "seed": curr_seed, "makespan": alns_res.best_cmax,
                "lb": lb, "opt": exact_opt, "gap_lb_pct": gap_lb, "gap_opt_pct": gap_opt,
                "runtime": alns_res.elapsed_time, "eval_count": alns_res.total_evals,
                "is_optimal": (alns_res.best_cmax == exact_opt if exact_opt else False)
            })
            
            # (e) CP-SAT Matheuristic (warm started with ALNS-WDP) for small/medium instances
            if inst.n <= 20 and seed_idx == 0:
                math_perm, math_cmax, math_time, math_meta = solve_cpsat_matheuristic(
                    inst.p, inst.r, inst.s, inst.s0, alns_res.best_perm, time_limit=budget
                )
                if math_cmax is not None:
                    m_gap_lb = ((math_cmax - lb) / lb) * 100.0
                    m_gap_opt = ((math_cmax - exact_opt) / exact_opt * 100.0) if exact_opt else None
                    _add_record({
                        "instance": inst.name, "n": inst.n, "alpha": inst.alpha, "setup_type": setup_type,
                        "family": inst.family, "method": "CP_SAT_Matheuristic", "seed": curr_seed,
                        "makespan": math_cmax, "lb": lb, "opt": exact_opt, "gap_lb_pct": m_gap_lb,
                        "gap_opt_pct": m_gap_opt, "runtime": math_time,
                        "eval_count": math_meta.get("branches", 0), "is_optimal": (math_meta["status"] == "OPTIMAL")
                    })
                    
    df = pd.DataFrame(records)
    csv_path = out_dir / "single_objective_benchmarks.csv"
    df.to_csv(csv_path, index=False)
    print(f"\n[Benchmarking Done] Saved {len(df)} strictly unique records to {csv_path}")
    return df


def run_convergence_experiments(
    instances: List[Instance],
    results_dir: str = "results",
) -> pd.DataFrame:
    """Records detailed makespan convergence over elapsed time for GA, SA, and ALNS-WDP."""
    out_dir = Path(results_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    records = []
    
    for inst in instances:
        budget = max(2.0, 0.04 * inst.n)
        seed = 1001
        
        # GA
        _, _, _, _, ga_hist = solve_ga(inst.p, inst.r, inst.s, inst.s0, pop_size=40, time_limit=budget, seed=seed)
        for t, val in ga_hist:
            records.append({"instance": inst.name, "n": inst.n, "method": "GA", "time": t, "makespan": val})
            
        # SA
        _, _, _, _, sa_hist = solve_sa(inst.p, inst.r, inst.s, inst.s0, time_limit=budget, seed=seed)
        for t, val in sa_hist:
            records.append({"instance": inst.name, "n": inst.n, "method": "SA", "time": t, "makespan": val})
            
        # ALNS-WDP
        cfg = ALNSConfig(time_limit=budget, window_size_k=min(8, inst.n), seed=seed)
        alns_res = solve_alns_wdp(inst.p, inst.r, inst.s, inst.s0, config=cfg)
        for t, val in alns_res.convergence_history:
            records.append({"instance": inst.name, "n": inst.n, "method": "ALNS_WDP", "time": t, "makespan": val})
            
    df = pd.DataFrame(records)
    csv_path = out_dir / "convergence_curves.csv"
    df.to_csv(csv_path, index=False)
    return df


def run_ablation_experiments(
    instances: List[Instance],
    results_dir: str = "results",
    num_seeds: int = 15,
) -> pd.DataFrame:
    """
    Executes ablation study across 5 variants:
    1. Full ALNS-WDP
    2. ALNS w/o Window-DP
    3. ALNS w/o Adaptive Bandit Weights
    4. Plain ALNS (No Window DP, No Adaptive Weights)
    5. Window-DP as Final Polish Only
    """
    out_dir = Path(results_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    records = []
    
    variants = [
        ("ALNS_WDP_Full", True, True, False),
        ("ALNS_No_WindowDP", False, True, False),
        ("ALNS_No_AdaptWeights", True, False, False),
        ("Plain_ALNS", False, False, False),
        ("WindowDP_FinalPolishOnly", False, True, True),
    ]
    
    for inst in instances:
        lb = compute_lower_bound(inst.p, inst.r, inst.s, inst.s0)
        budget = max(1.2, 0.03 * inst.n)
        
        for v_name, enable_dp, enable_adapt, final_only in variants:
            for s_idx in range(num_seeds):
                seed = 777 + s_idx * 13
                t_start = time.perf_counter()
                deadline = t_start + budget
                alns_time_limit = max(0.1, budget * 0.85) if final_only else budget
                cfg = ALNSConfig(
                    time_limit=alns_time_limit,
                    window_size_k=min(8, inst.n),
                    enable_window_dp=enable_dp,
                    enable_adaptive_weights=enable_adapt,
                    seed=seed,
                )
                res = solve_alns_wdp(inst.p, inst.r, inst.s, inst.s0, config=cfg)
                
                # If final_only: run sliding window sweep once on the best permutation within remaining budget
                if final_only and inst.n >= 8 and time.perf_counter() < deadline:
                    from src.alns.window_dp import sliding_window_dp_sweep
                    fin_perm, fin_cmax, _ = sliding_window_dp_sweep(
                        res.best_perm, min(8, inst.n), inst.p, inst.r, inst.s, inst.s0, deadline=deadline
                    )
                    best_c = fin_cmax
                else:
                    best_c = res.best_cmax
                    
                actual_elapsed = time.perf_counter() - t_start
                gap_lb = ((best_c - lb) / lb) * 100.0
                records.append({
                    "instance": inst.name, "n": inst.n, "alpha": inst.alpha,
                    "variant": v_name, "seed": seed, "makespan": best_c,
                    "lb": lb, "gap_lb_pct": gap_lb, "runtime": actual_elapsed,
                    "dp_improvements": res.window_dp_improvements,
                })
                
    df = pd.DataFrame(records)
    csv_path = out_dir / "ablation_results.csv"
    df.to_csv(csv_path, index=False)
    return df


def run_window_dp_design_study(
    instances: List[Instance],
    results_dir: str = "results",
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Studies window size k sensitivity (k in {4, 6, 8, 10, 12})
    and window placement strategy (sliding vs worst_setup vs random).
    """
    out_dir = Path(results_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    k_records = []
    strat_records = []
    
    k_values = [4, 6, 8, 10, 12]
    strategies = ["sliding", "worst_setup", "random"]
    
    for inst in instances:
        lb = compute_lower_bound(inst.p, inst.r, inst.s, inst.s0)
        budget = max(1.2, 0.03 * inst.n)
        
        # 1. k sensitivity
        for k in k_values:
            if k > inst.n:
                continue
            for s_idx in range(5):
                seed = 100 + s_idx * 11
                cfg = ALNSConfig(time_limit=budget, window_size_k=k, enable_window_dp=True, seed=seed)
                res = solve_alns_wdp(inst.p, inst.r, inst.s, inst.s0, config=cfg)
                gap_lb = ((res.best_cmax - lb) / lb) * 100.0
                k_records.append({
                    "instance": inst.name, "n": inst.n, "k": k, "seed": seed,
                    "makespan": res.best_cmax, "lb": lb, "gap_lb_pct": gap_lb,
                    "runtime": res.elapsed_time, "dp_improvements": res.window_dp_improvements
                })
                
        # 2. Placement strategy
        for strat in strategies:
            for s_idx in range(5):
                seed = 200 + s_idx * 13
                cfg = ALNSConfig(
                    time_limit=budget, window_size_k=min(8, inst.n),
                    dp_placement_strategy=strat, enable_window_dp=True, seed=seed
                )
                res = solve_alns_wdp(inst.p, inst.r, inst.s, inst.s0, config=cfg)
                gap_lb = ((res.best_cmax - lb) / lb) * 100.0
                strat_records.append({
                    "instance": inst.name, "n": inst.n, "strategy": strat, "seed": seed,
                    "makespan": res.best_cmax, "lb": lb, "gap_lb_pct": gap_lb,
                    "runtime": res.elapsed_time, "dp_improvements": res.window_dp_improvements
                })
                
    df_k = pd.DataFrame(k_records)
    df_strat = pd.DataFrame(strat_records)
    
    df_k.to_csv(out_dir / "sensitivity_k.csv", index=False)
    df_strat.to_csv(out_dir / "strategy_placement.csv", index=False)
    return df_k, df_strat


def run_biobjective_experiments(
    instances: List[Instance],
    num_seeds: int = 15,
    results_dir: str = "results",
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Executes true bi-objective benchmarking comparing NSGA-II vs ALNS-WDP
    using authentic scalarized sweeps across 11 discrete lambda weights in [0, 1].
    Evaluates both Hypervolume and Inverted Generational Distance (IGD).
    """
    out_dir = Path(results_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    front_records = []
    metric_records = []
    
    for inst in instances:
        print(f"\n[Bi-Objective] Evaluating {inst.name} (n={inst.n}, alpha={inst.alpha})...")
        
        # Reference normalization bounds
        P_sum = sum(inst.p)
        W_sum = sum(inst.w)
        norm_c = float(P_sum + 12 * inst.n)
        norm_t = float(W_sum * P_sum * 0.4)
        budget = max(1.5, 0.04 * inst.n)
        
        all_inst_solutions = []
        
        # 1. NSGA-II across multiple seeds
        nsga_runs = []
        for seed_idx in range(num_seeds):
            seed = 500 + seed_idx * 17
            perms, front, el, ev = solve_nsga2(
                inst.p, inst.r, inst.s, inst.s0, inst.d, inst.w,
                pop_size=50, time_limit=budget, seed=seed
            )
            nsga_runs.append((seed, front, el, ev))
            for pt in front:
                all_inst_solutions.append(pt)
                if seed_idx == 0:
                    front_records.append({
                        "instance": inst.name, "n": inst.n, "method": "NSGA-II",
                        "c_max": float(pt[0]), "twt": float(pt[1])
                    })
                    
        # 2. ALNS-WDP Scalarized Sweeps across seeds
        lambdas = np.linspace(0.0, 1.0, 11)
        alns_sweeps_by_seed = []
        
        for seed_idx in range(num_seeds):
            alns_front_pts = []
            t_start = time.perf_counter()
            lam_budget = budget / len(lambdas)
            seed_alns_evals = 0
            
            for lam in lambdas:
                sub_seed = 600 + seed_idx * 31 + int(lam * 100)
                cfg = ALNSConfig(
                    time_limit=lam_budget,
                    window_size_k=min(8, inst.n),
                    scalar_lambda=lam,
                    norm_cmax=norm_c,
                    norm_twt=norm_t,
                    seed=sub_seed,
                )
                res = solve_alns_wdp(
                    inst.p, inst.r, inst.s, inst.s0, d=inst.d, w=inst.w, config=cfg
                )
                seed_alns_evals += res.total_evals
                c_val, twt_val = compute_bi_objective(
                    res.best_perm, inst.p, inst.r, inst.s, inst.s0, inst.d, inst.w
                )
                alns_front_pts.append([c_val, twt_val])
                all_inst_solutions.append([c_val, twt_val])
                
                if seed_idx == 0:
                    front_records.append({
                        "instance": inst.name, "n": inst.n, "method": "ALNS-WDP (Scalarized)",
                        "c_max": float(c_val), "twt": float(twt_val)
                    })
                    
            alns_time_taken = time.perf_counter() - t_start
            alns_sweeps_by_seed.append((np.array(alns_front_pts), alns_time_taken, seed_alns_evals))
            
        # 3. Construct True Combined Non-Dominated Reference Set Z*
        all_pts = np.array(all_inst_solutions)
        # Filter non-dominated points
        is_efficient = np.ones(len(all_pts), dtype=bool)
        for i, c in enumerate(all_pts):
            if is_efficient[i]:
                # Keep points not dominated by c
                is_efficient[is_efficient] = np.any(all_pts[is_efficient] < c, axis=1) | np.all(all_pts[is_efficient] == c, axis=1)
                is_efficient[i] = True
        z_star = all_pts[is_efficient]
        
        # Common reference point for Hypervolume (1.3x max in z_star)
        ref_point = np.array([np.max(z_star[:, 0]) * 1.3, np.max(z_star[:, 1]) * 1.3 + 10.0])
        
        # 4. Compute Metrics per Seed
        for seed_idx in range(num_seeds):
            seed, nsga_front, el_n, ev_n = nsga_runs[seed_idx]
            hv_nsga = compute_hypervolume(nsga_front, ref_point)
            igd_nsga = compute_igd_metric(nsga_front, z_star)
            
            alns_front, alns_t, alns_ev = alns_sweeps_by_seed[seed_idx]
            hv_alns = compute_hypervolume(alns_front, ref_point)
            igd_alns = compute_igd_metric(alns_front, z_star)
            
            metric_records.append({
                "instance": inst.name, "n": inst.n, "seed": seed, "method": "NSGA-II",
                "hypervolume": hv_nsga, "igd": igd_nsga, "num_solutions": len(nsga_front),
                "runtime": el_n, "eval_count": ev_n
            })
            metric_records.append({
                "instance": inst.name, "n": inst.n, "seed": seed, "method": "ALNS-WDP (Scalarized)",
                "hypervolume": hv_alns, "igd": igd_alns, "num_solutions": len(alns_front),
                "runtime": alns_t, "eval_count": alns_ev
            })
            
    df_fronts = pd.DataFrame(front_records)
    df_metrics = pd.DataFrame(metric_records)
    
    df_fronts.to_csv(out_dir / "pareto_fronts.csv", index=False)
    df_metrics.to_csv(out_dir / "biobjective_metrics.csv", index=False)
    return df_fronts, df_metrics
