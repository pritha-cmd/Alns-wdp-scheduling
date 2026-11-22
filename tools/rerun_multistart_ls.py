"""
Re-runs MultiStart_LS across all 20 instances x 30 seeds using the full wall-clock budget.
Runs in parallel across CPU cores to complete in ~60 seconds.
Updates results/single_objective_benchmarks.csv in-place.
"""

import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from concurrent.futures import ProcessPoolExecutor
import pandas as pd
from src.instances import load_all_benchmark_instances, Instance
from src.baselines.local_search import multi_start_local_search


def run_single_ls_job(args):
    inst_dict, seed, budget = args
    p = inst_dict["p"]
    r = inst_dict["r"]
    s = inst_dict["s"]
    s0 = inst_dict["s0"]
    name = inst_dict["name"]
    n = inst_dict["n"]
    alpha = inst_dict["alpha"]
    setup_type = "sym" if inst_dict["is_symmetric"] else "asym"
    family = inst_dict["family"]
    
    perm, cmax, el, ev = multi_start_local_search(p, r, s, s0, time_limit=budget, seed=seed)
    return {
        "instance": name, "n": n, "alpha": alpha, "setup_type": setup_type,
        "family": family, "method": "MultiStart_LS", "seed": seed, "makespan": cmax,
        "runtime": el, "eval_count": ev
    }


def main():
    print("Loading benchmark instances...")
    df_bench = pd.read_csv("results/single_objective_benchmarks.csv")
    inst_names = df_bench["instance"].unique()
    
    all_insts = load_all_benchmark_instances(Path("data"))
    inst_map = {inst.name: inst for inst in all_insts}
    
    jobs = []
    seeds = [42 + i * 17 for i in range(30)]
    
    for name in inst_names:
        inst = inst_map[name]
        budget = max(0.75, 0.03 * inst.n)
        inst_dict = {
            "name": inst.name, "n": inst.n, "alpha": inst.alpha,
            "is_symmetric": inst.is_symmetric, "family": inst.family,
            "p": inst.p, "r": inst.r, "s": inst.s, "s0": inst.s0
        }
        for s in seeds:
            jobs.append((inst_dict, s, budget))
            
    print(f"Launching {len(jobs)} MultiStart_LS runs across 8 processes...")
    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(run_single_ls_job, jobs))
    t1 = time.perf_counter()
    print(f"Completed {len(results)} runs in {t1 - t0:.2f} seconds.")
    
    df_new_ls = pd.DataFrame(results)
    
    # Merge with dual lower bounds and exact optima from existing df_bench
    lb_map = df_bench.groupby("instance")["lb"].first().to_dict()
    opt_map = df_bench.groupby("instance")["opt"].first().to_dict()
    
    df_new_ls["lb"] = df_new_ls["instance"].map(lb_map)
    df_new_ls["opt"] = df_new_ls["instance"].map(opt_map)
    df_new_ls["gap_lb_pct"] = ((df_new_ls["makespan"] - df_new_ls["lb"]) / df_new_ls["lb"]) * 100.0
    df_new_ls["gap_opt_pct"] = df_new_ls.apply(
        lambda row: ((row["makespan"] - row["opt"]) / row["opt"] * 100.0) if pd.notna(row["opt"]) else None,
        axis=1
    )
    df_new_ls["is_optimal"] = df_new_ls.apply(
        lambda row: (row["makespan"] == row["opt"]) if pd.notna(row["opt"]) else False,
        axis=1
    )
    
    # Remove old MultiStart_LS records and append new ones
    df_other = df_bench[df_bench["method"] != "MultiStart_LS"]
    df_updated = pd.concat([df_other, df_new_ls], ignore_index=True)
    
    # Verify uniqueness
    dups = df_updated.duplicated(subset=["instance", "method", "seed"]).sum()
    assert dups == 0, f"Found {dups} duplicates after updating MultiStart_LS!"
    
    df_updated.to_csv("results/single_objective_benchmarks.csv", index=False)
    print("Successfully updated results/single_objective_benchmarks.csv!")
    
    # Print runtime parity check
    S = ["ALNS_WDP", "SA", "GA", "MultiStart_LS"]
    g = df_updated[df_updated.method.isin(S)].groupby(["instance", "method"]).runtime.mean().reset_index()
    R = g.pivot(index="instance", columns="method", values="runtime")
    print("\n=== Runtime Parity Check vs Fastest Method ===")
    print(R.div(R.min(axis=1), axis=0).mean().round(4))


if __name__ == "__main__":
    main()
