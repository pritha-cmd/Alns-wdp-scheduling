# Phase 5: Independent Mathematical and Experimental Correction Report

**Project**: Single-Machine Scheduling with Sequence-Dependent Setup Times and Release Dates ($1 \mid r_j, s_{ij} \mid C_{\max}$) and Bi-Objective Variant ($1 \mid r_j, s_{ij} \mid (C_{\max}, \sum w_j T_j)$)  
**Evaluated Hybrid Metaheuristic**: ALNS-WDP (Adaptive Large Neighborhood Search with Exact Window Dynamic Programming and Bandit Operator Selection)  
**Audit Phase**: Phase 5 — Mathematical Formulation Audit, Lower Bound Admissibility Correction, Empirical Results Recalculation, and Setup-Dominance Statistical Harmonization  
**Date**: November 2026  
**Status**: 100% Verified and Audited  

---

## Executive Summary

Phase 5 conducted an exhaustive, independent mathematical audit of the single-machine scheduling research repository, focusing on the theoretical validity of the dual lower bound formulation, exact recalculation of affected empirical gaps, statistical family definitions for the controlled setup-time dominance sensitivity study, and complete synchronization across all academic deliverables.

### Key Outcomes:
1. **Mathematical Lower Bound Correction**: Discovered that an internal subset assignment setup term $C_{\text{AP}}(S_a)$ previously added to the release-anchor bound is *inadmissible* (invalid) for arbitrary non-metric setup matrices because earlier-released jobs outside $S_a$ can interleave between subset jobs, bypassing internal transitions. Replaced with the valid processing-only release-anchor bound $\max_{a \in V} (r_a + \sum_{k \in S_a} p_k)$.
2. **Empirical Recalculation**: Across all 20 benchmark instances and 8 ablation instances, lower bounds were recomputed. Makespans, runtimes, and seed evaluations were 100% preserved. Lower bound values changed on exactly 4 benchmark instances (`derived_berlin52_n52_a30`: 770 $\to$ 758; `n100_a30_sym_s11004`: 1239 $\to$ 1236; `n10_a60_sym_s2007`: 124 $\to$ 122; `n15_a60_asym_s2506`: 250 $\to$ 246). The mean gap to LB for ALNS-WDP shifted from 5.20% to **5.47%** (SA: 6.65%, GA: 7.70%, MultiStart_LS: 14.89%). Proven optimality gaps on small instances ($n \le 20$) are 100% identical and unchanged (ALNS-WDP 0.45%, MultiStart_LS 0.27%, SA 0.40%, GA 1.97%).
3. **Statistical Dual-Family Calibration**: Defined exploratory ($m=3$ per configuration) versus confirmatory global ($m=60$) Holm-Bonferroni correction families for the controlled setup-dominance experiment (2,400 runs). Confirmed that ALNS-WDP dominates all 10/10 asymmetric settings ($p < 0.0001$). On symmetric settings, corrected win/tie/loss reporting on `n30_a30_sym` $\beta=1.0$ (MultiStart_LS won 28/30 runs, SA won 27/30 runs, $p < 0.0001$), and reassessed `n50_a30_sym` $\beta=2.0$ vs SA: raw $p=0.0300$, exploratory Holm $p=0.0435$, but global Holm $p=0.3295$ (fails statistical significance).
4. **Budget & Discretization Forensics**: Audited MultiStart-LS runtimes showing an average $+6.6\%$ overrun (0.96s vs 0.90s, 1.60s vs 1.50s) caused by un-preempted descent iterations. Documented integer rounding effects yielding 27.8%–42.4% zero-setup arcs at $\beta=0.1$ and 0% at $\beta \ge 1.0$.
5. **Full Artifact Synchronization**: Synchronized LaTeX report (`report/report.tex`), compiled publication-grade PDF (`report/report.pdf`, 1.78 MB), presentation slides (`slides/presentation.pptx`), academic abstract (`docs/abstract.md`, exactly 246 words $\le 250$), scientific novelty statement (`docs/novelty.md`), viva defense preparation (`docs/VIVA_QA.md`), and automated verification script (`tools/check_claims.py`, 100% PASS).

---

## 1. Audit and Mathematical Correction of the Dual Lower Bound

### 1.1 The Mathematical Formulation Under Audit
In scheduling under sequence-dependent setup times and release dates ($1 \mid r_j, s_{ij} \mid C_{\max}$), an admissible lower bound must satisfy $LB(I) \le C_{\max}^*(I)$ for all valid problem instances $I$.

The previous implementation in `src/lower_bound.py` combined three components:
$$LB_{\text{prior}} = \max\left( LB_{\text{AP}}, \; LB_{\text{heads}}, \; LB_{\text{subset\_AP}} \right)$$
where:
1. $LB_{\text{AP}} = \sum_{j=1}^n p_j + C_{\text{AP}}(V)$ is the Hungarian Linear Sum Assignment Problem relaxation on the augmented transition matrix (including depot 0).
2. $LB_{\text{heads}} = \max_{j=1}^n (r_j + p_j)$ is the single-job head bound.
3. $LB_{\text{subset\_AP}} = \max_{a \in V} \left( r_a + \sum_{k \in S_a} p_k + C_{\text{AP}}(S_a) \right)$ was intended as an anchor subset lower bound, where $S_a = \{k \in V \mid r_k \ge r_a\}$ is the subset of jobs released at or after anchor job $a$, and $C_{\text{AP}}(S_a)$ is the assignment cost on transitions restricted strictly to $S_a$.

### 1.2 Mathematical Proof of Inadmissibility: The Interleaving Counterexample
The assumption underlying $C_{\text{AP}}(S_a)$ is that jobs in $S_a$ must form a closed set of internal transitions, meaning they must transition directly into each other. **This assumption is false for arbitrary non-metric sequence-dependent setup matrices.**

#### Minimal Counterexample:
Consider an instance with $n = 3$ jobs $V = \{A, B, C\}$:
- Processing times: $p_A = 1, p_B = 1, p_C = 1$.
- Release dates: $r_A = 0, r_B = 1, r_C = 1$.
- Initial setups from depot: $s0_A = 0, s0_B = 0, s0_C = 0$.
- Inter-job transition setup matrix $s$:
  $$s = \begin{pmatrix} 0 & 0 & 0 \\ 0 & 0 & 100 \\ 0 & 100 & 0 \end{pmatrix}$$
  (Transitions between $B$ and $C$ incur a massive setup penalty of 100 in both directions; transitions to and from $A$ incur 0 setup).

#### Flawed Bound Evaluation:
Select anchor job $a = B$ (or $C$). The subset of jobs with $r_k \ge r_B = 1$ is $S_B = \{B, C\}$.
- Sum of processing times in $S_B$: $\sum_{k \in S_B} p_k = p_B + p_C = 1 + 1 = 2$.
- Internal assignment problem on $S_B$: Transitions within $\{B, C\}$ require $B \to C$ or $C \to B$, giving $C_{\text{AP}}(S_B) = 100$.
- The prior anchor subset formula computed:
  $$LB_{\text{subset\_AP}} = r_B + p_B + p_C + C_{\text{AP}}(S_B) = 1 + 2 + 100 = 103$$

#### True Feasible Schedule:
Evaluate the schedule permutation $\pi = [B, A, C]$:
1. Machine starts at $t=0$, initial setup $s0_B = 0$.
2. Job $B$ is released at $r_B = 1$. Processing begins at $S_B = \max(r_B, 0) = 1$.
3. Job $B$ finishes at $C_B = 1 + p_B = 1 + 1 = 2$.
4. Machine transitions to job $A$: setup $s_{BA} = 0$.
5. Job $A$ is released at $r_A = 0$. Start time $S_A = \max(0, 2 + 0) = 2$.
6. Job $A$ finishes at $C_A = 2 + p_A = 2 + 1 = 3$.
7. Machine transitions to job $C$: setup $s_{AC} = 0$.
8. Job $C$ is released at $r_C = 1$. Start time $S_C = \max(1, 3 + 0) = 3$.
9. Job $C$ finishes at $C_C = 3 + p_C = 3 + 1 = 4$.

Makespan of $\pi$:
$$C_{\max}(\pi) = 4$$
Since $C_{\max}^* \le 4$, but $LB_{\text{subset\_AP}} = 103$, the prior lower bound severely overestimated optimal makespan ($LB > C_{\max}^*$), violating the fundamental definition of a lower bound.

#### Underlying Cause:
Job $A$ belongs to $V \setminus S_B$ because $r_A = 0 < r_B = 1$. Schedule $\pi$ **interleaves** job $A$ between $B$ and $C$. By inserting an earlier-released job between the subset jobs, the schedule completely circumvents the expensive direct internal transition $B \to C$. Therefore, an internal assignment setup relaxation restricted to a release subset is invalid whenever interleaving is possible.

### 1.3 Corrected Mathematical Formulation (Theorem 2)
To guarantee admissibility under arbitrary setup structures, the subset assignment setup term is removed. The corrected dual lower bound is formulated as:

$$\boxed{LB = \max\left( \sum_{j=1}^n p_j + C_{\text{AP}}(V), \; \max_{j \in V} (r_j + p_j), \; \max_{a \in V} \left( r_a + \sum_{k \in S_a} p_k \right) \right)}$$

where:
- $V = \{1, \dots, n\}$ is the complete set of jobs.
- $C_{\text{AP}}(V)$ is the Hungarian assignment relaxation over the complete augmented graph $V \cup \{0\}$, which is valid because every job must appear exactly once in the global sequence.
- $\max_{j \in V} (r_j + p_j)$ enforces individual job availability.
- $S_a = \{k \in V \mid r_k \ge r_a\}$ is the set of jobs released at or after anchor $a$.

**Proof of Validity**:
1. For any feasible schedule $\pi$, total processing time is $\sum_{j=1}^n p_j$, and the sequence of setups forms a directed Hamiltonian path from depot 0. Since the assignment problem is a continuous relaxation of the Hamiltonian path problem, $\sum_{i=1}^n s_{\pi(i-1), \pi(i)} \ge C_{\text{AP}}(V)$. Hence $C_{\max}(\pi) \ge \sum p_j + C_{\text{AP}}(V)$.
2. For any job $j$, processing cannot begin before $r_j$, so $C_j(\pi) \ge r_j + p_j$. Thus $C_{\max}(\pi) \ge \max_j (r_j + p_j)$.
3. For any anchor job $a \in V$, all jobs in $S_a$ have release dates $r_k \ge r_a$. In any schedule $\pi$, let $k^* \in S_a$ be the last job among $S_a$ to be completed. None of the $|S_a|$ jobs can start processing before $r_a$. Because the machine is non-preemptive and can process at most one job at a time, the cumulative machine time dedicated to processing the jobs in $S_a$ after time $r_a$ is at least $\sum_{k \in S_a} p_k$. Therefore, the completion time of $k^*$ must satisfy $C_{k^*}(\pi) \ge r_a + \sum_{k \in S_a} p_k$. Since $C_{\max}(\pi) \ge C_{k^*}(\pi)$, the bound holds for all $a \in V$.
4. Taking the maximum of valid lower bounds yields an admissible lower bound: $LB \le C_{\max}^*$ for all instances. $\blacksquare$

### 1.4 Automated Regression Testing
In `tests/test_lower_bound.py`, two new explicit unit regression tests were added:
1. `test_lower_bound_interleaving_counterexample`: Instantiates the 3-job interleaving instance, asserts that $LB = 3 \le C_{\max}^* = 4$, and asserts that the returned bound does not exceed optimal makespan.
2. `test_lower_bound_non_metric_asymmetric_setups`: Tests non-metric setup matrices with extreme release dates, verifying that $LB \le C_{\max}^*$ against exact brute-force solutions.

---

## 2. Recalculation of Affected Empirical Results

To maintain absolute data integrity without re-running long-running stochastic benchmarks, `tools/recalculate_lb_results.py` was executed. The script recalculated the exact lower bound for every instance using the corrected formula, updated the `lb` and `gap_lb_pct` columns in all results CSVs, and left makespans, runtimes, and seeds 100% untouched.

### 2.1 Instances with Modified Lower Bounds
Across the 20 benchmark instances, the lower bound changed on **exactly 4 instances**:

| Instance Key | $n$ | Topology | $\alpha$ | Old LB | New LB | $\Delta$ LB | Dominating Bound Component |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `derived_berlin52_n52_a30` | 52 | Sym (TSPLIB) | 0.3 | 770 | **758** | -12 (-1.56%) | Global AP: $\sum p + C_{\text{AP}}$ |
| `n100_a30_sym_s11004` | 100 | Sym | 0.3 | 1239 | **1236** | -3 (-0.24%) | Global AP: $\sum p + C_{\text{AP}}$ |
| `n10_a60_sym_s2007` | 10 | Sym | 0.6 | 124 | **122** | -2 (-1.61%) | Processing Anchor: $\max_a (r_a + \sum p)$ |
| `n15_a60_asym_s2506` | 15 | Asym | 0.6 | 250 | **246** | -4 (-1.60%) | Processing Anchor: $\max_a (r_a + \sum p)$ |

On the remaining 16 benchmark instances and all 20 controlled setup-dominance configurations, the global assignment term $\sum p + C_{\text{AP}}(V)$ strictly dominated the release anchor term, resulting in identical lower bound values.

### 2.2 Impact on Benchmark Suite Results (`results/single_objective_benchmarks.csv`)
Recalculating lower bounds produced minor adjustments to the mean gap to lower bound across all 20 benchmark instances (2,535 total records):

| Algorithm | Old Mean Gap to LB (%) | **New Mean Gap to LB (%)** | $\Delta$ Gap (%) | Mean Makespan | Mean Runtime (s) | Friedman Rank |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **ALNS-WDP (Proposed)** | 5.20% | **5.47%** | +0.27% | 504.18 | 1.39 s | **1.98** |
| **Simulated Annealing (SA)** | 6.37% | **6.65%** | +0.28% | 522.62 | 1.37 s | 2.38 |
| **Genetic Algorithm (GA)** | 7.43% | **7.70%** | +0.27% | 522.20 | 1.37 s | 3.12 |
| **MultiStart Local Search** | 14.59% | **14.89%** | +0.30% | 630.85 | 1.42 s | 2.52 |

> **Critical Note on Gap to Optimum**:
> Proven optimality gaps on the 11 small instances ($n \le 20$, evaluated against exact Held-Karp DP) are **100% UNCHANGED**, because true mathematical optima $C_{\max}^*$ are independent of lower bounds:
> - MultiStart_LS: **0.27%** (Hit rate: 85.2%)
> - Simulated Annealing (SA): **0.40%** (Hit rate: 79.1%)
> - ALNS-WDP: **0.45%** (Hit rate: 67.9%)
> - Genetic Algorithm (GA): **1.97%** (Hit rate: 41.2%)

### 2.3 Impact on Component Ablation Results (`results/ablation_results.csv`)
Across 600 runs on 8 representative instances:

| Ablation Variant | Old Mean Gap to LB (%) | **New Mean Gap to LB (%)** | $\Delta$ Gap (%) | Mean Makespan | Mean Runtime (s) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `WindowDP_FinalPolishOnly` | 4.77% | **5.03%** | +0.26% | 559.93 | 1.09 s |
| `ALNS_WDP_Full` | 4.80% | **5.06%** | +0.26% | 559.51 | 1.20 s |
| `ALNS_No_AdaptWeights` | 4.87% | **5.13%** | +0.26% | 559.67 | 1.19 s |
| `Plain_ALNS` | 4.95% | **5.20%** | +0.25% | 561.91 | 1.18 s |
| `ALNS_No_WindowDP` | 5.05% | **5.31%** | +0.26% | 562.35 | 1.20 s |

### 2.4 Impact on Stratified Topology Comparison (`results/stratified_topology_comparison.csv`)

| Topology | Instances | Algorithm | Old Gap (%) | **New Gap (%)** | Mean Makespan | W / T / L vs ALNS | ALNS Improvement (%) |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| **Asymmetric** | 9 | **ALNS-WDP** | 4.18% | **4.38%** | 612.62 | -- | -- |
| | 9 | SA | 7.15% | **7.38%** | 653.84 | 6W / 2T / 1L | +2.69% |
| | 9 | GA | 8.87% | **9.15%** | 652.47 | 9W / 0T / 0L | +4.34% |
| | 9 | MultiStart_LS | 18.89% | **19.24%** | 830.72 | 6W / 2T / 1L | +10.12% |
| **Symmetric** | 11 | **ALNS-WDP** | 6.03% | **6.37%** | 415.45 | -- | -- |
| | 11 | SA | 5.73% | **6.06%** | 415.26 | 3W / 4T / 4L | -0.29% |
| | 11 | GA | 6.25% | **6.52%** | 415.62 | 6W / 3T / 2L | +0.13% |
| | 11 | MultiStart_LS | 11.08% | **11.32%** | 467.32 | 3W / 4T / 4L | +3.75% |

---

## 3. Statistical Correction for Setup-Dominance Sensitivity Study

In Stage 1 of Phase 5, a controlled setup-dominance experiment was executed using 4 base instances ($n \in \{30, 50\}$, asymmetric and symmetric, $\alpha=0.3$) scaled across $\beta \in \{0.1, 0.5, 1.0, 2.0, 5.0\}$ ($\rho_s \in [0.06, 4.30]$), generating 2,400 raw runs across 30 random seeds under matched nominal budgets.

### 3.1 Definition of Dual Hypothesis Families
To prevent statistical confusion, we explicitly defined two inferential families across the 60 pairwise Wilcoxon comparisons in `results/sensitivity_rho_statistical_tests.csv`:
1. **Exploratory Family ($m=3$ per configuration)**: Applies step-down Holm correction across the 3 competitor comparisons (ALNS vs GA, ALNS vs SA, ALNS vs MultiStart_LS) for each individual $(base, \beta)$ setting.
2. **Confirmatory Global Family ($m=60$ global)**: Applies a single step-down Holm-Bonferroni correction across all 60 comparisons conducted in the entire sensitivity study.

### 3.2 Correction on `n30_a30_sym` at $\beta=1.0$ (Win/Tie/Loss Correction)
An audit of raw makespans revealed an error in prior narrative reporting:
- On `n30_a30_sym` at $\beta=1.0$, MultiStart_LS achieved a mean makespan of 381.77 vs ALNS-WDP's 388.47.
- **True Record**: MultiStart_LS won **28 runs**, tied **1 run**, and lost **1 run** against ALNS-WDP (28W / 1T / 1L).
- **True Record vs SA**: SA achieved a mean makespan of 383.67, winning **27 runs**, tying **0 runs**, and losing **3 runs** against ALNS-WDP (27W / 0T / 3L).
- Under both exploratory ($m=3$) and global ($m=60$) Holm corrections, both competitors are statistically significantly superior to ALNS-WDP on this configuration ($p < 0.0001$).
- **Correction Applied**: Updated `docs/RESEARCH_STRENGTHENING_AUDIT.md`, `report/report.tex`, `report/generate_pdf.py`, and `docs/VIVA_QA.md` to reflect these exact numbers.

### 3.3 Reassessment of Large Symmetric Setting (`n50_a30_sym` at $\beta=2.0$)
On `n50_a30_sym` at $\beta=2.0$ ($\rho_s = 1.32$):
- ALNS-WDP mean makespan: 569.17.
- SA mean makespan: 564.00 (SA won 20 runs, tied 2, lost 8).
- Raw Wilcoxon p-value: $p = 0.0300$ ($0.02995$).
- **Under Exploratory Family ($m=3$)**: SA was ranked 2nd among tests with non-zero differences behind GA ($p = 0.02174 \times 2 = 0.0435$); taking the cumulative maximum of ordered adjusted p-values yields $\text{exploratory\_holm\_p} = \max(0.0435, 0.02995 \times 1) = \mathbf{0.0435}$.
- **Under Confirmatory Global Family ($m=60$)**: Because 60 comparisons are evaluated simultaneously, taking the cumulative maximum across all tests yields:
  $$\text{global\_holm\_p} = \mathbf{0.3295}$$
- **Conclusion**: Under the rigorous confirmatory standard, SA's advantage on `n50_a30_sym` at $\beta=2.0$ **fails to achieve statistical significance** ($p = 0.3295 > 0.05$). Thus, on large symmetric instances, the performance difference between ALNS-WDP and SA remains statistically inconclusive.

### 3.4 Summary of Setup-Dominance Sensitivity Results
Table below summarizes the 20 configurations evaluated across 30 seeds per cell:

| Base Instance | $\beta$ | $\rho_s$ | ALNS-WDP Gap (%) | SA Gap (%) | GA Gap (%) | MS-LS Gap (%) | ALNS Dominance vs Competitors |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **`n30_a30_asym`** | 0.1 | 0.07 | **0.65%** | 1.06% | 1.48% | 0.91% | ALNS sweeps 3/3 (global $p < 0.0001$) |
| | 0.5 | 0.40 | **3.26%** | 7.34% | 10.20% | 8.15% | ALNS sweeps 3/3 (global $p < 0.0001$) |
| | 1.0 | 0.79 | **4.51%** | 9.74% | 13.26% | 9.79% | ALNS sweeps 3/3 (global $p < 0.0001$) |
| | 2.0 | 1.58 | **7.52%** | 14.55% | 20.81% | 19.42% | ALNS sweeps 3/3 (global $p < 0.0001$) |
| | 5.0 | 3.96 | **13.49%** | 23.49% | 30.01% | 34.55% | ALNS sweeps 3/3 (global $p < 0.0001$) |
| **`n30_a30_sym`** | 0.1 | 0.06 | 1.36% | 1.53% | 1.75% | **1.31%** | MS-LS lowest gap |
| | 0.5 | 0.30 | 3.92% | 3.77% | 4.74% | **3.30%** | MS-LS lowest gap |
| | 1.0 | 0.60 | 6.87% | 5.64% | 7.49% | **5.21%** | MS-LS lowest gap (MS-LS won 28/30) |
| | 2.0 | 1.21 | 7.91% | 8.05% | 10.08% | **7.44%** | MS-LS lowest gap |
| | 5.0 | 3.02 | 11.72% | 11.50% | 14.41% | **11.22%** | MS-LS lowest gap |
| **`n50_a30_asym`** | 0.1 | 0.08 | **0.76%** | 1.17% | 1.13% | 4.20% | ALNS sweeps 3/3 (global $p < 0.0001$) |
| | 0.5 | 0.43 | **5.90%** | 10.94% | 10.96% | 24.81% | ALNS sweeps 3/3 (global $p < 0.0001$) |
| | 1.0 | 0.86 | **7.46%** | 13.25% | 15.21% | 37.31% | ALNS sweeps 3/3 (global $p < 0.0001$) |
| | 2.0 | 1.72 | **9.22%** | 21.96% | 24.54% | 65.17% | ALNS sweeps 3/3 (global $p < 0.0001$) |
| | 5.0 | 4.30 | **12.87%** | 35.63% | 43.18% | 118.30% | ALNS sweeps 3/3 (global $p < 0.0001$) |
| **`n50_a30_sym`** | 0.1 | 0.06 | **0.62%** | 1.10% | 1.01% | 1.66% | ALNS lowest gap |
| | 0.5 | 0.33 | 6.08% | 5.99% | **5.74%** | 12.62% | GA lowest gap |
| | 1.0 | 0.66 | 7.95% | **7.33%** | 9.00% | 19.94% | SA lowest gap |
| | 2.0 | 1.32 | 10.80% | **9.79%** | 11.77% | 29.07% | SA lowest gap (global $p = 0.3295$, non-sig) |
| | 5.0 | 3.29 | 15.34% | **14.97%** | 16.41% | 36.51% | SA lowest gap |

---

## 4. Computational Budget and Scaling Discretization Forensics

### 4.1 MultiStart-LS Timeout Overrun Forensics
An audit of all 2,400 runtimes in `results/sensitivity_rho.csv` revealed a systematic runtime deviation:
- Nominal time limit for $n=30$: $t_{\text{limit}} = \max(0.75, 0.03 \times 30) = 0.90$ s.
  - ALNS-WDP: $0.887 \pm 0.010$ s
  - SA: $0.901 \pm 0.003$ s
  - GA: $0.901 \pm 0.004$ s
  - **MultiStart_LS**: $\mathbf{0.957 \pm 0.021}$ s (**+6.3% overrun**)
- Nominal time limit for $n=50$: $t_{\text{limit}} = \max(0.75, 0.03 \times 50) = 1.50$ s.
  - ALNS-WDP: $1.479 \pm 0.015$ s
  - SA: $1.501 \pm 0.005$ s
  - GA: $1.502 \pm 0.007$ s
  - **MultiStart_LS**: $\mathbf{1.600 \pm 0.031}$ s (**+6.7% overrun**)

**Forensic Cause**:
In `src/baselines/local_search.py`, the continuous multi-start loop executes:
```python
while time.perf_counter() - start_time < time_limit:
  current = random_permutation()
  current = two_opt_descent(current)  # Executes full 2-opt descent
```
The deadline check occurs only *between* multi-start restarts. Once a 2-opt local search descent begins, it evaluates candidate moves until reaching a local minimum without mid-descent interruption. On $n=50$, a single 2-opt descent can take 80–120 ms. If a descent begins at $t = 1.48$ s, it runs to completion, terminating at $t \approx 1.60$ s.

**Mitigation & Documentation**:
Because MultiStart_LS already overran its nominal budget by ~6.6%, its competitive advantage on symmetric instances cannot be attributed to budget starvation. This overrun has been formally documented in all reports.

### 4.2 Integer Rounding Discretization and Zero-Setup Arcs
To preserve integer data types ($s_{ij} \in \mathbb{Z}^+$), scaled setups were computed via nearest-integer rounding: $s'_{ij} = \lfloor \beta \cdot s_{ij} \rceil$.

Analysis of the resulting setup matrices revealed a discretization artifact at low scaling factors:
- At $\beta = 0.1$:
  - Original setups $s_{ij} \in [1, 4]$ round to $\lfloor 0.1 \times s_{ij} \rceil = 0$.
  - In `n30_a30_asym`, exactly **27.8%** of directed arcs became $0$.
  - In `n50_a30_sym`, exactly **42.4%** of directed arcs became $0$.
- At $\beta \ge 1.0$:
  - Zero-setup arcs: **0.0%**.

**Consequence**: At $\beta = 0.1$, the problem landscape features numerous zero-cost transitions, clustering jobs into zero-penalty equivalence classes. As $\beta \ge 1.0$, setups are strictly positive, and topological differentiation expands.

---

## 5. Documentation Synchronization Inventory

Every academic file in the repository was audited and updated to ensure 100% agreement with `results/*.csv`:

| File Path | Description of Updates Applied |
| :--- | :--- |
| `docs/abstract.md` | Abstract condensed to exactly 246 words ($\le 250$). Updated mean gap to LB (5.47%), competitor gaps (SA 6.65%, GA 7.70%, MS-LS 14.89%), small-instance optimum order (MS-LS 0.27% < SA 0.40% < ALNS 0.45% < GA 1.97%), ablation results ($n=100$ Holm $p < 0.05$), and bi-objective significance counts (lower IGD on 3/6, Holm-significant on 1/6; NSGA-II higher HV on 5/6, Holm-significant on 5/6). |
| `report/report.tex` | IEEEtran journal manuscript updated. Formulated RQ1–RQ3 in Section 1; populated Section 2 with 14 verified literature citations (0 unverified entries); replaced subset setup bound with Theorem 2 processing-only release anchor bound and documented the interleaving counterexample; embedded Table 5 and Figure 8; calibrated claims across limitations and conclusion. |
| `report/generate_pdf.py` | Added Section 5.2 (Controlled Setup-Time Dominance Study) with Table 5 and Figure 8; updated Theorem 2 explanation; updated limitations numbers (179.6 vs 177.0, 275.1 vs 274.0, 485.7 vs 479.5/480.7); updated traceability matrix with setup dominance CSVs. |
| `report/report.pdf` | Recompiled via `report/generate_pdf.py` (ReportLab). Output file size: 1.78 MB. Verified via PyMuPDF text extraction to contain "5.47%", "Figure 8", and "ALNS-WDP". |
| `slides/generate_presentation.py` & `slides/presentation.pptx` | 5-slide professional presentation (16:9 widescreen, all text $\ge 14$ pt). Updated Slide 4 table and metrics to 5.47%. Verified all speaker notes present. |
| `docs/novelty.md` | Corrected Theorem 2 to processing-only anchor bound; documented the interleaving counterexample; updated summary table; updated empirical gap to 5.47%; added setup dominance findings. |
| `docs/VIVA_QA.md` | Rewrote Q4 with the processing-only release anchor lower bound and the interleaving counterexample; updated Q18 ablation metrics (Full 5.06%, Plain 5.20%, etc.); updated Q20 failure analysis with corrected loss numbers and setup-dominance findings; updated Q23 test count to 26. |
| `docs/RESEARCH_STRENGTHENING_AUDIT.md` | Updated Section 3.1.3 to mark setup-dominance experiment as executed; recorded findings, dual Holm families, MultiStart-LS overrun, and discretization percentages; updated Section 4.1 test count to 26. |
| `docs/CHANGELOG.md` | Chronologically logged all Phase 5 modifications, mathematical corrections, test expansions, and verification results. |
| `tools/check_claims.py` | Extended claim verification script with Phase 5 assertions: 2,400 sensitivity rows, 4 base instances, 5 betas, 80 summary rows, 60 statistical tests, dual Holm p-values, $\rho_s$ interval, MultiStart-LS timeout overrun, and PyMuPDF text extraction from `report/report.pdf`. |

---

## 6. Verification and Regression Testing

### 6.1 Pytest Test Suite Execution
Executing `python -m pytest tests/ -q` executes 26 unit tests covering schedule evaluation, lower bound admissibility, dynamic programming exactness, window DP monotonicity, and budget enforcement:

```
..........................                                               [100%]
26 passed in 14.47s
```

### 6.2 Automated Claim Verification Script (`tools/check_claims.py`)
Executing `python tools/check_claims.py` performs 55 rigorous verification assertions across all CSVs, figures, docs, LaTeX sources, PDFs, and presentations:

```
===========================================================================
RUNNING AUTOMATED CLAIM VERIFICATION (tools/check_claims.py)
===========================================================================

--- 1. File Artifacts Verification ---
  [PASS] File exists: single_objective_benchmarks.csv     (272538 bytes)
  [PASS] File exists: summary_metrics.csv                 (26654 bytes)
  [PASS] File exists: convergence_curves.csv              (21249 bytes)
  [PASS] File exists: ablation_results.csv                (50635 bytes)
  [PASS] File exists: sensitivity_k.csv                   (3932 bytes)
  [PASS] File exists: biobjective_metrics.csv             (18194 bytes)
  [PASS] File exists: biobjective_statistical_tests.csv   (1687 bytes)
  [PASS] File exists: stratified_topology_comparison.csv  (672 bytes)
  [PASS] File exists: statistical_tests.csv               (2084 bytes)
  [PASS] File exists: metaheuristic_statistical_tests.csv (530 bytes)
  [PASS] File exists: friedman_ranks.csv                  (404 bytes)
  [PASS] File exists: ablation_statistical_tests.csv      (5135 bytes)
  [PASS] File exists: run_manifest.json                   (3085 bytes)
  [PASS] File exists: sensitivity_rho.csv                 (221260 bytes)
  [PASS] File exists: sensitivity_rho_summary.csv         (8088 bytes)
  [PASS] File exists: sensitivity_rho_statistical_tests.csv (7664 bytes)
  [PASS] Figure exists: fig1_scalability_runtime.png      (163693 bytes)
  [PASS] Figure exists: fig2_optimality_gaps.png          (181086 bytes)
  [PASS] Figure exists: fig3_convergence.png              (113061 bytes)
  [PASS] Figure exists: fig4_pareto_fronts.png            (114404 bytes)
  [PASS] Figure exists: fig5_ablation_study.png           (120468 bytes)
  [PASS] Figure exists: fig6_sensitivity_k.png            (172393 bytes)
  [PASS] Figure exists: fig7_sensitivity_alpha.png        (88907 bytes)
  [PASS] Figure exists: fig8_sensitivity_rho.png          (583271 bytes)
  [PASS] Documentation exists: abstract.md                (1673 bytes)
  [PASS] Documentation exists: problem_analysis.md        (16681 bytes)
  [PASS] Documentation exists: novelty.md                 (9646 bytes)
  [PASS] Documentation exists: AUDIT.md                   (10319 bytes)
  [PASS] Documentation exists: VIVA_QA.md                 (32628 bytes)
  [PASS] Documentation exists: window_dp_correctness.md   (6409 bytes)
  [PASS] Documentation exists: CHANGELOG.md               (34804 bytes)
  [PASS] Documentation exists: README.md                  (7372 bytes)

--- 2. Benchmark CSV Data Integrity ---
  [PASS] Single-objective row uniqueness                  Found 0 duplicate rows
  [PASS] Instance diversity count == 20                   20 instances loaded
  [PASS] Setup topology diversity                         Topologies: ['sym', 'asym']
  [PASS] Release date alpha diversity (0, 0.3, 0.6)       Alphas: [0.0, 0.3, 0.6]
  [PASS] Seed count for ALNS_WDP == 30                    Min seeds/instance: 30
  [PASS] Seed count for GA == 30                          Min seeds/instance: 30
  [PASS] Seed count for SA == 30                          Min seeds/instance: 30
  [PASS] Seed count for MultiStart_LS == 30               Min seeds/instance: 30
  [PASS] Ablation row uniqueness                          Found 0 duplicates across 600 rows
  [PASS] Ablation row count == 600                        Rows: 600
  [PASS] Ablation variants match exact 5 valid configs    Variants verified
  [PASS] Ablation max runtime ratio <= 1.15x FinalPolish  Max ratio: 1.149x
  [PASS] Ablation average runtime ratio ~ 1.097x          Mean ratio: 1.096x
  [PASS] Stratified comparison has 8 rows                 Found 8 rows
  [PASS] Stratified asymmetric ALNS-WDP gap ~ 4.38%       Found: 4.38%
  [PASS] Stratified symmetric ALNS-WDP gap ~ 6.37%        Found: 6.37%
  [PASS] Bi-objective statistical tests has 12 rows       Found 12 rows
  [PASS] Setup dominance sensitivity rows == 2400         Found 2400 rows
  [PASS] Setup dominance sensitivity row uniqueness       Found 0 duplicate rows
  [PASS] Setup dominance base instances == 4              Found 4 base instances
  [PASS] Setup dominance beta levels == 5                 Found 5 beta levels
  [PASS] Setup dominance min seeds per cell == 30         Min seeds: 30
  [PASS] MultiStart_LS runtime n=30 overrun ~6.6%         Found: 0.957s
  [PASS] MultiStart_LS runtime n=50 overrun ~6.6%         Found: 1.600s
  [PASS] Setup dominance summary rows == 80               Found 80 rows
  [PASS] Setup ratio rho_s spans [0.06, 4.30]             Range: [0.0574, 4.2953]
  [PASS] Setup dominance statistical tests == 60          Found 60 rows
  [PASS] Setup dominance has exploratory & global Holm    Verified dual families
  [PASS] n30_a30_sym beta=1.0 MultiStart_LS wins 28/30    Wins: 28
  [PASS] n50_a30_sym beta=2.0 SA raw p = 0.0300           Found: 0.0300
  [PASS] n50_a30_sym beta=2.0 SA global Holm p = 0.3295   Found: 0.3295

--- 3. Ground Truth Metrics Calculation ---
  Ground Truth: ALNS_WDP Mean Gap to LB = 5.47% (+/- 3.84%)
  Ground Truth: ALNS_WDP Mean Gap to Opt (n<=20) = 0.45%
  Ground Truth: ALNS_WDP Mean Runtime = 1.39 s
  Ground Truth: SA Mean Gap to LB = 6.65%
  Ground Truth: GA Mean Gap to LB = 7.70%
  Ground Truth: MultiStart_LS Mean Gap to LB = 14.89%
  Ground Truth: Metaheuristic Statistical Tests (3 comparisons)
    - vs GA             : Holm p = 1.4560e-02 (all), 9.4757e-03 (no ties)
    - vs SA             : Holm p = 1.2808e-01 (all), 1.2808e-01 (no ties)
    - vs MultiStart_LS  : Holm p = 1.2808e-01 (all), 1.2808e-01 (no ties)

--- 4. Cross-Verification with docs/abstract.md ---
  [PASS] Abstract instance count matches CSV (20)         Claimed: 20, Actual: 20
  [PASS] Abstract seeds count matches (30)                Claimed: 30
  [PASS] Abstract Mean Gap to LB matches CSV (tol 0.15%)  Claimed: 5.47%, Actual: 5.47%
  [PASS] Abstract Mean Gap to Opt matches CSV (tol 0.15%) Claimed: 0.45%, Actual: 0.45%

--- 5. Cross-Verification with report/report.tex ---
  [PASS] report.tex instance count matches CSV (20)       Claimed: 20, Actual: 20
  [PASS] report.tex stochastic seeds matches (30)         Claimed: 30
  [PASS] report.tex Gap to LB matches CSV (tol 0.15%)     Claimed: 5.47%, Actual: 5.47%
  [PASS] report.tex tab:small_instances contains all 11   Verified 11 instances
  [PASS] report.tex tab:small_instances average row       0.45% / 67.9% | 0.27% / 85.2% | 0.40% / 79.1%
  [PASS] report/report.pdf compiled and >500KB            Size: 1785334 bytes
  [PASS] report.pdf text contains '5.47%'                 Found '5.47%'
  [PASS] report.pdf text contains 'Figure 8'              Found 'Figure 8'
  [PASS] report.pdf text contains 'ALNS-WDP'              Found 'ALNS-WDP'

--- 6. Verification of slides/presentation.pptx ---
  [PASS] slides/presentation.pptx exists and >50KB        Size: 388524 bytes
  [PASS] slides count == exactly 5                        Slide count: 5
  [PASS] All 5 slides have comprehensive speaker notes    Verified
  [PASS] Slide 4 cites exact ALNS-WDP gap to LB (5.47%)   Found: 5.47%
  [PASS] Slide 4 cites exact gap to opt (0.45%)           Found: 0.45%
  [PASS] Slide 4 table dimensions == 9x6                  9x6
  [PASS] Slide 4 table data matches CSV                   All 8 data rows verified

--- 7. Documentation Integrity & Fabricated Variants Audit ---
  [PASS] VIVA_QA.md free of fabricated variants           Clean
  [PASS] VIVA_QA.md free of stale metrics                 Clean
  [PASS] VIVA_QA.md does not cite stale ALNS-WDP 5.20%    Clean
  [PASS] novelty.md free of fabricated variants           Clean
  [PASS] novelty.md free of stale metrics                 Clean
  [PASS] novelty.md does not cite stale ALNS-WDP 5.20%    Clean
  [PASS] problem_analysis.md free of fabricated variants  Clean
  [PASS] problem_analysis.md free of stale metrics        Clean
  [PASS] problem_analysis.md does not cite stale 5.20%    Clean
  [PASS] window_dp_correctness.md free of variants        Clean
  [PASS] window_dp_correctness.md free of stale metrics   Clean
  [PASS] window_dp_correctness.md does not cite 5.20%     Clean
  [PASS] docs/VIVA_QA.md documents all 5 real variants    Verified
  [PASS] docs/VIVA_QA.md does not claim false O(n log n)  Verified
  [PASS] All documentation free of 'Q-learning'           Replaced with bandit / exponential moving-average

===========================================================================
ALL CLAIM VERIFICATION CHECKS PASSED SUCCESSFULLY! (100% PASS)
===========================================================================
```

---

## 7. Remaining Honest Scientific Limitations

1. **Window-DP Makespan Specialization in Bi-Objective Search**:
   While ALNS-WDP optimizes the composite scalarized objective $\lambda C_{\max} + (1-\lambda) \text{TWT}$ during destroy-and-repair transitions, its exact sliding-window Held-Karp polisher is mathematically formulated strictly for makespan ($C_{\max}$) minimization. NSGA-II evaluates Pareto dominance directly over the bi-objective space $(C_{\max}, \sum w_j T_j)$, which explains why NSGA-II achieved statistically significantly higher Hypervolume on 5/6 instances (Holm $p \le 0.0018$). ALNS-WDP's strength lies in intense makespan compression, as evidenced by its significantly lower Inverted Generational Distance (IGD) on `n20_a30_sym` (102.49 vs 399.85, Holm $p = 0.0018$).
2. **2-Opt Segment Reversal Advantage on Symmetric Euclidean Landscapes**:
   On symmetric setup matrices satisfying the triangle inequality, MultiStart Local Search and Simulated Annealing remain highly competitive and occasionally outperform ALNS-WDP (e.g. on `n30_a30_sym` at $\beta=1.0$, MultiStart_LS won 28/30 runs). In symmetric topologies ($s_{uv} = s_{vu}$), reversing an entire subsegment $\pi(i \dots j) \to \pi(j \dots i)$ untangles Euclidean crossings without modifying internal transition costs. Standard ALNS destroy-and-repair heuristics remove and reinsert jobs sequentially, preserving subsequence orientation and requiring multiple coordinated moves to reverse a tour segment.
3. **Small-Instance Heuristic Redundancy ($n \le 8$)**:
   For instances with $n \le 8$, exact solvers (OR-Tools CP-SAT and Held-Karp bitmask DP) prove optimality in under 15 milliseconds. Applying a stochastic hybrid metaheuristic with destroy-repair loops and sliding-window DP on instances of this size introduces unnecessary computational overhead.
4. **Single Instance at $n=200$**:
   Due to computational budget constraints, the scalability benchmark at $n=200$ was evaluated on a single representative instance (`n200_a30_asym_s21003`). While multi-instance distributions were tested for $n \in \{4, \dots, 100\}$, broader empirical generalization to $n=200$ across diverse arrival topologies requires caution.
5. **Absence of Adaptive Weight Significance**:
   While the discounted exponential moving average bandit update dynamically concentrates selection probabilities on high-performing operators, the component ablation across 600 runs showed no statistically significant performance difference over static uniform weights ($p = 1.000$). Adaptive weighting functions as an exploratory mechanism rather than a confirmed driver of solution quality.

