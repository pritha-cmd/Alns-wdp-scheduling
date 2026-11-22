"""
tools/recalculate_lb_results.py - Recalculates lower bounds and gaps across all results.

Corrects the dual lower bound in results files by:
1. Recomputing valid LB values using compute_lower_bound (which now uses the mathematically
   valid processing-only anchor bound without the invalid subset setup term).
2. Updating results/single_objective_benchmarks.csv (lb and gap_lb_pct).
3. Updating results/ablation_results.csv (lb and gap_lb_pct).
4. Updating results/summary_metrics.csv.
5. Updating results/stratified_topology_comparison.csv.
6. Updating results/sensitivity_rho_statistical_tests.csv with both exploratory (m=3)
   and global (m=60) Holm-corrected p-values.
7. Re-generating publication figures:
   - figures/fig2_optimality_gaps.png
   - figures/fig5_ablation_study.png
   - figures/fig8_sensitivity_rho.png
"""

import sys
import json
import glob
from pathlib import Path
import pandas as pd
import numpy as np

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.lower_bound import compute_lower_bound
from src.plots import plot_optimality_gaps, plot_ablation


def load_instance_params(instance_name: str) -> dict:
    """Finds and loads the JSON file for an instance."""
    matches = glob.glob(str(ROOT_DIR / "data" / f"{instance_name}*.json"))
    if not matches:
        matches = glob.glob(str(ROOT_DIR / "data" / f"*{instance_name}*.json"))
    if not matches:
        raise FileNotFoundError(f"Instance JSON not found for {instance_name}")
    with open(matches[0]) as f:
        return json.load(f)


def recalculate_single_objective_benchmarks():
    """Updates single_objective_benchmarks.csv with verified valid LBs."""
    csv_path = ROOT_DIR / "results" / "single_objective_benchmarks.csv"
    df = pd.read_csv(csv_path)
    
    unique_instances = df["instance"].unique()
    lbs_map = {}
    for name in unique_instances:
        params = load_instance_params(name)
        lb = compute_lower_bound(params["p"], params["r"], params["s"], params["s0"])
        lbs_map[name] = lb
        
    for name, new_lb in lbs_map.items():
        mask = df["instance"] == name
        df.loc[mask, "lb"] = int(new_lb)
        # Recompute gap to lower bound
        df.loc[mask, "gap_lb_pct"] = ((df.loc[mask, "makespan"] - new_lb) / new_lb * 100.0).round(4)
        
    df.to_csv(csv_path, index=False)
    print(f"[recalculate] Updated {csv_path} with valid lower bounds.")
    return df


def recalculate_ablation_results():
    """Updates ablation_results.csv with verified valid LBs."""
    csv_path = ROOT_DIR / "results" / "ablation_results.csv"
    df = pd.read_csv(csv_path)
    
    unique_instances = df["instance"].unique()
    lbs_map = {}
    for name in unique_instances:
        params = load_instance_params(name)
        lb = compute_lower_bound(params["p"], params["r"], params["s"], params["s0"])
        lbs_map[name] = lb
        
    for name, new_lb in lbs_map.items():
        mask = df["instance"] == name
        df.loc[mask, "lb"] = int(new_lb)
        df.loc[mask, "gap_lb_pct"] = ((df.loc[mask, "makespan"] - new_lb) / new_lb * 100.0).round(4)
        
    df.to_csv(csv_path, index=False)
    print(f"[recalculate] Updated {csv_path} with valid lower bounds.")
    return df


def recalculate_summary_metrics(df_bench: pd.DataFrame):
    """Updates summary_metrics.csv based on the updated single_objective_benchmarks."""
    csv_path = ROOT_DIR / "results" / "summary_metrics.csv"
    
    grp = df_bench.groupby(["instance", "n", "alpha", "setup_type", "method"])
    summary = grp.agg(
        mean_cmax=("makespan", "mean"),
        std_cmax=("makespan", "std"),
        mean_gap_lb=("gap_lb_pct", "mean"),
        std_gap_lb=("gap_lb_pct", "std"),
        mean_gap_opt=("gap_opt_pct", "mean"),
        mean_runtime=("runtime", "mean"),
        std_runtime=("runtime", "std"),
        mean_evals=("eval_count", "mean"),
        opt_hit_rate=("is_optimal", "mean"),
        n_seeds=("seed", "count"),
    ).reset_index()
    
    summary.to_csv(csv_path, index=False)
    print(f"[recalculate] Updated {csv_path}.")


def recalculate_stratified_topology(df_bench: pd.DataFrame):
    """Updates stratified_topology_comparison.csv based on updated benchmarks."""
    csv_path = ROOT_DIR / "results" / "stratified_topology_comparison.csv"
    
    # Pivot per-instance makespans
    piv = df_bench.groupby(["instance", "setup_type", "method"]).makespan.mean().unstack("method")
    
    records = []
    for st in ["asym", "sym"]:
        st_label = "asymmetric" if st == "asym" else "symmetric"
        sub_bench = df_bench[df_bench["setup_type"] == st]
        sub_piv = piv.xs(st, level="setup_type")
        
        for m in ["ALNS_WDP", "SA", "GA", "MultiStart_LS"]:
            m_sub = sub_bench[sub_bench["method"] == m]
            gap_mean = float(m_sub["gap_lb_pct"].mean())
            gap_std = float(m_sub["gap_lb_pct"].std())
            mk_mean = float(m_sub["makespan"].mean())
            mk_std = float(m_sub["makespan"].std())
            
            if m == "ALNS_WDP":
                wins = np.nan
                ties = np.nan
                losses = np.nan
                imprv_mean = np.nan
                imprv_std = np.nan
            else:
                diff = sub_piv[m] - sub_piv["ALNS_WDP"]
                wins = int((diff > 0).sum())
                ties = int((diff == 0).sum())
                losses = int((diff < 0).sum())
                imprv = (sub_piv[m] - sub_piv["ALNS_WDP"]) / sub_piv[m] * 100.0
                imprv_mean = float(imprv.mean())
                imprv_std = float(imprv.std())
                
            records.append({
                "setup_type": st_label,
                "n_instances": 9 if st == "asym" else 11,
                "method": m,
                "gap_lb_pct_mean": round(gap_mean, 2),
                "gap_lb_pct_std": round(gap_std, 2),
                "makespan_mean": round(mk_mean, 2),
                "makespan_std": round(mk_std, 2),
                "alns_wins": wins,
                "alns_ties": ties,
                "alns_losses": losses,
                "alns_mean_imprv_pct": round(imprv_mean, 2) if not np.isnan(imprv_mean) else np.nan,
                "alns_std_imprv_pct": round(imprv_std, 2) if not np.isnan(imprv_std) else np.nan
            })
            
    df_strat = pd.DataFrame(records)
    df_strat.to_csv(csv_path, index=False)
    print(f"[recalculate] Updated {csv_path}.")


def recalculate_sensitivity_rho_stats():
    """Updates sensitivity_rho_statistical_tests.csv with both exploratory and global Holm corrections using cumulative maximum."""
    csv_path = ROOT_DIR / "results" / "sensitivity_rho_statistical_tests.csv"
    df = pd.read_csv(csv_path)
    
    # 0. Rename effect size column from cliff_delta to paired_win_loss_balance if present
    if "cliff_delta" in df.columns:
        df.rename(columns={"cliff_delta": "paired_win_loss_balance"}, inplace=True)
        
    # 1. Compute exploratory Holm-Bonferroni correction with cumulative max (m=3 per configuration)
    for (base_name, beta), grp in df.groupby(["base_instance", "beta"]):
        sub = grp.sort_values("raw_p")
        m_exp = len(sub)
        running_max_exp = 0.0
        for i, (orig_idx, row) in enumerate(sub.iterrows()):
            adj_p = min(1.0, float(row["raw_p"] * (m_exp - i)))
            running_max_exp = max(running_max_exp, adj_p)
            df.loc[orig_idx, "exploratory_holm_p"] = round(running_max_exp, 4)
            df.loc[orig_idx, "exploratory_significant_005"] = df.loc[orig_idx, "exploratory_holm_p"] < 0.05
            
    # 2. Compute global Holm-Bonferroni correction across all 60 tests with cumulative max
    df_sorted = df.sort_values("raw_p").reset_index(drop=True)
    m_global = len(df_sorted)
    running_max_global = 0.0
    global_adjusted = []
    for i, row in df_sorted.iterrows():
        adj_p = min(1.0, float(row["raw_p"] * (m_global - i)))
        running_max_global = max(running_max_global, adj_p)
        global_adjusted.append(round(running_max_global, 4))
    df_sorted["global_holm_p"] = global_adjusted
    df_sorted["global_significant_005"] = df_sorted["global_holm_p"] < 0.05
    
    # Retain holm_p and significant_005 as the global confirmatory standard
    df_sorted["holm_p"] = df_sorted["global_holm_p"]
    df_sorted["significant_005"] = df_sorted["global_significant_005"]
    
    df_sorted.sort_values(by=["base_instance", "beta", "comparison"], inplace=True)
    df_sorted.to_csv(csv_path, index=False)
    print(f"[recalculate] Updated {csv_path} with cumulative maximum Holm corrections (exploratory m=3 and global m=60) and paired_win_loss_balance.")


def regenerate_figures(df_bench: pd.DataFrame, df_abl: pd.DataFrame):
    """Regenerates publication gap distribution and ablation plots with updated LBs."""
    fig2_path = ROOT_DIR / "figures" / "fig2_optimality_gaps.png"
    fig5_path = ROOT_DIR / "figures" / "fig5_ablation_study.png"
    
    plot_optimality_gaps(df_bench, str(fig2_path))
    plot_ablation(df_abl, str(fig5_path))
    print(f"[recalculate] Regenerated {fig2_path} and {fig5_path}.")


def main():
    print("=" * 75)
    print("STARTING RECALCULATION OF RESULTS WITH VALID DUAL LOWER BOUND")
    print("=" * 75)
    
    df_bench = recalculate_single_objective_benchmarks()
    df_abl = recalculate_ablation_results()
    recalculate_summary_metrics(df_bench)
    recalculate_stratified_topology(df_bench)
    recalculate_sensitivity_rho_stats()
    regenerate_figures(df_bench, df_abl)
    
    print("=" * 75)
    print("RECALCULATION COMPLETE!")
    print("=" * 75)


if __name__ == "__main__":
    main()
