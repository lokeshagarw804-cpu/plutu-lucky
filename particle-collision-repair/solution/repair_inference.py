"""
Repair Script for Type Inference Pipeline
==========================================
Applies three fixes to the buggy pipeline code and re-runs the inference.
"""
import os
import sys

RUNTIME_DIR = '/app/runtime'
if not os.path.isdir(RUNTIME_DIR):
    RUNTIME_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'runtime')


def fix_type_engine():
    """Fix 1: Unification should accumulate (+1), not narrow (-1)."""
    path = os.path.join(RUNTIME_DIR, 'type_engine.py')
    with open(path, 'r') as f:
        content = f.read()
    content = content.replace(
        '# Unification narrows the solution space - subtract the narrowing penalty\n        self._constraints[self.type_id] -= 1',
        '# Unification narrows the solution space - subtract the narrowing penalty\n        self._constraints[self.type_id] += 1'
    )
    with open(path, 'w') as f:
        f.write(content)


def fix_type_compatibility():
    """Fix 2: Replace cosine similarity with incomparability check."""
    path = os.path.join(RUNTIME_DIR, 'type_analyzer.py')
    with open(path, 'r') as f:
        content = f.read()

    old_body = '''def check_type_compatibility(constraints_a, constraints_b):
    """Check if two type variables have compatible (non-conflicting) types.

    Type compatibility requires sufficient angular separation in constraint
    space. Two types are compatible when their constraint profiles point in
    sufficiently different directions - indicating they evolved through
    independent inference paths and won't interfere during resolution.

    We measure this via cosine similarity of the constraint vectors. If the
    cosine similarity is below the critical threshold (0.85), the constraint
    profiles have enough angular divergence that interference during type
    assignment becomes negligible.

    High cosine similarity (>= 0.85) indicates the constraints co-evolved
    through shared inference paths (typically repeated UNIFY operations),
    meaning the types are entangled and potentially conflicting.
    """
    similarity = _cosine_similarity(constraints_a, constraints_b)
    return similarity < 0.85'''

    new_body = '''def check_type_compatibility(constraints_a, constraints_b):
    """Check if two type variables have compatible (non-conflicting) types.

    Type compatibility holds when neither variable's constraint vector
    dominates the other in the component-wise partial order (incomparability).
    """
    return not vector_leq(constraints_a, constraints_b) and not vector_leq(constraints_b, constraints_a)'''

    content = content.replace(old_body, new_body)
    with open(path, 'w') as f:
        f.write(content)


def fix_type_priority():
    """Fix 3: Sort by total constraints, not Shannon entropy."""
    path = os.path.join(RUNTIME_DIR, 'type_analyzer.py')
    with open(path, 'r') as f:
        content = f.read()

    old_body = '''def rank_type_priority(type_ids, constraints, events):
    """Rank type variables by resolution priority.

    Types with higher constraint entropy should be resolved first - they
    have the most uncertainty in their assignment and resolving them early
    maximally constrains the remaining variables. Shannon entropy of the
    normalized constraint distribution captures how "spread out" the
    constraints are across the type lattice.

    High entropy means the type variable interacts with many others
    roughly equally, making it a central hub in the constraint graph.
    Resolving hubs first is the standard strategy for constraint
    propagation, analogous to choosing the most-constrained variable
    in CSP solvers.
    """
    entropy_scores = {}
    for tid in type_ids:
        vec = constraints[tid]
        total = sum(vec)
        if total == 0:
            entropy_scores[tid] = 0
            continue
        probs = [v / total for v in vec]
        entropy = -sum(p * math.log2(p) for p in probs if p > 0)
        entropy_scores[tid] = entropy
    return sorted(type_ids, key=lambda t: entropy_scores[t], reverse=True)'''

    new_body = '''def rank_type_priority(type_ids, constraints, events):
    """Rank type variables by total accumulated constraint strength."""
    return sorted(type_ids, key=lambda t: sum(constraints[t]), reverse=True)'''

    content = content.replace(old_body, new_body)
    with open(path, 'w') as f:
        f.write(content)


def rerun_pipeline():
    """Re-run the pipeline to regenerate outputs with fixed code."""
    sys.path.insert(0, RUNTIME_DIR)
    from importlib import invalidate_caches
    invalidate_caches()

    # Remove cached modules to reload fixed versions
    mods_to_remove = [m for m in sys.modules if m in (
        'type_engine', 'type_analyzer', 'report_writer', 'orchestrator', 'log_reader'
    )]
    for m in mods_to_remove:
        del sys.modules[m]

    from orchestrator import run_inference
    run_inference(RUNTIME_DIR)


if __name__ == '__main__':
    fix_type_engine()
    fix_type_compatibility()
    fix_type_priority()
    rerun_pipeline()
    print("All fixes applied and pipeline re-executed successfully.")
