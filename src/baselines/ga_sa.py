"""
Single-Objective Genetic Algorithm (GA) and Simulated Annealing (SA)
for 1 | r_j, s_ij | C_max.
"""

import time
import math
import random
from typing import List, Tuple, Dict, Any
from src.evaluator import compute_makespan


def ox_crossover(parent1: List[int], parent2: List[int], rng: random.Random) -> Tuple[List[int], List[int]]:
    """Order Crossover (OX) preserving relative order and valid permutations."""
    n = len(parent1)
    if n <= 2:
        return list(parent1), list(parent2)
        
    idx1, idx2 = sorted(rng.sample(range(n), 2))
    
    def _ox_child(p1, p2):
        child = [-1] * n
        child[idx1 : idx2 + 1] = p1[idx1 : idx2 + 1]
        p1_set = set(child[idx1 : idx2 + 1])
        
        # Fill remaining positions circularly from p2
        p2_pos = (idx2 + 1) % n
        curr = (idx2 + 1) % n
        while -1 in child:
            candidate = p2[p2_pos]
            if candidate not in p1_set:
                child[curr] = candidate
                curr = (curr + 1) % n
            p2_pos = (p2_pos + 1) % n
        return child
        
    child1 = _ox_child(parent1, parent2)
    child2 = _ox_child(parent2, parent1)
    return child1, child2


def mutate_perm(perm: List[int], rng: random.Random) -> List[int]:
    """Applies swap, insert, or inversion mutation with equal probability."""
    n = len(perm)
    if n < 2:
        return list(perm)
    m_type = rng.choice(["swap", "insert", "invert"])
    res = list(perm)
    i, j = sorted(rng.sample(range(n), 2))
    if m_type == "swap":
        res[i], res[j] = res[j], res[i]
    elif m_type == "insert":
        val = res.pop(i)
        res.insert(j, val)
    else:  # invert
        res[i : j + 1] = reversed(res[i : j + 1])
    return res


def solve_ga(
    p: List[int],
    r: List[int],
    s: List[List[int]],
    s0: List[int],
    pop_size: int = 50,
    time_limit: float = 10.0,
    seed: int = 42,
    p_crossover: float = 0.85,
    p_mutation: float = 0.25,
) -> Tuple[List[int], int, float, int, List[Tuple[float, int]]]:
    """
    Standard Single-Objective Genetic Algorithm with elitism and OX crossover.
    Returns: best_perm, best_cmax, elapsed_time, total_evals, convergence_curve [(time, cmax)]
    """
    start_time = time.perf_counter()
    rng = random.Random(seed)
    n = len(p)
    eval_count = 0
    convergence = []
    
    # 1. Population initialization
    population = []
    fitnesses = []
    
    # Seed with ERD order
    erd = sorted(range(n), key=lambda j: (r[j], p[j]))
    population.append(erd)
    c_erd = compute_makespan(erd, p, r, s, s0)
    fitnesses.append(c_erd)
    eval_count += 1
    
    for _ in range(pop_size - 1):
        ind = list(range(n))
        rng.shuffle(ind)
        population.append(ind)
        c = compute_makespan(ind, p, r, s, s0)
        fitnesses.append(c)
        eval_count += 1
        
    best_idx = int(min(range(pop_size), key=lambda i: fitnesses[i]))
    best_cmax = fitnesses[best_idx]
    best_perm = list(population[best_idx])
    convergence.append((time.perf_counter() - start_time, best_cmax))
    
    # Generational evolution loop
    while time.perf_counter() - start_time < time_limit:
        # Elitism: retain top 2
        sorted_indices = sorted(range(pop_size), key=lambda i: fitnesses[i])
        new_pop = [list(population[sorted_indices[0]]), list(population[sorted_indices[1]])]
        new_fit = [fitnesses[sorted_indices[0]], fitnesses[sorted_indices[1]]]
        
        while len(new_pop) < pop_size:
            # Tournament selection (size 3)
            def _select():
                cand_idx = rng.sample(range(pop_size), 3)
                return population[min(cand_idx, key=lambda i: fitnesses[i])]
                
            p1 = _select()
            p2 = _select()
            
            # Crossover
            if rng.random() < p_crossover:
                c1, c2 = ox_crossover(p1, p2, rng)
            else:
                c1, c2 = list(p1), list(p2)
                
            # Mutation
            if rng.random() < p_mutation:
                c1 = mutate_perm(c1, rng)
            if rng.random() < p_mutation:
                c2 = mutate_perm(c2, rng)
                
            fit1 = compute_makespan(c1, p, r, s, s0)
            eval_count += 1
            new_pop.append(c1)
            new_fit.append(fit1)
            if fit1 < best_cmax:
                best_cmax = fit1
                best_perm = list(c1)
                convergence.append((time.perf_counter() - start_time, best_cmax))
                
            if len(new_pop) < pop_size:
                fit2 = compute_makespan(c2, p, r, s, s0)
                eval_count += 1
                new_pop.append(c2)
                new_fit.append(fit2)
                if fit2 < best_cmax:
                    best_cmax = fit2
                    best_perm = list(c2)
                    convergence.append((time.perf_counter() - start_time, best_cmax))
                    
        population = new_pop
        fitnesses = new_fit
        
    elapsed = time.perf_counter() - start_time
    convergence.append((elapsed, best_cmax))
    return best_perm, best_cmax, elapsed, eval_count, convergence


def solve_sa(
    p: List[int],
    r: List[int],
    s: List[List[int]],
    s0: List[int],
    time_limit: float = 10.0,
    seed: int = 42,
    t_initial: float = 100.0,
    alpha: float = 0.99,
    reheat_interval: int = 2000,
) -> Tuple[List[int], int, float, int, List[Tuple[float, int]]]:
    """
    Simulated Annealing with geometric cooling and stagnation reheating.
    """
    start_time = time.perf_counter()
    rng = random.Random(seed)
    n = len(p)
    eval_count = 0
    convergence = []
    
    # Initial state: ERD or random
    current_perm = sorted(range(n), key=lambda j: (r[j], p[j]))
    current_cmax = compute_makespan(current_perm, p, r, s, s0)
    eval_count += 1
    
    best_perm = list(current_perm)
    best_cmax = current_cmax
    convergence.append((0.0, best_cmax))
    
    T = t_initial
    stagnant_steps = 0
    
    while time.perf_counter() - start_time < time_limit:
        # Neighborhood move
        cand_perm = mutate_perm(current_perm, rng)
        cand_cmax = compute_makespan(cand_perm, p, r, s, s0)
        eval_count += 1
        
        delta = cand_cmax - current_cmax
        if delta < 0 or (T > 1e-4 and rng.random() < math.exp(-delta / T)):
            current_perm = cand_perm
            current_cmax = cand_cmax
            if current_cmax < best_cmax:
                best_cmax = current_cmax
                best_perm = list(current_perm)
                convergence.append((time.perf_counter() - start_time, best_cmax))
                stagnant_steps = 0
            else:
                stagnant_steps += 1
        else:
            stagnant_steps += 1
            
        T *= alpha
        if stagnant_steps >= reheat_interval:
            # Reheat
            T = t_initial * 0.5
            stagnant_steps = 0
            
    elapsed = time.perf_counter() - start_time
    convergence.append((elapsed, best_cmax))
    return best_perm, best_cmax, elapsed, eval_count, convergence

