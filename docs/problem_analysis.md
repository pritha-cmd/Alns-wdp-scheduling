# Theoretical Problem Analysis: Single-Machine Scheduling

## 1. Formal Problem Definition: Base Problem ($1 \mid\mid C_{\max}$)

### 1.1 Inputs and Parameters
Let $J = \{1, 2, \dots, n\}$ denote a finite set of $n$ independent, non-preemptive jobs to be processed on a single continuously available machine.
Each job $j \in J$ is characterized by:
- Processing time: $p_j \in \mathbb{Z}^+$, representing the uninterrupted duration required on the machine.

For the baseline instance originating from Practical Problem 4:
- $n = 4$
- Jobs: $A, B, C, D$ with processing times:
  $$p_A = 3, \quad p_B = 5, \quad p_C = 2, \quad p_D = 4$$
- Release dates: $r_j = 0$ for all $j \in J$.
- Setup times: $s_{ij} = 0$ for all pairs $i, j \in J$.
- Precedence constraints: $\emptyset$ (jobs are independent).

### 1.2 Decision Variables and Schedule Representation
A schedule is uniquely defined by a permutation (bijection) $\pi: \{1, 2, \dots, n\} \to J$, where $\pi(k)$ denotes the job assigned to position $k \in \{1, \dots, n\}$ in the processing sequence.
Let $S_j \ge 0$ denote the start time of job $j$, and $C_j = S_j + p_j$ denote its completion time.

### 1.3 Feasibility Constraints
A schedule is feasible if and only if:
1. **Uninterrupted Non-preemption**: For every job $j$, processing spans $[S_j, C_j)$ with $C_j - S_j = p_j$.
2. **Machine Capacity (Non-concurrency)**: For any pair of distinct jobs $i \ne j$, the machine processes at most one job at any instant:
   $$(S_i, C_i) \cap (S_j, C_j) = \emptyset$$
   Under sequence $\pi$, this enforces:
   $$S_{\pi(k)} \ge C_{\pi(k-1)} \quad \forall k \in \{2, \dots, n\}, \quad \text{with } S_{\pi(1)} \ge 0$$
3. **Availability**: All jobs are available at time zero: $S_j \ge 0 \quad \forall j \in J$.

### 1.4 Objective Function
The objective is the minimization of the **makespan** $C_{\max}$, defined as the completion time of the last processed job:
$$C_{\max}(\pi) = \max_{j \in J} C_j = C_{\pi(n)}$$

### 1.5 Graham Three-Field Notation
Following the standard classification scheme introduced by Graham, Lawler, Lenstra, and Rinnooy Kan (1979) ($\alpha \mid \beta \mid \gamma$):
- $\alpha = 1$: Single machine environment.
- $\beta = \emptyset$: No release dates, no setup times, non-preemptive processing, no precedence restrictions.
- $\gamma = C_{\max}$: Minimization of the maximum completion time (makespan).
Hence, the base problem is denoted as **$1 \mid\mid C_{\max}$**.

---

## 2. Rigorous Proof of Triviality and Complexity

### Theorem 1 (Makespan Invariance in $1 \mid\mid C_{\max}$)
*For any instance of the single-machine scheduling problem $1 \mid\mid C_{\max}$ with non-negative processing times $p_j$ and $r_j = 0$, every semi-active schedule (i.e., schedule with no unnecessary idle time) achieves identical makespan:*
$$C_{\max}(\pi) = \sum_{j=1}^n p_j \quad \forall \pi \in \Pi_n$$
*where $\Pi_n$ is the set of all $n!$ job permutations.*

#### Proof:
In any semi-active schedule without unforced machine idling:
1. The first job begins immediately at machine availability:
   $$S_{\pi(1)} = 0 \implies C_{\pi(1)} = p_{\pi(1)}$$
2. For each subsequent position $k \in \{2, \dots, n\}$, since all remaining jobs are available at $t=0$ and no setup delays exist, the machine starts job $\pi(k)$ immediately upon completion of job $\pi(k-1)$:
   $$S_{\pi(k)} = C_{\pi(k-1)} \implies C_{\pi(k)} = C_{\pi(k-1)} + p_{\pi(k)}$$
3. By mathematical induction on $k$:
   $$C_{\pi(k)} = \sum_{m=1}^k p_{\pi(m)}$$
4. Setting $k = n$, the makespan is:
   $$C_{\max}(\pi) = C_{\pi(n)} = \sum_{m=1}^n p_{\pi(m)} = \sum_{j \in J} p_j$$
Since addition over the real numbers is commutative and associative, the sum $\sum_{m=1}^n p_{\pi(m)}$ is invariant under any permutation $\pi \in \Pi_n$. $\blacksquare$

### Corollary 1.1 (Base Case Optimality)
For the 4-job instance from Practical Problem 4:
$$C_{\max}^* = p_A + p_B + p_C + p_D = 3 + 5 + 2 + 4 = 14$$
All $4! = 24$ permutations are globally optimal solutions with makespan exactly equal to 14.

### Computational Complexity of $1 \mid\mid C_{\max}$
Because any arbitrary permutation $\pi$ yields an optimal schedule, an optimal schedule can be produced in **$O(n)$ time** (or $O(1)$ additional time if the input list is already provided). The decision version:
$$\text{"Does there exist a schedule with } C_{\max} \le K\text{?"}$$
is solved trivially by checking if $\sum_{j=1}^n p_j \le K$, which requires $O(n)$ additions and a single comparison. Therefore:
- The base problem $1 \mid\mid C_{\max}$ is strictly in **$\mathbf{P}$** and is computationally trivial.
- It is **not NP-hard**.

---

## 3. Explicit Modeling Assumptions for the Extended Problem ($1 \mid r_j, s_{ij} \mid C_{\max}$)

To establish a mathematically rigorous foundation, the extended problem studied in this research operates under the following explicit operational assumptions:

1. **Anticipatory Setup Times**:
   Setups are machine-dependent. The transition setup between job $i$ and job $j$ ($s_{ij}$) begins immediately at the instant machine finishes job $i$ ($C_i$), regardless of whether job $j$ has arrived at the facility. Consequently, the machine completes preparation for job $j$ at time $C_i + s_{ij}$. Because job $j$ cannot be mounted or processed before its release date $r_j$, the actual processing start time is:
   $$S_j = \max\left(r_j, \, C_i + s_{ij}\right)$$
   This reflects industrial reality where machine re-tooling, calibration, or cleaning occurs prior to workpiece loading.
2. **Initial Machine State (Depot Setup)**:
   The machine begins at time $t = 0$ in an idle neutral state (depot 0). The first job $\pi(1)$ incurs an initial setup time $s0_{\pi(1)}$ from the depot. Thus:
   $$S_{\pi(1)} = \max\left(r_{\pi(1)}, \, s0_{\pi(1)}\right)$$
3. **Setup Matrix Properties and Triangle Inequality**:
   - **Asymmetric Family**: Transition costs $s_{ij}$ are independent random integers in $[1, 15]$ ($i \ne j$, $s_{ii} = 0$). In general, this family **does not satisfy the triangle inequality** ($s_{ik} \le s_{ij} + s_{jk}$ is not guaranteed), modeling chemical batching or metal stamping where sequence reversals incur asymmetric changeovers.
   - **Symmetric Family**: Derived from Euclidean 2D coordinates scaled and rounded to integers, with $s_{ij} = s_{ji}$ and $s_{ii} = 0$. This family **strictly satisfies the triangle inequality**.
4. **Deterministic Integer Data**:
   All parameters ($p_j, r_j, s_{ij}, s0_j, d_j, w_j$) are strictly non-negative integers.
5. **Non-preemption**:
   Once processing starts on job $j$, it cannot be interrupted until complete duration $p_j$ has elapsed.

---

## 4. Complexity Ladder and Formal Reduction Sketches

The computational complexity transitions systematically as constraints are added:

| Variant | Graham Notation | Complexity | Dominant Paradigm / Reduction | Primary Citations |
| :--- | :--- | :--- | :--- | :--- |
| **Base Case** | $1 \mid\mid C_{\max}$ | **$\mathbf{P}$** ($O(n)$) | Commutative addition; all sequences optimal | Graham et al. (1979) |
| **Precedence Constraints** | $1 \mid \text{prec} \mid C_{\max}$ | **$\mathbf{P}$** ($O(n + m)$) | Topological Sort of DAG | Lawler (1973) |
| **Release Dates Alone** | $1 \mid r_j \mid C_{\max}$ | **$\mathbf{P}$** ($O(n \log n)$) | Earliest Release Date (ERD) / Shortest Idle | Baker (1974); Pinedo (2016) |
| **Preemption + Release Dates** | $1 \mid r_j, pmtn \mid C_{\max}$ | **$\mathbf{P}$** ($O(n \log n)$) | ERD dispatching rule is exact | Horn (1974) |
| **Sequence-Dependent Setups** | $1 \mid s_{ij} \mid C_{\max}$ | **Strongly NP-hard** | Reduction from ATSP / Directed Hamiltonian Path | Garey & Johnson (1979); Pinedo (2016) |
| **Setups + Release Dates** | $1 \mid r_j, s_{ij} \mid C_{\max}$ | **Strongly NP-hard** | Generalizes ATSP with Time Windows (TSPTW) | Rinnooy Kan (1976); Pinedo (2016) |
| **Maximum Lateness** | $1 \mid r_j \mid L_{\max}$ | **Strongly NP-hard** | Reduction from 3-Partition | Lenstra, Rinnooy Kan, Brucker (1977) |
| **Total Weighted Tardiness** | $1 \mid\mid \sum w_j T_j$ | **Strongly NP-hard** | Reduction from 3-Partition | Lawler (1977); Lenstra et al. (1977) |
| **Bi-Objective Variant** | $1 \mid r_j, s_{ij} \mid (C_{\max}, \sum w_j T_j)$ | **Strongly NP-hard** | Generalizes both $1 \mid r_j, s_{ij} \mid C_{\max}$ and $1 \mid\mid \sum w_j T_j$ | Garey & Johnson (1979); Lawler (1977) |

### Reduction Sketches for Key Transitions

#### A. Reduction: ATSP to $1 \mid s_{ij} \mid C_{\max}$
- **Target Problem**: Given a directed complete graph $G=(V, E)$ with edge weights $c_{ij} \ge 0$, find a Hamiltonian path starting at vertex 0 that visits all vertices in $V$ with total weight $\le K$.
- **Transformation**: Define $n = |V|-1$ jobs corresponding to vertices $\{1, \dots, |V|-1\}$. Set $p_j = 0$ (or any constant $p > 0$) for all jobs. Set setup times $s_{ij} = c_{ij}$ and $s0_j = c_{0j}$. Set release dates $r_j = 0$.
- **Equivalence**: In this scheduling instance, $C_{\max}(\pi) = \sum p_j + s0_{\pi(1)} + \sum_{k=2}^n s_{\pi(k-1), \pi(k)}$. Since $\sum p_j$ is constant, $C_{\max}(\pi) \le \sum p_j + K$ if and only if the sequence of jobs defines a directed Hamiltonian path in $G$ of cost $\le K$.
- **Conclusion**: Since Directed Hamiltonian Path is strongly NP-complete (Garey & Johnson, 1979), $1 \mid s_{ij} \mid C_{\max}$ is **strongly NP-hard**.

#### B. Reduction: TSP with Time Windows to $1 \mid r_j, s_{ij} \mid C_{\max}$
When release dates $r_j > 0$ are present, each job cannot start before $r_j$. In the decision problem "Can all jobs finish by deadline $D$?", setting release dates $r_j$ and individual deadlines $d_j$ directly maps to the TSP with Time Windows (TSPTW), where visits must occur within $[r_j, d_j]$. Because TSPTW is strongly NP-complete even on trees or planar graphs, $1 \mid r_j, s_{ij} \mid C_{\max}$ is strongly NP-hard.

---

## 5. Explicit Mapping to Practical Sheet Problem 3 (ATSP) with Worked Example

To directly connect this research to the practical course tutorials, we observe:
- **Practical Sheet Problem 4** ($1 \mid\mid C_{\max}$): Is the degenerate special case where all $s_{ij} = 0$ and $r_j = 0$.
- **Practical Sheet Problem 3** (Vehicle Routing / ATSP): Is the setup-only special case ($1 \mid s_{ij} \mid C_{\max}$) where the vehicle travel costs between customer locations are isomorphic to machine setup transitions.

### Worked Example: Adding Setups to the 4-Job Practical Instance
Consider the 4 practical jobs:
$$p_A = 3, \quad p_B = 5, \quad p_C = 2, \quad p_D = 4, \quad \sum_{j} p_j = 14$$
Suppose machine setups depend on sequence transitions according to the following setup matrix (with initial setup $s_0$ from depot):

$$s_0 = \begin{bmatrix} s_{0A} & s_{0B} & s_{0C} & s_{0D} \end{bmatrix} = \begin{bmatrix} 2 & 1 & 4 & 5 \end{bmatrix}$$

$$s = \begin{pmatrix}
- & 8 & 1 & 6 \\
2 & - & 7 & 3 \\
9 & 2 & - & 4 \\
3 & 5 & 6 & -
\end{pmatrix}$$
*(Rows represent predecessor job $i \in \{A, B, C, D\}$; columns represent successor job $j \in \{A, B, C, D\}$)*.

#### Evaluating Sequence 1: $\pi_1 = (B, D, A, C)$
1. Start at depot 0 $\to$ Job B: setup $s_{0B} = 1$. Start B at 1, finishes at $C_B = 1 + p_B = 1 + 5 = 6$.
2. Job B $\to$ Job D: setup $s_{BD} = 3$. Start D at $6 + 3 = 9$, finishes at $C_D = 9 + p_D = 9 + 4 = 13$.
3. Job D $\to$ Job A: setup $s_{DA} = 3$. Start A at $13 + 3 = 16$, finishes at $C_A = 16 + p_A = 16 + 3 = 19$.
4. Job A $\to$ Job C: setup $s_{AC} = 1$. Start C at $19 + 1 = 20$, finishes at $C_C = 20 + p_C = 20 + 2 = 22$.

$$\text{Total Setup Time} = 1 + 3 + 3 + 1 = 8$$
$$C_{\max}(\pi_1) = \sum p_j + \text{Total Setup} = 14 + 8 = \mathbf{22}$$

#### Evaluating Sequence 2: $\pi_2 = (A, B, C, D)$
1. Start at depot 0 $\to$ Job A: setup $s_{0A} = 2$. Start A at 2, finishes at $C_A = 2 + 3 = 5$.
2. Job A $\to$ Job B: setup $s_{AB} = 8$. Start B at $5 + 8 = 13$, finishes at $C_B = 13 + 5 = 18$.
3. Job B $\to$ Job C: setup $s_{BC} = 7$. Start C at $18 + 7 = 25$, finishes at $C_C = 25 + 2 = 27$.
4. Job C $\to$ Job D: setup $s_{CD} = 4$. Start D at $27 + 4 = 31$, finishes at $C_D = 31 + 4 = 35$.

$$\text{Total Setup Time} = 2 + 8 + 7 + 4 = 21$$
$$C_{\max}(\pi_2) = 14 + 21 = \mathbf{35}$$

#### Concrete Implication
While in Problem 4 both permutations yielded identical makespan 14, introducing setup transitions causes makespan to diverge by **$35 - 22 = 13$ time units (a 59.1% penalty)**! Minimizing makespan is now exactly equivalent to finding the shortest Hamiltonian path in the ATSP graph from Problem 3.

---

## 6. Research Questions and Testable Hypotheses

To guide empirical investigation with academic rigor, this research poses four explicit questions:

### Research Question 1 (RQ1: Local Window DP Contribution)
*Does embedding an exact sliding-window Held-Karp dynamic programming polisher inside an Adaptive Large Neighborhood Search framework achieve statistically significant makespan reductions compared to plain ALNS under identical wall-clock time budgets?*
- **Hypothesis H1**: Because sequence-dependent setups create tight combinatorial interdependencies across adjacent jobs, an exact $k$-job DP ($k \in [6, 10]$) will systematically resolve sub-optimal local orderings that stochastic pairwise swaps cannot traverse, resulting in a statistically significant lower mean gap to lower bound ($p < 0.05$ via paired Wilcoxon test with Holm correction).

### Research Question 2 (RQ2: Scaling and Problem Topologies)
*How does the performance benefit of ALNS-WDP vary as problem size scales ($n \in [10, 200]$), release date congestion increases ($\alpha \in \{0.0, 0.3, 0.6\}$), and setup topologies shift between symmetric (Euclidean) and asymmetric?*
- **Hypothesis H2a**: At $\alpha = 0.0$ (no release delay), setup times completely dictate makespan variance, maximizing the relative advantage of ALNS-WDP.
- **Hypothesis H2b**: As $\alpha$ increases to $0.6$, release delays introduce unavoidable machine idling that dominates makespan, compressing the percentage gap between metaheuristics.
- **Hypothesis H2c**: Asymmetric instances exhibit greater local search landscape ruggedness than symmetric instances, yielding larger margins of improvement for ALNS-WDP over standard Genetic Algorithms.

### Research Question 3 (RQ3: Boundary with Exact Methods)
*At what problem scale $n$ and time threshold does ALNS-WDP surpass exact mathematical programming (CP-SAT MILP) in solution quality, and where does it fail against exact methods?*
- **Hypothesis H3**: For small instances ($n \le 15$), CP-SAT and exact global Held-Karp DP will reach proven mathematical optimality in $<1$~s, exposing an initialization overhead in ALNS-WDP. For $n \ge 30$, branch-and-cut in CP-SAT will suffer combinatorial thrashing, while ALNS-WDP will deliver superior makespan within identical time budgets.

### Research Question 4 (RQ4: Multi-Objective Landscape)
*How does scalarized ALNS-WDP compare with standard Pareto evolutionary search (NSGA-II) in approximating the bi-objective frontier $(C_{\max}, \sum w_j T_j)$ measured by Hypervolume and Inverted Generational Distance (IGD)?*
- **Hypothesis H4**: NSGA-II maintains wider population diversity along intermediate Pareto trade-off regions, whereas scalarized ALNS-WDP achieves superior convergence at the extreme ends of the frontier due to deep single-objective neighborhood intensification.

---

## 7. References
1. **Graham, R. L., Lawler, E. L., Lenstra, J. K., & Rinnooy Kan, A. H. G.** (1979). Optimization and approximation in deterministic sequencing and scheduling: a survey. *Annals of Discrete Mathematics*, 5, 287-326.
2. **Garey, M. R., & Johnson, D. S.** (1979). *Computers and Intractability: A Guide to the Theory of NP-Completeness*. W. H. Freeman and Company, San Francisco.
3. **Pinedo, M. L.** (2016). *Scheduling: Theory, Algorithms, and Systems* (5th ed.). Springer, New York.
4. **Lawler, E. L.** (1973). Optimal sequencing of a single machine subject to precedence constraints. *Management Science*, 19(5), 544-546.
5. **Lenstra, J. K., Rinnooy Kan, A. H. G., & Brucker, P.** (1977). Complexity of machine scheduling problems. *Annals of Discrete Mathematics*, 1, 343-362.
6. **Lawler, E. L.** (1977). A 'pseudopolynomial' algorithm for sequencing jobs to minimize total tardiness. *Annals of Discrete Mathematics*, 1, 331-342.
7. **Rinnooy Kan, A. H. G.** (1976). *Machine Scheduling Problems: Classification, Complexity and Computations*. Nijhoff, The Hague.
8. **Baker, K. R.** (1974). *Introduction to Sequencing and Scheduling*. John Wiley & Sons, New York.
9. **Horn, W. A.** (1974). Some simple scheduling algorithms. *Naval Research Logistics Quarterly*, 21(1), 177-185.
