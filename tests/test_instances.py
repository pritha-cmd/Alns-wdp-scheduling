"""
Unit tests for Instance Generator (src/instances.py).
"""
import tempfile
from pathlib import Path
import pytest
import numpy as np
from src.instances import generate_instance, get_base_4job_instance, Instance


def test_instance_reproducibility():
    """Verify that same seed produces identical instance parameters."""
    inst1 = generate_instance(n=10, alpha=0.3, setup_type="asymmetric", seed=999)
    inst2 = generate_instance(n=10, alpha=0.3, setup_type="asymmetric", seed=999)
    
    assert inst1.p == inst2.p
    assert inst1.r == inst2.r
    assert inst1.s == inst2.s
    assert inst1.s0 == inst2.s0
    assert inst1.d == inst2.d
    assert inst1.w == inst2.w


def test_instance_serialization():
    """Verify that save and load preserve all properties identically."""
    inst = generate_instance(n=12, alpha=0.6, setup_type="symmetric", seed=555)
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_file = Path(tmpdir) / "test_inst.json"
        inst.save(tmp_file)
        loaded = Instance.load(tmp_file)
        
        assert loaded.name == inst.name
        assert loaded.n == inst.n
        assert loaded.p == inst.p
        assert loaded.r == inst.r
        assert loaded.s == inst.s
        assert loaded.s0 == inst.s0
        assert loaded.d == inst.d
        assert loaded.w == inst.w
        assert loaded.is_symmetric == inst.is_symmetric
        assert loaded.alpha == inst.alpha


def test_symmetric_setup_matrix():
    """Verify that symmetric instances have symmetric setup matrix."""
    inst = generate_instance(n=10, alpha=0.3, setup_type="symmetric", seed=777)
    s = np.array(inst.s)
    assert np.allclose(s, s.T), "Matrix must be symmetric"
    for i in range(inst.n):
        assert inst.s[i][i] == 0, "Diagonal of setup matrix must be 0"


def test_parameter_bounds():
    """Verify generated parameter values lie within specified bounds."""
    for n in [8, 15]:
        for alpha in [0.0, 0.3, 0.6]:
            for s_type in ["asymmetric", "symmetric"]:
                inst = generate_instance(n=n, alpha=alpha, setup_type=s_type, seed=42)
                assert all(1 <= pj <= 20 for pj in inst.p)
                assert all(1 <= wj <= 10 for wj in inst.w)
                if alpha == 0.0:
                    assert all(rj == 0 for rj in inst.r)
                else:
                    max_allowed_r = np.ceil(alpha * sum(inst.p))
                    assert all(0 <= rj <= max_allowed_r for rj in inst.r)
                for i in range(n):
                    for j in range(n):
                        if i != j:
                            assert 1 <= inst.s[i][j] <= 15
                        else:
                            assert inst.s[i][j] == 0

