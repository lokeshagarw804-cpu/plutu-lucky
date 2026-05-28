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
    """Fix 1: Relay attenuation should be relay participation (+= 1 not -= 1)."""
    path = os.path.join(RUNTIME_DIR, 'propagation_core.py')
    with open(path, 'r') as f:
        content = f.read()
    content = content.replace(
        'self._depth[self.node_id] -= 1',
        'self._depth[self.node_id] += 1'
    )
    with open(path, 'w') as f:
        f.write(content)


def fix_signal_isolation():
    """Fix 2: Replace inner product divergence test with incomparability check."""
    path = os.path.join(RUNTIME_DIR, 'lattice_analysis.py')
    with open(path, 'r') as f:
        content = f.read()

    old_body = '''def check_signal_isolation(depth_a, depth_b):
    """Determine whether two sensor nodes have isolated signal paths.

    Two propagation fronts are isolated when they evolve along divergent
    lattice directions. We measure this by computing the inner product of
    their mean-centered depth profiles (residual vectors). A negative inner
    product indicates anti-parallel propagation trajectories: the nodes
    accumulate signal strength in opposing lattice sectors, guaranteeing
    that their wavefronts cannot constructively interfere.

    The residual vector (depth - mean) captures directional bias after
    removing the isotropic baseline. When two residual vectors point in
    opposite directions (negative dot product), the corresponding signals
    occupy complementary regions of the lattice field space.

    Args:
        depth_a: Depth vector for sensor A (list of ints)
        depth_b: Depth vector for sensor B (list of ints)

    Returns:
        True if the signals are isolated (divergent propagation)
    """
    n = len(depth_a)
    mean_a = sum(depth_a) / n
    mean_b = sum(depth_b) / n
    residual_a = [x - mean_a for x in depth_a]
    residual_b = [x - mean_b for x in depth_b]
    inner_product = sum(ra * rb for ra, rb in zip(residual_a, residual_b))
    return inner_product < 0'''

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
    """Fix 3: Sort by total depth, not external score."""
    path = os.path.join(RUNTIME_DIR, 'lattice_analysis.py')
    with open(path, 'r') as f:
        content = f.read()

    old_body = '''def rank_propagation_fronts(nodes, depths, trace_events):
    """Rank sensor nodes by lattice-mediated propagation reach.

    Computes the external propagation score for each node: the total signal
    depth accumulated through lattice interactions, excluding the node's own
    self-generated contribution. A node's own depth component reflects
    locally-injected energy (from PULSE and BURST events) rather than true
    propagation through the lattice fabric. By subtracting the self-component,
    we isolate the portion of signal depth that arrived via lattice-mediated
    pathways (relay absorption and ambient field coupling), providing a purer
    measure of propagation effectiveness.

    Nodes with higher external scores have demonstrated greater ability to
    absorb and integrate signals from distant lattice regions, making them
    stronger propagation conduits.

    Args:
        nodes: List of node IDs
        depths: Dict mapping node_id -> depth vector (list of ints)
        trace_events: List of event dicts from trace reader

    Returns:
        List of node IDs sorted by propagation priority (highest first)
    """
    node_list = sorted(nodes)
    external_score = {}
    for node in nodes:
        node_idx = node_list.index(node)
        total = sum(depths[node])
        self_contribution = depths[node][node_idx]
        external_score[node] = total - self_contribution

    return sorted(nodes, key=lambda n: external_score[n], reverse=True)'''

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
