"""
Automated Verification Script: tools/check_claims.py
Cross-examines empirical data in results/*.csv against all claims, numbers,
instance counts, gaps, and p-values cited in:
- docs/abstract.md
- report/report.tex
- report/report.pdf
- report/generate_pdf.py
- slides/generate_presentation.py
- slides/presentation.pptx
- docs/VIVA_QA.md
- docs/novelty.md
- docs/problem_analysis.md
- docs/window_dp_correctness.md

Exits with code 0 if all claims PASS, or code 1 if any claim FAILS.
"""

import sys
import re
import json
from pathlib import Path
import pandas as pd
import numpy as np
import pptx


def run_checks() -> bool:
    print("=" * 75)
    print("RUNNING AUTOMATED CLAIM VERIFICATION (tools/check_claims.py)")
    print("=" * 75)

    all_passed = True
    results_dir = Path("results")
    figures_dir = Path("figures")
    docs_dir = Path("docs")
    report_dir = Path("report")
    slides_dir = Path("slides")

    def log_check(name: str, passed: bool, detail: str = ""):
        nonlocal all_passed
        status = "[PASS]" if passed else "[FAIL]"
        if not passed:
            all_passed = False
        print(f"  {status} {name:<48} {detail}")

    # 1. Check Artifact Files Existence
    print("\n--- 1. File Artifacts Verification ---")
    required_files = [
        results_dir / "single_objective_benchmarks.csv",
        results_dir / "summary_metrics.csv",
        results_dir / "convergence_curves.csv",
        results_dir / "ablation_results.csv",
        results_dir / "sensitivity_k.csv",
        results_dir / "biobjective_metrics.csv",
        results_dir / "biobjective_statistical_tests.csv",
        results_dir / "stratified_topology_comparison.csv",
        results_dir / "statistical_tests.csv",
        results_dir / "metaheuristic_statistical_tests.csv",
        results_dir / "friedman_ranks.csv",
        results_dir / "ablation_statistical_tests.csv",
        results_dir / "run_manifest.json",
        results_dir / "sensitivity_rho.csv",
        results_dir / "sensitivity_rho_summary.csv",
        results_dir / "sensitivity_rho_statistical_tests.csv",
    ]
    for rf in required_files:
        exists = rf.exists() and rf.stat().st_size > 0
        log_check(f"File exists: {rf.name}", exists, f"({rf.stat().st_size if exists else 0} bytes)")

    required_figs = [
        figures_dir / "fig1_scalability_runtime.png",
        figures_dir / "fig2_optimality_gaps.png",
        figures_dir / "fig3_convergence.png",
        figures_dir / "fig4_pareto_fronts.png",
        figures_dir / "fig5_ablation_study.png",
        figures_dir / "fig6_sensitivity_k.png",
        figures_dir / "fig7_sensitivity_alpha.png",
        figures_dir / "fig8_sensitivity_rho.png",
    ]
    for rfig in required_figs:
        exists = rfig.exists() and rfig.stat().st_size > 1000
        log_check(f"Figure exists: {rfig.name}", exists, f"({rfig.stat().st_size if exists else 0} bytes)")

    required_docs = [
        docs_dir / "abstract.md",
        docs_dir / "problem_analysis.md",
        docs_dir / "novelty.md",
        docs_dir / "AUDIT.md",
        docs_dir / "VIVA_QA.md",
        docs_dir / "window_dp_correctness.md",
        docs_dir / "CHANGELOG.md",
        Path("README.md"),
    ]
    for rd in required_docs:
        exists = rd.exists() and rd.stat().st_size > 100
        log_check(f"Documentation exists: {rd.name}", exists, f"({rd.stat().st_size if exists else 0} bytes)")

    if not (results_dir / "single_objective_benchmarks.csv").exists():
        print("\nERROR: single_objective_benchmarks.csv not found! Aborting verification.")
        return False

    # 2. Check Data Integrity and Uniqueness
    print("\n--- 2. Benchmark CSV Data Integrity ---")
    df_bench = pd.read_csv(results_dir / "single_objective_benchmarks.csv")
    
    dup_bench = df_bench.duplicated(subset=["instance", "method", "seed"]).sum()
    log_check("Single-objective row uniqueness", dup_bench == 0, f"Found {dup_bench} duplicate rows")

    unique_instances = df_bench["instance"].unique()
    num_instances = len(unique_instances)
    log_check("Instance diversity count == 20", num_instances == 20, f"{num_instances} instances loaded")

    # Check setup diversity (both sym and asym)
    setup_types = df_bench["setup_type"].unique()
    has_both_setups = ("sym" in setup_types) and ("asym" in setup_types)
    log_check("Setup topology diversity", has_both_setups, f"Topologies: {list(setup_types)}")

    # Check alpha diversity (all 0.0, 0.3, 0.6)
    alphas = df_bench["alpha"].round(1).unique()
    has_all_alphas = all(a in alphas for a in [0.0, 0.3, 0.6])
    log_check("Release date alpha diversity (0, 0.3, 0.6)", has_all_alphas, f"Alphas: {list(alphas)}")

    # Check stochastic seeds count (30 seeds per stochastic method)
    stoch_methods = ["ALNS_WDP", "GA", "SA", "MultiStart_LS"]
    for sm in stoch_methods:
        sm_df = df_bench[df_bench["method"] == sm]
        seeds_per_inst = sm_df.groupby("instance")["seed"].nunique()
        min_seeds = seeds_per_inst.min() if len(seeds_per_inst) > 0 else 0
        log_check(f"Seed count for {sm} == 30", min_seeds == 30, f"Min seeds/instance: {min_seeds}")

    # Check ablation results integrity
    df_abl = pd.read_csv(results_dir / "ablation_results.csv")
    dup_abl = df_abl.duplicated(subset=["instance", "variant", "seed"]).sum()
    log_check("Ablation row uniqueness", dup_abl == 0, f"Found {dup_abl} duplicates across {len(df_abl)} rows")
    log_check("Ablation row count == 600", len(df_abl) == 600, f"Rows: {len(df_abl)}")

    valid_variants = {
        "ALNS_WDP_Full", "ALNS_No_WindowDP", "ALNS_No_AdaptWeights",
        "Plain_ALNS", "WindowDP_FinalPolishOnly"
    }
    actual_variants = set(df_abl["variant"].unique())
    log_check("Ablation variants match exact 5 valid configurations",
              actual_variants == valid_variants, f"Variants: {actual_variants}")

    # Check ablation runtime overhead vs FinalPolishOnly
    abl_rt = df_abl.groupby(["instance", "variant"])["runtime"].mean().unstack()
    abl_ratios = abl_rt.div(abl_rt["WindowDP_FinalPolishOnly"], axis=0)
    max_abl_ratio = abl_ratios.max().max()
    mean_abl_ratio = abl_ratios[["ALNS_WDP_Full", "ALNS_No_WindowDP", "ALNS_No_AdaptWeights", "Plain_ALNS"]].mean().mean()
    log_check("Ablation max runtime ratio <= 1.15x FinalPolishOnly", max_abl_ratio <= 1.15,
              f"Max ratio: {max_abl_ratio:.3f}x")
    log_check("Ablation average runtime ratio ~ 1.097x", abs(mean_abl_ratio - 1.097) < 0.02,
              f"Mean ratio: {mean_abl_ratio:.3f}x")

    # Check stratified topology comparison integrity
    strat_path = results_dir / "stratified_topology_comparison.csv"
    if strat_path.exists():
        df_strat = pd.read_csv(strat_path)
        log_check("Stratified comparison has 8 rows (4 methods x 2 topologies)", len(df_strat) == 8,
                  f"Found {len(df_strat)} rows")
        asym_alns = df_strat[(df_strat["setup_type"] == "asymmetric") & (df_strat["method"] == "ALNS_WDP")]
        sym_alns = df_strat[(df_strat["setup_type"] == "symmetric") & (df_strat["method"] == "ALNS_WDP")]
        if len(asym_alns) > 0 and len(sym_alns) > 0:
            asym_gap = asym_alns["gap_lb_pct_mean"].values[0]
            sym_gap = sym_alns["gap_lb_pct_mean"].values[0]
            log_check("Stratified asymmetric ALNS-WDP gap ~ 4.38%", abs(asym_gap - 4.38) < 0.05,
                      f"Found: {asym_gap:.2f}%")
            log_check("Stratified symmetric ALNS-WDP gap ~ 6.37%", abs(sym_gap - 6.37) < 0.05,
                      f"Found: {sym_gap:.2f}%")

    # Check bi-objective statistical tests integrity
    bio_stat_path = results_dir / "biobjective_statistical_tests.csv"
    if bio_stat_path.exists():
        df_bio_stat = pd.read_csv(bio_stat_path)
        log_check("Bi-objective statistical tests has 12 rows (6 inst x 2 metrics)", len(df_bio_stat) == 12,
                  f"Found {len(df_bio_stat)} rows")
        # Check n20_a30_sym IGD is significant
        n20_igd = df_bio_stat[(df_bio_stat["instance"].str.contains("n20_a30_sym")) & (df_bio_stat["metric"] == "IGD")]
        if len(n20_igd) > 0:
            holm_p = n20_igd["holm_p"].values[0]
            log_check("Bi-objective n20_a30_sym IGD significant (Holm p=0.0018)", abs(holm_p - 0.00183) < 0.0005,
                      f"Found: {holm_p:.4f}")

    # Check controlled setup dominance sensitivity data integrity
    rho_path = results_dir / "sensitivity_rho.csv"
    if rho_path.exists():
        df_rho = pd.read_csv(rho_path)
        log_check("Setup dominance sensitivity rows == 2400", len(df_rho) == 2400, f"Found {len(df_rho)} rows")
        dup_rho = df_rho.duplicated(subset=["instance", "method", "seed"]).sum()
        log_check("Setup dominance sensitivity row uniqueness", dup_rho == 0, f"Found {dup_rho} duplicate rows")
        base_insts = df_rho["base_instance"].nunique()
        log_check("Setup dominance base instances == 4", base_insts == 4, f"Found {base_insts} base instances")
        betas = df_rho["beta"].nunique()
        log_check("Setup dominance beta levels == 5", betas == 5, f"Found {betas} beta levels")
        rho_seeds = df_rho.groupby(["base_instance", "beta", "method"])["seed"].nunique().min()
        log_check("Setup dominance min seeds per cell == 30", rho_seeds == 30, f"Min seeds: {rho_seeds}")

        # Check MultiStart-LS timeout overrun (~6.6% overrun due to finishing active descent)
        ms_n30_rt = df_rho[(df_rho["n"] == 30) & (df_rho["method"] == "MultiStart_LS")]["runtime"].mean()
        ms_n50_rt = df_rho[(df_rho["n"] == 50) & (df_rho["method"] == "MultiStart_LS")]["runtime"].mean()
        log_check("MultiStart_LS runtime n=30 overrun ~6.6% (0.96s vs 0.90s)", abs(ms_n30_rt - 0.96) < 0.03,
                  f"Found: {ms_n30_rt:.3f}s")
        log_check("MultiStart_LS runtime n=50 overrun ~6.6% (1.60s vs 1.50s)", abs(ms_n50_rt - 1.60) < 0.03,
                  f"Found: {ms_n50_rt:.3f}s")

    rho_sum_path = results_dir / "sensitivity_rho_summary.csv"
    if rho_sum_path.exists():
        df_rho_sum = pd.read_csv(rho_sum_path)
        log_check("Setup dominance summary rows == 80", len(df_rho_sum) == 80, f"Found {len(df_rho_sum)} rows")
        min_rho = df_rho_sum["rho_s"].min()
        max_rho = df_rho_sum["rho_s"].max()
        log_check("Setup ratio rho_s spans [0.06, 4.30]", (min_rho < 0.08) and (max_rho > 4.0),
                  f"Range: [{min_rho:.4f}, {max_rho:.4f}]")

    rho_stat_path = results_dir / "sensitivity_rho_statistical_tests.csv"
    if rho_stat_path.exists():
        df_rho_stat = pd.read_csv(rho_stat_path)
        log_check("Setup dominance statistical tests == 60", len(df_rho_stat) == 60, f"Found {len(df_rho_stat)} rows")
        has_dual_families = ("exploratory_holm_p" in df_rho_stat.columns) and ("global_holm_p" in df_rho_stat.columns)
        log_check("Setup dominance has exploratory and global Holm p-values", has_dual_families)
        
        # Check monotonicity of exploratory_holm_p
        exp_monotonic = True
        for (b, beta), grp in df_rho_stat.groupby(["base_instance", "beta"]):
            sub_s = grp.sort_values("raw_p")
            p_list = sub_s["exploratory_holm_p"].tolist()
            if not all(x <= y for x, y in zip(p_list, p_list[1:])):
                exp_monotonic = False
                break
        log_check("Exploratory Holm p-values monotonically non-decreasing (cummax)", exp_monotonic)

        # Check monotonicity of global_holm_p
        sub_g = df_rho_stat.sort_values("raw_p")
        p_g_list = sub_g["global_holm_p"].tolist()
        global_monotonic = all(x <= y for x, y in zip(p_g_list, p_g_list[1:]))
        log_check("Global Holm p-values monotonically non-decreasing (cummax)", global_monotonic)

        # Check effect size column
        has_pwlb = ("paired_win_loss_balance" in df_rho_stat.columns) and df_rho_stat["paired_win_loss_balance"].between(-1.0, 1.0).all()
        log_check("Effect size paired_win_loss_balance in [-1.0, 1.0]", has_pwlb)

        # Verify n30_a30_sym beta=1.0 MS-LS and SA wins against ALNS-WDP
        n30_b1_ms = df_rho_stat[(df_rho_stat["base_instance"] == "n30_a30_sym") & 
                                (df_rho_stat["beta"] == 1.0) & 
                                (df_rho_stat["comparison"] == "ALNS_WDP_vs_MultiStart_LS")]
        if len(n30_b1_ms) > 0:
            ms_wins = n30_b1_ms["losses"].values[0]
            log_check("n30_a30_sym beta=1.0 MultiStart_LS wins 28/30 vs ALNS", ms_wins == 28, f"Wins: {ms_wins}")

        # Verify n50_a30_sym beta=2.0 SA comparison: raw p = 0.0300, exploratory Holm p = 0.0435, global Holm p = 0.3295 (non-significant)
        n50_b2_sa = df_rho_stat[(df_rho_stat["base_instance"] == "n50_a30_sym") & 
                                (df_rho_stat["beta"] == 2.0) & 
                                (df_rho_stat["comparison"] == "ALNS_WDP_vs_SA")]
        if len(n50_b2_sa) > 0:
            sa_raw_p = n50_b2_sa["raw_p"].values[0]
            sa_exp_p = n50_b2_sa["exploratory_holm_p"].values[0]
            sa_global_p = n50_b2_sa["global_holm_p"].values[0]
            log_check("n50_a30_sym beta=2.0 SA raw p = 0.0300", abs(sa_raw_p - 0.0300) < 0.005, f"Found: {sa_raw_p:.4f}")
            log_check("n50_a30_sym beta=2.0 SA exploratory Holm p = 0.0435", abs(sa_exp_p - 0.0435) < 0.005, f"Found: {sa_exp_p:.4f}")
            log_check("n50_a30_sym beta=2.0 SA global Holm p = 0.3295 (non-sig)", abs(sa_global_p - 0.3295) < 0.005, f"Found: {sa_global_p:.4f}")

    # 3. Ground Truth Numerical Metrics
    print("\n--- 3. Ground Truth Metrics Calculation ---")
    alns_df = df_bench[df_bench["method"] == "ALNS_WDP"]
    alns_mean_gap_lb = alns_df["gap_lb_pct"].mean()
    alns_std_gap_lb = alns_df["gap_lb_pct"].std()
    alns_mean_runtime = alns_df["runtime"].mean()

    # Opt gap on small instances (n <= 20 with exact opt)
    alns_small_df = alns_df[alns_df["n"] <= 20].dropna(subset=["gap_opt_pct"])
    alns_mean_gap_opt = alns_small_df["gap_opt_pct"].mean() if len(alns_small_df) > 0 else 0.0

    print(f"  Ground Truth: ALNS_WDP Mean Gap to LB = {alns_mean_gap_lb:.2f}% (+/- {alns_std_gap_lb:.2f}%)")
    print(f"  Ground Truth: ALNS_WDP Mean Gap to Opt (n<=20) = {alns_mean_gap_opt:.2f}%")
    print(f"  Ground Truth: ALNS_WDP Mean Runtime = {alns_mean_runtime:.2f} s")

    # Check competitors
    comp_metrics = {}
    for comp in ["SA", "GA", "MultiStart_LS"]:
        c_df = df_bench[df_bench["method"] == comp]
        if len(c_df) > 0:
            comp_metrics[comp] = {
                "gap_lb": c_df["gap_lb_pct"].mean(),
                "runtime": c_df["runtime"].mean(),
            }
            print(f"  Ground Truth: {comp} Mean Gap to LB = {comp_metrics[comp]['gap_lb']:.2f}%")

    # Check statistical tests
    df_stat = pd.read_csv(results_dir / "metaheuristic_statistical_tests.csv")
    print(f"  Ground Truth: Metaheuristic Statistical Tests ({len(df_stat)} comparisons)")
    for _, r in df_stat.iterrows():
        print(f"    - vs {r['method']:<15}: Holm p = {r['holm_p_all']:.4e} (all), {r['holm_p_no_ties']:.4e} (no ties)")

    # 4. Cross-Verification with docs/abstract.md
    print("\n--- 4. Cross-Verification with docs/abstract.md ---")
    abstract_path = Path("docs/abstract.md")
    if abstract_path.exists():
        abs_text = abstract_path.read_text(encoding="utf-8")

        inst_match = re.search(r"(\d+)\s+benchmark instances", abs_text)
        if inst_match:
            claimed_n = int(inst_match.group(1))
            log_check("Abstract instance count matches CSV (20)", claimed_n == num_instances,
                      f"Claimed: {claimed_n}, Actual: {num_instances}")
        else:
            log_check("Abstract instance count pattern found", False, "Pattern not matched")

        seed_match = re.search(r"(\d+)\s+(?:independent stochastic\s+)?seeds", abs_text)
        if seed_match:
            claimed_seeds = int(seed_match.group(1))
            log_check("Abstract seeds count matches (30)", claimed_seeds == 30,
                      f"Claimed: {claimed_seeds}")
        else:
            log_check("Abstract seeds claim found", False, "Pattern not matched")

        gap_match = re.search(r"gap to.*?(?:dual|lower bound).*?(\d+\.\d+)%", abs_text, re.IGNORECASE)
        if gap_match:
            claimed_gap = float(gap_match.group(1))
            diff_gap = abs(claimed_gap - alns_mean_gap_lb)
            log_check("Abstract Mean Gap to LB matches CSV (tol 0.15%)", diff_gap < 0.15,
                      f"Claimed: {claimed_gap:.2f}%, Actual: {alns_mean_gap_lb:.2f}%")
        else:
            log_check("Abstract Gap to LB pattern found", False, "Pattern not matched")

        opt_match = re.search(r"(?:gap to optimum.*?ALNS[-_]WDP\s*|gap to optimum(?:\s+of)?\s*)(\d+\.\d+)%", abs_text, re.IGNORECASE)
        if opt_match:
            claimed_opt = float(opt_match.group(1))
            diff_opt = abs(claimed_opt - alns_mean_gap_opt)
            log_check("Abstract Mean Gap to Opt matches CSV (tol 0.15%)", diff_opt < 0.15,
                      f"Claimed: {claimed_opt:.2f}%, Actual: {alns_mean_gap_opt:.2f}%")
        else:
            log_check("Abstract Gap to Opt pattern found", False, "Pattern not matched")

        rt_match = re.search(r"mean runtime of.*?(\d+\.\d+)\s*s", abs_text, re.IGNORECASE)
        if rt_match:
            claimed_rt = float(rt_match.group(1))
            diff_rt = abs(claimed_rt - alns_mean_runtime)
            log_check("Abstract Mean Runtime matches CSV (tol 0.15s)", diff_rt < 0.15,
                      f"Claimed: {claimed_rt:.2f}s, Actual: {alns_mean_runtime:.2f}s")

        # Check budget statement: within 6%
        has_within_6_abs = "within 6%" in abs_text
        has_within_5_abs = "within 5%" in abs_text
        log_check("docs/abstract.md cites 'within 6%' (and not 'within 5%')", has_within_6_abs and not has_within_5_abs)

    # 5. Cross-Verification with report/report.tex
    print("\n--- 5. Cross-Verification with report/report.tex ---")
    tex_path = Path("report/report.tex")
    if tex_path.exists():
        tex_text = tex_path.read_text(encoding="utf-8")
        
        # Check budget statement in report.tex (escaped or unescaped %)
        has_within_6_tex = ("within 6%" in tex_text) or (r"within 6\%" in tex_text)
        has_within_5_tex = ("within 5%" in tex_text) or (r"within 5\%" in tex_text)
        log_check("report.tex cites 'within 6%' (and not 'within 5%')", has_within_6_tex and not has_within_5_tex)

        tex_inst = re.search(r"(?:across|benchmarked|evaluated|suite of)\s+(\d+)\s+problem instances", tex_text, re.IGNORECASE)
        if not tex_inst:
            tex_inst = re.search(r"(\d+)\s+problem instances", tex_text)
        if tex_inst:
            claimed_n = int(tex_inst.group(1))
            log_check("report.tex instance count matches CSV (20)", claimed_n == num_instances,
                      f"Claimed: {claimed_n}, Actual: {num_instances}")

        tex_seeds = re.search(r"(\d+)\s+independent stochastic seeds", tex_text)
        if tex_seeds:
            claimed_s = int(tex_seeds.group(1))
            log_check("report.tex stochastic seeds matches (30)", claimed_s == 30,
                      f"Claimed: {claimed_s}")

        tex_gap = re.search(r"gap to.*?(?:lower bound|dual).*?(\d+\.\d+)\\%", tex_text, re.IGNORECASE)
        if tex_gap:
            claimed_g = float(tex_gap.group(1))
            diff_g = abs(claimed_g - alns_mean_gap_lb)
            log_check("report.tex Gap to LB matches CSV (tol 0.15%)", diff_g < 0.15,
                      f"Claimed: {claimed_g:.2f}%, Actual: {alns_mean_gap_lb:.2f}%")

        # Check per-instance table tab:small_instances in report.tex
        small_df = df_bench[df_bench["opt"].notna()]
        small_instances = small_df["instance"].unique()
        all_inst_matched = True
        for inst in small_instances:
            clean_name = inst.replace("_", "\\_")
            if clean_name not in tex_text:
                all_inst_matched = False
                log_check(f"report.tex contains {inst}", False, "Missing in table")
                break
        log_check(f"report.tex tab:small_instances contains all {len(small_instances)} small instances",
                  all_inst_matched, f"Verified {len(small_instances)} instances")

        # Check average row in tab:small_instances
        has_avg_row = r"\textbf{Average ($n \le 20$)} & -- & -- & -- & 0.45 & 67.9 & 0.27 & 85.2 & 0.40 & 79.1" in tex_text
        log_check("report.tex tab:small_instances average row matches CSV", has_avg_row,
                  "0.45% / 67.9% | 0.27% / 85.2% | 0.40% / 79.1%")

    # Check report/generate_pdf.py for runtime budget statement
    gen_pdf_path = Path("report/generate_pdf.py")
    if gen_pdf_path.exists():
        gen_text = gen_pdf_path.read_text(encoding="utf-8")
        has_within_6_gen = "within 6%" in gen_text
        has_within_5_gen = "within 5%" in gen_text
        log_check("report/generate_pdf.py cites 'within 6%' (and not 'within 5%')",
                  has_within_6_gen and not has_within_5_gen,
                  "Verified 'within 6%'" if (has_within_6_gen and not has_within_5_gen) else "FAILED")

    # Check report.pdf exists and > 500KB
    pdf_path = Path("report/report.pdf")
    log_check("report/report.pdf compiled and >500KB", pdf_path.exists() and pdf_path.stat().st_size > 500000,
              f"Size: {pdf_path.stat().st_size if pdf_path.exists() else 0} bytes")

    # PyMuPDF text extraction checking for key claims in report.pdf
    if pdf_path.exists():
        import pymupdf
        doc = pymupdf.open(str(pdf_path))
        full_pdf_text = ""
        for page in doc:
            full_pdf_text += page.get_text()
        doc.close()
        has_547_pdf = "5.47%" in full_pdf_text
        has_fig8_pdf = "Figure 8" in full_pdf_text
        has_alns_pdf = "ALNS-WDP" in full_pdf_text
        has_within_6_pdf = "within 6%" in full_pdf_text
        log_check("report.pdf text contains '5.47%'", has_547_pdf, "Found '5.47%'" if has_547_pdf else "MISSING")
        log_check("report.pdf text contains 'Figure 8'", has_fig8_pdf, "Found 'Figure 8'" if has_fig8_pdf else "MISSING")
        log_check("report.pdf text contains 'ALNS-WDP'", has_alns_pdf, "Found 'ALNS-WDP'" if has_alns_pdf else "MISSING")
        log_check("report.pdf text contains 'within 6%'", has_within_6_pdf, "Found 'within 6%'" if has_within_6_pdf else "MISSING")

    # 6. Cross-Verification with slides/presentation.pptx
    print("\n--- 6. Verification of slides/presentation.pptx ---")
    pptx_path = Path("slides/presentation.pptx")
    log_check("slides/presentation.pptx exists and >50KB", pptx_path.exists() and pptx_path.stat().st_size > 50000,
              f"Size: {pptx_path.stat().st_size if pptx_path.exists() else 0} bytes")

    if pptx_path.exists():
        prs = pptx.Presentation(pptx_path)
        log_check("slides count == exactly 5", len(prs.slides) == 5, f"Slide count: {len(prs.slides)}")
        
        # Check that each slide has speaker notes
        notes_present = all(s.has_notes_slide and len(s.notes_slide.notes_text_frame.text.strip()) > 50 for s in prs.slides)
        log_check("All 5 slides have comprehensive speaker notes", notes_present)

        # Check slide 3 text for budget statement
        s3_text = ""
        for shape in prs.slides[2].shapes:
            if shape.has_text_frame:
                s3_text += shape.text_frame.text + " "
        has_within_6_s3 = "within 6%" in s3_text
        log_check("Slide 3 cites 'within 6%'", has_within_6_s3)

        # Check slide 4 text for exact metrics
        s4_text = ""
        for shape in prs.slides[3].shapes:
            if shape.has_text_frame:
                s4_text += shape.text_frame.text + " "
        
        has_520 = f"{alns_mean_gap_lb:.2f}%" in s4_text
        log_check(f"Slide 4 cites exact ALNS-WDP gap to LB ({alns_mean_gap_lb:.2f}%)", has_520,
                  f"Found: {alns_mean_gap_lb:.2f}%" if has_520 else "MISSING")
        
        has_045 = f"{alns_mean_gap_opt:.2f}%" in s4_text
        log_check(f"Slide 4 cites exact gap to opt ({alns_mean_gap_opt:.2f}%)", has_045,
                  f"Found: {alns_mean_gap_opt:.2f}%" if has_045 else "MISSING")

        # Check Slide 4 table numbers against stratified_topology_comparison.csv
        strat_file = results_dir / "stratified_topology_comparison.csv"
        if strat_file.exists():
            df_strat_check = pd.read_csv(strat_file)
            table_shapes = [s for s in prs.slides[3].shapes if s.has_table]
            if table_shapes:
                t_s4 = table_shapes[0].table
                s4_table_rows = []
                for r_idx in range(len(t_s4.rows)):
                    s4_table_rows.append([t_s4.cell(r_idx, c_idx).text.strip() for c_idx in range(len(t_s4.columns))])
                
                log_check("Slide 4 table dimensions == 9x6", len(t_s4.rows) == 9 and len(t_s4.columns) == 6,
                          f"{len(t_s4.rows)}x{len(t_s4.columns)}")
                
                s4_matched = True
                for r_idx, r in df_strat_check.iterrows():
                    row_in_table = s4_table_rows[r_idx + 1]
                    exp_alg = r["method"]
                    exp_gap = f"{r['gap_lb_pct_mean']:.2f}%"
                    if row_in_table[1] != exp_alg or row_in_table[2] != exp_gap:
                        s4_matched = False
                        log_check(f"Slide 4 row {r_idx+1} {exp_alg}", False,
                                  f"Expected {exp_alg} {exp_gap}, found {row_in_table[1]} {row_in_table[2]}")
                        break
                log_check("Slide 4 table data matches stratified_topology_comparison.csv", s4_matched,
                          "All 8 data rows verified")

    # 7. Documentation Integrity and Absence of Fabricated Variants/Numbers
    print("\n--- 7. Documentation Integrity & Fabricated Variants Audit ---")
    forbidden_variants = ["No_Regret_Repair", "No_Worst_Setup_Destroy", "No_Shaw_Destroy"]
    forbidden_stale_numbers = ["4.18%", "6.03%", "4.80%", "14.59%", "0.23%", "1.56 s", "1.56s", "39.45", "0.0015", "0.0220"]
    
    audited_docs = [
        docs_dir / "VIVA_QA.md",
        docs_dir / "novelty.md",
        docs_dir / "problem_analysis.md",
        docs_dir / "window_dp_correctness.md",
    ]
    
    for doc in audited_docs:
        if not doc.exists():
            log_check(f"Doc file {doc.name} exists", False)
            continue
        text = doc.read_text(encoding="utf-8")
        
        # Check forbidden variants
        found_fb = [v for v in forbidden_variants if v in text]
        log_check(f"{doc.name} free of fabricated variants", len(found_fb) == 0,
                  f"Violations: {found_fb}" if found_fb else "Clean")
        
        # Check stale numbers
        found_sn = [sn for sn in forbidden_stale_numbers if sn in text]
        log_check(f"{doc.name} free of stale metrics", len(found_sn) == 0,
                  f"Violations: {found_sn}" if found_sn else "Clean")

        # Check that ALNS-WDP is not claimed to have 5.20% gap
        has_stale_alns_520 = bool(re.search(r"ALNS[-_]WDP\b[^\n]*?(?:achieves|gap|to LB)\s*5\.20%", text, re.IGNORECASE))
        log_check(f"{doc.name} does not cite stale ALNS-WDP 5.20% gap", not has_stale_alns_520)

    # Check VIVA_QA.md contains all 5 real ablation variants
    viva_text = (docs_dir / "VIVA_QA.md").read_text(encoding="utf-8") if (docs_dir / "VIVA_QA.md").exists() else ""
    has_all_5_viva = all(v in viva_text for v in valid_variants)
    log_check("docs/VIVA_QA.md documents all 5 real ablation variants", has_all_5_viva)

    # Check VIVA_QA.md complexity does not claim O(n log n) per iteration
    has_false_n_log_n = re.search(r"O\(n\s*\\log\s*n\)\s*per\s*iteration", viva_text, re.IGNORECASE)
    log_check("docs/VIVA_QA.md does not claim false O(n log n) per iteration", has_false_n_log_n is None)

    # Check that 'Q-learning' is completely absent from all documentation, report, and slides
    q_docs = [
        docs_dir / "abstract.md",
        docs_dir / "problem_analysis.md",
        docs_dir / "novelty.md",
        docs_dir / "VIVA_QA.md",
        report_dir / "report.tex",
        slides_dir / "generate_presentation.py",
    ]
    for qd in q_docs:
        if qd.exists():
            t = qd.read_text(encoding="utf-8")
            has_q = bool(re.search(r"\bQ-learning\b", t, re.IGNORECASE))
            log_check(f"{qd.name} free of 'Q-learning'", not has_q, "Replaced with bandit / exponential moving-average" if not has_q else "FOUND Q-learning")

    print("\n" + "=" * 75)
    if all_passed:
        print("ALL CLAIM VERIFICATION CHECKS PASSED SUCCESSFULLY! (100% PASS)")
    else:
        print("SOME CHECKS FAILED! Please inspect failed checks above.")
    print("=" * 75)
    return all_passed


if __name__ == "__main__":
    success = run_checks()
    sys.exit(0 if success else 1)
