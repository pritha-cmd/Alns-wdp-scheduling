"""
Publication-Grade Visualizations for Single-Machine Scheduling:
Generates 300 DPI high-resolution figures for report and presentation slides.
"""

from pathlib import Path
from typing import Optional
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


# Set publication styling
sns.set_theme(style="whitegrid", palette="deep")
plt.rcParams.update({
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.titlesize": 13,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "figure.titlesize": 14,
    "font.family": "sans-serif",
})


def plot_runtime_scalability(df: pd.DataFrame, out_path: str = "figures/fig1_scalability_runtime.png") -> None:
    """Figure 1: Runtime vs Problem Size n across methods (log-log scale)."""
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
    
    key_methods = ["Exact_DP", "CP_SAT_EqualBudget", "GA", "SA", "ALNS_WDP"]
    sub_df = df[df["method"].isin(key_methods)].copy()
    
    mean_rt = sub_df.groupby(["method", "n"])["runtime"].mean().reset_index()
    
    palette = {
        "Exact_DP": "#8c564b",
        "CP_SAT_EqualBudget": "#2ca02c",
        "GA": "#1f77b4",
        "SA": "#ff7f0e",
        "ALNS_WDP": "#d62728",
    }
    markers = {
        "Exact_DP": "s",
        "CP_SAT_EqualBudget": "D",
        "GA": "o",
        "SA": "^",
        "ALNS_WDP": "*",
    }
    
    for m in key_methods:
        m_data = mean_rt[mean_rt["method"] == m]
        if not m_data.empty:
            label_clean = m.replace("_EqualBudget", "").replace("_", "-")
            ax.plot(
                m_data["n"], m_data["runtime"],
                label=label_clean,
                color=palette.get(m, "gray"),
                marker=markers.get(m, "o"),
                linewidth=2.0,
                markersize=8,
            )
            
    ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    ax.set_xlabel("Instance Size $n$ (log scale)")
    ax.set_ylabel("Runtime (seconds, log scale)")
    ax.set_title("Runtime Scalability Across Exact and Metaheuristic Solvers", fontweight="bold", pad=12)
    ax.legend(title="Algorithm", frameon=True)
    
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved: {out_path}")


def plot_optimality_gaps(df: pd.DataFrame, out_path: str = "figures/fig2_optimality_gaps.png") -> None:
    """Figure 2: Gap to Valid Dual Lower Bound (%) across problem sizes."""
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
    
    eval_methods = ["MultiStart_LS", "GA", "SA", "ALNS_WDP"]
    sub_df = df[df["method"].isin(eval_methods)].copy()
    sub_df["method"] = sub_df["method"].str.replace("_", "-")
    
    sns.boxplot(
        data=sub_df,
        x="n",
        y="gap_lb_pct",
        hue="method",
        palette=["#9467bd", "#1f77b4", "#ff7f0e", "#d62728"],
        ax=ax,
        showmeans=True,
        meanprops={"marker": "o", "markerfacecolor": "white", "markeredgecolor": "black"}
    )
    
    ax.set_xlabel("Instance Size $n$")
    ax.set_ylabel("Gap to Dual Lower Bound (%)")
    ax.set_title("Solution Quality: Percentage Gap to Valid Dual Lower Bound", fontweight="bold", pad=12)
    ax.legend(title="Algorithm", frameon=True)
    
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved: {out_path}")


def plot_convergence(df: pd.DataFrame, out_path: str = "figures/fig3_convergence.png") -> None:
    """Figure 3: Search Trajectory and Convergence over Elapsed Time."""
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
    
    sample_inst = df["instance"].iloc[0]
    sub_df = df[df["instance"] == sample_inst]
    
    palette = {"GA": "#1f77b4", "SA": "#ff7f0e", "ALNS_WDP": "#d62728"}
    
    for m in ["GA", "SA", "ALNS_WDP"]:
        m_data = sub_df[sub_df["method"] == m].sort_values("time")
        if not m_data.empty:
            ax.step(
                m_data["time"], m_data["makespan"],
                label=m.replace("_", "-"),
                color=palette.get(m, "gray"),
                linewidth=2.2,
                where="post",
            )
            
    ax.set_xlabel("Wall-Clock Time (seconds)")
    ax.set_ylabel("Current Best Makespan $C_{\\max}$")
    ax.set_title(f"Search Trajectory and Convergence: {sample_inst}", fontweight="bold", pad=12)
    ax.legend(title="Algorithm", frameon=True)
    
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved: {out_path}")


def plot_pareto_fronts(df: pd.DataFrame, out_path: str = "figures/fig4_pareto_fronts.png") -> None:
    """Figure 4: Bi-Objective Pareto Front Comparison: NSGA-II vs ALNS-WDP (Scalarized)."""
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 5.5), dpi=300)
    
    inst_name = df["instance"].iloc[0]
    sub_df = df[df["instance"] == inst_name]
    
    sns.scatterplot(
        data=sub_df,
        x="c_max",
        y="twt",
        hue="method",
        style="method",
        palette={"NSGA-II": "#1f77b4", "ALNS-WDP (Scalarized)": "#d62728"},
        markers={"NSGA-II": "o", "ALNS-WDP (Scalarized)": "s"},
        s=80,
        ax=ax,
    )
    
    ax.set_xlabel("Makespan $C_{\\max}$")
    ax.set_ylabel("Total Weighted Tardiness ($\\sum w_j T_j$)")
    ax.set_title(f"Bi-Objective Approximation Front: {inst_name}", fontweight="bold", pad=12)
    ax.legend(title="Method", frameon=True)
    
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved: {out_path}")


def plot_ablation(df: pd.DataFrame, out_path: str = "figures/fig5_ablation_study.png") -> None:
    """Figure 5: Ablation Analysis of ALNS-WDP Core Components."""
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(9, 5), dpi=300)
    
    name_map = {
        "ALNS_WDP_Full": "Full ALNS-WDP",
        "ALNS_No_WindowDP": "w/o Window-DP",
        "ALNS_No_AdaptWeights": "w/o Bandit Weights",
        "Plain_ALNS": "Plain ALNS",
        "WindowDP_FinalPolishOnly": "DP Final Only",
    }
    plot_df = df.copy()
    plot_df["variant_clean"] = plot_df["variant"].map(name_map)
    
    sns.barplot(
        data=plot_df,
        x="n",
        y="gap_lb_pct",
        hue="variant_clean",
        palette=["#2ca02c", "#1f77b4", "#ff7f0e", "#d62728", "#9467bd"],
        ax=ax,
        errorbar="se",
    )
    
    ax.set_xlabel("Instance Size $n$")
    ax.set_ylabel("Gap to Dual Lower Bound (%)")
    ax.set_title("Ablation Study: Contribution of Window-DP & Bandit Weights", fontweight="bold", pad=12)
    ax.legend(title="Variant", frameon=True)
    
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved: {out_path}")


def plot_sensitivity_k(df: pd.DataFrame, out_path: str = "figures/fig6_sensitivity_k.png") -> None:
    """Figure 6: Sensitivity of Solution Quality and Overhead to Window Size k."""
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    fig, ax1 = plt.subplots(figsize=(8, 5), dpi=300)
    
    grouped = df.groupby("k").agg(
        mean_gap=("gap_lb_pct", "mean"),
        mean_time=("runtime", "mean"),
        mean_imp=("dp_improvements", "mean"),
    ).reset_index()
    
    color1 = "#1f77b4"
    ax1.set_xlabel("Window DP Size $k$")
    ax1.set_ylabel("Mean Gap to LB (%)", color=color1)
    line1 = ax1.plot(grouped["k"], grouped["mean_gap"], color=color1, marker="o", linewidth=2.5, label="Gap to LB (%)")
    ax1.tick_params(axis="y", labelcolor=color1)
    
    ax2 = ax1.twinx()
    color2 = "#d62728"
    ax2.set_ylabel("DP Improvements per Run", color=color2)
    line2 = ax2.plot(grouped["k"], grouped["mean_imp"], color=color2, marker="s", linestyle="--", linewidth=2.0, label="DP Improvements")
    ax2.tick_params(axis="y", labelcolor=color2)
    
    plt.title("Effect of Window DP Size $k$ on Solution Polish and Improvements", fontweight="bold", pad=12)
    
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc="upper right")
    
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved: {out_path}")


def plot_sensitivity_alpha(df: pd.DataFrame, out_path: str = "figures/fig7_sensitivity_alpha.png") -> None:
    """Figure 7: Impact of Release Date Congestion Factor alpha."""
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
    
    sub_df = df[df["method"].isin(["GA", "SA", "ALNS_WDP"])].copy()
    sub_df["method"] = sub_df["method"].str.replace("_", "-")
    
    sns.barplot(
        data=sub_df,
        x="alpha",
        y="gap_lb_pct",
        hue="method",
        palette=["#1f77b4", "#ff7f0e", "#d62728"],
        ax=ax,
        errorbar="se",
    )
    
    ax.set_xlabel("Release Date Factor $\\alpha$ ($r_j \\in [0, \\alpha \\sum p]$)")
    ax.set_ylabel("Mean Gap to LB (%)")
    ax.set_title("Sensitivity of Heuristics to Release Date Dispersion $\\alpha$", fontweight="bold", pad=12)
    ax.legend(title="Algorithm", frameon=True)
    
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved: {out_path}")


def generate_all_plots() -> None:
    """Reads saved CSV results and regenerates all figures."""
    res_dir = Path("results")
    if (res_dir / "single_objective_benchmarks.csv").exists():
        df_bench = pd.read_csv(res_dir / "single_objective_benchmarks.csv")
        plot_runtime_scalability(df_bench)
        plot_optimality_gaps(df_bench)
        plot_sensitivity_alpha(df_bench)
        
    if (res_dir / "convergence_curves.csv").exists():
        df_conv = pd.read_csv(res_dir / "convergence_curves.csv")
        plot_convergence(df_conv)
        
    if (res_dir / "pareto_fronts.csv").exists():
        df_pareto = pd.read_csv(res_dir / "pareto_fronts.csv")
        plot_pareto_fronts(df_pareto)
        
    if (res_dir / "ablation_results.csv").exists():
        df_abl = pd.read_csv(res_dir / "ablation_results.csv")
        plot_ablation(df_abl)
        
    if (res_dir / "sensitivity_k.csv").exists():
        df_k = pd.read_csv(res_dir / "sensitivity_k.csv")
        plot_sensitivity_k(df_k)
