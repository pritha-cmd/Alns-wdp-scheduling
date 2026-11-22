# AUDIT.md: Comprehensive Technical and Empirical Audit

**Audit Date**: November 2026  
**Auditor**: Session 2 (Phase R0 Audit)  
**Target Codebase**: Single-Machine Scheduling Research Project (ALNS-WDP)

---

## 1. Executive Summary of Audit Findings

An exhaustive forensic inspection of the codebase, generated CSV result logs, figures, LaTeX report, compiled PDF, and slide deck identified six critical discrepancies between reported claims and underlying empirical data. While core components (the evaluator, base-case proof, Held-Karp bitmask DP, and ALNS operators) are mathematically sound and unit-tested, the experimental pipeline suffered from instance-filtering defects, duplicate data entries, un-scalarized bi-objective sweeps, and over-generalized statistical claims.

---

## 2. Detailed Discrepancies and Root-Cause Analysis

### Issue 1: Instance Filtering Defect and Missing Release Date Dispersion
- **Observed Claim**: Abstract, report, and slides claim benchmarking across 16 instances covering sizes $n \in [4, 200]$, setup topologies (symmetric and asymmetric), and release date congestion factors $\alpha \in \{0.0, 0.3, 0.6\}$.
- **Actual Empirical State in `results/single_objective_benchmarks.csv`**:
  - The dataset contains only 11 distinct instance names.
  - Every single instance in the CSV has $\alpha = 0.0$!
  - Every non-base instance is asymmetric (`_asym_`).
- **Root Cause**:
  In `run_all.py` (lines 44–55), instance loading used:
  ```python
  asym_files = list(data_dir.glob(f"n{n}_*asym*.json"))
  sym_files = list(data_dir.glob(f"n{n}_*sym*.json"))
  if asym_files:
      bench_instances.append(Instance.load(asym_files[0]))
  if sym_files and n in [8, 15, 30, 50, 100]:
      bench_instances.append(Instance.load(sym_files[0]))
  ```
  Because the substring `"sym"` is contained within `"asym"`, `*sym*.json` matched both asymmetric and symmetric instances. In Python's glob order, `_asym_` sorted before `_sym_`, causing `sym_files[0]` to load the exact same asymmetric instance as `asym_files[0]`. Furthermore, indexing `[0]` picked only the first match, which was always $\alpha = 0.0$.
- **Consequence for Figures**:
  Figure 7 (`fig7_sensitivity_alpha.png`) was plotted from `df_bench` where only $\alpha = 0.0$ existed, rendering the plot uninformative and misleading.
- **Required Action (Phase R2)**:
  Fix glob filtering to strictly separate `*_sym_*.json` and `*_asym_*.json`. Incorporate all $\alpha \in \{0.0, 0.3, 0.6\}$ across symmetric and asymmetric families into the benchmark matrix.

---

### Issue 2: Duplicate Rows in Benchmark and Bi-Objective Logs
- **Observed Data**:
  - `single_objective_benchmarks.csv` contains 728 rows, of which 226 are duplicates on `(instance, method, seed)`.
  - `biobjective_metrics.csv` contains duplicate rows for instances $n=8$ and $n=50$.
- **Root Cause**:
  Direct consequence of Issue 1: because `sym_files[0]` loaded the asymmetric instance, the identical instance was appended twice into `bench_instances` for sizes $n \in \{8, 15, 30, 50, 100\}$. The benchmarking loop processed the duplicate instance objects independently and appended duplicate rows.
- **Required Action (Phase R2)**:
  Ensure `bench_instances` contains strictly unique instances. Add an automated regression assertion in unit tests verifying uniqueness on `(instance, method, seed)`.

---

### Issue 3: Invalidation of Bi-Objective Weighted Sweeps
- **Observed Claim**:
  The report claims a comparison between NSGA-II and ALNS-WDP using scalarized weighted sweeps: $\min \lambda C_{\max} + (1 - \lambda) \sum w_j T_j$.
- **Actual Code State in `src/experiments.py`**:
  ```python
  for lam in lambdas:
      cfg = ALNSConfig(time_limit=0.5, window_size_k=min(8, inst.n), seed=int(lam * 100) + 1)
      res = solve_alns_wdp(inst.p, inst.r, inst.s, inst.s0, config=cfg)
      cmax, twt = compute_bi_objective(res.best_perm, inst.p, inst.r, inst.s, inst.s0, inst.d, inst.w)
  ```
  `solve_alns_wdp` only minimized makespan $C_{\max}$! Parameter `lam` was merely used as a random seed multiplier (`seed=int(lam * 100) + 1`). Total weighted tardiness was never optimized during search.
- **Required Action (Phase R2 & R3)**:
  Pass the scalarization weight $\lambda$ directly into the evaluation and acceptance functions of ALNS-WDP (or implement an $\epsilon$-constraint polisher). Re-run true bi-objective benchmarks against NSGA-II with both Hypervolume and Inverted Generational Distance (IGD).

---

### Issue 4: Severe Truncation of Statistical Tests (Wilcoxon and Friedman)
- **Observed Claim**:
  The report states: "Friedman ranking confirms statistical significance ($p = 0.0342$)" and cites paired Wilcoxon signed-rank tests.
- **Actual State in `results/statistical_tests.csv`**:
  Every single Wilcoxon test row had `wilcoxon_stat = NaN`, `p_value = 1.0`, and `significant_0_05 = False`!
- **Root Cause**:
  In `src/stats.py`:
  ```python
  inst_pivot = df.pivot_table(index=["instance", "n"], columns="method", values="makespan", aggfunc="mean").dropna()
  ```
  `dropna()` was executed across all columns simultaneously. Because `Brute_Force` was only evaluated on $n \le 10$ and `Exact_DP` on $n \le 15$, `dropna()` discarded all instances with $n > 10$. This left only 4 instances in the pivot table! With $N = 4$, Wilcoxon signed-rank cannot compute a non-trivial test statistic ($N < 5$ requirement in `scipy.stats.wilcoxon`).
- **Required Action (Phase R2)**:
  Compute pairwise Wilcoxon tests between ALNS-WDP and each competitor on the subset of instances where both methods ran, applying Holm-Bonferroni correction. Conduct Friedman tests on the full instance set for all methods that ran across all instances.

---

### Issue 5: Imprecise Terminology ("Optimality Gap" vs. "Gap to Lower Bound")
- **Observed Text**:
  Throughout the report and slides, the metric $(C_{\max} - LB) / LB$ is referred to as "Optimality Gap".
- **Critique**:
  $LB$ is a dual assignment lower bound, not the true optimum $C_{\max}^*$. Calling this an "optimality gap" is technically imprecise and penalizes the heuristic when the lower bound is loose.
- **Required Action**:
  Rename metric to **"Gap to Lower Bound"** (or **"Gap to LB"**). Reserve **"Gap to Optimum"** exclusively for small instances ($n \le 20$) where true mathematical optimality is established via exact DP or CP-SAT.

---

### Issue 6: Premature Claims of Dominance and Unverified Numbers
- **Observed Text**:
  Phrases like "strictly dominates", "state of the art", and "reduces makespan gaps by over 19%" appeared without rigorous confidence intervals or statistical qualification.
- **Required Action (Phase R5 & R6)**:
  Temper all language to academic standards. Use cautious terminology ("consistently achieves smaller makespan gaps", "effective combination"). Include standard deviations, bootstrap confidence intervals, and exact script references for every reported figure.

---

## 3. Corrective Plan of Action

| Phase | Core Objective | Key Deliverables |
| :--- | :--- | :--- |
| **R1** | Theoretical Rigor & Problem Analysis | Rewrite `docs/problem_analysis.md`: explicit assumptions, complexity ladder, worked 4-job ATSP example, testable RQs. |
| **R2** | Experimental Design Overhaul | Fix instance loading (all $\alpha$, sym/asym, derived TSPLIB), 30 seeds, exact DP up to $n \le 20$, tightened lower bound + 1000 validation tests, CP-SAT study, true bi-objective scalarization with HV & IGD, `run_manifest.json`. |
| **R3** | Algorithmic Improvements | Scale-normalized SA temperature, bandit update with weight floor, $O(n)$ incremental makespan evaluation, adaptive window size $k$, window DP correctness/monotonicity proof. |
| **R4** | Rigorous Ablation & Sensitivity | Full ablation across all instance cells $\times$ 30 seeds with Holm-corrected tests; multi-seed sensitivity on $k$, $\alpha$, and $n$. |
| **R5** | Honest Novelty Boundary | Author `docs/novelty.md` establishing exact literature boundaries. |
| **R6** | Comprehensive Report & Visualizations | Re-compile 10–15 page report (`report.pdf` & `report.tex`), 5 slides (`presentation.pptx`), automated audit script `tools/check_claims.py`. |
| **R7** | Viva Defense Prep & Housekeeping | Author `docs/VIVA_QA.md` (25 questions), `README.md`, clean environment. |

---

## 4. Results Directory Forensic Inventory (Step 1 v2 Audit)

As of Session 2 (November 13, 2026), the contents of `results/` are:

| File Name | File Size | Timestamp | Rows | Status & Forensic Audit Findings |
| :--- | :--- | :--- | :--- | :--- |
| `single_objective_benchmarks.csv` | 296,582 bytes | 2026-11-13 12:12:32 | 2,535 | **COMPLETE & VALID**. Fully regenerated in Session 2. Covers 20 unique instances, all $\alpha \in \{0.0, 0.3, 0.6\}$, both symmetric & asymmetric, derived TSPLIB (`bayg29`, `berlin52`), 30 seeds per stochastic method, 0 duplicates. |
| `ablation_results.csv` | 56,448 bytes | 2026-11-13 12:31:08 | 600 | **COMPLETE & VALID**. Generated in Session 2 across 8 instances $\times$ 5 variants $\times$ 15 seeds. Covers $\alpha \in \{0.0, 0.3, 0.6\}$, sym and asym, 0 duplicates. Reused directly. |
| `convergence_curves.csv` | 21,249 bytes | 2026-11-13 12:12:57 | 411 | **COMPLETE & VALID**. Generated in Session 2 across GA, SA, and ALNS-WDP on $n=15$ and $n=50$. |
| `sensitivity_k.csv` | 3,932 bytes | 2026-11-13 12:34:03 | 50 | **COMPLETE & VALID**. Window size design study ($k \in \{4, 6, 8, 10, 12\}$). |
| `strategy_placement.csv` | 2,615 bytes | 2026-11-13 12:34:03 | 30 | **COMPLETE & VALID**. Placement strategy study (sliding vs worst-setup vs random). |
| `run_manifest.json` | 1,234 bytes | 2026-11-13 12:44:49 | N/A | **COMPLETE & VALID**. Detailed system environment, package versions, and random seed manifest. |
| `biobjective_metrics.csv` | Pending | Pending | -- | **IN PROGRESS**. Real scalarized $\lambda$ sweep vs NSGA-II currently executing. |
| `pareto_fronts.csv` | Pending | Pending | -- | **IN PROGRESS**. Pareto front point coordinates from scalarized sweep. |
| `statistical_tests.csv` | Pending | Pending | -- | **PENDING STEP 8**. Derived from `single_objective_benchmarks.csv` with Holm-Bonferroni correction. |
| `friedman_ranks.csv` | Pending | Pending | -- | **PENDING STEP 8**. Friedman ranks derived from `single_objective_benchmarks.csv`. |


