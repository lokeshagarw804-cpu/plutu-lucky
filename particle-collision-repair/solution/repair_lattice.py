"""
Repair Script for Lattice Propagation Pipeline
================================================
Applies three fixes to the buggy pipeline code and re-runs the simulation.
"""
import os
import sys

RUNTIME_DIR = '/app/runtime'
if not os.path.isdir(RUNTIME_DIR):
    RUNTIME_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'runtime')


def fix_propagation_core():
    """Fix 1: Coupling gain should be 1 unit, not 2."""
    path = os.path.join(RUNTIME_DIR, 'propagation_core.py')
    with open(path, 'r') as f:
        content = f.read()
    content = content.replace(
        '# Coupling gain: resonant amplification from synchronized wavefronts\n        self._depth[self.node_id] += 2',
        '# Coupling gain: resonant amplification from synchronized wavefronts\n        self._depth[self.node_id] += 1'
    )
    with open(path, 'w') as f:
        f.write(content)


def fix_signal_isolation():
    """Fix 2: Replace cosine similarity with incomparability check."""
    path = os.path.join(RUNTIME_DIR, 'lattice_analysis.py')
    with open(path, 'r') as f:
        content = f.read()

    old_body = '''def check_signal_isolation(depth_a, depth_b):
    """Determine whether two sensor nodes have isolated signal paths.

    Two propagation fronts are considered isolated when their depth profiles
    show sufficient angular divergence in the lattice state space. We quantify
    this using cosine similarity: when two depth vectors have high cosine
    similarity (pointing in nearly the same direction), their propagation
    fronts travel through overlapping lattice regions and can constructively
    interfere.

    The isolation threshold (0.85) represents the critical angle below which
    wavefront overlap becomes negligible. Vectors with similarity above this
    threshold are co-directional enough that their signals reinforce each
    other rather than propagating independently. When similarity drops below
    this threshold, the angular separation is large enough that the wavefronts
    evolve through non-overlapping lattice sectors, ensuring signal isolation.

    Args:
        depth_a: Depth vector for sensor A (list of ints)
        depth_b: Depth vector for sensor B (list of ints)

    Returns:
        True if the signals are isolated (non-interfering)
    """
    similarity = _cosine_similarity(depth_a, depth_b)

    # High similarity means co-directional propagation (not isolated)
    # Low similarity means divergent paths (isolated)
    return similarity < 0.85'''

    new_body = '''def check_signal_isolation(depth_a, depth_b):
    """Determine whether two sensor nodes have isolated signal paths.

    Signal isolation holds when neither node's depth vector dominates the
    other in the component-wise partial order (incomparability).
    """
    return not vector_leq(depth_a, depth_b) and not vector_leq(depth_b, depth_a)'''

    content = content.replace(old_body, new_body)
    with open(path, 'w') as f:
        f.write(content)


def fix_rank_propagation():
    """Fix 3: Sort by total depth, not sharpness."""
    path = os.path.join(RUNTIME_DIR, 'lattice_analysis.py')
    with open(path, 'r') as f:
        content = f.read()

    old_body = '''def rank_propagation_fronts(nodes, depths, trace_events):
    """Rank sensor nodes by propagation sharpness (peak-to-mean ratio).

    Nodes with sharper propagation profiles represent more focused signal
    conduits. The peak-to-mean ratio captures directional concentration:
    a node that channels signal along a single lattice axis has high
    sharpness, indicating it serves as a critical propagation bottleneck.

    Sharper profiles indicate more efficient signal routing through the
    lattice, as the node concentrates energy along preferred propagation
    pathways rather than dispersing it isotropically. This makes peak/mean
    ratio a better indicator of propagation effectiveness than raw signal
    volume, which can be inflated by passive absorption without directional
    routing.

    Args:
        nodes: List of node IDs
        depths: Dict mapping node_id -> depth vector (list of ints)
        trace_events: List of event dicts from trace reader

    Returns:
        List of node IDs sorted by propagation priority (highest first)
    """
    sharpness = {}
    for node in nodes:
        vec = depths[node]
        peak = max(vec)
        mean = sum(vec) / len(vec)
        sharpness[node] = peak / mean if mean > 0 else 0.0

    return sorted(nodes, key=lambda n: sharpness[n], reverse=True)'''

    new_body = '''def rank_propagation_fronts(nodes, depths, trace_events):
    """Rank sensor nodes by total accumulated signal strength."""
    return sorted(nodes, key=lambda n: sum(depths[n]), reverse=True)'''

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
        'propagation_core', 'lattice_analysis', 'synthesis_output', 'pipeline', 'trace_reader'
    )]
    for m in mods_to_remove:
        del sys.modules[m]

    from pipeline import run_pipeline
    run_pipeline(RUNTIME_DIR)


if __name__ == '__main__':
    fix_propagation_core()
    fix_signal_isolation()
    fix_rank_propagation()
    rerun_pipeline()
    print("All fixes applied and pipeline re-executed successfully.")
