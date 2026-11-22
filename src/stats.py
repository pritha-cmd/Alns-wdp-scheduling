"""
Statistical Significance Analysis Suite:
- Paired Wilcoxon signed-rank tests on per-instance means
- Holm-Bonferroni multi-hypothesis p-value correction
- Friedman ranking test and Nemenyi critical difference
- Effect sizes: win/tie/loss, mean % improvement, 95% bootstrap confidence intervals
"""

from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon, friedmanchisquare


def compute_bootstrap_ci(
    data: np.ndarray,
    n_resamples: int = 2000,
    confidence_level: float = 0.95,
    seed: int = 42,
) -> Tuple[float, float]:
    """Computes non-parametric bootstrap confidence interval for the mean."""
    if len(data) == 0:
        return 0.0, 0.0
    rng = np.random.default_rng(seed)
    boot_means = [
        float(np.mean(rng.choice(data, size=len(data), replace=True)))
        for _ in range(n_resamples)
    ]
    alpha = (1.0 - confidence_level) / 2.0
    lower = float(np.percentile(boot_means, 100.0 * alpha))
    upper = float(np.percentile(boot_means, 100.0 * (1.0 - alpha)))
    return lower, upper


def holm_bonferroni_correction(p_values: List[float]) -> List[float]:
    """
    Applies step-down Holm-Bonferroni family-wise error rate correction.
    """
    m = len(p_values)
    if m == 0:
        return []
        
    # Sort indices by p-value
    indexed_p = sorted(enumerate(p_values), key=lambda x: x[1])
    adjusted = [0.0] * m
    running_max = 0.0
    
    for rank, (orig_idx, p_val) in enumerate(indexed_p):
        multiplier = m - rank
        adj_p = min(1.0, p_val * multiplier)
        running_max = max(running_max, adj_p)
        adjusted[orig_idx] = min(1.0, running_max)
        
    return adjusted


def compute_statistical_tests(
    df: pd.DataFrame,
    target_method: str = "ALNS_WDP",
    results_dir: str = "results",
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Computes rigorous statistical comparisons with Holm-corrected Wilcoxon tests,
    bootstrap confidence intervals, and Friedman average ranks.
    """
    out_dir = Path(results_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Summary Metrics by Method and Size n
    summary = df.groupby(["method", "n"]).agg(
        mean_makespan=("makespan", "mean"),
        std_makespan=("makespan", "std"),
        min_makespan=("makespan", "min"),
        mean_gap_lb=("gap_lb_pct", "mean"),
        std_gap_lb=("gap_lb_pct", "std"),
        mean_runtime=("runtime", "mean"),
        total_evals=("eval_count", "mean"),
    ).reset_index()
    summary.to_csv(out_dir / "summary_metrics.csv", index=False)
    
    # 2. Pairwise Wilcoxon Signed-Rank Tests (Evaluated per competitor on common instances)
    all_methods = [m for m in df["method"].unique() if m != target_method]
    wilcoxon_records = []
    raw_p_values = []
    
    for comp_m in all_methods:
        # Filter instances where both target_method and comp_m were evaluated
        sub_df = df[df["method"].isin([target_method, comp_m])]
        piv = sub_df.pivot_table(index="instance", columns="method", values="makespan", aggfunc="mean").dropna()
        
        n_common = len(piv)
        if n_common == 0:
            continue
            
        target_vals = piv[target_method].values
        comp_vals = piv[comp_m].values
        
        diff = comp_vals - target_vals  # Positive when target_method is better (lower makespan)
        pct_improvement = ((comp_vals - target_vals) / comp_vals) * 100.0
        
        wins = int(np.sum(diff > 1e-6))
        ties = int(np.sum(np.abs(diff) <= 1e-6))
        losses = int(np.sum(diff < -1e-6))
        mean_diff = float(np.mean(diff))
        mean_pct_imp = float(np.mean(pct_improvement))
        
        ci_lower, ci_upper = compute_bootstrap_ci(pct_improvement)
        
        non_zero = diff[np.abs(diff) > 1e-6]
        if len(non_zero) >= 5:
            try:
                stat, p_val = wilcoxon(comp_vals, target_vals, alternative="two-sided")
            except Exception:
                stat, p_val = np.nan, 1.0
        else:
            stat, p_val = np.nan, 1.0
            
        raw_p_values.append(p_val)
        wilcoxon_records.append({
            "comparison": f"{target_method} vs {comp_m}",
            "method": comp_m,
            "n_instances": n_common,
            "target_wins": wins,
            "ties": ties,
            "target_losses": losses,
            "mean_makespan_diff": mean_diff,
            "mean_pct_improvement": mean_pct_imp,
            "ci_95_lower": ci_lower,
            "ci_95_upper": ci_upper,
            "wilcoxon_stat": stat,
            "raw_p_value": p_val,
        })
        
    # Apply Holm-Bonferroni correction
    adj_p = holm_bonferroni_correction(raw_p_values)
    for idx, record in enumerate(wilcoxon_records):
        record["holm_p_value"] = adj_p[idx]
        record["significant_0_05"] = bool(adj_p[idx] < 0.05)
        
    df_wilcoxon = pd.DataFrame(wilcoxon_records).sort_values("mean_pct_improvement", ascending=False)
    df_wilcoxon.to_csv(out_dir / "statistical_tests.csv", index=False)
    
    # 3. Friedman Ranking across 4 Metaheuristics ONLY (ALNS_WDP, SA, GA, MultiStart_LS)
    metaheuristics = [target_method, "SA", "GA", "MultiStart_LS"]
    avail_meta = [m for m in metaheuristics if m in df["method"].unique()]
    
    if len(avail_meta) == 4:
        pivot_meta = df[df["method"].isin(avail_meta)].pivot_table(
            index="instance", columns="method", values="makespan", aggfunc="mean"
        ).dropna()[avail_meta]
        
        N = len(pivot_meta)
        k = len(avail_meta)  # 4
        df_deg = k - 1       # 3
        
        f_stat, f_pval = friedmanchisquare(*[pivot_meta[col].values for col in avail_meta])
        ranks = pivot_meta.rank(axis=1, ascending=True)
        avg_ranks = ranks.mean(axis=0)
        
        # Nemenyi critical difference calculation (alpha=0.05, q_0.05=2.569 for k=4)
        q_alpha = 2.569
        cd_val = float(q_alpha * np.sqrt((k * (k + 1)) / (6.0 * N)))
        
        friedman_records = []
        for col in avail_meta:
            friedman_records.append({
                "method": col,
                "average_rank": float(avg_ranks[col]),
                "friedman_stat": float(f_stat),
                "degrees_of_freedom": df_deg,
                "friedman_p_value": float(f_pval),
                "nemenyi_cd": cd_val,
                "n_blocks": N,
            })
        df_friedman = pd.DataFrame(friedman_records).sort_values("average_rank")
    else:
        df_friedman = pd.DataFrame()
        
    df_friedman.to_csv(out_dir / "friedman_ranks.csv", index=False)
    
    # 4. Metaheuristic-Specific Wilcoxon Comparisons (with and without global tie instances)
    meta_comps = ["GA", "SA", "MultiStart_LS"]
    sub_meta = df[df["method"].isin([target_method] + meta_comps)]
    piv_all = sub_meta.pivot_table(index="instance", columns="method", values="makespan", aggfunc="mean").dropna()
    
    # Identify tie instances where all 4 metaheuristics have identical makespan
    ptp = piv_all.max(axis=1) - piv_all.min(axis=1)
    non_tie_instances = piv_all.index[ptp > 1e-4].tolist()
    
    meta_records = []
    for comp_m in meta_comps:
        if comp_m not in piv_all.columns:
            continue
        # (a) Across all instances (N=20)
        diff_all = piv_all[comp_m].values - piv_all[target_method].values
        w_all = int(np.sum(diff_all > 1e-6))
        t_all = int(np.sum(np.abs(diff_all) <= 1e-6))
        l_all = int(np.sum(diff_all < -1e-6))
        nz_all = diff_all[np.abs(diff_all) > 1e-6]
        p_all = float(wilcoxon(piv_all[comp_m].values, piv_all[target_method].values).pvalue) if len(nz_all) > 0 else 1.0
        
        # (b) Excluding tie instances (N=17)
        piv_nt = piv_all.loc[non_tie_instances]
        diff_nt = piv_nt[comp_m].values - piv_nt[target_method].values
        w_nt = int(np.sum(diff_nt > 1e-6))
        t_nt = int(np.sum(np.abs(diff_nt) <= 1e-6))
        l_nt = int(np.sum(diff_nt < -1e-6))
        nz_nt = diff_nt[np.abs(diff_nt) > 1e-6]
        p_nt = float(wilcoxon(piv_nt[comp_m].values, piv_nt[target_method].values).pvalue) if len(nz_nt) > 0 else 1.0
        
        meta_records.append({
            "comparison": f"{target_method} vs {comp_m}",
            "method": comp_m,
            "raw_p_all": p_all,
            "wins_all": w_all, "ties_all": t_all, "losses_all": l_all,
            "n_all": len(piv_all),
            "raw_p_no_ties": p_nt,
            "wins_no_ties": w_nt, "ties_no_ties": t_nt, "losses_no_ties": l_nt,
            "n_no_ties": len(piv_nt),
        })
        
    df_meta_stat = pd.DataFrame(meta_records)
    # Apply Holm correction to metaheuristic comparisons
    df_meta_stat["holm_p_all"] = holm_bonferroni_correction(df_meta_stat["raw_p_all"].tolist())
    df_meta_stat["holm_p_no_ties"] = holm_bonferroni_correction(df_meta_stat["raw_p_no_ties"].tolist())
    df_meta_stat.to_csv(out_dir / "metaheuristic_statistical_tests.csv", index=False)
    
    return summary, df_wilcoxon, df_friedman


def compute_ablation_statistics(
    ablation_csv: str = "results/ablation_results.csv",
    results_dir: str = "results",
) -> pd.DataFrame:
    """
    Computes rigorous Holm-corrected statistical tests on the ablation study:
    Family (a): across all 8 instances x 4 competitors vs ALNS_WDP_Full
    Family (b): pre-specified hypothesis test on n=100 instances (4 comparisons)
    """
    out_dir = Path(results_dir)
    p_abl = Path(ablation_csv)
    if not p_abl.exists():
        return pd.DataFrame()
        
    df_abl = pd.read_csv(p_abl)
    full_var = "ALNS_WDP_Full"
    comp_vars = [v for v in df_abl["variant"].unique() if v != full_var]
    
    # 1. Per-instance Wilcoxon signed-rank across 15 seeds
    records = []
    for inst, g in df_abl.groupby("instance"):
        n_val = g["n"].iloc[0]
        f_vals = g[g["variant"] == full_var].sort_values("seed")["makespan"].values
        for v in comp_vars:
            o_vals = g[g["variant"] == v].sort_values("seed")["makespan"].values
            diff = o_vals - f_vals  # Positive when Full is better (lower makespan)
            wins = int(np.sum(diff > 1e-6))
            ties = int(np.sum(np.abs(diff) <= 1e-6))
            losses = int(np.sum(diff < -1e-6))
            mean_diff = float(np.mean(diff))
            
            non_zero = diff[np.abs(diff) > 1e-6]
            if len(non_zero) >= 3:
                try:
                    stat, p_val = wilcoxon(o_vals, f_vals, alternative="two-sided")
                except Exception:
                    stat, p_val = np.nan, 1.0
            else:
                stat, p_val = np.nan, 1.0
                
            records.append({
                "instance": inst,
                "n": n_val,
                "comparison": f"{full_var} vs {v}",
                "variant": v,
                "full_mean": float(np.mean(f_vals)),
                "variant_mean": float(np.mean(o_vals)),
                "mean_diff": mean_diff,
                "wins": wins,
                "ties": ties,
                "losses": losses,
                "wilcoxon_stat": stat,
                "raw_p_value": p_val,
                "is_n100": (n_val == 100),
            })
            
    df_abl_stat = pd.DataFrame(records)
    
    # Family (a): Holm correction over all 32 tests (8 instances x 4 variants)
    df_abl_stat["holm_p_family_all"] = holm_bonferroni_correction(df_abl_stat["raw_p_value"].tolist())
    
    # Family (b): Holm correction on pre-specified n=100 instances only
    n100_indices = df_abl_stat.index[df_abl_stat["is_n100"]].tolist()
    n100_raw_p = df_abl_stat.loc[n100_indices, "raw_p_value"].tolist()
    n100_adj_p = holm_bonferroni_correction(n100_raw_p)
    df_abl_stat["holm_p_n100_family"] = np.nan
    for idx, adj in zip(n100_indices, n100_adj_p):
        df_abl_stat.loc[idx, "holm_p_n100_family"] = adj
        
    df_abl_stat.to_csv(out_dir / "ablation_statistical_tests.csv", index=False)
    return df_abl_stat
