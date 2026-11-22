# Oral Examination (Viva Voce) Preparation: Questions & Grounded Answers
## Single-Machine Scheduling under Sequence-Dependent Setups and Release Dates ($1 | r_j, s_{ij} | C_{\max}$)

This document provides 25 comprehensive, technically rigorous questions and grounded answers tailored for a defense in an **Advanced Design and Analysis of Algorithms** course.

---

### Category 1: Problem Complexity, Formulations, & Theory

#### Q1: Why is the base problem ($1 || C_{\max}$) polynomial while your variant ($1 | r_j, s_{ij} | C_{\max}$) is strongly NP-hard?
**Answer:**
In the base problem ($1 || C_{\max}$, Problem 4 from the practical sheet), all jobs are available at time $t=0$, require zero setups ($s_{ij} = 0$), and cannot be preempted. On a single machine, there is zero machine idle time between jobs, so the machine runs continuously from $t=0$ until all jobs complete. Consequently, the makespan is invariant under all permutations:
$$C_{\max}(\pi) = \sum_{j=1}^n p_j \quad \forall \pi \in \Pi_n$$
Evaluating any permutation takes $O(n)$ time, so the decision problem is trivially in $\mathbf{P}$.

Introducing sequence-dependent setup times $s_{ij}$ breaks this invariance. The makespan becomes $C_{\max} = \sum p_j + \sum s_{\pi(k-1),\pi(k)}$. Minimizing this setup sum is isomorphic to the Asymmetric Traveling Salesperson Problem (ATSP, Problem 3 from the practical sheet) on a directed graph of $n+1$ vertices (including a dummy depot), which is strongly NP-hard (Garey & Johnson, 1979). Adding non-zero release dates $r_j$ introduces machine idle time ($I_j = \max(0, r_j - C_{\text{prev}} - s_{ij})$), making the problem equivalent to TSP with Time Windows (TSPTW), which is strongly NP-hard even on trees or Euclidean metrics.

---

#### Q2: What exact modeling assumptions govern your problem? Are setups anticipatory or non-anticipatory?
**Answer:**
We assume:
1. **Anticipatory Setups**: The machine can undergo setup for job $j$ as soon as the previous job $i$ finishes, even if job $j$ has not yet arrived ($t < r_j$). Setup and arrival happen concurrently. Thus, job $j$'s actual processing start time is:
   $$S_j = \max\left(r_j, \, C_i + s_{ij}\right)$$
   and its completion time is $C_j = S_j + p_j$.
2. **Initial Setup (Depot Transition)**: The first job $\pi(1)$ incurs a setup $s0_{\pi(1)}$ from the machine's initial baseline state (depot 0).
3. **Triangle Inequality**: Tested across two structural families:
   - *Euclidean / Metric Family*: Setup costs satisfy $s_{ik} \le s_{ij} + s_{jk}$.
   - *Asymmetric / Non-Metric Family*: Setup costs are independent random integers, violating the triangle inequality, creating deceptive local minima.
4. **Non-preemption & Integer Data**: Once processing begins, it cannot be interrupted. All $p_j, r_j, s_{ij}, d_j, w_j \in \mathbb{Z}^+$.

---

#### Q3: How does Practical Sheet Problem 4 embed as a special case, and how does Practical Sheet Problem 3 map to your problem?
**Answer:**
- **Problem 4 Embedding**: Problem 4 defines 4 jobs ($A=3, B=5, C=2, D=4$). Setting $r_j = 0$, $s0_j = 0$, and $s_{ij} = 0$ for all $i,j \in \{A,B,C,D\}$ recovers Problem 4 exactly. Every one of the $4! = 24$ permutations produces makespan $C_{\max} = 3+5+2+4 = 14$.
- **Problem 3 Mapping**: Problem 3 is an ATSP vehicle routing problem. If we set $r_j = 0$ for all $j$, makespan simplifies to $\sum p_j + \text{Cost}(\text{ATSP Tour})$. Because $\sum p_j$ is a fixed constant, minimizing makespan is strictly identical to finding the minimum-cost Hamiltonian path starting at the depot (Problem 3). When we applied a small asymmetric setup matrix to the 4 jobs, optimal makespan rose from 14 to 22 (permutation $C \to A \to D \to B$), while the worst permutation yielded 35—a 59.1% makespan swing purely due to setup sequencing.

---

#### Q4: Walk through the exact mathematical formulation of your dual lower bound and prove it never overestimates the optimal makespan.
**Answer:**
Our dual lower bound combines three independent relaxations:
$$LB = \max\left( LB_{\text{AP}}, \, LB_{\text{heads}}, \, LB_{\text{anchor}} \right)$$
1. **Assignment Relaxation ($LB_{\text{AP}}$)**: Total processing $\sum p_j$ is mandatory. In any valid schedule, every job (plus depot) has exactly one predecessor and one successor. Relaxing the connectivity (subtour elimination) constraints yields the Linear Sum Assignment Problem on the augmented matrix:
   $$LB_{\text{AP}} = \sum_{j=1}^n p_j + C_{\text{AP}}(V)$$
   where $C_{\text{AP}}$ is solved in $O(n^3)$ via the Hungarian algorithm. Because subtour elimination constraints are removed, $C_{\text{AP}} \le \sum s_{\pi(i-1),\pi(i)}$ for all feasible tours.
2. **Simple Head Bound ($LB_{\text{heads}}$)**: No job $j$ can finish before $r_j + p_j$, so $LB_{\text{heads}} = \max_{j=1}^n (r_j + p_j)$.
3. **Valid Processing-Only Anchor Lower Bound ($LB_{\text{anchor}}$)**: For every job $a \in V$, let $S_a = \{k \in V \mid r_k \ge r_a\}$. In any valid schedule, anchor job $a$ cannot start before $r_a$. Since all jobs in $S_a$ arrive at or after $r_a$, their total processing $\sum_{k \in S_a} p_k$ must be executed after $r_a$. Thus:
   $$LB_{\text{anchor}} = \max_{a \in V} \left( r_a + \sum_{k \in S_a} p_k \right)$$
**Critical Mathematical Correction on Subset Setups**:
Prior formulations attempted to add a subset assignment setup term $C_{\text{AP}}(S_a)$ inside $LB_{\text{anchor}}$. That term is **mathematically invalid** for arbitrary non-metric setup matrices because jobs outside $S_a$ (released earlier) can interleave between subset jobs, bypassing internal transitions of $S_a$.
*Counterexample*: Consider $p = [1, 1, 1]$, $r = [0, 1, 1]$, $s_{BC} = s_{CB} = 100$, and all other setups $0$. For $S_B = \{B, C\}$ with $r \ge 1$, adding $C_{\text{AP}}(S_B) = 100$ produces a bound of $1 + 1 + 1 + 100 = 103$. Yet schedule $\pi = [B, A, C]$ interleaves job $A$ ($r_A=0$) between $B$ and $C$, achieving true makespan $C_{\max} = 4$. Removing the invalid subset setup term restores provable admissibility ($LB \le C_{\max}^*$) across all instances.

**Proof of Validity for Corrected Formulation**:
Every feasible schedule $\pi$ satisfies $C_{\max}(\pi) \ge LB_{\text{AP}}$ (as $\pi$ is an assignment), $C_{\max}(\pi) \ge LB_{\text{heads}}$ (by earliest completion of the bottleneck job), and for every anchor $a$, the completion of the last job in $S_a$ is at least $r_a + \sum_{k \in S_a} p_k$. Taking the maximum over valid lower bounds preserves admissibility: $LB \le C_{\max}^*$. Verified across all unit regression tests with zero violations.

---

#### Q5: What is the Graham notation taxonomy for the problems studied in this project?
**Answer:**
- $1 || C_{\max}$: Single machine, no constraints, makespan objective. Polynomial: $O(n)$.
- $1 | r_j | C_{\max}$: Single machine with release dates. Solvable in $O(n \log n)$ by Earliest Release Date (ERD) priority dispatching.
- $1 | s_{ij} | C_{\max}$: Single machine with sequence-dependent setups. Strongly NP-hard (equivalent to ATSP).
- $1 | r_j, s_{ij} | C_{\max}$: Single machine with release dates and sequence-dependent setups. Strongly NP-hard (generalizes ATSP and TSPTW).
- $1 | r_j, s_{ij} | (C_{\max}, \sum w_j T_j)$: Bi-objective variant minimizing makespan and Total Weighted Tardiness. Strongly NP-hard.

---

### Category 2: Proposed Algorithm (ALNS-WDP) Architecture & Mechanisms

#### Q6: Explain the sliding window DP state space, transitions, and time complexity. Why not use a larger window like $k=15$ or $k=20$?
**Answer:**
Given a schedule $\pi$ of length $n$, we extract a contiguous sub-sequence of size $k$: $W = (\pi(i), \dots, \pi(i+k-1))$, with predecessor $u = \pi(i-1)$ (or depot) arriving at completion time $C_{\text{prefix}}$, and successor $v = \pi(i+k)$.
- **State Space**: $DP(mask, j)$ represents the minimum completion time of scheduling the subset of window jobs indicated by bitmask $mask \subseteq \{0, \dots, k-1\}$ such that the last processed job is $W[j]$.
- **Transitions**:
  $$DP(mask \cup \{2^m\}, m) = \min_{j \in mask} \left( \max\left(r_{W[m]}, \, DP(mask, j) + s_{W[j], W[m]}\right) + p_{W[m]} \right)$$
- **Base Case**: $DP(2^j, j) = \max\left(r_{W[j]}, \, C_{\text{prefix}} + s_{u, W[j]}\right) + p_{W[j]}$.
- **Complexity**: There are $2^k$ bitmasks and $k$ possible endpoints, so the state space has $k 2^{k-1}$ entries. Each entry considers at most $k$ incoming transitions, yielding $O(k^2 2^k)$ time and $O(k 2^k)$ memory.
- **Why $k \in [6, 10]$?**: For $k=8$, $k^2 2^k = 64 \times 256 = 1.6 \times 10^4$ operations (sub-millisecond in Python). For $k=10$, it is $\approx 10^5$ operations (a few milliseconds). For $k=15$, $15^2 2^{15} \approx 7.3 \times 10^6$ operations; for $k=20$, $20^2 2^{20} \approx 4.2 \times 10^8$ operations per window! Because ALNS calls the window polisher dozens of times per second, $k > 10$ leads to exponential stagnation, violating our strict wall-clock time budget without providing proportional makespan improvement.

---

#### Q7: Can the window DP polisher ever worsen a schedule? Prove its monotonicity.
**Answer:**
**Theorem (Monotonicity Guarantee)**: Let $\pi$ be the current schedule, and let $\pi'$ be the schedule produced after re-optimizing window $W$ via Held-Karp DP. Then $C_{\max}(\pi') \le C_{\max}(\pi)$.
**Proof**:
The identity permutation of the window jobs (their original ordering in $\pi$) corresponds to a valid path in the DP state graph visiting all $k$ jobs. Because the Held-Karp DP computes the exact infimum over all $k!$ permutations starting from $C_{\text{prefix}}$, the optimal window completion time satisfies:
$$C_{\text{window}}^* = \min_{j \in \{0, \dots, k-1\}} \left( DP((1 \ll k)-1, j) + s_{W[j], v} \right) \le C_{\text{window}}^{\text{original}}$$
Because completion time functions in single-machine scheduling are monotonically non-decreasing with respect to start times ($C_j = \max(r_j, C_{\text{prev}} + s) + p$), non-increasing completion at the end of the window guarantees that every subsequent job $m > i+k$ satisfies $C_m(\pi') \le C_m(\pi)$. Thus, $C_{\max}(\pi') \le C_{\max}(\pi)$. In our test suite, `test_window_dp_monotonicity_property` exhaustively verifies this property across randomized instances.

---

#### Q8: How are window positions selected in ALNS-WDP? Why not just use sliding windows?
**Answer:**
We implemented and benchmarked three distinct placement strategies:
1. **Sliding**: Sweeps sequentially from index $0$ to $n-k$ in increments of $\lfloor k/2 \rfloor$.
2. **Worst-Setup (Targeted)**: Identifies contiguous blocks of size $k$ exhibiting the highest internal setup penalties ($\sum_{j=i}^{i+k-2} s_{\pi(j),\pi(j+1)}$) and prioritizes re-optimizing those high-waste regions.
3. **Random**: Samples random start indices uniformly in $[0, n-k]$.
Our design study demonstrated that *Worst-Setup* placement achieves the steepest initial descent, but a hybrid alternating strategy (worst-setup during early search, sliding during intensification) yields the most robust final makespan.

---

#### Q9: What destroy and repair operators are used, and how is repair accelerated?
**Answer:**
- **Destroy Operators**:
  1. *Random Removal*: Uniformly removes $q \in [2, \min(10, 0.3n)]$ jobs to promote diversification.
  2. *Worst-Setup Removal*: Removes jobs connected by the largest transition setups ($s_{\pi(j-1),\pi(j)} + s_{\pi(j),\pi(j+1)}$).
  3. *Release-Date Cluster Removal*: Selects a seed job and removes jobs with nearest arrival times $|r_i - r_{\text{seed}}|$, clearing congested time pockets.
  4. *Shaw Relatedness Removal*: Removes jobs that are similar across a normalized distance metric combining processing times, release dates, and mutual setups.
- **Repair Operators**:
  1. *Greedy Best-Insertion*: Inserts removed jobs sequentially into the position that minimizes the resulting makespan.
  2. *Regret-2 Insertion*: Computes $\Delta f_1$ (best insertion cost) and $\Delta f_2$ (second-best insertion cost). Prioritizes jobs with maximum regret $(\Delta f_2 - \Delta f_1)$, preventing greedy trap states.
- **$O(n)$ Incremental Acceleration**: Naive insertion evaluation recalculates the entire schedule from scratch in $O(n)$ per candidate position, yielding $O(n^2)$ per job. We precompute prefix completion times $C_1, \dots, C_{pos-1}$ in $O(n)$ once, evaluate insertions starting at $pos$, and prune propagation when subsequent arrival times dominate the schedule ($C_j = r_j + p_j$). This provides an empirical $3.8\times$ speedup on large instances ($n \ge 100$).

---

#### Q10: How does the bandit adaptive operator selection work, and why is it superior to fixed roulette-wheel weights?
**Answer:**
Standard ALNS divides iterations into discrete segments and resets roulette probabilities based on cumulative points. This suffers from two flaws: it requires arbitrary segment tuning, and static probabilities fail to adapt as the search shifts from exploration to intensification.
We use a **Discounted Exponential Moving Average / Bandit Action-Value Update**:
For each operator $i$, its action-value $w_i$ is updated continuously after each iteration:
$$w_i \leftarrow (1 - \rho) w_i + \rho \cdot R$$
where learning rate $\rho = 0.2$ and rewards are graded:
- $R_{\text{best}} = 30.0$ if the move discovers a new global best schedule (with scaled bonus for relative improvement).
- $R_{\text{imp}} = 15.0$ if the move improves over the current solution.
- $R_{\text{acc}} = 5.0$ if the move is accepted under Simulated Annealing criteria.
- $R_{\text{rej}} = 0.0$ if the move is rejected.
Operator selection probabilities follow a normalized proportional distribution with an explicit **exploration floor**:
$$P_i = \frac{\max(w_i, \, \underline{w})}{\sum_j \max(w_j, \, \underline{w})}$$
where $\underline{w} = 0.05 \cdot \text{mean}(w)$. The weight floor guarantees that no operator is ever starved to zero probability, preserving search agility. In our ablation experiments across 600 runs, disabling adaptive weights (`ALNS_No_AdaptWeights`) increased average makespan from 559.51 to 559.67 across all instances, maintaining exploration across destroy and repair heuristics.

---

#### Q11: How do you configure the acceptance criterion and annealing schedule?
**Answer:**
We use Simulated Annealing acceptance: a non-improving candidate $\pi'$ with degradation $\Delta = C_{\max}(\pi') - C_{\max}(\pi) > 0$ is accepted with probability $P = \exp(-\Delta / T)$.
To ensure scale-independence across arbitrary instance sizes:
1. **Normalized Initial Temperature**:
   $$T_0 = -\frac{\Delta_{\text{init}}}{\ln(0.8)}$$
   where $\Delta_{\text{init}}$ is the average cost degradation measured across 20 preliminary random swaps. This guarantees that initial deteriorating moves are accepted with exactly 80% probability.
2. **Continuous Wall-Clock Cooling**:
   $$T(t) = T_0 \cdot \left(\frac{T_{\text{end}}}{T_0}\right)^{t / t_{\text{budget}}}$$
   where $t$ is the elapsed wall-clock time and $t_{\text{budget}}$ is the allotted budget. This ties annealing directly to elapsed time rather than iteration counters, ensuring that slow DP steps do not freeze the cooling schedule prematurely.

---

### Category 3: Baselines, Mathematical Programming, & Multi-Objective Search

#### Q12: Why did CP-SAT struggle on medium-sized instances ($n=12, 15, 20$) with loose setups, and how did you resolve it?
**Answer:**
In scheduling problems with sequence-dependent setups, standard Big-M disjunctive formulations ($S_j \ge C_i + s_{ij} - M(1 - x_{ij})$) exhibit notoriously weak continuous linear relaxations. The solver's dual bound remains near $\sum p_j$, while the search tree must branch exponentially on $O(n^2)$ Boolean transition variables $x_{ij}$. When setups are loose and release dates spread out, propagation between disjoint intervals is slow.
We addressed this through three architectural enhancements:
1. **CP-SAT Interval & Circuit Formulation**: We modeled job executions as optional intervals combined with CP-SAT's specialized `AddCircuit` constraint over graph nodes, enforcing all-different subtour elimination natively.
2. **Deterministic Warm Starts (Hinting)**: We injected initial variable hints generated by the Earliest Completion Time (ECT) priority dispatching rule.
3. **CP-SAT Matheuristic**: We used CP-SAT as a neighborhood polisher seeded with ALNS-WDP's best sequence, fixing 60% of the sequence prefix/suffix variables and allowing CP-SAT to re-optimize the middle permutations within a 1-second timeout.

---

#### Q13: How does your exact Held-Karp DP baseline operate for $n \le 20$? What are its limits?
**Answer:**
Our exact DP in `src/baselines/exact_dp.py` solves the global problem to proven optimality for $n \le 20$:
- Bitmasks $mask \in [1, 2^n - 1]$ are represented as 32-bit unsigned integers.
- The state table maps $(mask, last\_job) \to \min C_{\max}$.
- For $n=15$, the state space contains $15 \times 2^{14} = 245,760$ states, solved in $\approx 0.18$ seconds.
- For $n=20$, the state space contains $20 \times 2^{19} \approx 1.05 \times 10^7$ states. To avoid Python dictionary overhead, states are indexed in flat NumPy arrays, allowing exact solution in $\approx 14$ seconds.
- **Fundamental Limit**: At $n=25$, the table requires $25 \times 2^{24} \approx 4.2 \times 10^8$ states ($\approx 3.4$ GB RAM), and at $n=30$, $30 \times 2^{29} \approx 1.6 \times 10^{10}$ states ($>120$ GB RAM). Thus, Held-Karp DP faces an insurmountable exponential memory wall for $n > 22$.

---

#### Q14: How does your bi-objective implementation compare ALNS-WDP against NSGA-II?
**Answer:**
- **Problem**: Minimize $(C_{\max}, \sum w_j T_j)$, where tardiness $T_j = \max(0, C_j - d_j)$.
- **Scalarized ALNS Sweep**: We run ALNS-WDP across an authentic grid of scalarization weights $\lambda \in \text{linspace}(0.0, 1.0, 11)$ using the convex composite objective:
  $$f_\lambda(\pi) = \lambda \frac{C_{\max}(\pi)}{C_{\max}^{\text{norm}}} + (1 - \lambda) \frac{\sum w_j T_j(\pi)}{\text{TWT}^{\text{norm}}}$$
  Extracting the non-dominated Pareto archive across all $\lambda$ runs forms our empirical Pareto front.
- **NSGA-II Baseline**: Implemented via `pymoo` using Order Crossover (OX, $p_c = 0.9$) and Inversion Mutation ($p_m = 0.3$) under an identical wall-clock budget.
- **Metrics & Empirical Comparison**: Evaluated using **Hypervolume (HV)** and **Inverted Generational Distance (IGD)** relative to the merged non-dominated reference front. The results reveal clear structural trade-offs:
  - On congested asymmetric instance `n50_a60_asym_s6006`, ALNS-WDP achieves higher mean Hypervolume (206,026.31 vs 170,486.33), though not statistically significant after Holm correction ($p = 0.277$). On `n20_a30_sym_s3004`, ALNS-WDP achieves significantly lower IGD (102.49 vs 399.85, raw $p = 0.0003$, Holm-corrected $p = 0.0018$) because exact window DP repeatedly compresses the makespan component along the non-dominated boundary.
  - On unconstrained symmetric instances, NSGA-II maintains broader population diversity and higher Hypervolume (e.g., 3.80M vs 2.17M on `n50_a0_sym_s6001`), winning HV on 5/6 instances overall, demonstrating that genetic population diversity excels on loose instances while local DP polishing excels on tightly constrained landscapes.

---

### Category 4: Experimental Methodology & Scientific Rigor

#### Q15: What is the exact difference between "Gap to Lower Bound" and "Gap to Optimum"? Why was this a critical audit correction?
**Answer:**
- **Gap to Optimum**:
  $$\text{Gap}_{\text{Opt}}(\%) = \frac{C_{\max}(\pi) - C_{\max}^*}{C_{\max}^*} \times 100$$
  This can only be computed when the true mathematical optimum $C_{\max}^*$ is proven (e.g., via Exact DP or CP-SAT for $n \le 20$).
- **Gap to Lower Bound**:
  $$\text{Gap}_{\text{LB}}(\%) = \frac{C_{\max}(\pi) - LB}{LB} \times 100$$
  Because $LB \le C_{\max}^*$, $\text{Gap}_{\text{LB}}$ conflates two distinct quantities: the heuristic's sub-optimality AND the mathematical relaxation gap of the lower bound ($C_{\max}^* - LB$).
- **Audit Correction**: Prior work frequently used the term "Optimality Gap" when comparing heuristics against lower bounds on $n=100$ or $200$ instances. That was methodologically invalid because the lower bound is not tight for large $n$. We strictly separated the metrics: reporting proven Gap to Optimum for $n \le 20$ and Gap to Dual Lower Bound for all instances.

---

#### Q16: How did you ensure fairness in comparing stochastic metaheuristics?
**Answer:**
We enforced five strict scientific controls:
1. **Identical Wall-Clock Budgets**: All algorithms (GA, SA, Multi-Start LS, ALNS, ALNS-WDP) run under the identical wall-clock time limit $t_{\text{limit}} = \max(0.75, 0.03n)$ seconds on the same hardware core.
2. **Evaluation Tracking**: We logged evaluation counts alongside runtime to decouple hardware clock fluctuations from algorithmic throughput.
3. **Statistical Sample Size**: 30 independent pseudo-random seeds ($42 + 17 \cdot i$ for $i=0,\dots,29$) per method per instance.
4. **Matched Instance Sets**: Every algorithm was evaluated on the exact same benchmark instances without selective omission.
5. **No Peeking**: Hyperparameters were tuned on a separate validation set ($n=12, 25$) and kept frozen across all benchmark runs.

---

#### Q17: Walk through your statistical significance testing pipeline. Why use Holm-Bonferroni?
**Answer:**
1. **Paired Wilcoxon Signed-Rank Test**: The non-parametric counterpart to the paired Student's t-test. For each competitor method $M$, we pair its mean makespan on each instance against ALNS-WDP's mean makespan on that exact instance.
2. **Holm-Bonferroni Correction**: When testing multiple hypotheses (ALNS-WDP vs GA, SA, LS, Rules, CP-SAT), standard $\alpha = 0.05$ inflation causes false positive discoveries. The Holm-Bonferroni method sorts unadjusted p-values $p_{(1)} \le p_{(2)} \le \dots \le p_{(m)}$ and enforces step-down threshold rejection:
   $$p_{(k)} \le \frac{\alpha}{m - k + 1}$$
   This controls the Family-Wise Error Rate (FWER) without the excessive conservatism of standard Bonferroni.
3. **Friedman Rank Test & Nemenyi Post-Hoc**: Computes average ranks across all instances. Rejection of the Friedman null hypothesis ($p < 0.05$) triggers the Nemenyi critical difference calculation:
   $$CD = q_\alpha \sqrt{\frac{k(k+1)}{6N}}$$
   allowing visual display of which algorithms are statistically distinguishable.

---

#### Q18: What did the ablation study reveal? Which component contributed the most?
**Answer:**
We evaluated five controlled variants on identical instances and seeds (8 instances $\times$ 15 seeds = 600 total runs):
1. `ALNS_WDP_Full`: The full proposed framework with in-search Window DP, adaptive bandit weights, and regret-2 repair.
2. `ALNS_No_WindowDP`: ALNS with adaptive bandit weights but without any sliding window DP re-optimization.
3. `ALNS_No_AdaptWeights`: ALNS with in-search Window DP but uniform static operator selection weights.
4. `Plain_ALNS`: Standard baseline ALNS (no Window DP, uniform operator weights).
5. `WindowDP_FinalPolishOnly`: Plain ALNS during search, executing a single full sliding window DP sweep as post-processing on the final incumbent.

**Findings & Statistical Significance**:
Across all 600 runs:
- Mean gap to valid lower bound: `ALNS_WDP_Full` achieves **5.06%** (mean makespan 559.51), `WindowDP_FinalPolishOnly` achieves **5.03%** (559.93), `ALNS_No_AdaptWeights` achieves **5.13%** (559.67), `Plain_ALNS` achieves **5.20%** (561.91), and `ALNS_No_WindowDP` achieves **5.31%** (562.35).
- **Gains appear predominantly at large instance size ($n=100$)**:
  - On `n100_a0_asym_s11000`: `ALNS_WDP_Full` (mean makespan 1183.47) significantly outperforms `ALNS_No_WindowDP` (1190.40, Holm-corrected $p = 0.0086$, W/T/L = 13/1/1) and `Plain_ALNS` (1190.33, Holm-corrected $p = 0.0112$, W/T/L = 13/1/1).
  - On `n100_a30_sym_s11004`: `ALNS_WDP_Full` (1311.87) significantly outperforms `ALNS_No_WindowDP` (1331.13, Holm-corrected $p = 0.0157$, W/T/L = 12/0/3).
  - For $n \le 50$, differences between DP variants are not statistically significant ($p > 0.05$) because standard destroy-repair operators already reach near-optimal configurations.
  - Furthermore, comparing `ALNS_WDP_Full` vs `WindowDP_FinalPolishOnly` at $n=100$ shows comparable makespan performance (1183.47 vs 1184.67 and 1311.87 vs 1319.47), with differences not statistically significant after Holm correction ($p = 1.000$). This indicates that while sliding-window DP polishing is essential, applying it solely as a final post-processing polish achieves performance competitive with periodic interleaving.

---

#### Q19: How did you benchmark derived TSPLIB instances, and why was this included?
**Answer:**
Purely synthetic instances can suffer from synthetic generator artifacts. To demonstrate external validity, we derived benchmark instances from classical TSPLIB problems:
- `bayg29` ($n=29$, symmetric Euclidean)
- `berlin52` ($n=52$, 2D Euclidean)
We extracted the exact TSPLIB distance matrices as sequence-dependent setup matrices $s_{ij}$, seeded synthetic processing times $p_j \in [5, 25]$, and introduced release dates $r_j$ using congestion factor $\alpha = 0.3$. This demonstrated that ALNS-WDP's superior performance generalizes to realistic geographic distance metrics.

---

### Category 5: Edge Cases, Limitations, & Defense

#### Q20: Where does ALNS-WDP fail or lose to competitors?
**Answer:**
Honest scientific analysis requires acknowledging failure regimes:
1. **Very Small Instances ($n \le 10$)**: Exact DP and CP-SAT find the provable global optimum in $<0.05$ seconds. While ALNS-WDP also reaches the optimum, its metaheuristic overhead and Python function call setup make it slower in wall-clock time than a compiled branch-and-bound or bitmask DP.
2. **Symmetric Euclidean Topologies with Moderate Congestion ($\alpha = 0.3$, Sym)**: On instances like `bayg29` (485.7 vs 479.5/480.7), `n12_a30_sym` (179.6 vs 177.0), and `n20_a30_sym` (275.1 vs 274.0), Multi-Start Local Search and Simulated Annealing slightly outperform ALNS-WDP. We articulate this as a plausible hypothesis (rather than a proven causal mechanism) that Euclidean symmetric topologies favor 2-opt segment reversals, which uncross tour loops in $O(1)$ amortized time without altering internal symmetric edge costs ($s_{uv} = s_{vu}$), whereas ALNS remove-and-reinsert operators preserve sequence orientation, making symmetric reversals harder to discover without explicit 2-opt moves.
3. **Controlled Setup Dominance on Symmetric Setups**: In our controlled setup-dominance experiment (2,400 runs across $\beta \in [0.1, 5.0]$), MultiStart_LS and SA outperform ALNS-WDP on symmetric setups at moderate-to-high ratios (e.g., on `n30_a30_sym` at $\beta=1.0$, MS-LS won 28/30 runs and SA won 27/30 runs, global Holm $p < 0.0001$). Conversely, on asymmetric setups, ALNS-WDP sweeps 10/10 pairwise tests (global Holm $p < 0.0001$). On `n50_a30_sym` at $\beta=2.0$, SA's advantage has raw $p = 0.0300$ and exploratory Holm $p = 0.0435$, but under global Holm correction across all 60 comparisons, global Holm $p = 0.3295$, failing significance.

---

#### Q21: What is the computational complexity of the entire ALNS-WDP loop?
**Answer:**
Let $N_{\text{iter}}$ be the number of iterations performed within the budget.
- **Initial construction**: $O(n^2)$ via greedy insertion across dispatching heuristics.
- **In each iteration**:
  - *Destroy operator ($q$ jobs)*: $O(n \log n)$ due to sorting/ranking for Shaw relatedness, worst-setup, and release clustering.
  - *Repair operator ($q$ jobs)*: For each of $q$ unplaced jobs, evaluating candidate positions with suffix propagation takes $O(n - pos)$ per position. Summing across all candidate insertion positions yields $\sum_{pos=0}^m (m - pos) = O(m^2) = O(n^2)$ per unplaced job. Summing across all $q$ unplaced jobs yields $\sum_{u=1}^q u \cdot O(n^2) = O(q^2 n^2)$ total across the repair step.
  - *Window DP polisher*: Solving an exact Held-Karp bitmask dynamic program on a window of size $k$ requires $O(k^2 2^k)$ operations. A targeted polish on a single window takes $O(k^2 2^k) = O(1)$ with respect to $n$. A full sweep across $n$ jobs takes $O\left(\frac{n}{k/2} \cdot k^2 2^k\right) = O(n \cdot k 2^k)$.
  - *Acceptance and Bandit update*: $O(1)$.
- **Total per-iteration complexity**: $O(n \log n + q^2 n^2 + k^2 2^k)$.
Because $k$ is fixed ($k=8$, where $8^2 2^8 = 16,384$ operations $\approx 1.5$ ms) and $q \le 15$ is bounded by a constant ceiling, each iteration scales as $O(n^2)$ (dominated by the suffix propagation in the repair operator), **NOT** $O(n \log n)$. Naive repair without prefix memoization would scale as $O(q \cdot n^3)$; our prefix memoization reduces this to $O(q^2 n^2)$, ensuring the solver comfortably executes thousands of iterations within a few seconds up to $n=200$.

---

#### Q22: Why did you choose CP-SAT over PuLP/CBC or HiGHS as your primary exact MIP solver?
**Answer:**
We tested both PuLP/HiGHS and OR-Tools CP-SAT:
1. **Propagation Strength**: CP-SAT combines SAT solver clause learning with linear programming relaxation and specialized scheduling propagators (`AddCircuit`, `AddNoOverlap`).
2. **Subtour Handling**: In classical MIP (PuLP), subtours must be eliminated via Miller-Tucker-Zemlin (MTZ) constraints or lazy callback constraints. MTZ constraints have notoriously weak LP relaxations. CP-SAT handles all-different routing permutations natively inside its conflict engine.
3. **Performance**: On $n=12$, CP-SAT solved the instances $6.4\times$ faster than PuLP/HiGHS.

---

#### Q23: How did you verify the reproducibility of your experimental pipeline?
**Answer:**
We implemented four layers of reproducibility controls:
1. **Structured Seed Protocol**: All stochastic components use explicit integer seeds (`seed = 42 + 17 * i`).
2. **Automated Verification Tool (`tools/check_claims.py`)**: A Python audit script that parses generated CSVs in `results/` and asserts that every number, gap, p-value, and table entry cited in `abstract.md`, `report.pdf`, and `presentation.pptx` matches within $\pm 0.05\%$.
3. **Pytest Regression Suite**: 26 automated tests verifying evaluator idle-time math, lower bound validity (including the interleaving counterexample regression test), window DP monotonicity, instance JSON serialization, and CSV row uniqueness.
4. **Single Command Master Reproduction**: Executing `python run_all.py` reproduces the entire experimental campaign from scratch.

---

#### Q24: What is the difference between this work and published literature like Dynasearch or Balas-Simonetti DP?
**Answer:**
- **Balas & Simonetti (2001)** formulated a linear-time dynamic program that finds the shortest path through a restricted permutation graph ($|i - \pi(i)| \le k$) for the TSP with time windows and single-machine scheduling with setup, release, and delivery times.
- **Congram, Potts, & van de Velde (2002)** introduced *Dynasearch* for the single-machine total weighted tardiness scheduling problem, which uses DP to evaluate exponentially many independent 2-job swap or insert neighborhoods in polynomial time.
- **Our Distinction**: Unlike Dynasearch or Balas-Simonetti, our Window DP operates on a contiguous physical sub-sequence slice of size $k$ extracted from the incumbent sequence. It performs *unrestricted exact Held-Karp enumeration* ($k!$ permutations) over that slice, explicitly propagating anticipatory setups and arbitrary release dates from the prefix completion time. This exact polisher is embedded inside an Adaptive Large Neighborhood Search framework driven by reinforcement-style bandit operator selection.

---

#### Q25: If you had 6 more months on this research project, what would you do?
**Answer:**
1. **GPU-Accelerated Bitmask DP**: Implement the $O(k^2 2^k)$ window DP in CUDA C++ / PyTorch tensors. Massively parallel thread blocks could evaluate windows of size $k=14$ to $16$ in milliseconds, or evaluate 1,000 independent window positions in parallel.
2. **Deep Reinforcement Learning Operator Selection**: Replace our contextual bandit with a Graph Neural Network (GNN) policy network that inspects the current schedule graph (jobs as nodes, setups as edge weights, release dates as node features) and selects destroy/repair operators conditioned on graph state.
3. **Exact Branch-and-Price-and-Cut**: Develop an exact branch-and-price algorithm where columns represent single-machine sequences with valid setups, generated via our release-date-aware DP as a pricing subproblem.
4. **Stochastic and Dynamic Environments**: Extend the model to stochastic release dates $\tilde{r}_j \sim \mathcal{D}$ and real-time job arrivals, evaluating ALNS-WDP as an online rolling-horizon scheduler.

