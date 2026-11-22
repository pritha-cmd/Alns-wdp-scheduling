"""
NSGA-II Bi-Objective Baseline using Pymoo:
Minimizes (C_max, sum w_j T_j) for 1 | r_j, s_ij | (C_max, TWT).
Permutation encoding with Order Crossover (OX) and Inversion Mutation.
Includes Hypervolume and Inverted Generational Distance (IGD) calculations.
"""

import time
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
from pymoo.core.problem import Problem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.operators.sampling.rnd import PermutationRandomSampling
from pymoo.operators.crossover.ox import OrderCrossover
from pymoo.operators.mutation.inversion import InversionMutation
from pymoo.optimize import minimize
from pymoo.indicators.hv import Hypervolume
from pymoo.indicators.igd import IGD

from src.evaluator import compute_bi_objective


class SingleMachineBiObjectiveProblem(Problem):
    """Pymoo Problem specification for single machine bi-objective scheduling."""
    def __init__(
        self,
        p: List[int],
        r: List[int],
        s: List[List[int]],
        s0: List[int],
        d: List[int],
        w: List[int],
    ):
        self.p = p
        self.r = r
        self.s = s
        self.s0 = s0
        self.d = d
        self.w = w
        super().__init__(
            n_var=len(p),
            n_obj=2,
            n_ieq_constr=0,
            xl=0,
            xu=len(p) - 1,
            vtype=int,
        )

    def _evaluate(self, x, out, *args, **kwargs):
        pop_size = x.shape[0]
        f_vals = np.zeros((pop_size, 2), dtype=float)
        
        for i in range(pop_size):
            perm = x[i].tolist()
            cmax, twt = compute_bi_objective(
                perm, self.p, self.r, self.s, self.s0, self.d, self.w
            )
            f_vals[i, 0] = cmax
            f_vals[i, 1] = twt
            
        out["F"] = f_vals


def solve_nsga2(
    p: List[int],
    r: List[int],
    s: List[List[int]],
    s0: List[int],
    d: List[int],
    w: List[int],
    pop_size: int = 50,
    n_gen: int = 60,
    time_limit: Optional[float] = None,
    seed: int = 42,
) -> Tuple[np.ndarray, np.ndarray, float, int]:
    """
    Executes NSGA-II to approximate the Pareto front for (C_max, TWT).
    Supports either generational budget (n_gen) or strict wall-clock time limit.
    """
    start_time = time.perf_counter()
    problem = SingleMachineBiObjectiveProblem(p, r, s, s0, d, w)
    
    algorithm = NSGA2(
        pop_size=pop_size,
        sampling=PermutationRandomSampling(),
        crossover=OrderCrossover(prob=0.9),
        mutation=InversionMutation(prob=0.3),
        eliminate_duplicates=True,
    )
    
    if time_limit is not None and time_limit > 0:
        from pymoo.termination import get_termination
        termination = get_termination("time", time_limit)
    else:
        termination = ("n_gen", n_gen)
        
    res = minimize(
        problem,
        algorithm,
        termination,
        seed=seed,
        verbose=False,
    )
    
    elapsed = time.perf_counter() - start_time
    pareto_solutions = res.X if res.X is not None else np.array([])
    pareto_front = res.F if res.F is not None else np.array([])
    n_evals = res.algorithm.evaluator.n_eval
    
    return pareto_solutions, pareto_front, elapsed, n_evals


def compute_hypervolume(front: np.ndarray, ref_point: np.ndarray) -> float:
    """Computes hypervolume indicator given Pareto front and reference point."""
    if len(front) == 0:
        return 0.0
    hv = Hypervolume(ref_point=ref_point)
    return float(hv.do(front))


def compute_igd_metric(front: np.ndarray, reference_front: np.ndarray) -> float:
    """Computes Inverted Generational Distance (IGD) against reference front."""
    if len(front) == 0 or len(reference_front) == 0:
        return float("inf")
    igd = IGD(reference_front)
    return float(igd.do(front))
