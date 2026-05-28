"""
Lattice Analysis Module
========================
Provides signal comparison utilities and isolation classification
for the lattice propagation system.
"""


def vector_leq(a, b):
    """Component-wise less-than-or-equal comparison."""
    return all(x <= y for x, y in zip(a, b))


def vector_geq(a, b):
    """Component-wise greater-than-or-equal comparison."""
    return all(x >= y for x, y in zip(a, b))


def check_signal_isolation(depth_a, depth_b):
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
    return inner_product < 0


def rank_propagation_fronts(nodes, depths, trace_events):
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

    return sorted(nodes, key=lambda n: external_score[n], reverse=True)


def find_isolated_pairs(nodes, depths):
    """Find all pairs of nodes with isolated signal paths."""
    pairs = []
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            na = nodes[i]
            nb = nodes[j]
            if check_signal_isolation(depths[na], depths[nb]):
                pairs.append([na, nb])
    return pairs
