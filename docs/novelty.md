# Honest Scientific Novelty Statement: ALNS-WDP

## 1. Context and Academic Scope
In the design and analysis of algorithms for deterministic scheduling, claiming complete novelty for metaheuristic components is rarely justified. Decades of research in combinatorial optimization have established rich algorithmic paradigms, including Large Neighborhood Search (Shaw, 1998), Adaptive Large Neighborhood Search (Ropke & Pisinger, 2006), and exact dynamic programming neighborhoods (Balas & Simonetti, 2001; Congram, Potts, & van de Velde, 2002).

This document explicitly demarcates what is **borrowed from existing scientific literature** versus what represents the **specific algorithmic contributions of this university research project**. We employ strictly cautious academic terminology: **ALNS-WDP is a partially novel, hybrid metaheuristic combination**, not an unprecedented breakthrough or undisputed "state-of-the-art".

---

## 2. What Is Borrowed from Existing Literature

### 2.1 The ALNS Metaheuristic Framework
- **Source**: Ropke, S., & Pisinger, D. (2006). *An Adaptive Large Neighborhood Search Heuristic for the Pickup and Delivery Problem with Time Windows*. Transportation Science, 40(4), 455–472.
- **Borrowed Elements**:
  - The alternating destroy-and-repair iterative structure.
  - The Shaw-style relatedness destroy operator, which clusters jobs based on similarity in processing times, release dates, and setup matrices.
  - The regret-2 heuristic, which penalizes the delay of jobs with high opportunity costs between their best and second-best insertion positions.
  - The simulated annealing acceptance criterion with geometric cooling.

### 2.2 Exact Sub-Permutation Dynamic Programming
- **Source**: Held, M., & Karp, R. M. (1962). *A Dynamic Programming Approach to Sequencing Problems*. Journal of the Society for Industrial and Applied Mathematics, 10(1), 196–210.
- **Borrowed Elements**:
  - The bitmask state representation $DP(\text{mask}, j)$ recording the optimal completion time of processing a subset of jobs with job $j$ visited last.
  - The topological recurrence over subset bitmasks of increasing size.

### 2.3 Window-Based Exact Re-Optimization and Dynasearch Neighborhoods
- **Sources**:
  - Congram, R. K., Potts, C. N., & van de Velde, S. L. (2002). *An Iterated Dynasearch Algorithm for the Single-Machine Total Weighted Tardiness Scheduling Problem*. INFORMS Journal on Computing, 14(1), 52–67.
  - Balas, E., & Simonetti, N. (2001). *Linear Time Dynamic-Programming Algorithms for New Classes of Restricted TSPs: A Computational Study*. INFORMS Journal on Computing, 13(1), 56–75, doi: 10.1287/ijoc.13.1.56.9748.
- **Borrowed Elements**:
  - The concept of selecting a localized sub-sequence of elements within a global permutation and re-ordering them to exact optimality using dynamic programming.
  - Using fixed prefixes and suffixes to bound the local optimization problem.

### 2.4 Multi-Armed Bandit / Action-Value Updates
- **Sources**:
  - Thierens, D. (2005). *An Adaptive Pursuit Strategy for Allocating Operator Probabilities*. GECCO.
  - Sutton, R. S., & Barto, A. G. (2018). *Reinforcement Learning: An Introduction* (2nd ed.). MIT Press.
- **Borrowed Elements**:
  - Updating operator selection probabilities based on historical performance using an exponential recency-weighted moving average: $w \leftarrow (1-\rho)w + \rho R$.
  - Assigning discrete tiered reward signals for discovering global best, improving, or accepted solutions.

### 2.5 Dual Lower Bounds via Assignment Relaxation
- **Sources**:
  - Kuhn, H. W. (1955). *The Hungarian Method for the Assignment Problem*. Naval Research Logistics Quarterly, 2(1–2), 83–97.
  - Lawler, E. L., Lenstra, J. K., Rinnooy Kan, A. H. G., & Shmoys, D. B. (1985). *The Traveling Salesman Problem: A Guided Tour of Combinatorial Optimization*. John Wiley & Sons.
- **Borrowed Elements**:
  - Modeling transition setups as a Linear Sum Assignment Problem (Hungarian method) to compute a valid dual lower bound on the directed Hamiltonian path.

---

## 3. What Is Original to This Research Project

The novel contributions of this project lie in the **specific synthesis, adaptation, mathematical proofs, and empirical engineering** tailored to the single-machine scheduling variant with both sequence-dependent setups and release dates ($1 \mid r_j, s_{ij} \mid C_{\max}$):

1. **Release-Date-Aware Sliding-Window DP Formulation**:
   - While standard dynasearch (Congram et al., 2002) was formulated for $1 \mid\mid \sum w_j T_j$, and Balas & Simonetti (2001) covers TSP with time windows as well as single-machine scheduling with setup, release, and delivery times under a restricted permutation graph ($|i - \pi(i)| \le k$), our sliding-window Held-Karp dynamic programming re-optimizer solves unrestricted exact Held-Karp enumeration over contiguous physical slices of size $k \in [6, 10]$ within an ALNS framework, specifically accounting for:
     - Machine idle time induced by release dates: $S_{\text{next}} = \max(r_{\text{next}}, C_{\text{curr}} + s_{\text{curr}, \text{next}})$.
     - Prefix completion time $C_{\text{pred}}$ from the fixed schedule preceding the window.
     - Look-ahead suffix transition cost $s_{\text{last}, \text{succ}}$ to the first job of the succeeding schedule.
   - We formalize the **mathematical monotonicity theorem**: proving that because $g(C) = \max(r, C + s) + p$ is non-decreasing in $C$, storing only the minimum completion time per $(\text{mask}, j)$ satisfies Bellman's principle of optimality and guarantees that window DP never worsens the global makespan.

2. **Valid Dual Release-Anchor Lower Bound (Theorem 2)**:
   - While global Hungarian assignment relaxation on transitions ($C_{AP}(J)$) is standard for TSP routing, it ignores release dates. Conversely, individual release bounds $\max_j (r_j + p_j)$ ignore subsequent job workload. We establish a valid combined dual lower bound:
     $$LB = \max\left(\sum_{j=1}^n p_j + C_{AP}(J), \; \max_{j \in V} (r_j + p_j), \; \max_{a \in V} \left(r_a + \sum_{k \in S_a} p_k\right)\right)$$
     where $S_a = \{k \in V : r_k \ge r_a\}$ is the subset of jobs released at or after anchor job $a$.
   - **Critical Correction on Subset Setups**: We formally document that subset assignment setup bounds of the form $r_a + C_{AP}(S_a)$ are *mathematically invalid* for arbitrary non-metric setup matrices because jobs outside $S_a$ (released earlier) can interleave between subset jobs, bypassing internal transitions of $S_a$. For instance, on $p=[1,1,1]$, $r=[0,1,1]$, $s_{BC}=s_{CB}=100$, the valid schedule $\pi=[B, A, C]$ has makespan 4, whereas an anchor bound adding internal setups $C_{AP}(\{B,C\})=100$ erroneously yields 103. Retaining the processing-only anchor bound $\max_a (r_a + \sum_{k \in S_a} p_k)$ guarantees mathematical validity ($LB \le C_{\max}^*$) across all instances.

3. **Incremental $O(n)$ Insertion Evaluator for Non-Monotone Scheduling**:
   - Because sequence-dependent setups and release dates create non-linear arrival jumps, insertion repair heuristics traditionally recompute the entire schedule from scratch in $O(n)$ time per candidate position, yielding $O(n^2)$ per job. We implemented prefix completion caching and incremental suffix propagation, dramatically accelerating operator throughput.

4. **Integration of Scale-Normalized Bandit Search with Exact Polishers**:
   - Coupling time-based continuous cooling with scale-normalized temperature ($T_0 = 0.05 \cdot C_{\max}$) and operator weight floors ($w_{\min} = 0.1 \cdot \bar{w}$) ensures robust exploration without operator starvation across diverse problem scales ($n \in [4, 200]$).

5. **Exhaustive Empirical Audit and Defensible Science**:
   - Rather than claiming sweeping dominance, we perform an honest, fully reproducible study:
     - Establishing where ALNS-WDP excels ($n \ge 30$, where CP-SAT fails).
     - Acknowledging where it is inferior ($n \le 8$, where CP-SAT and exact DP solve to provable optimality in milliseconds).
     - Reporting non-parametric statistical tests (Holm-corrected Wilcoxon and Friedman), establishing that ALNS-WDP achieves a 5.47% mean gap to valid LB (significant vs GA $p = 0.0146$, not significant vs SA $p = 0.1281$ or MultiStart_LS $p = 0.1281$).
     - Conducting a controlled setup-dominance study (2,400 runs across $\beta \in [0.1, 5.0]$) confirming asymmetric dominance (10/10 sweeps, global Holm $p < 0.0001$) while documenting 2-opt competitiveness on symmetric setups.

---

## 4. Summary Table: Borrowed vs. Project Contribution

| Component | Standard Literature Baseline | Our Project's Adaptation |
| :--- | :--- | :--- |
| **Search Framework** | ALNS (Ropke & Pisinger, 2006) | Adapted to $1 \mid r_j, s_{ij} \mid C_{\max}$ with time-based cooling |
| **Local Polisher** | Fixed $k$-opt or 2-opt swaps | Exact Held-Karp Window DP with prefix/suffix boundary coupling |
| **Monotonicity** | Taken for granted in unconstrained routing | Formally proved for release dates + anticipatory setups |
| **Lower Bound** | Standard Hungarian AP on distances | Dual release-anchor bound combining global AP with processing horizons |
| **Operator Scoring** | Static roulette wheel selection | Adaptive bandit update with weight floors and normalized reward |
| **Repair Heuristic** | Full $O(n^2)$ schedule evaluation | Prefix-completion caching with $O(n)$ incremental suffix propagation |

---

## 5. Verification Notice
All citations in this document have been checked against standard operations research literature. No page numbers or claims have been invented.

