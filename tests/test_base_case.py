"""
Verification of Problem 4 from the practical sheet:
4 jobs: A=3, B=5, C=2, D=4, r_j=0, s_ij=0.
Objective: minimize C_max.
Proof verification: all 4! = 24 permutations must yield makespan C_max = 14.
"""
import itertools
import pytest

def test_base_4job_makespan_invariance():
    jobs = {'A': 3, 'B': 5, 'C': 2, 'D': 4}
    job_ids = list(jobs.keys())
    all_perms = list(itertools.permutations(job_ids))
    
    assert len(all_perms) == 24, "There must be exactly 4! = 24 permutations."
    
    makespans = []
    for perm in all_perms:
        current_time = 0
        for job in perm:
            current_time += jobs[job]
        makespans.append(current_time)
        
    # Every permutation must yield exactly sum(p_j) = 14
    for makespan in makespans:
        assert makespan == 14, f"Permutation resulted in {makespan}, expected 14"
        
    assert min(makespans) == 14
    assert max(makespans) == 14
    print(f"Verified: all {len(all_perms)} permutations have C_max = 14. Minimum is 14.")

if __name__ == "__main__":
    test_base_4job_makespan_invariance()

