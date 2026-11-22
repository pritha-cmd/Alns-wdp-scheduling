"""
Parallel Budget-Enforced Benchmark and Ablation Re-Runner:
tools/rerun_budget_enforced.py

Re-runs:
1. ALNS_WDP across all 20 benchmark instances x 30 seeds with strict deadline checks.
2. Ablation across 8 instances x 5 variants x 15 seeds (600 runs) with strict runtime control.
3. Bi-objective benchmark across 6 instances x 15 seeds with equal wall-clock budgets.
"""

import sys
import os
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple
import concurrent.futures
import pandas as pd
import numpy as np

# Ensure project root is in path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.instances import Instance, get_base_4job_instance, generate_derived_tsplib_instance
from src.alns.solver import solve_alns_wdp, ALNSConfig
from src.alns.window_dp import sliding_window_dp_sweep
from src.baselines.nsga2 import solve_nsga2, compute_hypervolume, compute_igd_metric
from src.evaluator import compute_bi_objective, compute_makespan
from src.lower_bound import compute_lower_bound


def load_target_instances() -> Dict[str, Instance]:
    """Loads all 20 benchmark instances using load_all_benchmark_instances."""
    from src.instances import load_all_benchmark_instances
    all_instances = load_all_benchmark_instances()
    inst_by_name = {inst.name: inst for inst in all_instances}
    
    df_existing = pd.read_csv(ROOT_DIR / "results" / "single_objective_benchmarks.csv")
    unique_names = df_existing["instance"].unique()
    
    result = {}
    for name in unique_names:
        if name in inst_by_name:
            result[name] = inst_by_name[name]
        else:
            print(f"Warning: instance {name} not found in load_all_benchmark_instances!")
            
    return result


def run_alns_single_seed(task: Dict[str, Any]) -> Dict[str, Any]:
    """Worker function for a single ALNS run."""
    inst = task["instance_obj"]
    seed = task["seed"]
    budget = task["budget"]
    lb = task["lb"]
    opt = task["opt"]
    
    cfg = ALNSConfig(
        time_limit=budget,
        window_size_k=min(8, inst.n),
        enable_window_dp=True,
        enable_adaptive_weights=True,
        seed=seed,
    )
    res = solve_alns_wdp(inst.p, inst.r, inst.s, inst.s0, config=cfg)
    
    gap_lb = ((res.best_cmax - lb) / lb) * 100.0
    gap_opt = ((res.best_cmax - opt) / opt * 100.0) if (opt is not None and not pd.isna(opt)) else None
    is_opt = (res.best_cmax == opt) if (opt is not None and not pd.isna(opt)) else False
    
    return {
        "instance": inst.name,
        "n": inst.n,
        "alpha": inst.alpha,
        "setup_type": "sym" if inst.is_symmetric else "asym",
        "family": inst.family,
        "method": "ALNS_WDP",
        "seed": seed,
        "makespan": res.best_cmax,
        "lb": lb,
        "opt": opt,
        "gap_lb_pct": gap_lb,
        "gap_opt_pct": gap_opt,
        "runtime": res.elapsed_time,
        "eval_count": res.total_evals,
        "is_optimal": is_opt,
    }


def run_ablation_single_run(task: Dict[str, Any]) -> Dict[str, Any]:
    """Worker function for an ablation run."""
    inst = task["instance_obj"]
    v_name = task["variant"]
    enable_dp = task["enable_dp"]
    enable_adapt = task["enable_adapt"]
    final_only = task["final_only"]
    seed = task["seed"]
    budget = task["budget"]
    lb = task["lb"]
    
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
    
    if final_only and inst.n >= 8 and (time.perf_counter() < deadline):
        fin_perm, fin_cmax, imp = sliding_window_dp_sweep(
            res.best_perm, min(8, inst.n), inst.p, inst.r, inst.s, inst.s0, deadline=deadline
        )
        best_c = fin_cmax
    else:
        best_c = res.best_cmax
        
    actual_elapsed = time.perf_counter() - t_start
    gap_lb = ((best_c - lb) / lb) * 100.0
    
    return {
        "instance": inst.name,
        "n": inst.n,
        "alpha": inst.alpha,
        "variant": v_name,
        "seed": seed,
        "makespan": best_c,
        "lb": lb,
        "gap_lb_pct": gap_lb,
        "runtime": actual_elapsed,
        "dp_improvements": res.window_dp_improvements,
    }


def run_biobjective_inst(task: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Worker function for bi-objective benchmark on one instance."""
    inst = task["instance_obj"]
    num_seeds = task["num_seeds"]
    budget = max(1.5, 0.04 * inst.n)
    
    P_sum = sum(inst.p)
    W_sum = sum(inst.w)
    norm_c = float(P_sum + 12 * inst.n)
    norm_t = float(W_sum * P_sum * 0.4)
    
    all_inst_solutions = []
    front_records = []
    metric_records = []
    
    # 1. NSGA-II across seeds with EQUAL budget
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
        
    # 3. Construct True Reference Set
    all_pts = np.array(all_inst_solutions)
    is_efficient = np.ones(len(all_pts), dtype=bool)
    for i, c in enumerate(all_pts):
        if is_efficient[i]:
            is_efficient[is_efficient] = np.any(all_pts[is_efficient] < c, axis=1) | np.all(all_pts[is_efficient] == c, axis=1)
            is_efficient[i] = True
    z_star = all_pts[is_efficient]
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
        
    return front_records, metric_records


def main():
    print("=" * 75)
    print("STARTING BUDGET-ENFORCED RE-RUN PIPELINE")
    print("=" * 75)
    
    inst_dict = load_target_instances()
    print(f"Loaded {len(inst_dict)} target instances successfully.")
    
    results_dir = ROOT_DIR / "results"
    
    # -------------------------------------------------------------
    # 1. RE-RUN ALNS-WDP FOR SINGLE-OBJECTIVE BENCHMARKS
    # -------------------------------------------------------------
    print("\n--- 1. Re-running ALNS-WDP (20 instances x 30 seeds = 600 runs) ---")
    df_existing = pd.read_csv(results_dir / "single_objective_benchmarks.csv")
    alns_tasks = []
    
    for inst_name, inst_obj in inst_dict.items():
        sub = df_existing[df_existing["instance"] == inst_name]
        lb = sub["lb"].iloc[0] if len(sub) > 0 else compute_lower_bound(inst_obj.p, inst_obj.r, inst_obj.s, inst_obj.s0)
        opt = sub["opt"].dropna().iloc[0] if (len(sub) > 0 and len(sub["opt"].dropna()) > 0) else None
        budget = max(0.75, 0.03 * inst_obj.n)
        
        for seed_idx in range(30):
            seed = 42 + seed_idx * 17
            alns_tasks.append({
                "instance_obj": inst_obj,
                "seed": seed,
                "budget": budget,
                "lb": lb,
                "opt": opt,
            })
            
    t0 = time.perf_counter()
    new_alns_records = []
    max_workers = min(16, os.cpu_count() or 4)
    print(f"Executing {len(alns_tasks)} ALNS-WDP runs across {max_workers} worker processes...")
    
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(run_alns_single_seed, task) for task in alns_tasks]
        for idx, fut in enumerate(concurrent.futures.as_completed(futures)):
            rec = fut.result()
            new_alns_records.append(rec)
            if (idx + 1) % 100 == 0 or (idx + 1) == len(alns_tasks):
                print(f"  [ALNS Progress] {idx + 1} / {len(alns_tasks)} completed ({time.perf_counter() - t0:.1f}s)")
                
    df_new_alns = pd.DataFrame(new_alns_records)
    print(f"ALNS-WDP re-run finished in {time.perf_counter() - t0:.1f}s.")
    print(f"New ALNS-WDP Mean Gap to LB: {df_new_alns['gap_lb_pct'].mean():.2f}%")
    print(f"New ALNS-WDP Mean Runtime: {df_new_alns['runtime'].mean():.2f}s")
    
    # Merge into single_objective_benchmarks.csv
    df_non_alns = df_existing[df_existing["method"] != "ALNS_WDP"]
    df_updated_bench = pd.concat([df_non_alns, df_new_alns], ignore_index=True)
    df_updated_bench.to_csv(results_dir / "single_objective_benchmarks.csv", index=False)
    print(f"Updated {results_dir / 'single_objective_benchmarks.csv'} ({len(df_updated_bench)} rows).")

    # -------------------------------------------------------------
    # 2. RE-RUN ABLATION STUDY
    # -------------------------------------------------------------
    print("\n--- 2. Re-running Ablation Study (8 instances x 5 variants x 15 seeds = 600 runs) ---")
    abl_inst_names = [
        "n10_a0_asym_s2000", "n10_a60_sym_s2007", "n20_a0_asym_s3000", "n20_a30_sym_s3004",
        "n50_a0_sym_s6001", "n50_a60_asym_s6006", "n100_a0_asym_s11000", "n100_a30_sym_s11004"
    ]
    variants = [
        ("ALNS_WDP_Full", True, True, False),
        ("ALNS_No_WindowDP", False, True, False),
        ("ALNS_No_AdaptWeights", True, False, False),
        ("Plain_ALNS", False, False, False),
        ("WindowDP_FinalPolishOnly", False, True, True),
    ]
    
    abl_tasks = []
    for name in abl_inst_names:
        inst_obj = inst_dict[name]
        lb = compute_lower_bound(inst_obj.p, inst_obj.r, inst_obj.s, inst_obj.s0)
        budget = max(1.2, 0.03 * inst_obj.n)
        
        for v_name, enable_dp, enable_adapt, final_only in variants:
            for s_idx in range(15):
                seed = 777 + s_idx * 13
                abl_tasks.append({
                    "instance_obj": inst_obj,
                    "variant": v_name,
                    "enable_dp": enable_dp,
                    "enable_adapt": enable_adapt,
                    "final_only": final_only,
                    "seed": seed,
                    "budget": budget,
                    "lb": lb,
                })
                
    t0_abl = time.perf_counter()
    new_abl_records = []
    print(f"Executing {len(abl_tasks)} ablation runs across {max_workers} worker processes...")
    
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(run_ablation_single_run, task) for task in abl_tasks]
        for idx, fut in enumerate(concurrent.futures.as_completed(futures)):
            rec = fut.result()
            new_abl_records.append(rec)
            if (idx + 1) % 100 == 0 or (idx + 1) == len(abl_tasks):
                print(f"  [Ablation Progress] {idx + 1} / {len(abl_tasks)} completed ({time.perf_counter() - t0_abl:.1f}s)")
                
    df_new_abl = pd.DataFrame(new_abl_records)
    df_new_abl.to_csv(results_dir / "ablation_results.csv", index=False)
    print(f"Ablation re-run finished in {time.perf_counter() - t0_abl:.1f}s ({len(df_new_abl)} rows).")

    # -------------------------------------------------------------
    # 3. RE-RUN BI-OBJECTIVE EXPERIMENTS
    # -------------------------------------------------------------
    print("\n--- 3. Re-running Bi-Objective Study (6 instances x 15 seeds with equal budget) ---")
    bio_names = [
        "n8_a0_sym_s1801", "n8_a30_asym_s1803", "n20_a0_asym_s3000",
        "n20_a30_sym_s3004", "n50_a0_sym_s6001", "n50_a60_asym_s6006"
    ]
    bio_tasks = [{"instance_obj": inst_dict[name], "num_seeds": 15} for name in bio_names]
    
    t0_bio = time.perf_counter()
    all_front_records = []
    all_metric_records = []
    
    with concurrent.futures.ProcessPoolExecutor(max_workers=min(6, os.cpu_count() or 2)) as executor:
        futures = [executor.submit(run_biobjective_inst, task) for task in bio_tasks]
        for fut in concurrent.futures.as_completed(futures):
            fr, mr = fut.result()
            all_front_records.extend(fr)
            all_metric_records.extend(mr)
            print(f"  [Bi-Objective] Instance finished ({time.perf_counter() - t0_bio:.1f}s)")
            
    df_fronts = pd.DataFrame(all_front_records)
    df_fronts.to_csv(results_dir / "pareto_fronts.csv", index=False)
    df_metrics = pd.DataFrame(all_metric_records)
    df_metrics.to_csv(results_dir / "biobjective_metrics.csv", index=False)
    print(f"Bi-objective re-run finished in {time.perf_counter() - t0_bio:.1f}s.")
    
    print("\n" + "=" * 75)
    print("ALL BUDGET-ENFORCED RE-RUNS COMPLETED SUCCESSFULLY!")
    print("=" * 75)


if __name__ == "__main__":
    main()
