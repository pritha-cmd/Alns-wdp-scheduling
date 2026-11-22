"""
Regression tests verifying CSV data uniqueness and integrity.
"""
from pathlib import Path
import pytest
import pandas as pd


def test_single_objective_csv_row_uniqueness():
    """Verify single_objective_benchmarks.csv contains strictly unique (instance, method, seed) records."""
    csv_path = Path("results/single_objective_benchmarks.csv")
    if not csv_path.exists():
        pytest.skip("results/single_objective_benchmarks.csv does not exist yet.")
        
    df = pd.read_csv(csv_path)
    dups = df.duplicated(subset=["instance", "method", "seed"]).sum()
    assert dups == 0, f"Found {dups} duplicate rows in {csv_path}!"


def test_biobjective_metrics_csv_uniqueness():
    """Verify biobjective_metrics.csv contains strictly unique (instance, method, seed) records."""
    csv_path = Path("results/biobjective_metrics.csv")
    if not csv_path.exists():
        pytest.skip("results/biobjective_metrics.csv does not exist yet.")
        
    df = pd.read_csv(csv_path)
    if "seed" in df.columns:
        dups = df.duplicated(subset=["instance", "method", "seed"]).sum()
        assert dups == 0, f"Found {dups} duplicate rows in {csv_path}!"

