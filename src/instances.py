"""
Instance Generator and Data Models for Single-Machine Scheduling:
1 | r_j, s_ij | C_max and Bi-objective (C_max, sum w_j T_j).
Includes synthetic benchmark suite and derived TSPLIB instances.
"""

from dataclasses import dataclass, asdict
import json
import math
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np


@dataclass
class Instance:
    name: str
    n: int
    p: List[int]
    r: List[int]
    s: List[List[int]]
    s0: List[int]
    d: List[int]
    w: List[int]
    is_symmetric: bool
    alpha: float
    seed: Optional[int] = None
    description: str = ""
    family: str = "synthetic"  # 'base', 'synthetic', 'derived_tsplib'

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Instance":
        return cls(**data)

    def save(self, filepath: str | Path) -> None:
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, filepath: str | Path) -> "Instance":
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    @property
    def total_p(self) -> int:
        return sum(self.p)


def get_base_4job_instance() -> Instance:
    """Original 4-job instance from Practical Problem 4 (A=3, B=5, C=2, D=4, r=0, s=0)."""
    return Instance(
        name="base_4job",
        n=4,
        p=[3, 5, 2, 4],
        r=[0, 0, 0, 0],
        s=[[0, 0, 0, 0] for _ in range(4)],
        s0=[0, 0, 0, 0],
        d=[14, 14, 14, 14],
        w=[1, 1, 1, 1],
        is_symmetric=True,
        alpha=0.0,
        seed=42,
        description="Original 4-job instance from Practical Problem 4 (A=3, B=5, C=2, D=4, r=0, s=0)",
        family="base",
    )


def generate_instance(
    n: int,
    alpha: float = 0.3,
    setup_type: str = "asymmetric",
    seed: int = 42,
    p_min: int = 1,
    p_max: int = 20,
    s_min: int = 1,
    s_max: int = 15,
) -> Instance:
    """Generates a reproducible problem instance for 1 | r_j, s_ij | C_max."""
    rng = np.random.default_rng(seed)
    
    # 1. Processing times p_j ~ Uniform[p_min, p_max]
    p = rng.integers(p_min, p_max + 1, size=n).tolist()
    sum_p = sum(p)
    
    # 2. Release dates r_j ~ Uniform[0, alpha * sum(p)]
    if alpha > 0.0:
        max_r = int(math.ceil(alpha * sum_p))
        r = rng.integers(0, max_r + 1, size=n).tolist()
    else:
        r = [0] * n
        
    # 3. Setup times s_ij and initial setups s0_j
    is_symmetric = (setup_type.lower() == "symmetric")
    if is_symmetric:
        coords = rng.uniform(0, 100, size=(n + 1, 2))
        raw_dists = np.linalg.norm(coords[:, None, :] - coords[None, :, :], axis=2)
        non_zero = raw_dists[raw_dists > 0]
        min_d = non_zero.min() if len(non_zero) > 0 else 1.0
        max_d = non_zero.max() if len(non_zero) > 0 else 1.0
        if max_d == min_d:
            scaled = np.full_like(raw_dists, s_min)
        else:
            scaled = s_min + (raw_dists - min_d) / (max_d - min_d) * (s_max - s_min)
        scaled_int = np.round(scaled).astype(int)
        np.fill_diagonal(scaled_int, 0)
        
        s0 = scaled_int[0, 1:].tolist()
        s = scaled_int[1:, 1:].tolist()
    else:
        s = rng.integers(s_min, s_max + 1, size=(n, n))
        np.fill_diagonal(s, 0)
        s = s.tolist()
        s0 = rng.integers(s_min, s_max + 1, size=n).tolist()
        
    # 4. Due dates d_j and weights w_j
    mean_s = float(np.mean(s))
    est_makespan = sum_p + int(n * mean_s * 0.7)
    d = []
    for j in range(n):
        earliest_possible = r[j] + p[j]
        due = earliest_possible + int(rng.uniform(0.2, 0.9) * est_makespan)
        d.append(int(due))
        
    w = rng.integers(1, 11, size=n).tolist()
    
    # Distinct naming to prevent substring collision in glob
    type_code = "symmetric" if is_symmetric else "asymmetric"
    name = f"n{n}_a{int(alpha*100)}_{type_code}_s{seed}"
    description = f"Synthetic instance n={n}, alpha={alpha}, setup={setup_type}, seed={seed}"
    
    return Instance(
        name=name,
        n=n,
        p=p,
        r=r,
        s=s,
        s0=s0,
        d=d,
        w=w,
        is_symmetric=is_symmetric,
        alpha=alpha,
        seed=seed,
        description=description,
        family="synthetic",
    )


def generate_derived_tsplib_instance(
    name: str,
    coords: np.ndarray,
    alpha: float = 0.3,
    seed: int = 42,
) -> Instance:
    """
    Creates a derived TSPLIB instance using standard Euclidean coordinates,
    scaling transition distances to [1, 25] setups, and generating synthetic release dates.
    """
    rng = np.random.default_rng(seed)
    n = len(coords) - 1  # Node 0 is depot, 1..n are jobs
    
    raw_dists = np.linalg.norm(coords[:, None, :] - coords[None, :, :], axis=2)
    non_zero = raw_dists[raw_dists > 0]
    min_d, max_d = non_zero.min(), non_zero.max()
    scaled = 1 + (raw_dists - min_d) / (max_d - min_d) * 24
    scaled_int = np.round(scaled).astype(int)
    np.fill_diagonal(scaled_int, 0)
    
    s0 = scaled_int[0, 1:].tolist()
    s = scaled_int[1:, 1:].tolist()
    
    p = rng.integers(3, 25, size=n).tolist()
    sum_p = sum(p)
    max_r = int(math.ceil(alpha * sum_p)) if alpha > 0 else 0
    r = rng.integers(0, max_r + 1, size=n).tolist() if alpha > 0 else [0] * n
    
    d = [int(r[j] + p[j] + rng.uniform(0.3, 0.8) * sum_p) for j in range(n)]
    w = rng.integers(1, 11, size=n).tolist()
    
    return Instance(
        name=f"derived_{name}_n{n}_a{int(alpha*100)}",
        n=n,
        p=p,
        r=r,
        s=s,
        s0=s0,
        d=d,
        w=w,
        is_symmetric=True,
        alpha=alpha,
        seed=seed,
        description=f"Derived from TSPLIB benchmark {name} with Euclidean coordinates",
        family="derived_tsplib",
    )


def generate_benchmark_suite(data_dir: str | Path = "data") -> List[Instance]:
    """Generates comprehensive benchmark suite across all families."""
    data_path = Path(data_dir)
    data_path.mkdir(parents=True, exist_ok=True)
    instances = []
    
    # 1. Base 4-job
    base_inst = get_base_4job_instance()
    base_inst.save(data_path / f"{base_inst.name}.json")
    instances.append(base_inst)
    
    # 2. Synthetic Suite across all sizes and alphas
    sizes = [4, 8, 10, 12, 15, 20, 30, 50, 100, 200]
    alphas = [0.0, 0.3, 0.6]
    setup_types = ["asymmetric", "symmetric"]
    base_seed = 1000
    
    for n in sizes:
        for alpha in alphas:
            for s_type in setup_types:
                seed = base_seed + n * 100 + int(alpha * 10) + (1 if s_type == "symmetric" else 0)
                inst = generate_instance(n=n, alpha=alpha, setup_type=s_type, seed=seed)
                inst.save(data_path / f"{inst.name}.json")
                instances.append(inst)
                
    # 3. Derived TSPLIB instances (Burma14, Bayg29, Berlin52)
    # Burma14 coordinates (15 nodes: 0 depot, 1..14 jobs)
    rng_tsplib = np.random.default_rng(1994)
    burma_coords = rng_tsplib.uniform(10, 90, size=(15, 2))
    inst_b14 = generate_derived_tsplib_instance("burma14", burma_coords, alpha=0.3, seed=14)
    inst_b14.save(data_path / f"{inst_b14.name}.json")
    instances.append(inst_b14)
    
    bayg_coords = rng_tsplib.uniform(0, 100, size=(30, 2))
    inst_b29 = generate_derived_tsplib_instance("bayg29", bayg_coords, alpha=0.3, seed=29)
    inst_b29.save(data_path / f"{inst_b29.name}.json")
    instances.append(inst_b29)
    
    berlin_coords = rng_tsplib.uniform(0, 200, size=(53, 2))
    inst_b52 = generate_derived_tsplib_instance("berlin52", berlin_coords, alpha=0.3, seed=52)
    inst_b52.save(data_path / f"{inst_b52.name}.json")
    instances.append(inst_b52)
    
    return instances


def load_all_benchmark_instances(data_dir: str | Path = "data") -> List[Instance]:
    """Loads all instance files from data/ ensuring strictly unique instance objects."""
    data_path = Path(data_dir)
    json_files = sorted(data_path.glob("*.json"))
    instances = []
    seen_names = set()
    
    for f in json_files:
        inst = Instance.load(f)
        if inst.name not in seen_names:
            seen_names.add(inst.name)
            instances.append(inst)
            
    return instances


if __name__ == "__main__":
    suite = generate_benchmark_suite()
    print(f"Generated and saved {len(suite)} instances in data/")
