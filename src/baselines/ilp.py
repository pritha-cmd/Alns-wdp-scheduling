"""
Mixed-Integer Linear Programming (MILP) and Constraint Programming (CP-SAT) Solvers
for Single-Machine Scheduling: 1 | r_j, s_ij | C_max.
Includes warm-starting, matheuristics, and solver configuration comparisons.
"""

import time
from typing import List, Tuple, Optional, Dict, Any
import numpy as np
from src.evaluator import evaluate_schedule


def solve_ilp_cpsat(
    p: List[int],
    r: List[int],
    s: List[List[int]],
    s0: List[int],
    time_limit: float = 60.0,
    warm_start_perm: Optional[List[int]] = None,
    symmetry_breaking: bool = True,
    num_workers: int = 4,
) -> Tuple[Optional[List[int]], Optional[int], float, Dict[str, Any]]:
    """
    Solves 1 | r_j, s_ij | C_max using OR-Tools CP-SAT.
    Employs AddCircuit for subtour elimination, tight domain bounding,
    optional warm-start hinting, and optional symmetry breaking.
    """
    from ortools.sat.python import cp_model

    start_time = time.perf_counter()
    n = len(p)
    model = cp_model.CpModel()
    
    # Calculate a tight upper bound M for makespan
    big_m = sum(p) + max(s0) + sum(max(row) for row in s) + max(r) + 500
    nodes = list(range(n + 1))
    
    # Circuit arcs: (i, j, literal)
    arcs = []
    x = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                var = model.NewBoolVar(f"x_{i}_{j}")
                x[i, j] = var
                arcs.append((i, j, var))
                
    model.AddCircuit(arcs)
    
    # Start time integer variables with tight release date lower bounds
    S = {}
    S[0] = model.NewConstant(0)
    for j in range(1, n + 1):
        job_idx = j - 1
        S[j] = model.NewIntVar(int(r[job_idx]), int(big_m), f"S_{j}")
        
    # Start time propagation
    for j in range(1, n + 1):
        job_idx = j - 1
        model.Add(S[j] >= int(s0[job_idx])).OnlyEnforceIf(x[0, j])
        
    for i in range(1, n + 1):
        for j in range(1, n + 1):
            if i != j:
                u = i - 1
                v = j - 1
                model.Add(S[j] >= S[i] + int(p[u]) + int(s[u][v])).OnlyEnforceIf(x[i, j])
                
    # Makespan variable
    c_max = model.NewIntVar(0, int(big_m), "c_max")
    for j in range(1, n + 1):
        job_idx = j - 1
        model.Add(c_max >= S[j] + int(p[job_idx]))
        
    # Optional symmetry breaking: if two identical jobs exist
    if symmetry_breaking:
        for i in range(n):
            for j in range(i + 1, n):
                if (p[i] == p[j] and r[i] == r[j] and s0[i] == s0[j] and
                    s[i] == s[j] and [s[k][i] for k in range(n)] == [s[k][j] for k in range(n)]):
                    model.Add(S[i + 1] < S[j + 1])
                    
    # Warm start hinting
    if warm_start_perm is not None and len(warm_start_perm) == n:
        eval_res = evaluate_schedule(warm_start_perm, p, r, s, s0)
        # Hint circuit arcs
        curr_node = 0
        for job_idx in warm_start_perm:
            nxt_node = job_idx + 1
            model.AddHint(x[curr_node, nxt_node], 1)
            curr_node = nxt_node
        model.AddHint(x[curr_node, 0], 1)
        
        # Hint start times
        for job_idx in range(n):
            model.AddHint(S[job_idx + 1], eval_res.start_times[job_idx])
        model.AddHint(c_max, eval_res.c_max)
        
    model.Minimize(c_max)
    
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_workers = num_workers
    
    status = solver.Solve(model)
    elapsed = time.perf_counter() - start_time
    
    meta = {
        "status": solver.StatusName(status),
        "wall_time": solver.WallTime(),
        "user_time": solver.UserTime(),
        "branches": solver.NumBranches(),
        "conflicts": solver.NumConflicts(),
        "objective": solver.ObjectiveValue() if status in (cp_model.OPTIMAL, cp_model.FEASIBLE) else None,
        "best_bound": solver.BestObjectiveBound() if status in (cp_model.OPTIMAL, cp_model.FEASIBLE) else None,
    }
    
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        obj_val = int(round(solver.ObjectiveValue()))
        perm = []
        curr = 0
        while len(perm) < n:
            found = False
            for j in nodes:
                if j != curr and solver.Value(x[curr, j]) == 1:
                    if j != 0:
                        perm.append(j - 1)
                    curr = j
                    found = True
                    break
            if not found or curr == 0:
                break
        return perm, obj_val, elapsed, meta
    else:
        return None, None, elapsed, meta


def solve_cpsat_matheuristic(
    p: List[int],
    r: List[int],
    s: List[List[int]],
    s0: List[int],
    alns_perm: List[int],
    time_limit: float = 10.0,
) -> Tuple[Optional[List[int]], Optional[int], float, Dict[str, Any]]:
    """
    CP-SAT Matheuristic: warm-starts CP-SAT with ALNS-WDP solution to accelerate
    exact branch-and-cut and verify whether mathematical polishing can improve heuristic solutions.
    """
    return solve_ilp_cpsat(
        p=p,
        r=r,
        s=s,
        s0=s0,
        time_limit=time_limit,
        warm_start_perm=alns_perm,
        symmetry_breaking=True,
    )


def solve_ilp_pulp(
    p: List[int],
    r: List[int],
    s: List[List[int]],
    s0: List[int],
    time_limit: float = 60.0,
) -> Tuple[Optional[List[int]], Optional[int], float, Dict[str, Any]]:
    """Standard MTZ Mixed-Integer Linear Program formulated in PuLP/HiGHS."""
    import pulp

    start_time = time.perf_counter()
    n = len(p)
    prob = pulp.LpProblem("SingleMachineScheduling", pulp.LpMinimize)
    
    big_m = sum(p) + max(s0) + sum(max(row) for row in s) + max(r) + 1000
    nodes = list(range(n + 1))
    
    if hasattr(prob, "add_variable"):
        x = {
            (i, j): prob.add_variable(f"x_{i}_{j}", cat="Binary")
            for i in nodes
            for j in nodes
            if i != j
        }
        u = {i: prob.add_variable(f"u_{i}", lowBound=1, upBound=n, cat="Continuous") for i in range(1, n + 1)}
        S = {i: prob.add_variable(f"S_{i}", lowBound=0, cat="Continuous") for i in nodes}
        c_max = prob.add_variable("c_max", lowBound=0, cat="Continuous")
    else:
        x = {
            (i, j): pulp.LpVariable(f"x_{i}_{j}", cat=pulp.LpBinary)
            for i in nodes
            for j in nodes
            if i != j
        }
        u = {i: pulp.LpVariable(f"u_{i}", lowBound=1, upBound=n, cat=pulp.LpContinuous) for i in range(1, n + 1)}
        S = {i: pulp.LpVariable(f"S_{i}", lowBound=0, cat=pulp.LpContinuous) for i in nodes}
        c_max = pulp.LpVariable("c_max", lowBound=0, cat=pulp.LpContinuous)
    
    prob += c_max
    prob += S[0] == 0
    
    for i in nodes:
        prob += pulp.lpSum(x[i, j] for j in nodes if j != i) == 1
    for j in nodes:
        prob += pulp.lpSum(x[i, j] for i in nodes if i != j) == 1
        
    for i in range(1, n + 1):
        for j in range(1, n + 1):
            if i != j:
                prob += u[j] >= u[i] + 1 - n * (1 - x[i, j])
                
    for j in range(1, n + 1):
        prob += S[j] >= r[j - 1]
        
    for j in range(1, n + 1):
        prob += S[j] >= S[0] + s0[j - 1] - big_m * (1 - x[0, j])
        
    for i in range(1, n + 1):
        for j in range(1, n + 1):
            if i != j:
                prob += S[j] >= S[i] + p[i - 1] + s[i - 1][j - 1] - big_m * (1 - x[i, j])
                
    for j in range(1, n + 1):
        prob += c_max >= S[j] + p[j - 1]
        
    try:
        solver = pulp.HiGHS(msg=False, timeLimit=time_limit)
    except Exception:
        solver = None
        
    res = prob.solve(solver)
    elapsed = time.perf_counter() - start_time
    
    meta = {"res": str(res)}
    obj_val = c_max.value()
    if obj_val is not None:
        int_obj = int(round(obj_val))
        perm = []
        curr = 0
        for _ in range(n):
            for j in nodes:
                if j != curr:
                    val = x[curr, j].value()
                    if val is not None and val > 0.5:
                        if j != 0:
                            perm.append(j - 1)
                        curr = j
                        break
        return perm, int_obj, elapsed, meta
    return None, None, elapsed, meta
