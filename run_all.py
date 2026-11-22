"""
Master Reproduction Pipeline for Single-Machine Scheduling Research Project.
Executes core experimental benchmark suite end-to-end:
1. Pytest unit and regression test suite (26 tests)
2. Single-objective benchmarking (18 diverse instances, 30 seeds per method, all alphas, sym/asym, derived TSPLIB)
3. Convergence profiling (GA vs SA vs ALNS-WDP)
4. Ablation study across 5 variants
5. Window DP design study (k in {4,6,8,10,12}, placement strategies)
6. True scalarized bi-objective comparison with NSGA-II (Hypervolume & IGD)
7. Statistical tests (Wilcoxon with Holm-Bonferroni correction, Friedman ranking, bootstrap CIs)
8. High-resolution figure generation (300 DPI Figures 1–7)
9. Hardware and reproducibility manifest generation

REPRODUCTION SCOPE NOTE:
This script reproduces the core single-objective and bi-objective experimental campaign.
It does NOT independently execute:
- Lower-bound recalculation and admissible anchor evaluation (tools/recalculate_lb_results.py)
- The controlled setup-time dominance sensitivity study (tools/run_rho_sensitivity.py, 2,400 runs)
- PDF report compilation (report/generate_pdf.py)
- Presentation generation (slides/generate_presentation.py)
- Automated claim verification (tools/check_claims.py)
For complete end-to-end reproduction of all research deliverables, follow the multi-step workflow in README.md.
"""

import sys
import time
from pathlib import Path
import pytest
import pandas as pd

from src.instances import (
    Instance,
    generate_benchmark_suite,
    load_all_benchmark_instances,
    get_base_4job_instance,
)
from src.experiments import (
    generate_run_manifest,
    run_single_objective_experiments,
    run_convergence_experiments,
    run_ablation_experiments,
    run_window_dp_design_study,
    run_biobjective_experiments,
)
from src.stats import compute_statistical_tests
from src.plots import generate_all_plots


def select_diverse_benchmark_instances(all_instances: list[Instance]) -> list[Instance]:
    """
    Selects a balanced, diverse benchmark subset covering:
    - Base 4-job instance
    - All n in {8, 10, 12, 15, 20, 30, 50, 100, 200}
    - All alpha in {0.0, 0.3, 0.6}
    - Both symmetric and asymmetric setup topologies
    - Derived TSPLIB instances
    """
    inst_by_name = {inst.name: inst for inst in all_instances}
    selected = []
    
    # 1. Base 4-job
    if "base_4job" in inst_by_name:
        selected.append(inst_by_name["base_4job"])
    else:
        selected.append(get_base_4job_instance())
        
    # 2. Balanced matrix covering sizes, alphas, and setup families
    target_specs = [
        # (n, alpha, is_symmetric)
        (8, 0.3, False),
        (8, 0.0, True),
        (10, 0.0, False),
        (10, 0.6, True),
        (12, 0.3, False),
        (12, 0.3, True),
        (15, 0.6, False),
        (15, 0.0, True),
        (20, 0.0, False),
        (20, 0.3, True),
        (30, 0.3, False),
        (30, 0.6, True),
        (50, 0.6, False),
        (50, 0.0, True),
        (100, 0.0, False),
        (100, 0.3, True),
        (200, 0.3, False),
    ]
    
    for n, alpha, is_sym in target_specs:
        matched = [
            inst for inst in all_instances
            if inst.n == n and abs(inst.alpha - alpha) < 1e-3 and inst.is_symmetric == is_sym and inst.family == "synthetic"
        ]
        if matched:
            selected.append(matched[0])
            
    # 3. Derived TSPLIB instances
    tsplib_instances = [inst for inst in all_instances if inst.family == "derived_tsplib"]
    for inst in tsplib_instances[:2]:  # Burma14, Bayg29
        selected.append(inst)
        
    # Verify strict uniqueness
    seen = set()
    unique_selected = []
    for inst in selected:
        if inst.name not in seen:
            seen.add(inst.name)
            unique_selected.append(inst)
            
    return unique_selected


def main():
    print("=" * 75)
    print("STARTING MASTER REPRODUCTION PIPELINE: SINGLE-MACHINE SCHEDULING (SESSION 2)")
    print("=" * 75)
    
    start_total = time.perf_counter()
    
    # Step 1: Run Pytest Suite
    print("\n>>> STEP 1: Running Complete Pytest Unit & Regression Suite...")
    retcode = pytest.main(["-v", "tests"])
    if retcode != 0:
        print("ERROR: Unit tests failed! Aborting pipeline.")
        sys.exit(retcode)
    print("SUCCESS: All unit tests passed.")
    
    # Step 2: Ensure Data Directory and Benchmark Instances Exist
    print("\n>>> STEP 2: Loading Benchmark Instances...")
    data_dir = Path("data")
    all_instances = load_all_benchmark_instances(data_dir)
    if len(all_instances) < 30:
        print("Generating complete benchmark suite in data/...")
        all_instances = generate_benchmark_suite(data_dir)
        
    bench_instances = select_diverse_benchmark_instances(all_instances)
    print(f"Loaded {len(bench_instances)} strictly unique benchmark instances covering all alphas and families:")
    for inst in bench_instances:
        s_type = "sym" if inst.is_symmetric else "asym"
        print(f"  - {inst.name:<30} (n={inst.n:<3}, alpha={inst.alpha:<3}, setup={s_type:<4}, family={inst.family})")
        
    # Step 3: Run Single-Objective Experiments across 30 Seeds
    bench_csv = Path("results/single_objective_benchmarks.csv")
    if bench_csv.exists() and bench_csv.stat().st_size > 1000:
        print(f"\n>>> STEP 3: Loading existing Single-Objective Benchmarks from {bench_csv}...")
        df_bench = pd.read_csv(bench_csv)
    else:
        print("\n>>> STEP 3: Executing Single-Objective Benchmarks (30 Seeds per Stochastic Method)...")
        df_bench = run_single_objective_experiments(
            instances=bench_instances,
            num_seeds=30,
            base_budget_per_run=0.75,
            results_dir="results",
        )
    
    # Assert row uniqueness
    dup_count = df_bench.duplicated(subset=["instance", "method", "seed"]).sum()
    assert dup_count == 0, f"Found {dup_count} duplicate rows in single_objective_benchmarks.csv!"
    print(f"Verified row uniqueness: 0 duplicates across {len(df_bench)} records.")
    
    # Step 4: Run Convergence Curves
    conv_csv = Path("results/convergence_curves.csv")
    if conv_csv.exists() and conv_csv.stat().st_size > 500:
        print(f"\n>>> STEP 4: Loading existing Convergence Curves from {conv_csv}...")
        df_conv = pd.read_csv(conv_csv)
    else:
        print("\n>>> STEP 4: Recording Convergence Curves...")
        conv_subset = [inst for inst in bench_instances if inst.n in [15, 50]]
        df_conv = run_convergence_experiments(conv_subset, results_dir="results")
    
    # Step 5: Run Ablation Study across 5 Variants
    abl_csv = Path("results/ablation_results.csv")
    if abl_csv.exists() and abl_csv.stat().st_size > 500:
        print(f"\n>>> STEP 5: Loading existing Ablation Study from {abl_csv}...")
        df_abl = pd.read_csv(abl_csv)
    else:
        print("\n>>> STEP 5: Executing Ablation Study (5 Variants x 15 Seeds)...")
        abl_subset = [inst for inst in bench_instances if inst.n in [10, 20, 50, 100]]
        df_abl = run_ablation_experiments(abl_subset, results_dir="results", num_seeds=15)
    
    # Step 6: Run Window DP Design Study (k in {4,6,8,10,12} and Placement Strategies)
    sens_csv = Path("results/sensitivity_k.csv")
    if sens_csv.exists() and sens_csv.stat().st_size > 500:
        print(f"\n>>> STEP 6: Loading existing Window DP Design Study from {sens_csv}...")
        df_k = pd.read_csv(sens_csv)
        strat_csv = Path("results/sensitivity_placement.csv")
        df_strat = pd.read_csv(strat_csv) if strat_csv.exists() else pd.DataFrame()
    else:
        print("\n>>> STEP 6: Executing Window DP Design & Placement Study...")
        study_subset = [inst for inst in bench_instances if inst.n in [12, 30, 50]]
        df_k, df_strat = run_window_dp_design_study(study_subset, results_dir="results")
    
    # Step 7: Run Bi-Objective Experiments (Real Scalarized Sweeps vs NSGA-II)
    biobj_csv = Path("results/biobjective_metrics.csv")
    if biobj_csv.exists() and biobj_csv.stat().st_size > 500:
        print(f"\n>>> STEP 7: Loading existing Bi-Objective Metrics from {biobj_csv}...")
        df_biobj_metrics = pd.read_csv(biobj_csv)
        front_csv = Path("results/pareto_fronts.csv")
        df_fronts = pd.read_csv(front_csv) if front_csv.exists() else pd.DataFrame()
    else:
        print("\n>>> STEP 7: Executing Bi-Objective Experiments (15 Seeds, HV & IGD)...")
        biobj_subset = [inst for inst in bench_instances if inst.n in [8, 20, 50]]
        df_fronts, df_biobj_metrics = run_biobjective_experiments(biobj_subset, num_seeds=15, results_dir="results")
    
    # Step 8: Compute Rigorous Statistical Tests
    print("\n>>> STEP 8: Computing Statistical Tests (Wilcoxon + Holm, Bootstrap CIs, Friedman)...")
    summary, df_wilcoxon, df_friedman = compute_statistical_tests(
        df_bench, target_method="ALNS_WDP", results_dir="results"
    )
    
    print("\n--- Wilcoxon Paired Signed-Rank Tests with Holm Correction (vs ALNS-WDP) ---")
    cols_show = ["method", "n_instances", "target_wins", "ties", "target_losses", "mean_pct_improvement", "holm_p_value", "significant_0_05"]
    print(df_wilcoxon[cols_show].to_string(index=False))
    
    print("\n--- Friedman Average Ranks & Nemenyi CD ---")
    if not df_friedman.empty:
        print(df_friedman[["method", "average_rank", "friedman_stat", "friedman_p_value", "nemenyi_cd"]].to_string(index=False))
        
    # Step 9: Generate High-Resolution Visualizations (300 DPI)
    print("\n>>> STEP 9: Generating Publication-Grade Visualizations (300 DPI)...")
    generate_all_plots()
    
    # Step 10: Generate Run Manifest
    print("\n>>> STEP 10: Generating Hardware and Run Manifest...")
    manifest_path = generate_run_manifest(
        results_dir="results",
        extra_meta={
            "num_benchmark_instances": len(bench_instances),
            "stochastic_seeds": 30,
            "ablation_variants": 5,
            "biobjective_seeds": 15,
            "total_benchmark_records": len(df_bench),
        }
    )
    print(f"Saved run manifest to {manifest_path}")
    
    elapsed_total = time.perf_counter() - start_total
    print("\n" + "=" * 75)
    print(f"PIPELINE COMPLETED SUCCESSFULLY IN {elapsed_total:.2f} SECONDS!")
    print("=" * 75)
    print("\n[NOTE] Complete end-to-end reproduction sequence:")
    print("  1. python run_all.py                        (core experiments, tests, and plots)")
    print("  2. python tools/recalculate_lb_results.py   (evaluates admissible lower bounds and refreshes Figs 2 & 5)")
    print("  3. python tools/run_rho_sensitivity.py      (controlled setup dominance study, 2,400 runs, Fig 8)")
    print("  4. python report/generate_pdf.py            (compiles report/report.pdf, 1.78 MB)")
    print("  5. python slides/generate_presentation.py   (generates slides/presentation.pptx)")
    print("  6. python tools/check_claims.py             (verifies 100% data consistency)")


if __name__ == "__main__":
    main()
