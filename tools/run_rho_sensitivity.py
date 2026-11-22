"""
Controlled Setup-Time Dominance Sensitivity Experiment
tools/run_rho_sensitivity.py

Investigates algorithm sensitivity to setup-time dominance ratio:
  rho_s = mean(s_{ij}) / mean(p_j)
by scaling setup matrices by beta in [0.1, 0.5, 1.0, 2.0, 5.0] across 4 representative instances:
  - n=30, asymmetric, alpha=0.3
  - n=30, symmetric,  alpha=0.3
  - n=50, asymmetric, alpha=0.3
  - n=50, symmetric,  alpha=0.3

Holding p_j, r_j, and initial depot setups s0_j strictly fixed.
Evaluates 4 algorithms under matched wall-clock budgets across 30 paired random seeds.
Outputs:
  - results/sensitivity_rho.csv
  - results/sensitivity_rho_summary.csv
  - results/sensitivity_rho_statistical_tests.csv
  - figures/fig8_sensitivity_rho.png
"""

import sys
import os
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple
from concurrent.futures import ProcessPoolExecutor, as_completed
import pandas as pd
import numpy as np
from scipy.stats import wilcoxon
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.alns.solver import solve_alns_wdp, ALNSConfig
from src.baselines.ga_sa import solve_ga, solve_sa
from src.baselines.local_search import multi_start_local_search
from src.evaluator import compute_makespan
from src.lower_bound import compute_lower_bound

SEEDS = [
    42, 59, 76, 93, 110, 127, 144, 161, 178, 195,
    212, 229, 246, 263, 280, 297, 314, 331, 348, 365,
    382, 399, 416, 433, 450, 467, 484, 501, 518, 535
]

BASE_INSTANCES = [
    {"name": "n30_a30_asym", "file": "data/n30_a30_asym_s4003.json", "n": 30, "alpha": 0.3, "topology": "asym", "budget": 0.90},
    {"name": "n30_a30_sym",  "file": "data/n30_a30_sym_s4004.json",  "n": 30, "alpha": 0.3, "topology": "sym",  "budget": 0.90},
    {"name": "n50_a30_asym", "file": "data/n50_a30_asym_s6003.json", "n": 50, "alpha": 0.3, "topology": "asym", "budget": 1.50},
    {"name": "n50_a30_sym",  "file": "data/n50_a30_sym_s6004.json",  "n": 50, "alpha": 0.3, "topology": "sym",  "budget": 1.50},
]

BETAS = [0.1, 0.5, 1.0, 2.0, 5.0]
METHODS = ["ALNS_WDP", "SA", "GA", "MultiStart_LS"]


def worker_solve(task_args: Dict[str, Any]) -> Dict[str, Any]:
    """Worker task executing a single run of one method on one scaled instance and seed."""
    method = task_args["method"]
    p = task_args["p"]
    r = task_args["r"]
    s = task_args["s"]
    s0 = task_args["s0"]
    budget = task_args["budget"]
    seed = task_args["seed"]
    lb = task_args["lb"]
    
    t0 = time.perf_counter()
    if method == "ALNS_WDP":
        cfg = ALNSConfig(time_limit=budget, window_size_k=8, seed=seed)
        res = solve_alns_wdp(p, r, s, s0, config=cfg)
        cmax = res.best_cmax
        elapsed = res.elapsed_time
        eval_count = res.total_evals
    elif method == "SA":
        perm, cmax, elapsed, eval_count, _ = solve_sa(p, r, s, s0, time_limit=budget, seed=seed)
    elif method == "GA":
        perm, cmax, elapsed, eval_count, _ = solve_ga(p, r, s, s0, pop_size=40, time_limit=budget, seed=seed)
    elif method == "MultiStart_LS":
        perm, cmax, elapsed, eval_count = multi_start_local_search(p, r, s, s0, time_limit=budget, seed=seed)
    else:
        raise ValueError(f"Unknown method {method}")
        
    gap_lb_pct = ((cmax - lb) / lb * 100.0) if lb > 0 else 0.0
    
    return {
        "instance": f"{task_args['base_name']}_b{task_args['beta']}",
        "base_instance": task_args["base_name"],
        "n": task_args["n"],
        "alpha": task_args["alpha"],
        "topology": task_args["topology"],
        "beta": task_args["beta"],
        "rho_s": task_args["rho_s"],
        "method": method,
        "seed": seed,
        "makespan": int(cmax),
        "lb": int(lb),
        "gap_lb_pct": float(round(gap_lb_pct, 4)),
        "runtime": float(round(elapsed, 4)),
        "eval_count": int(eval_count)
    }


def prepare_scaled_instances() -> List[Dict[str, Any]]:
    """Generates transformed instance specifications for each base instance and beta."""
    scaled_configs = []
    for base in BASE_INSTANCES:
        path = ROOT_DIR / base["file"]
        with open(path) as f:
            data = json.load(f)
        p = data["p"]
        r = data["r"]
        orig_s = np.array(data["s"])
        s0 = data["s0"]
        n = data["n"]
        
        p_arr = np.array(p)
        mask = ~np.eye(n, dtype=bool)
        p_mean = float(p_arr.mean())
        
        for beta in BETAS:
            s_scaled = np.round(orig_s * beta).astype(int)
            np.fill_diagonal(s_scaled, 0)
            s_list = s_scaled.tolist()
            
            s_mean = float(s_scaled[mask].mean())
            rho_s = float(round(s_mean / p_mean, 4))
            
            is_sym = bool(np.array_equal(s_scaled, s_scaled.T))
            expected_topology = base["topology"]
            if expected_topology == "sym" and not is_sym:
                raise ValueError(f"Symmetry broken in {base['name']} with beta {beta}")
            if expected_topology == "asym" and is_sym:
                raise ValueError(f"Asymmetry broken in {base['name']} with beta {beta}")
                
            lb = compute_lower_bound(p, r, s_list, s0)
            
            scaled_configs.append({
                "base_name": base["name"],
                "n": n,
                "alpha": base["alpha"],
                "topology": base["topology"],
                "beta": beta,
                "rho_s": rho_s,
                "p": p,
                "r": r,
                "s": s_list,
                "s0": s0,
                "lb": lb,
                "budget": base["budget"]
            })
    return scaled_configs


def run_experiment() -> pd.DataFrame:
    """Executes all 2,400 runs using ProcessPoolExecutor."""
    scaled_configs = prepare_scaled_instances()
    tasks = []
    for cfg in scaled_configs:
        for method in METHODS:
            for seed in SEEDS:
                task = dict(cfg)
                task["method"] = method
                task["seed"] = seed
                tasks.append(task)
                
    total_tasks = len(tasks)
    print(f"Total tasks to run: {total_tasks} across {len(scaled_configs)} configurations.")
    
    results = []
    start_time = time.time()
    workers = min(14, max(1, (os.cpu_count() or 4) - 2))
    print(f"Running on {workers} parallel worker processes...")
    
    with ProcessPoolExecutor(max_workers=workers) as executor:
        future_to_task = {executor.submit(worker_solve, t): t for t in tasks}
        completed = 0
        for future in as_completed(future_to_task):
            res = future.result()
            results.append(res)
            completed += 1
            if completed % 200 == 0 or completed == total_tasks:
                elapsed = time.time() - start_time
                print(f"  Progress: {completed}/{total_tasks} ({completed/total_tasks*100:.1f}%) in {elapsed:.1f}s")
                
    df = pd.DataFrame(results)
    # Sort for deterministic output
    df.sort_values(by=["base_instance", "beta", "method", "seed"], inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def compute_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Computes summary statistics (mean, std, median, IQR) for makespan, gap_lb_pct, and runtime."""
    records = []
    grouped = df.groupby(["base_instance", "n", "topology", "beta", "rho_s", "method"])
    for (base_name, n, topology, beta, rho_s, method), grp in grouped:
        mk = grp["makespan"]
        gap = grp["gap_lb_pct"]
        rt = grp["runtime"]
        ev = grp["eval_count"]
        
        q25_mk, q75_mk = np.percentile(mk, [25, 75])
        q25_gap, q75_gap = np.percentile(gap, [25, 75])
        
        records.append({
            "base_instance": base_name,
            "n": n,
            "topology": topology,
            "beta": beta,
            "rho_s": rho_s,
            "method": method,
            "n_runs": len(grp),
            "makespan_mean": round(float(mk.mean()), 2),
            "makespan_std": round(float(mk.std()), 2),
            "makespan_median": round(float(mk.median()), 2),
            "makespan_iqr": round(float(q75_mk - q25_mk), 2),
            "gap_lb_pct_mean": round(float(gap.mean()), 2),
            "gap_lb_pct_std": round(float(gap.std()), 2),
            "gap_lb_pct_median": round(float(gap.median()), 2),
            "gap_lb_pct_iqr": round(float(q75_gap - q25_gap), 2),
            "runtime_mean": round(float(rt.mean()), 3),
            "eval_count_mean": round(float(ev.mean()), 1)
        })
    df_summary = pd.DataFrame(records)
    return df_summary


def compute_statistical_tests(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes paired Wilcoxon signed-rank tests with step-down Holm-Bonferroni correction
    comparing ALNS_WDP vs {SA, GA, MultiStart_LS} across each configuration (base_instance, beta).
    """
    records = []
    configs = df[["base_instance", "n", "topology", "beta", "rho_s"]].drop_duplicates().values
    
    for base_name, n, topology, beta, rho_s in configs:
        sub = df[(df["base_instance"] == base_name) & (df["beta"] == beta)]
        alns_mk = sub[sub["method"] == "ALNS_WDP"].sort_values("seed")["makespan"].values
        
        raw_tests = []
        for other in ["SA", "GA", "MultiStart_LS"]:
            other_mk = sub[sub["method"] == other].sort_values("seed")["makespan"].values
            diff = alns_mk - other_mk
            wins = int(np.sum(diff < 0))
            ties = int(np.sum(diff == 0))
            losses = int(np.sum(diff > 0))
            
            # Paired Wilcoxon
            if np.all(diff == 0):
                p_val = 1.0
            else:
                try:
                    stat, p_val = wilcoxon(alns_mk, other_mk)
                except Exception:
                    p_val = 1.0
            
            # Effect size: Paired win-loss balance on matched seeds: (W - L) / (W + L)
            paired_balance = (wins - losses) / (wins + losses) if (wins + losses) > 0 else 0.0
            # Relative mean gap difference
            mean_diff_pct = float(np.mean(diff) / np.mean(other_mk) * 100.0)
            
            raw_tests.append({
                "base_instance": base_name,
                "n": n,
                "topology": topology,
                "beta": beta,
                "rho_s": rho_s,
                "comparison": f"ALNS_WDP_vs_{other}",
                "wins": wins,
                "ties": ties,
                "losses": losses,
                "mean_diff_pct": round(mean_diff_pct, 2),
                "paired_win_loss_balance": round(paired_balance, 3),
                "raw_p": p_val
            })
            
        # Apply Holm correction across the 3 competitor comparisons for this configuration
        # using cumulative maximum of ordered adjusted p-values
        raw_tests.sort(key=lambda x: x["raw_p"])
        m = len(raw_tests)
        running_max_exp = 0.0
        for i, t in enumerate(raw_tests):
            adj_p = min(1.0, t["raw_p"] * (m - i))
            running_max_exp = max(running_max_exp, adj_p)
            t["exploratory_holm_p"] = round(running_max_exp, 4)
            t["exploratory_significant_005"] = bool(running_max_exp < 0.05)
            records.append(t)
            
    df_stats = pd.DataFrame(records)
    
    # Apply global Holm correction across all 60 tests using cumulative maximum
    df_sorted = df_stats.sort_values("raw_p").reset_index(drop=True)
    m_global = len(df_sorted)
    running_max_global = 0.0
    global_adjusted = []
    for i, row in df_sorted.iterrows():
        adj_p = min(1.0, float(row["raw_p"] * (m_global - i)))
        running_max_global = max(running_max_global, adj_p)
        global_adjusted.append(round(running_max_global, 4))
    df_sorted["global_holm_p"] = global_adjusted
    df_sorted["global_significant_005"] = df_sorted["global_holm_p"] < 0.05
    
    # Retain holm_p and significant_005 aligned with global confirmatory standard
    df_sorted["holm_p"] = df_sorted["global_holm_p"]
    df_sorted["significant_005"] = df_sorted["global_significant_005"]
    
    df_sorted.sort_values(by=["base_instance", "beta", "comparison"], inplace=True)
    return df_sorted


def generate_plot(df_summary: pd.DataFrame, output_path: Path):
    """
    Generates a publication-grade 4-panel figure (fig8_sensitivity_rho.png):
    Subplots for each of the 4 base instances showing Gap to LB (%) vs rho_s for all 4 algorithms.
    """
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    fig, axes = plt.subplots(2, 2, figsize=(13, 9), sharey=False)
    
    instance_titles = {
        "n30_a30_asym": r"(a) $n=30$, Asymmetric ($\alpha=0.3$)",
        "n30_a30_sym":  r"(b) $n=30$, Symmetric ($\alpha=0.3$)",
        "n50_a30_asym": r"(c) $n=50$, Asymmetric ($\alpha=0.3$)",
        "n50_a30_sym":  r"(d) $n=50$, Symmetric ($\alpha=0.3$)",
    }
    
    color_map = {
        "ALNS_WDP": "#1f77b4",       # Blue
        "SA": "#ff7f0e",             # Orange
        "GA": "#2ca02c",             # Green
        "MultiStart_LS": "#d62728"   # Red
    }
    marker_map = {
        "ALNS_WDP": "o",
        "SA": "s",
        "GA": "^",
        "MultiStart_LS": "D"
    }
    
    coords = [
        ("n30_a30_asym", axes[0, 0]),
        ("n30_a30_sym",  axes[0, 1]),
        ("n50_a30_asym", axes[1, 0]),
        ("n50_a30_sym",  axes[1, 1]),
    ]
    
    for base_name, ax in coords:
        sub = df_summary[df_summary["base_instance"] == base_name]
        for method in METHODS:
            m_sub = sub[sub["method"] == method].sort_values("rho_s")
            x = m_sub["rho_s"]
            y = m_sub["gap_lb_pct_mean"]
            yerr = m_sub["gap_lb_pct_std"]
            ax.errorbar(
                x, y, yerr=yerr,
                label=method,
                color=color_map[method],
                marker=marker_map[method],
                linewidth=1.8,
                markersize=6,
                capsize=3,
                alpha=0.9
            )
        ax.set_title(instance_titles[base_name], fontsize=12, fontweight="bold", pad=8)
        ax.set_xlabel(r"Setup-Time Dominance Ratio ($\rho_s = \bar{s}/\bar{p}$)", fontsize=10)
        ax.set_ylabel("Gap to Lower Bound (%)", fontsize=10)
        ax.grid(True, linestyle="--", alpha=0.6)
        if base_name == "n30_a30_asym":
            ax.legend(frameon=True, fontsize=9, loc="upper right")
            
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"Saved figure: {output_path}")


def main():
    print("=" * 75)
    print("STARTING CONTROLLED SETUP-DOMINANCE EXPERIMENT (STAGE 1)")
    print("=" * 75)
    
    results_dir = ROOT_DIR / "results"
    figures_dir = ROOT_DIR / "figures"
    results_dir.mkdir(exist_ok=True)
    figures_dir.mkdir(exist_ok=True)
    
    out_csv = results_dir / "sensitivity_rho.csv"
    out_summary_csv = results_dir / "sensitivity_rho_summary.csv"
    out_stats_csv = results_dir / "sensitivity_rho_statistical_tests.csv"
    out_fig = figures_dir / "fig8_sensitivity_rho.png"
    
    if out_csv.exists() and len(pd.read_csv(out_csv)) == 2400:
        print(f"Loading existing raw results from {out_csv} (2400 rows)...")
        df = pd.read_csv(out_csv)
    else:
        df = run_experiment()
        df.to_csv(out_csv, index=False)
        print(f"Saved raw results: {out_csv} ({len(df)} rows)")
    
    df_summary = compute_summary(df)
    df_summary.to_csv(out_summary_csv, index=False)
    print(f"Saved summary: {out_summary_csv} ({len(df_summary)} rows)")
    
    df_stats = compute_statistical_tests(df)
    df_stats.to_csv(out_stats_csv, index=False)
    print(f"Saved statistical tests: {out_stats_csv} ({len(df_stats)} rows)")
    
    generate_plot(df_summary, out_fig)
    print("=" * 75)
    print("CONTROLLED SETUP-DOMINANCE EXPERIMENT COMPLETED SUCCESSFULLY!")
    print("=" * 75)


if __name__ == "__main__":
    main()

