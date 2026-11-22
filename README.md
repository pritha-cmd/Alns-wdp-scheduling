# Single-Machine Scheduling under Sequence-Dependent Setups and Release Dates ($1 | r_j, s_{ij} | C_{\max}$)
## Course Project: Advanced Design and Analysis of Algorithms

[![Tests](https://img.shields.io/badge/pytest-26%20passed-brightgreen.svg)](#test-suite)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](#installation--environment)
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](#license)

---

## 1. Project Overview

This research project investigates single-machine scheduling under sequence-dependent setup times and release dates ($1 | r_j, s_{ij} | C_{\max}$) and its bi-objective extension minimizing makespan and Total Weighted Tardiness ($1 | r_j, s_{ij} | (C_{\max}, \sum w_j T_j)$).

### Core Theoretical Insights
1. **Base Problem Triviality (Practical Sheet Problem 4)**: The unconstrained base problem ($1 || C_{\max}$) with jobs $A=3, B=5, C=2, D=4$ is mathematically trivial. Because no idle time can occur between jobs, every permutation yields $C_{\max} \equiv \sum p_j = 14$ in $O(n)$ time. The problem belongs to $\mathbf{P}$.
2. **NP-Hard Generalization (Practical Sheet Problem 3 Mapping)**: Incorporating sequence-dependent setups $s_{ij}$ renders makespan minimization isomorphic to the Asymmetric Traveling Salesperson Problem (ATSP, Problem 3). Adding release dates $r_j$ induces machine idle time, generalizing TSP with Time Windows (TSPTW), which is strongly NP-hard.
3. **Proposed Algorithm (ALNS-WDP)**: An Adaptive Large Neighborhood Search combining four destroy operators, accelerated $O(n)$ incremental repair heuristics, a **sliding window Held-Karp dynamic programming polisher** ($k \in [6, 10]$) with proven monotonicity, and reinforcement-style bandit operator selection.

---

## 2. Repository Architecture

```text
├── data/                    # JSON benchmark problem instances (n in {4..200}, sym/asym, TSPLIB)
├── docs/                    # Theoretical and empirical documentation
│   ├── problem_analysis.md  # Complexity proofs, reductions, and Graham notation taxonomy
│   ├── novelty.md           # Algorithmic differentiation, what is borrowed vs novel
│   ├── AUDIT.md             # Experimental audit log and methodological corrections
│   ├── VIVA_QA.md           # 25 oral defense examination questions with grounded answers
│   ├── CHANGELOG.md         # Chronological development and test state log
│   └── abstract.md          # ~200-word academic abstract
├── figures/                 # High-resolution publication plots (300 DPI PNGs)
├── report/                  # Formal research paper
│   ├── report.tex           # Complete LaTeX manuscript
│   ├── generate_pdf.py      # Automated ReportLab PDF generator
│   └── report.pdf           # Compiled publication PDF (10-15 page equivalent)
├── results/                 # Raw experimental CSV logs, Pareto data, and run manifest
├── slides/                  # Professional presentation
│   ├── generate_presentation.py # Automated PowerPoint generator with real figures
│   └── presentation.pptx    # Exactly 5 slides with speaker notes
├── src/                     # Core algorithmic implementation
│   ├── alns/                # Proposed ALNS-WDP solver, operators, and window DP
│   ├── baselines/           # Exact DP (n<=20), CP-SAT, GA, SA, LS, Rules, NSGA-II
│   ├── evaluator.py         # O(n) schedule and incremental makespan evaluation
│   ├── experiments.py       # Unified benchmarking harness (30 seeds, time budgets)
│   ├── instances.py         # Deterministic benchmark instance generator
│   ├── lower_bound.py       # Tightened Hungarian Assignment + Anchor dual lower bound
│   ├── plots.py             # 300 DPI visualization suite
│   └── stats.py             # Wilcoxon + Holm-Bonferroni, Friedman rank, Nemenyi CD
├── tests/                   # Pytest verification and stress test suite (26 tests)
├── tools/                   # Validation and verification tooling
│   └── check_claims.py      # Automated audit script matching text claims to results/*.csv
├── AGENTS.md                # Multi-agent research coordination protocol
├── requirements.txt         # Pinned project dependencies
└── run_all.py               # Master end-to-end reproduction script
```

---

## 3. Installation & Environment Setup

### Prerequisites
- Python 3.10+ (tested on Python 3.12 64-bit)
- Windows / Linux / macOS

### Installation Steps
```bash
# Clone the repository
git clone <repo-url>
cd "Advance Algo project"

# Install dependencies
pip install -r requirements.txt
```

---

## 4. End-to-End Reproduction Procedure

The complete research campaign consists of core benchmarking, dual lower bound calculation, setup-time dominance scaling, and publication deliverable builds. **`run_all.py` alone does not execute every experiment.** Complete reproduction requires sequential execution of the following dedicated scripts:

```bash
# Step 1: Run core test suite, single-objective benchmarks, convergence, ablation, bi-objective, and stats
python run_all.py

# Step 2: Compute admissible processing-only dual lower bounds and refresh benchmark gaps and figures
python tools/recalculate_lb_results.py

# Step 3: Run the controlled setup-time dominance experiment (2,400 runs across 4 base instances x 5 betas x 4 methods x 30 seeds)
python tools/run_rho_sensitivity.py

# Step 4: Recompile the formal research report PDF (1.78 MB)
python report/generate_pdf.py

# Step 5: Regenerate the 5-slide professional presentation PPTX
python slides/generate_presentation.py

# Step 6: Verify 100% agreement between text claims, tables, slides, and raw results CSVs
python tools/check_claims.py
```

---

## 5. Running Individual Modules

### Run Full Pytest Regression Suite (26 tests)
```bash
python -m pytest tests/ -v
```

### Validate Abstract and Report Claims against CSV Logs
```bash
python tools/check_claims.py
```

### Execute Controlled Setup-Time Dominance Sensitivity Study
```bash
python tools/run_rho_sensitivity.py
```

### Recompile the Formal Research Report PDF
```bash
python report/generate_pdf.py
```

### Regenerate the 5-Slide Presentation PPTX
```bash
python slides/generate_presentation.py
```

---

## 6. Key Empirical Findings

1. **Tightness on Small Instances ($n \le 20$, 11 instances)**: ALNS-WDP achieves an average gap to proven global optimum of **0.45%** ($\pm 0.79\%$), finding provably optimal schedules in 100% of runs for $n \le 10$. On small instances, optimality gaps rank MultiStart_LS (0.27%) < SA (0.40%) < ALNS-WDP (0.45%) < GA (1.97%).
2. **Superiority over Classical Metaheuristics**: Across all 20 benchmark instances ($n \in [4, 200]$) over 30 seeds, ALNS-WDP attains a mean gap to valid dual lower bound of **5.47%** ($\pm 3.84\%$, runtime 1.39 s), outperforming SA (6.65%, 1.37 s), GA (7.70%, 1.37 s), and MultiStart_LS (14.89%, 1.42 s). Runtimes across metaheuristics are strictly matched within 6% (runtime ratio $\le 1.058\times$, maximum runtime overrun $\le 3.8\%$).
3. **Non-Parametric Statistical Significance**: Paired Wilcoxon signed-rank tests with Holm-Bonferroni correction confirm that ALNS-WDP significantly outperforms GA ($p = 0.0146$ all, $p = 0.0095$ excluding ties). Differences vs SA ($p = 0.1281$) and MultiStart_LS ($p = 0.1281$) fail to achieve statistical significance. The Friedman rank test across all four metaheuristics confirms overall significance ($\chi^2 = 10.50, df = 3, p = 0.01476$, ALNS-WDP rank 1.98 vs SA 2.38, MultiStart_LS 2.52, GA 3.12; Nemenyi $CD = 1.049$).
4. **Controlled Setup Dominance Sensitivity ($\rho_s \in [0.06, 4.30]$, 2,400 runs)**: ALNS-WDP sweeps 10/10 pairwise tests against SA, GA, MultiStart_LS on asymmetric setups (all global Holm $p < 0.0001$), expanding its advantage to $-16.78\%$ on $n=50$. On symmetric Euclidean setups, MultiStart_LS and SA outperform ALNS-WDP at moderate-to-high setup ratios; we formulate this as a plausible hypothesis (rather than a proven causal mechanism) that 2-opt segment reversals untangle symmetric Euclidean loops in $O(1)$ amortized time without altering internal symmetric transition costs ($s_{uv} = s_{vu}$), whereas ALNS remove-and-reinsert operators preserve subsequence orientation without explicit reversals.
5. **Component Ablation ($n=100$)**: Exact window DP polishing delivers statistically significant makespan reductions at $n=100$ ($p = 0.0086$ asym, $p = 0.0157$ sym vs No_WindowDP), while Full ALNS-WDP vs final-polish-only is not statistically distinguishable ($p = 1.000$). Adaptive weights showed no benefit over uniform weights ($p = 1.000$).
6. **Bi-Objective Scheduling**: Under strictly equal wall-clock budgets (~1.65 s), NSGA-II achieves higher Hypervolume on unconstrained instances (5/6 wins, all Holm $p \le 0.0018$), whereas scalarized ALNS-WDP achieves superior convergence and lower Inverted Generational Distance (IGD) on tight, asymmetric instances (3/6 wins, e.g. IGD 102.49 vs 399.85 on `n20_a30_sym`, Holm $p = 0.0018$).

---

## 7. License
Academic and research use under the MIT License.

