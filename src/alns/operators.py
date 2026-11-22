"""
Adaptive Large Neighborhood Search (ALNS) Destroy and Repair Operators:
- Destroy: Random, Worst-Setup, Release-Cluster, Relatedness (Shaw)
- Repair: Incremental Greedy Best-Insertion, Incremental Regret-2 Insertion
"""

import math
import random
import time
from typing import List, Tuple, Set, Optional
from src.evaluator import (
    compute_makespan,
    compute_prefix_completions,
    evaluate_incremental_insertion_makespan,
)


# ----------------------------- DESTROY OPERATORS -----------------------------

def destroy_random(
    perm: List[int],
    q: int,
    rng: random.Random,
    **kwargs,
) -> Tuple[List[int], List[int]]:
    """Randomly removes q jobs from permutation."""
    n = len(perm)
    q = min(q, n - 1)
    remove_indices = sorted(rng.sample(range(n), q), reverse=True)
    partial = list(perm)
    removed = []
    for idx in remove_indices:
        removed.append(partial.pop(idx))
    return partial, removed


def destroy_worst_setup(
    perm: List[int],
    q: int,
    rng: random.Random,
    p: List[int],
    r: List[int],
    s: List[List[int]],
    s0: List[int],
    p_randomness: float = 3.0,
    **kwargs,
) -> Tuple[List[int], List[int]]:
    """
    Worst-Setup Removal:
    Identifies jobs responsible for large setup transitions or idle delays.
    """
    n = len(perm)
    q = min(q, n - 1)
    
    costs = []
    for idx, job in enumerate(perm):
        prev_job = perm[idx - 1] if idx > 0 else None
        next_job = perm[idx + 1] if idx < n - 1 else None
        
        setup_in = s0[job] if prev_job is None else s[prev_job][job]
        setup_out = s[job][next_job] if next_job is not None else 0
        direct_bypass = s[prev_job][next_job] if (prev_job is not None and next_job is not None) else 0
        
        cost = (setup_in + setup_out) - direct_bypass
        costs.append((cost, idx, job))
        
    costs.sort(key=lambda x: x[0], reverse=True)
    
    remove_indices = set()
    while len(remove_indices) < q and costs:
        y = rng.random()
        chosen_idx = int(math.floor((y ** p_randomness) * len(costs)))
        chosen_idx = min(chosen_idx, len(costs) - 1)
        _, orig_pos, job = costs.pop(chosen_idx)
        remove_indices.add(orig_pos)
        
    sorted_pos = sorted(remove_indices, reverse=True)
    partial = list(perm)
    removed = []
    for pos in sorted_pos:
        removed.append(partial.pop(pos))
        
    return partial, removed


def destroy_release_cluster(
    perm: List[int],
    q: int,
    rng: random.Random,
    r: List[int],
    **kwargs,
) -> Tuple[List[int], List[int]]:
    """
    Release-Date Cluster Removal:
    Picks a pivot job and removes jobs with temporally adjacent release dates.
    """
    n = len(perm)
    q = min(q, n - 1)
    pivot_pos = rng.randrange(n)
    pivot_job = perm[pivot_pos]
    pivot_r = r[pivot_job]
    
    distances = [(abs(r[job] - pivot_r), idx, job) for idx, job in enumerate(perm)]
    distances.sort(key=lambda x: x[0])
    
    selected_indices = sorted([item[1] for item in distances[:q]], reverse=True)
    partial = list(perm)
    removed = []
    for pos in selected_indices:
        removed.append(partial.pop(pos))
    return partial, removed


def destroy_relatedness(
    perm: List[int],
    q: int,
    rng: random.Random,
    p: List[int],
    r: List[int],
    s: List[List[int]],
    **kwargs,
) -> Tuple[List[int], List[int]]:
    """
    Shaw-style Relatedness Removal:
    Removes jobs with similar processing times, release dates, and setup profiles.
    """
    n = len(perm)
    q = min(q, n - 1)
    pivot_pos = rng.randrange(n)
    pivot_job = perm[pivot_pos]
    
    max_p = max(max(p), 1)
    max_r = max(max(r), 1)
    max_s = max(max(max(row) for row in s), 1)
    
    relatedness = []
    for idx, job in enumerate(perm):
        if idx == pivot_pos:
            continue
        rel = (
            0.4 * (abs(p[job] - p[pivot_job]) / max_p)
            + 0.4 * (abs(r[job] - r[pivot_job]) / max_r)
            + 0.2 * ((s[pivot_job][job] + s[job][pivot_job]) / (2 * max_s))
        )
        relatedness.append((rel, idx, job))
        
    relatedness.sort(key=lambda x: x[0])
    chosen_pos = [pivot_pos] + [item[1] for item in relatedness[: q - 1]]
    chosen_pos.sort(reverse=True)
    
    partial = list(perm)
    removed = []
    for pos in chosen_pos:
        removed.append(partial.pop(pos))
    return partial, removed


# ----------------------------- REPAIR OPERATORS -----------------------------

def repair_greedy_best_insertion(
    partial: List[int],
    removed: List[int],
    p: List[int],
    r: List[int],
    s: List[List[int]],
    s0: List[int],
    rng: random.Random,
    deadline: Optional[float] = None,
) -> List[int]:
    """
    Accelerated Greedy Best-Fit Insertion:
    Uses precomputed prefix completions and O(n - pos) incremental evaluation.
    Respects optional wall-clock deadline.
    """
    curr_perm = list(partial)
    unplaced = list(removed)
    rng.shuffle(unplaced)
    
    while unplaced:
        if deadline is not None and time.perf_counter() >= deadline:
            curr_perm.extend(unplaced)
            break
            
        best_job = None
        best_pos = None
        best_cmax = float("inf")
        
        prefix_c = compute_prefix_completions(curr_perm, p, r, s, s0)
        m = len(curr_perm)
        
        for job in unplaced:
            for pos in range(m + 1):
                c = evaluate_incremental_insertion_makespan(
                    curr_perm, prefix_c, job, pos, p, r, s, s0
                )
                if c < best_cmax:
                    best_cmax = c
                    best_job = job
                    best_pos = pos
                    
        curr_perm.insert(best_pos, best_job)
        unplaced.remove(best_job)
        
    return curr_perm


def repair_regret2_insertion(
    partial: List[int],
    removed: List[int],
    p: List[int],
    r: List[int],
    s: List[List[int]],
    s0: List[int],
    rng: random.Random,
    deadline: Optional[float] = None,
) -> List[int]:
    """
    Accelerated Regret-2 Insertion:
    Evaluates best and second-best insertion costs using incremental suffix evaluation.
    Inserts job with maximum regret (c2 - c1). Respects optional wall-clock deadline.
    """
    curr_perm = list(partial)
    unplaced = list(removed)
    
    while unplaced:
        if deadline is not None and time.perf_counter() >= deadline:
            curr_perm.extend(unplaced)
            break
            
        if len(unplaced) == 1 or len(curr_perm) == 0:
            return repair_greedy_best_insertion(curr_perm, unplaced, p, r, s, s0, rng, deadline=deadline)
            
        prefix_c = compute_prefix_completions(curr_perm, p, r, s, s0)
        m = len(curr_perm)
        
        best_regret = -float("inf")
        selected_job = None
        selected_pos = None
        
        for job in unplaced:
            best_cost = float("inf")
            second_best_cost = float("inf")
            best_p = 0
            
            for pos in range(m + 1):
                c = evaluate_incremental_insertion_makespan(
                    curr_perm, prefix_c, job, pos, p, r, s, s0
                )
                if c < best_cost:
                    second_best_cost = best_cost
                    best_cost = c
                    best_p = pos
                elif c < second_best_cost:
                    second_best_cost = c
                    
            regret = second_best_cost - best_cost
            if regret > best_regret:
                best_regret = regret
                selected_job = job
                selected_pos = best_p
                
        curr_perm.insert(selected_pos, selected_job)
        unplaced.remove(selected_job)
        
    return curr_perm
