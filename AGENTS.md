# AGENTS.md - Multi-Agent Research Coordination Protocol

## Project Summary
- **Domain**: Single-Machine Scheduling under Sequence-Dependent Setup Times and Release Dates ($1 | r_j, s_{ij} | C_{\max}$) and Bi-Objective variant ($1 | r_j, s_{ij} | (C_{\max}, \sum w_j T_j)$).
- **Core Observation**: The base problem ($1 || C_{\max}$, Problem 4 of the practical sheet with 4 jobs $A=3, B=5, C=2, D=4$) is trivial: every valid permutation yields $C_{\max} = \sum p_j = 14$ in $O(n)$ time.
- **NP-Hard Generalization**: Incorporating sequence-dependent setups $s_{ij}$ (isomorphic to ATSP / Problem 3 of the practical sheet) and release dates $r_j$ renders makespan minimization strongly NP-hard.
- **Proposed Algorithm**: **ALNS-WDP** (Adaptive Large Neighborhood Search with Exact Window Dynamic Programming and Reinforcement-Style Operator Selection).
- **Novelty Boundary**: Integrates exact sliding-window Held-Karp dynamic programming polishers ($k \in [6, 10]$) and a bandit/Q-learning adaptive weight update with exploration floor ($\underline{w} = 0.05$) within an ALNS framework; paired with assignment/release-date dual lower bounds.

---

## Architecture / Folder Map
- `data/`: Benchmark problem instances in JSON format (including 4-job base case, synthetic instances $n \in \{4, \dots, 200\}$ with varying setup structures and release date congestion factors $\alpha \in \{0.0, 0.3, 0.6\}$, and TSPLIB-derived `bayg29` and `berlin52`).
- `docs/`:
  - `problem_analysis.md`: Rigorous theoretical analysis, mathematical proof of base triviality, Graham notation taxonomy, complexity proofs, ATSP/Problem 3 mapping, worked 4-job ATSP example, and testable research questions (RQ1-RQ4).
  - `novelty.md`: Literature boundary analysis (what is borrowed vs novel combination) and honest failure analysis on symmetric instances.
  - `AUDIT.md`: Forensic audit log detailing all six root causes, file inventory table with timestamps and status.
  - `window_dp_correctness.md`: Monotonicity theorem, exactness proof, and exhaustive empirical verification against full factorial search.
  - `VIVA_QA.md`: 25 comprehensive oral defense questions and grounded answers across theory, algorithms, empirical results, and validity.
  - `CHANGELOG.md`: Chronological audit log of all file modifications and test states.
  - `abstract.md`: ~200-word academic abstract summarizing findings, exact numbers, and conclusions.
- `src/`:
  - `instances.py`: Reproducible synthetic instance generator with structured seeds and JSON serialisation.
  - `evaluator.py`: High-performance schedule evaluator computing completion times, setups, idle times, makespan, and weighted tardiness.
  - `lower_bound.py`: Valid dual lower bounds via Assignment Problem (Hungarian/Linear Sum Assignment) + release date relaxation.
  - `alns/`:
    - `operators.py`: Destroy and repair heuristics (worst-setup, cluster, relatedness, regret-2).
    - `window_dp.py`: Exact sliding window Held-Karp DP re-optimizer for sub-permutations of size $k$.
    - `solver.py`: Core ALNS-WDP loop with bandit Q-learning scoring, weight floor, and simulated annealing acceptance.
  - `baselines/`:
    - `brute_force.py`: Exact full factorial search for $n \le 10$.
    - `exact_dp.py`: Global Held-Karp bitmask DP for $n \le 20$.
    - `ilp.py`: Mixed-Integer Linear Programming models solved via OR-Tools CP-SAT and PuLP.
    - `ga_sa.py`: Single-objective Genetic Algorithm and Simulated Annealing with budget controls.
    - `dispatching.py`: Heuristics (SPT, ERD, Nearest-Setup, ECT).
    - `local_search.py`: Continuous multi-start 2-opt and relocate neighborhood descent running to budget exhaustion.
    - `nsga2.py`: Pymoo-based multi-objective evolutionary search for $(C_{\max}, \sum w_j T_j)$.
  - `experiments.py`: Unified benchmarking harness across instances and methods.
  - `stats.py`: Statistical significance analysis (Wilcoxon signed-rank with Holm correction, Friedman rank tests).
  - `plots.py`: Publication-grade visualization suite (scalability, gap distributions, convergence, Pareto fronts, ablation, sensitivity).
- `results/`: Raw benchmark CSV logs, Pareto front data, and statistical metrics.
- `figures/`: High-resolution figures (300 DPI PNGs).
- `report/`: Formal research report in LaTeX (`report.tex`) and compiled PDF (`report.pdf`, >1MB) via `generate_pdf.py`.
- `slides/`: 5-slide professional presentation PPTX (`presentation.pptx`) with embedded figures and speaker notes via `generate_presentation.py`.
- `tests/`: 24 pytest unit tests verifying evaluator accuracy, DP optimality, lower bound validity, instance reproducibility, CSV uniqueness, window DP monotonicity, and budget enforcement max overrun.
- `tools/`:
  - `check_claims.py`: Automated verification script asserting 100% agreement between text and results CSVs.
  - `rerun_multistart_ls.py`: Parallel continuous restart harness for MultiStart_LS.
- `run_all.py`: Master reproduction pipeline executing tests, experiments, stats, figures, report, and slides.
- `README.md` & `.gitignore`: Setup and reproduction instructions.

---

## Plan
- [x] P1 Setup and folder structure, AGENTS.md, requirements (Session 1)
- [x] P2 Problem analysis doc with proof and brute-force verification (Session 1)
- [x] P3 Instance generator and evaluator with tests (Session 1)
- [x] P4 Baselines: brute force, DP, ILP, GA, SA, dispatching rules (Session 1)
- [x] P5 NSGA-II bi-objective baseline (Session 1)
- [x] P6 Proposed ALNS-WDP and lower bound (Session 1)
- [x] P7 Experiments, statistics, figures (Session 1)
- [x] P8 Ablation and sensitivity (Session 1)
- [x] P9 Abstract, report, 5-slide PPT (Session 1)
- [x] P10 Final audit: every number in the report traces to results/*.csv; all tests pass; AGENTS.md handoff finalized (Session 1)

### Phase R: Audit, Repair, and Rigorous Strengthening (Session 2)
- [x] R0 Audit the existing artefacts (log findings in docs/AUDIT.md) (Session 2)
- [x] R1 Problem understanding: rewrite docs/problem_analysis.md (assumptions, complexity ladder, worked ATSP example, RQs & hypotheses) (Session 2)
- [x] R2 Experimental design overhaul (20 instances, sym/asym, $\alpha \in \{0, 0.3, 0.6\}$, TSPLIB-derived, 30 seeds, exact DP $n \le 20$, tightened LB + 23 tests, CP-SAT study & matheuristic, Holm-corrected stats + Friedman, real scalarized bi-objective with HV & IGD, run_manifest.json) (Session 2)
- [x] R3 Algorithm improvements (normalized SA temp, bandit action-value with weight floor $\underline{w} = 0.05$, strict timeout inside loops, adaptive $k$ study, window DP monotonicity proof & tests) (Session 2)
- [x] R4 Rigorous ablation and sensitivity (5 variants across 600 runs, 30 seeds for main benchmarks, Holm-corrected tests) (Session 2)
- [x] R5 Honest novelty statement (docs/novelty.md with literature boundaries and symmetric $\alpha=0.3$ failure mode) (Session 2)
- [x] R6 Report, abstract, slides (regenerated strictly from results, claim verification script tools/check_claims.py 100% PASS) (Session 2)
- [x] R7 Viva preparation and housekeeping (docs/VIVA_QA.md, README.md, .gitignore, clean deliverable) (Session 2)

---

## Decisions Log
- **Decision 1 (Package Stack)**: Installed `ortools`, `pulp`, `pymoo`, `python-pptx`, `reportlab` into user environment. CP-SAT provides state-of-the-art exact MIP solving; pymoo handles NSGA-II.
- **Decision 2 (Solver Priority)**: CP-SAT serves as primary exact MIP engine due to its superior performance on scheduling constraints, with PuLP/HiGHS available as secondary baseline.
- **Decision 3 (Test Runner)**: Use `python -m pytest` as standard command because python user scripts directory is accessed via module invocation.
- **Decision 4 (Instance Storage Format)**: Instances serialized as clean JSON schema containing explicit parameters ($p_j, r_j, s_{ij}, s0_j, d_j, w_j$). 61 standard benchmark instances generated in `data/` including the 4-job base case.
- **Decision 5 (MIP Solver Integration)**: In `src/baselines/ilp.py`, CP-SAT uses `AddCircuit` and conditional interval start constraints; PuLP uses `highspy` / HiGHS backend with MTZ sub-tour elimination. Both match exact DP and Brute Force on base and benchmark instances.
- **Decision 6 (NSGA-II Parameterization)**: PermutationRandomSampling with Order Crossover (prob=0.9), InversionMutation (prob=0.3), and Hypervolume metric against dynamic reference bounds.
- **Decision 7 (Dual Lower Bound Formulation)**: Dual lower bound formulated as $\max(\sum p_j + C_{AP}, \max_j (r_j + p_j), \max_j (r_j + \sum_{k: r_k \ge r_j} p_k))$ where $C_{AP}$ is the Hungarian assignment relaxation on transition setups. Proven valid and verified against exact DP.
- **Decision 8 (ALNS-WDP Structure)**: Integrates 4 destroy operators, 2 repair operators (greedy and regret-2), exact sliding window DP re-optimization ($k \in [6, 10]$), and bandit exponential moving average weight updates.
- **Decision 9 (PDF Generation Engine)**: Built ReportLab automated PDF builder in `report/generate_pdf.py` alongside comprehensive LaTeX source `report/report.tex`, ensuring high-resolution embedding of figures and tables in `report/report.pdf`.
- **Decision 10 (MultiStart_LS Continuous Restart)**: Modified MultiStart_LS to continuously restart until exhausting full allotted wall-clock budget, bringing runtime parity across all 4 metaheuristics within 6.5% (ALNS_WDP 1.56s, MultiStart_LS 1.42s, GA 1.37s, SA 1.37s).
- **Decision 11 (Real Bi-Objective Scalarized Sweep)**: Built true scalarized $\lambda \in [0, 1]$ sweep in `src/alns/solver.py` minimizing $\lambda C_{\max} + (1-\lambda) \text{TWT}$, generating non-dominated Pareto fronts evaluated via Hypervolume and Inverted Generational Distance (IGD).
- **Decision 12 (Bandit Weight Floor)**: Implemented exploration weight floor $\underline{w} = 0.05$ to guarantee that no destroy or repair operator is starved of exploration.
- **Decision 13 (Holm-Bonferroni Correction)**: Implemented step-down Holm-Bonferroni correction in `src/stats.py` across paired Wilcoxon tests to rigorously prevent family-wise type I error inflation.
- **Decision 14 (Automated Claim Verification)**: Created `tools/check_claims.py` to cross-examine every number, instance count, gap, and claim in `docs/abstract.md`, `report/report.tex`, `slides/presentation.pptx`, and documentation files against `results/*.csv`.
- **Decision 15 (Window DP Monotonicity Guarantee)**: Formally proved in `docs/window_dp_correctness.md` that because the identity ordering is evaluated within the Held-Karp state space, Window-DP never degrades completion time ($C_{\max}(\pi') \le C_{\max}(\pi)$). Verified across 100% of test instances.
- **Decision 16 (Honest Failure Mode Documentation)**: Formally documented in report, slides, and docs that 2-opt neighborhood descent slightly outperforms ALNS-WDP on symmetric $\alpha=0.3$ instances due to 2-opt segment reversals untangling symmetric loops in $O(1)$ time (labeled as a hypothesis).
- **Decision 17 (Internal Loop Deadline Enforcement)**: Added `perf_counter()` deadline checks inside repair loops, sliding-window DP loops, and final polish in `src/alns/solver.py`, strictly limiting maximum runtime overrun to $\le 3.8\%$ on any instance (well within $\le 5\%$ tolerance).
- **Decision 18 (Metaheuristics-Only Friedman Test)**: Evaluated Friedman ranking strictly across the four stochastic metaheuristics (`ALNS_WDP`, `SA`, `MultiStart_LS`, `GA`) yielding $\chi^2 = 10.50, df = 3, p = 0.01476$ (ranks sum to 10.00, Nemenyi $CD = 1.049$).
- **Decision 19 (Stratified Topology Breakdown)**: Quantified performance separately on asymmetric (9 instances) vs symmetric (11 instances) setup matrices (`results/stratified_topology_comparison.csv`). ALNS-WDP sweeps 9/9 wins vs GA (+4.34%) and +2.69% vs SA on asymmetric, but is level or behind on symmetric setups (vs SA 3W/4T/4L, -0.29%; GA beats ALNS on `n100_a30_sym`).
- **Decision 20 (Bi-Objective Statistical Tests)**: Implemented paired Wilcoxon tests with step-down Holm-Bonferroni correction over 15 seeds per instance for Hypervolume and IGD (`results/biobjective_statistical_tests.csv`). NSGA-II wins HV on 5/6 instances (all Holm $p \le 0.0018$); ALNS-WDP achieves significantly lower IGD on symmetric `n20_a30_sym` (Holm $p = 0.0018$).
- **Decision 21 (Slide Presentation Redesign)**: Redesigned `slides/presentation.pptx` with 16:9 widescreen layout, all bullet text $\ge 14$ pt (`Pt(14)` / `Pt(14.5)`), max 6 clean bullets per slide, native PowerPoint table for stratified topology comparison, and exported images to `slides/slide_images/*.png` for automated visual verification.
- **Decision 22 (Final Polish & Theoretical Precision)**: Fixed $1 \mid r_j \mid C_{\max}$ complexity in `report/report.tex` (polynomial via ERD in $O(n \log n)$; setups drive strong NP-hardness); condensed abstract to exactly 249 words including window-DP ablation findings ($n=100$ Holm $p < 0.05$), small-instance order (MS-LS 0.27% < SA 0.40% < ALNS-WDP 0.45% < GA 1.97%), and bi-objective significance counts; updated Slide 4 with "Symmetric + derived (11)", median improvements, and exploratory split footnote.
- **Decision 23 (IEEEtran Template Conversion & Reference Verification)**: Converted `report/report.tex` to official IEEEtran journal class (`\documentclass[journal]{IEEEtran}`) and placed `report/IEEEtran.cls` directly in directory. Removed nonexistent citation (Bianco et al. 1993), corrected Balas & Simonetti (2001) and Congram et al. (2002) bibliographic entries and problem scopes in `docs/novelty.md` and `docs/VIVA_QA.md`, marked unverified conference paper Shaw (1998) as `[verify]` with no invented metadata, added Related Work skeleton with section headings only, and removed all stray `---` lines. All 24 unit tests and 100% automated claim verification tests pass cleanly.
- **Decision 24 (Table Automation & Claim Alignment Pass)**: Built `tools/make_tables.py` to programmatically extract, format, and inject every results table in `report/report.tex` (main table with small-instance note, per-instance small optimality table, long stratified table, ablation table with no bold on Full) and Slide 4 table in `slides/generate_presentation.py` directly from CSVs. Removed markdown backticks and `**` (0 remaining). Corrected theoretical/empirical claims (CP-SAT optimality scope $n \le 8$; $k$ sensitivity covers $n=12$ only; removed $\alpha \ge 0.8$; updated limitations numbers; runtime parity within 6%; removed "Master Prompt"; conclusion states "lower mean gap, significant only vs GA" and "bandit"). Enhanced `tools/check_claims.py` to verify Slide 4 table and per-instance table. 100% PASS on claim checks and unit tests. Zero files touched in `results/`, `src/`, or `tests/`.
- **Decision 25 (Phase 1–4 Research Strengthening Audit Completed)**: Authored comprehensive audit document `docs/RESEARCH_STRENGTHENING_AUDIT.md` (351 lines) covering Phase 1 (Traceability matrix, evaluation of core experiments, computational budget parity, exact vs LB distinction, paired test subsets, Holm hypothesis families, bi-objective mechanism diagnostic), Phase 2 (Literature taxonomy, master table of verified citations with DOIs and zero invented metadata, novelty boundary), Phase 3 (Setup-time dominance ratio $\rho_s$ computed across all 20 benchmarks and 124 dataset files proving controlled scaling is necessary, failure-case diagnosis on all 6 loss instances showing 2-opt reversal advantage on symmetric $\alpha=0.3$ setups), and Phase 4 (Paper improvement blueprint, claims to weaken/remove). Adhered strictly to the zero-modifications rule: no source code, datasets, results CSVs, or PDFs were modified. All 24 unit tests and 100% claim checks verified cleanly.
- **Decision 26 (Controlled Setup-Dominance Sensitivity Experiment Executed)**: Implemented non-destructive experiment `tools/run_rho_sensitivity.py` evaluating 4 representative base instances ($n \in \{30, 50\}$, asym/sym, $\alpha=0.3$) scaled by $\beta \in \{0.1, 0.5, 1.0, 2.0, 5.0\}$ ($\rho_s \in [0.06, 4.30]$), holding $p_j, r_j, s0_j$ invariant. Evaluated ALNS-WDP, SA, GA, MultiStart_LS across 30 seeds (2,400 runs) under matched budgets. Results saved to `results/sensitivity_rho.csv`, `results/sensitivity_rho_summary.csv`, `results/sensitivity_rho_statistical_tests.csv`, and `figures/fig8_sensitivity_rho.png`. Confirmed asymmetric dominance of ALNS-WDP (10/10 sweeps vs SA, Holm $p < 0.0001$, gap advantage expanding to $-16.78\%$ on $n=50$) and 2-opt competitiveness on symmetric setups (MultiStart_LS lowest gap across all $\beta$ on $n=30$).
- **Decision 27 (Manuscript Revisions & Bibliography Grounding)**: Updated `report/report.tex`, `docs/abstract.md`, `tools/make_tables.py`, and `tools/check_claims.py`. Populated Section 2 Related Work with verified citations (14 citations, 100% matching `\bibitem` entries, 0 invented references), formulated RQ1--RQ3 in Section 1, added complete validity proof for Theorem 2 (Dual Anchor Lower Bound), added Table 5 and Figure 8 in Section 6.2, and calibrated claims across limitations and conclusion. Abstract strictly $\le 250$ words (246 words). All 24 unit tests and 100% claim verification assertions pass cleanly.
- **Decision 28 (Dual Lower Bound Admissibility Correction & Empirical Recalculation)**: Discovered that adding an internal assignment setup term $C_{\text{AP}}(S_a)$ to the release-anchor bound is inadmissible for non-metric setup matrices because earlier-released jobs outside $S_a$ can interleave between subset jobs, bypassing internal transitions (demonstrated on 3-job counterexample makespan 4 vs bound 103). Replaced with valid processing-only release-date anchor $\max_{a \in V} (r_a + \sum_{k \in S_a} p_k)$ in `src/lower_bound.py`. Recomputed lower bounds across results CSVs via `tools/recalculate_lb_results.py`: LB changed on exactly 4 benchmark instances (`berlin52`: 770 -> 758, `n100_a30_sym`: 1239 -> 1236, `n10_a60_sym`: 124 -> 122, `n15_a60_asym`: 250 -> 246). New mean gap to LB across 20 benchmark instances is 5.47% for ALNS-WDP (SA 6.65%, GA 7.70%, MultiStart_LS 14.89%). Proven optimality gaps on small instances ($n \le 20$) are 100% identical and unchanged (MS-LS 0.27% < SA 0.40% < ALNS 0.45% < GA 1.97%). Added 2 unit regression tests in `tests/test_lower_bound.py`, expanding test suite to 26 tests (100% pass).
- **Decision 29 (Setup-Dominance Statistical Harmonization & Deliverable Audit)**: Defined exploratory ($m=3$) vs confirmatory global ($m=60$) Holm correction families for the 2,400-run setup-dominance experiment. Corrected `n30_a30_sym` $\beta=1.0$ narrative (MultiStart_LS won 28/30 runs, SA won 27/30 runs, global $p < 0.0001$). Reassessed `n50_a30_sym` $\beta=2.0$ vs SA: raw $p=0.0300$, exploratory $p=0.0300$, but global Holm $p=0.3295$ (fails significance). Documented MultiStart-LS timeout overrun (~6.6%) due to completing active 2-opt descent iterations, and integer rounding discretization effects (27.8%–42.4% zero-setup arcs at $\beta=0.1$). Recompiled `report/report.pdf` (1.78 MB) via `report/generate_pdf.py` with Table 5 and Figure 8. Authored `docs/PHASE5_CORRECTION_REPORT.md`. Extended `tools/check_claims.py` with 55 verification checks including PyMuPDF text checks (100% PASS).
- **Decision 30 (Final Minor Correction Pass & Total Project Freeze)**: Completed the final minor correction pass. (1) Enforced cumulative maximum monotonicity ($p^{\text{Holm}}_{(i)} = \max_{j \le i} \widetilde{p}_{(j)}$) for both exploratory ($m=3$) and global ($m=60$) Holm-Bonferroni corrections in `tools/run_rho_sensitivity.py` and `tools/recalculate_lb_results.py`. (2) Regenerated `results/sensitivity_rho_statistical_tests.csv` without rerunning optimization experiments. (3) Corrected effect-size terminology: renamed `cliff_delta` to `paired_win_loss_balance` ($(W-L)/(W+L)$). (4) Cleaned up outdated documentation and added validity warnings in `src/lower_bound.py`. (5) Standardized runtime budget statement to "within 6% (runtime parity within 1.058x)" across `report/generate_pdf.py`, `report/report.tex`, `docs/abstract.md`, `slides/generate_presentation.py`, and `report/report.pdf`. (6) Clarified reproduction instructions in `run_all.py` and `README.md`. (7) Extended `tools/check_claims.py` to 112 checks (100% PASS). (8) Verified all 26 unit tests pass in 14.59s. (9) Authored `docs/FINAL_VALIDATION_REPORT.md` and declared the complete project strictly FROZEN.

---

## Known Issues / Bugs
- *None. All 26 pytest unit tests pass cleanly (100% pass), and tools/check_claims.py returns 100% PASS.*

---

## Experiment Status
- Complete benchmark suite executed: 2,535 runs recorded across 20 benchmark instances ($n \in \{4, \dots, 200\}$) over 30 independent random seeds under strictly matched budgets.
- Controlled setup-dominance suite executed: 2,400 runs across 4 base instances x 5 beta levels x 4 methods x 30 seeds under matched nominal budgets.
- Results files saved in `results/`:
  - `results/single_objective_benchmarks.csv` (2,535 records, 0 duplicates; ALNS-WDP gap to valid LB 5.47%, runtime 1.39s, gap to opt 0.45%)
  - `results/summary_metrics.csv` (aggregated metrics per method and size)
  - `results/convergence_curves.csv` (411 points across search trajectories)
  - `results/ablation_results.csv` (600 records across 5 variants, 0 duplicates; Full gap 5.06%, FinalPolishOnly 5.03%)
  - `results/sensitivity_k.csv` (50 records for $k \in \{4, 6, 8, 10, 12\}$)
  - `results/strategy_placement.csv` (30 records across placement heuristics)
  - `results/pareto_fronts.csv` (non-dominated frontier solutions)
  - `results/biobjective_metrics.csv` (180 records with measured eval counts, HV and IGD)
  - `results/statistical_tests.csv` (paired Wilcoxon tests across all baselines)
  - `results/metaheuristic_statistical_tests.csv` (Holm-corrected Wilcoxon tests across metaheuristics with and without ties)
  - `results/friedman_ranks.csv` (Friedman ranking: $\chi^2 = 10.50, df = 3, p = 0.01476$, ALNS-WDP rank 1.975)
  - `results/ablation_statistical_tests.csv` (Holm-corrected tests for all comparisons and $n=100$ family)
  - `results/stratified_topology_comparison.csv` (asymmetric vs symmetric setup performance breakdown: Asym ALNS 4.38%, Sym ALNS 6.37%)
  - `results/biobjective_statistical_tests.csv` (paired Wilcoxon + Holm tests over 15 seeds per instance for HV and IGD)
  - `results/run_manifest.json` (hardware, packages, seeds, and budget plan)
  - `results/sensitivity_rho.csv` (2,400 runs across 4 base instances x 5 beta levels x 4 methods x 30 seeds)
  - `results/sensitivity_rho_summary.csv` (80 rows of summary statistics across configurations)
  - `results/sensitivity_rho_statistical_tests.csv` (60 paired Wilcoxon + Holm tests across beta levels with exploratory and global Holm p-values)
- High-resolution (300 DPI) publication figures saved in `figures/`:
  - `figures/fig1_scalability_runtime.png`
  - `figures/fig2_optimality_gaps.png`
  - `figures/fig3_convergence.png`
  - `figures/fig4_pareto_fronts.png`
  - `figures/fig5_ablation_study.png`
  - `figures/fig6_sensitivity_k.png`
  - `figures/fig7_sensitivity_alpha.png`
  - `figures/fig8_sensitivity_rho.png`
- Research Report: `report/report.pdf` (compiled publication-grade PDF, 1.78 MB) and `report/report.tex` (source LaTeX IEEEtran).
- Professional Presentation: `slides/presentation.pptx` (exactly 5 slides, 16:9 widescreen, native stratified table, all text $\ge 14$ pt, comprehensive speaker notes) and verified slide images in `slides/slide_images/*.png`.
- Claim Verification Script: `tools/check_claims.py` (executes in <2s, returns code 0, 100% PASS across 55 assertions).
- Unit Tests: `tests/` (26 passing tests via `python -m pytest tests/` in 14.47s).
- Comprehensive Audit Deliverables: `docs/PHASE5_CORRECTION_REPORT.md` and `docs/RESEARCH_STRENGTHENING_AUDIT.md`.
- Master reproduction command: `python run_all.py`

---

## Handoff Note
- **Project Status**: 100% Complete. All phases P1–P10 and R0–R7 are fully executed, verified, and audited.
- **Traceability**: Every numerical claim in `docs/abstract.md`, `report/report.tex`, `report/report.pdf`, `slides/presentation.pptx`, and `docs/VIVA_QA.md` matches `results/*.csv` with 0 mismatches.
- **Verification Command**: Run `python tools/check_claims.py` and `python -m pytest tests/` to confirm all assertions and unit tests pass cleanly.

