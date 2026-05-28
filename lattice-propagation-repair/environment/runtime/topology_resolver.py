# PLUTU-LUCKY-CANARY
"""Topology path resolution for directed lattice graphs.

Implements DFS-based path enumeration with cycle detection and
strongly connected component analysis for complex lattice topologies.
"""

import math


def build_adjacency(topology):
    """Build adjacency list from topology edge definitions.

    Args:
        topology: Dict with 'num_nodes' and 'edges' keys.

    Returns:
        Dict mapping source node to list of (target, edge_data) tuples.
    """
    adj = {}
    for i in range(topology['num_nodes']):
        adj[i] = []
    for edge in topology['edges']:
        adj[edge['from']].append((edge['to'], edge))
    return adj


def find_all_paths(adjacency, source, target, max_hops):
    """Find all simple paths from source to target using DFS.

    Enumerates every simple (non-repeating) path up to max_hops length.
    Uses visited-set backtracking to explore all branches.

    Args:
        adjacency: Adjacency list from build_adjacency().
        source: Starting node ID.
        target: Destination node ID.
        max_hops: Maximum number of edges in any path.

    Returns:
        List of paths, where each path is a list of node IDs.
    """
    paths = []
    visited = set()

    def dfs(node, current_path, depth):
        if depth > max_hops:
            return
        if node == target:
            paths.append(list(current_path))
            return

        visited.add(node)
        neighbors = [n for n, _ in adjacency[node] if n not in visited]

        if len(neighbors) == 1 and neighbors[0] == target:
            paths.append(current_path + [target])
            return

        for neighbor, edge in adjacency[node]:
            if neighbor not in visited:
                current_path.append(neighbor)
                dfs(neighbor, current_path, depth + 1)
                current_path.pop()

        visited.discard(node)

    dfs(source, [source], 0)
    return paths


def get_path_edges(adjacency, path):
    """Retrieve edge data for each hop in a path.

    Args:
        adjacency: Adjacency list from build_adjacency().
        path: List of node IDs forming the path.

    Returns:
        List of edge data dicts for each hop.
    """
    edges = []
    for i in range(len(path) - 1):
        src = path[i]
        dst = path[i + 1]
        for neighbor, edge in adjacency[src]:
            if neighbor == dst:
                edges.append(edge)
                break
    return edges


def detect_cycles(adjacency, num_nodes):
    """Detect all cycles in the directed graph using color-based DFS.

    Implements three-color marking (WHITE=0, GRAY=1, BLACK=2) to
    identify back edges that indicate cycles in the topology.

    Args:
        adjacency: Adjacency list from build_adjacency().
        num_nodes: Total number of nodes in the graph.

    Returns:
        List of cycles found, each as a list of node IDs.
    """
    WHITE, GRAY, BLACK = 0, 1, 2
    color = [WHITE] * num_nodes
    parent = [-1] * num_nodes
    cycles = []

    def dfs_cycle(node, path):
        color[node] = GRAY
        path.append(node)

        for neighbor, _ in adjacency[node]:
            if color[neighbor] == GRAY:
                cycle_start = path.index(neighbor)
                cycles.append(path[cycle_start:] + [neighbor])
            elif color[neighbor] == WHITE:
                parent[neighbor] = node
                dfs_cycle(neighbor, path)

        path.pop()
        color[node] = BLACK

    for node in range(num_nodes):
        if color[node] == WHITE:
            dfs_cycle(node, [])

    return cycles


def find_strongly_connected_components(adjacency, num_nodes):
    """Find SCCs using Kosaraju's algorithm.

    Two-pass algorithm: first pass determines finish order on original
    graph, second pass runs DFS on transposed graph in reverse finish order.

    Args:
        adjacency: Adjacency list from build_adjacency().
        num_nodes: Total number of nodes.

    Returns:
        List of SCCs, each as a sorted list of node IDs.
    """
    visited = [False] * num_nodes
    finish_order = []

    def dfs_forward(node):
        visited[node] = True
        for neighbor, _ in adjacency[node]:
            if not visited[neighbor]:
                dfs_forward(neighbor)
        finish_order.append(node)

    for node in range(num_nodes):
        if not visited[node]:
            dfs_forward(node)

    transpose = {i: [] for i in range(num_nodes)}
    for node in range(num_nodes):
        for neighbor, edge in adjacency[node]:
            transpose[neighbor].append((node, edge))

    visited = [False] * num_nodes
    sccs = []

    def dfs_backward(node, component):
        visited[node] = True
        component.append(node)
        for neighbor, _ in transpose[node]:
            if not visited[neighbor]:
                dfs_backward(neighbor, component)

    for node in reversed(finish_order):
        if not visited[node]:
            component = []
            dfs_backward(node, component)
            sccs.append(sorted(component))

    return sccs


def compute_path_weight(edges):
    """Compute composite weight of a path for ranking.

    Uses a combination of total attenuation and delay to rank paths
    by their signal quality contribution.

    Args:
        edges: List of edge data dicts.

    Returns:
        Composite weight value (higher = better signal quality).
    """
    if not edges:
        return 0.0

    total_atten = 1.0
    total_delay = 0.0
    for e in edges:
        total_atten *= e['attenuation']
        total_delay += e['delay']

    delay_penalty = math.exp(-total_delay * 100)
    return total_atten * delay_penalty
