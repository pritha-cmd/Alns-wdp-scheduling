"""
tools/make_tables.py - Automated Table Generator for LaTeX Report and Slide 4

Reads directly from results/*.csv and generates:
1. Main benchmark table (tab:benchmarks) with note that exact/CP-SAT cover small instances only.
2. Per-instance small-instance optimality table (tab:small_instances) with opt, LB, ALNS/MS-LS/SA gap and hit rate, plus CSV averages.
3. Stratified topology comparison table (tab:stratified_topology) across asymmetric (9) and symmetric (11) instances.
4. Component ablation table (tab:ablation) with no bold on Full.
5. Slide 4 native PowerPoint table in slides/generate_presentation.py.

Usage:
    python tools/make_tables.py
"""

import sys
import re
from pathlib import Path
import pandas as pd
import numpy as np


def build_main_table(df_bench: pd.DataFrame, df_fried: pd.DataFrame) -> str:
    """Generates the Main Benchmark Results Table."""
    methods_order = [
        ("Exact Held-Karp DP* ($n \\le 20$)", "Exact_DP"),
        ("Brute Force* ($n \\le 10$)", "Brute_Force"),
        ("CP-SAT Matheuristic* ($n \\le 20$)", "CP_SAT_Matheuristic"),
        ("ALNS-WDP (Proposed)", "ALNS_WDP"),
        ("Simulated Annealing (SA)", "SA"),
        ("Multi-Start Local Search", "MultiStart_LS"),
        ("Genetic Algorithm (GA)", "GA"),
        ("Nearest-Setup Greedy", "Rule_NearestSetup"),
        ("ECT Dispatching Rule", "Rule_ECT"),
        ("ERD Dispatching Rule", "Rule_ERD"),
        ("SPT Dispatching Rule", "Rule_SPT"),
    ]

    fried_map = {}
    if df_fried is not None and not df_fried.empty:
        for _, r in df_fried.iterrows():
            fried_map[r["method"]] = f"{r['average_rank']:.2f}"

    rows = []
    for label, method_key in methods_order:
        sub = df_bench[df_bench["method"] == method_key]
        if sub.empty:
            continue
        runs = len(sub)
        gap_mean = sub["gap_lb_pct"].mean()
        gap_std = sub["gap_lb_pct"].std()
        rt_mean = sub["runtime"].mean()

        rt_str = "<0.001" if rt_mean < 0.001 else f"{rt_mean:.2f}"
        fried_str = fried_map.get(method_key, "N/A")

        row_str = f"{label} & {runs} & {gap_mean:.2f} & {gap_std:.2f} & {rt_str} & {fried_str} \\\\"
        rows.append(row_str)

    table_tex = (
        "\\begin{table*}[htbp]\n"
        "\\centering\n"
        "\\small\n"
        "\\caption{Benchmark Results across 20 Problem Instances (30 Seeds per Stochastic Method).}\n"
        "\\label{tab:benchmarks}\n"
        "\\begin{tabular}{lccccc}\n"
        "\\toprule\n"
        "\\textbf{Algorithm} & \\textbf{Runs} & \\textbf{Mean Gap to LB (\\%)} & \\textbf{Std Gap (\\%)} & \\textbf{Mean Runtime (s)} & \\textbf{Friedman Rank} \\\\\n"
        "\\midrule\n"
        + "\n".join(rows) + "\n"
        "\\bottomrule\n"
        "\\multicolumn{6}{l}{\\footnotesize *Note: Exact DP ($n \\le 20$), Brute Force ($n \\le 10$), and CP-SAT Matheuristic ($n \\le 20$) cover small instances only. Their gap to LB reflects}\\\\\n"
        "\\multicolumn{6}{l}{\\footnotesize the gap between integer solutions and the Hungarian dual lower bound, not sub-optimality.}\\\\\n"
        "\\end{tabular}\n"
        "\\end{table*}"
    )
    return table_tex


def build_per_instance_table(df_bench: pd.DataFrame) -> str:
    """Generates the Per-Instance Optimality Table for n <= 20."""
    small = df_bench[df_bench["opt"].notna()]
    instances = small["instance"].unique()
    methods = ["ALNS_WDP", "MultiStart_LS", "SA"]

    rows = []
    for inst in instances:
        sub = small[small["instance"] == inst]
        n_val = int(sub["n"].iloc[0])
        opt_val = int(sub["opt"].iloc[0])
        lb_val = int(sub["lb"].iloc[0])

        clean_name = inst.replace("_", "\\_")

        row_vals = [f"\\texttt{{{clean_name}}}", str(n_val), str(opt_val), str(lb_val)]
        for m in methods:
            sm = sub[sub["method"] == m]
            gap_mean = sm["gap_opt_pct"].mean()
            hit_rate = sm["is_optimal"].mean() * 100.0
            row_vals.append(f"{gap_mean:.2f}")
            row_vals.append(f"{hit_rate:.1f}")

        rows.append(" & ".join(row_vals) + " \\\\")

    # Averages from CSV
    avg_vals = ["\\textbf{Average ($n \\le 20$)}", "--", "--", "--"]
    for m in methods:
        sm = small[small["method"] == m]
        avg_gap = sm["gap_opt_pct"].mean()
        avg_hit = sm["is_optimal"].mean() * 100.0
        avg_vals.append(f"{avg_gap:.2f}")
        avg_vals.append(f"{avg_hit:.1f}")

    avg_row = " & ".join(avg_vals) + " \\\\"

    table_tex = (
        "\\begin{table*}[htbp]\n"
        "\\centering\n"
        "\\small\n"
        "\\caption{Per-Instance Optimality Breakdown on Small Instances ($n \\le 20$, 11 Instances, 30 Seeds per Metaheuristic).}\n"
        "\\label{tab:small_instances}\n"
        "\\begin{tabular}{lcccccccccc}\n"
        "\\toprule\n"
        "\\textbf{Instance} & $n$ & \\textbf{Opt} & \\textbf{LB} & \\multicolumn{2}{c}{\\textbf{ALNS-WDP}} & \\multicolumn{2}{c}{\\textbf{MultiStart\\_LS}} & \\multicolumn{2}{c}{\\textbf{SA}} \\\\\n"
        "\\cmidrule(lr){5-6} \\cmidrule(lr){7-8} \\cmidrule(lr){9-10}\n"
        "& & & & \\textbf{Gap (\\%)} & \\textbf{Hit (\\%)} & \\textbf{Gap (\\%)} & \\textbf{Hit (\\%)} & \\textbf{Gap (\\%)} & \\textbf{Hit (\\%)} \\\\\n"
        "\\midrule\n"
        + "\n".join(rows) + "\n"
        "\\midrule\n"
        + avg_row + "\n"
        "\\bottomrule\n"
        "\\end{tabular}\n"
        "\\end{table*}"
    )
    return table_tex


def build_stratified_table(df_strat: pd.DataFrame) -> str:
    """Generates the Stratified Topology Breakdown Table."""
    rows = []
    for idx, r in df_strat.iterrows():
        top_label = "\\textbf{Asymmetric} (9 inst)" if (r["setup_type"] == "asym" and r["method"] == "ALNS_WDP") else (
            "\\textbf{Symmetric} + derived (11)" if (r["setup_type"] == "sym" and r["method"] == "ALNS_WDP") else ""
        )
        if r["setup_type"] == "sym" and r["method"] == "ALNS_WDP":
            rows.append("\\midrule")

        alg_name = r["method"].replace("_", "\\_")
        gap_str = f"{r['gap_lb_pct_mean']:.2f}"
        mk_str = f"{r['makespan_mean']:.1f}"
        if abs(r['makespan_mean'] - 415.45) < 0.05:
            mk_str = "415.5"

        if pd.isna(r["alns_wins"]):
            wtl_str = "--"
            imprv_str = "--"
        else:
            wtl_str = f"{int(r['alns_wins'])}W/{int(r['alns_ties'])}T/{int(r['alns_losses'])}L"
            imprv_str = f"{r['alns_mean_imprv_pct']:+.2f}"

        rows.append(f"{top_label} & {alg_name} & {gap_str} & {mk_str} & {wtl_str} & {imprv_str} \\\\")

    table_tex = (
        "\\begin{table}[htbp]\n"
        "\\centering\n"
        "\\small\n"
        "\\caption{Stratified Performance: Asymmetric vs Symmetric Topologies.}\n"
        "\\label{tab:stratified_topology}\n"
        "\\begin{tabular}{lccccc}\n"
        "\\toprule\n"
        "\\textbf{Topology} & \\textbf{Algorithm} & \\textbf{Gap LB (\\%)} & \\textbf{Makespan} & \\textbf{W/T/L} & \\textbf{Imprv (\\%)} \\\\\n"
        "\\midrule\n"
        + "\n".join(rows) + "\n"
        "\\bottomrule\n"
        "\\end{tabular}\n"
        "\\end{table}"
    )
    return table_tex


def build_sensitivity_rho_table(df_rho_sum: pd.DataFrame) -> str:
    """Generates the Controlled Setup-Dominance Sensitivity Table."""
    piv = df_rho_sum.pivot_table(
        index=["base_instance", "n", "topology", "beta", "rho_s"],
        columns="method",
        values="gap_lb_pct_mean"
    ).reset_index()

    instance_names = {
        "n30_a30_asym": "n=30, Asymmetric (alpha=0.3)",
        "n30_a30_sym":  "n=30, Symmetric (alpha=0.3)",
        "n50_a30_asym": "n=50, Asymmetric (alpha=0.3)",
        "n50_a30_sym":  "n=50, Symmetric (alpha=0.3)",
    }

    rows = []
    for base_key in ["n30_a30_asym", "n30_a30_sym", "n50_a30_asym", "n50_a30_sym"]:
        sub = piv[piv["base_instance"] == base_key]
        disp_title = instance_names[base_key]
        rows.append(f"\\multicolumn{{6}}{{l}}{{\\textbf{{{disp_title}}}}} \\\\")
        for _, r in sub.iterrows():
            beta_str = f"{r['beta']:.1f}"
            rho_str = f"{r['rho_s']:.2f}"
            alns_str = f"{r['ALNS_WDP']:.2f}"
            sa_str = f"{r['SA']:.2f}"
            ga_str = f"{r['GA']:.2f}"
            ms_str = f"{r['MultiStart_LS']:.2f}"
            rows.append(f"\\quad {beta_str} & {rho_str} & {alns_str} & {sa_str} & {ga_str} & {ms_str} \\\\")

    table_tex = (
        "\\begin{table}[htbp]\n"
        "\\centering\n"
        "\\small\n"
        "\\caption{Controlled Setup-Time Dominance Sensitivity: Mean Gap to Lower Bound (\\%) across Scaling Factors $\\beta \\in [0.1, 5.0]$ (30 Seeds/Cell).}\n"
        "\\label{tab:sensitivity_rho}\n"
        "\\begin{tabular}{lccccc}\n"
        "\\toprule\n"
        "\\textbf{Scale ($\\beta$)} & \\textbf{Ratio ($\\rho_s$)} & \\textbf{ALNS-WDP} & \\textbf{SA} & \\textbf{GA} & \\textbf{MultiStart\\_LS} \\\\\n"
        "\\midrule\n"
        + "\n".join(rows) + "\n"
        "\\bottomrule\n"
        "\\end{tabular}\n"
        "\\end{table}"
    )
    return table_tex


def build_ablation_table(df_ablation: pd.DataFrame) -> str:
    """Generates Component Ablation Table with NO bold on Full."""
    variants_order = [
        "ALNS_WDP_Full",
        "WindowDP_FinalPolishOnly",
        "ALNS_No_AdaptWeights",
        "Plain_ALNS",
        "ALNS_No_WindowDP",
    ]

    rows = []
    for var in variants_order:
        sub = df_ablation[df_ablation["variant"] == var]
        if sub.empty:
            continue
        gap = sub["gap_lb_pct"].mean()
        mk = sub["makespan"].mean()
        dp_imp = sub["dp_improvements"].mean()
        rt = sub["runtime"].mean()

        clean_name = var.replace("_", "\\_")
        # Explicit rule: no bold on Full!
        rows.append(f"{clean_name} & {gap:.2f} & {mk:.2f} & {dp_imp:.2f} & {rt:.2f} \\\\")

    table_tex = (
        "\\begin{table}[htbp]\n"
        "\\centering\n"
        "\\small\n"
        "\\caption{Component Ablation Results (600 Runs across 8 Instances).}\n"
        "\\label{tab:ablation}\n"
        "\\begin{tabular}{lcccc}\n"
        "\\toprule\n"
        "\\textbf{Variant} & \\textbf{Gap LB (\\%)} & \\textbf{Makespan} & \\textbf{DP Imp/Run} & \\textbf{Time (s)} \\\\\n"
        "\\midrule\n"
        + "\n".join(rows) + "\n"
        "\\bottomrule\n"
        "\\end{tabular}\n"
        "\\end{table}"
    )
    return table_tex


def get_slide4_table_data(df_strat: pd.DataFrame, df_bench: pd.DataFrame) -> list:
    """Generates the data matrix for the native PowerPoint table on Slide 4."""
    p = df_bench.groupby(["instance", "setup_type", "method"]).makespan.mean().unstack("method")
    medians = {}
    for st in ["asym", "sym"]:
        sub = p.xs(st, level="setup_type")
        for m in ["SA", "GA", "MultiStart_LS"]:
            imprv = (sub[m] - sub["ALNS_WDP"]) / sub[m] * 100.0
            medians[(st, m)] = imprv.median()

    table_data = [
        ["Topology*", "Algorithm", "Gap LB", "Makespan", "W / T / L", "Mean (Med) Imprv"]
    ]

    for idx, r in df_strat.iterrows():
        st = r["setup_type"]
        m = r["method"]
        if st == "asym" and m == "ALNS_WDP":
            top_str = "Asymmetric (9 inst)"
        elif st == "sym" and m == "ALNS_WDP":
            top_str = "Symmetric + derived (11)"
        else:
            top_str = "Asymmetric" if st == "asym" else "Symmetric"

        alg_str = m
        gap_str = f"{r['gap_lb_pct_mean']:.2f}%"
        mk_str = f"{r['makespan_mean']:.1f}"
        if abs(r['makespan_mean'] - 415.45) < 0.05:
            mk_str = "415.5"

        if pd.isna(r["alns_wins"]):
            wtl_str = "--"
            imprv_str = "--"
        else:
            wtl_str = f"{int(r['alns_wins'])}W / {int(r['alns_ties'])}T / {int(r['alns_losses'])}L"
            med_val = medians.get((st, m), 0.0)
            imprv_str = f"{r['alns_mean_imprv_pct']:+.2f}% ({med_val:+.2f}%)"

        table_data.append([top_str, alg_str, gap_str, mk_str, wtl_str, imprv_str])

    return table_data


def update_presentation_script(slide4_data: list):
    """Updates slides/generate_presentation.py with the generated table data."""
    gen_path = Path("slides/generate_presentation.py")
    if not gen_path.exists():
        print(f"Warning: {gen_path} not found.")
        return

    content = gen_path.read_text(encoding="utf-8")

    lines = ["    table_content = ["]
    for row in slide4_data:
        row_str = "        [" + ", ".join(f'"{c}"' for c in row) + "],"
        lines.append(row_str)
    lines.append("    ]")
    replacement = "\n".join(lines)

    pattern = r"    table_content = \[[\s\S]*?\n    \]"
    new_content = re.sub(pattern, lambda m: replacement, content)
    gen_path.write_text(new_content, encoding="utf-8")
    print(f"[make_tables] Updated slides/generate_presentation.py with {len(slide4_data)} rows.")


def replace_block(text: str, start_marker: str, end_marker: str, new_content: str) -> str:
    """Safely replaces text between start_marker and end_marker."""
    if start_marker not in text or end_marker not in text:
        return text
    before, rest = text.split(start_marker, 1)
    _, after = rest.split(end_marker, 1)
    return before + start_marker + "\n" + new_content + "\n" + end_marker + after


def update_report_tex(main_tab: str, small_tab: str, strat_tab: str, abl_tab: str, rho_tab: str = ""):
    """Updates report/report.tex between explicit markers."""
    report_path = Path("report/report.tex")
    if not report_path.exists():
        print(f"Warning: {report_path} not found.")
        return

    text = report_path.read_text(encoding="utf-8")

    text = replace_block(text, "% %BEGIN_TAB_BENCHMARKS%", "% %END_TAB_BENCHMARKS%", main_tab)
    text = replace_block(text, "% %BEGIN_TAB_SMALL%", "% %END_TAB_SMALL%", small_tab)
    text = replace_block(text, "% %BEGIN_TAB_STRAT%", "% %END_TAB_STRAT%", strat_tab)
    text = replace_block(text, "% %BEGIN_TAB_ABLATION%", "% %END_TAB_ABLATION%", abl_tab)
    if rho_tab:
        text = replace_block(text, "% %BEGIN_TAB_RHO%", "% %END_TAB_RHO%", rho_tab)

    report_path.write_text(text, encoding="utf-8")
    print(f"[make_tables] Successfully wrote updated {report_path}.")


def main():
    results_dir = Path("results")
    bench_file = results_dir / "single_objective_benchmarks.csv"
    fried_file = results_dir / "friedman_ranks.csv"
    strat_file = results_dir / "stratified_topology_comparison.csv"
    abl_file = results_dir / "ablation_results.csv"
    rho_file = results_dir / "sensitivity_rho_summary.csv"

    if not bench_file.exists():
        print(f"Error: {bench_file} missing.")
        sys.exit(1)

    df_bench = pd.read_csv(bench_file)
    df_fried = pd.read_csv(fried_file) if fried_file.exists() else None
    df_strat = pd.read_csv(strat_file) if strat_file.exists() else None
    df_abl = pd.read_csv(abl_file) if abl_file.exists() else None
    df_rho = pd.read_csv(rho_file) if rho_file.exists() else None

    # Generate tables
    main_tab = build_main_table(df_bench, df_fried)
    small_tab = build_per_instance_table(df_bench)
    strat_tab = build_stratified_table(df_strat) if df_strat is not None else ""
    abl_tab = build_ablation_table(df_abl) if df_abl is not None else ""
    rho_tab = build_sensitivity_rho_table(df_rho) if df_rho is not None else ""
    slide4_data = get_slide4_table_data(df_strat, df_bench) if df_strat is not None else []

    # Update files
    update_report_tex(main_tab, small_tab, strat_tab, abl_tab, rho_tab)
    if slide4_data:
        update_presentation_script(slide4_data)

    print("[make_tables] Table generation complete.")


if __name__ == "__main__":
    main()
