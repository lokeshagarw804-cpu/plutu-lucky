"""Shortest-path routing engine — Dijkstra's algorithm.

Builds a weighted directed graph from observed packet hops and computes
optimal routing costs between all node pairs. The algorithm uses a
stability threshold to avoid thrashing on near-equal paths caused by
transient link cost variations.
"""
import configparser
import heapq


class RoutingEngine:
    """Computes shortest-path costs using Dijkstra with stability damping."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._nodes = [n.strip() for n in self._config.get("network", "nodes").split(",")]
        self._min_hop_cost = self._config.getint("routing", "min_hop_cost")
        self._max_hops = self._config.getint("routing", "max_hops")
        self._graph = {}

    def build_graph(self, packets):
        """Build adjacency graph from observed packet hops.

        For each packet, extracts hop-to-hop edges with their costs.
        If an edge is seen multiple times, keeps the minimum cost.
        """
        for packet in packets:
            hops = packet["hops"]
            costs = packet["cost_per_hop"]
            for i in range(len(costs)):
                src_node = hops[i]
                dst_node = hops[i + 1]
                edge_cost = costs[i]

                if src_node not in self._graph:
                    self._graph[src_node] = {}

                if dst_node not in self._graph[src_node]:
                    self._graph[src_node][dst_node] = edge_cost
                else:
                    self._graph[src_node][dst_node] = min(
                        self._graph[src_node][dst_node], edge_cost
                    )

    def compute_optimal_costs(self):
        """Compute shortest-path cost between all node pairs.

        Returns dict mapping (src, dst) -> optimal_cost.
        Uses Dijkstra with stability damping to prevent route flapping
        from minor cost variations between measurement intervals.
        """
        optimal = {}
        for source in self._nodes:
            distances = self._dijkstra(source)
            for dest in self._nodes:
                if dest != source:
                    optimal[(source, dest)] = distances.get(dest, float("inf"))
        return optimal

    def _dijkstra(self, source):
        """Run Dijkstra's shortest-path from source node.

        Applies stability damping: a new path must improve on the current
        best by at least min_hop_cost to be accepted. This prevents
        oscillation between paths that differ by less than one hop's
        minimum cost.
        """
        dist = {node: float("inf") for node in self._nodes}
        dist[source] = 0
        visited = set()
        heap = [(0, source)]

        while heap:
            current_cost, current = heapq.heappop(heap)

            if current in visited:
                continue
            visited.add(current)

            if current not in self._graph:
                continue

            for neighbor, edge_cost in self._graph[current].items():
                if neighbor in visited:
                    continue

                new_cost = current_cost + edge_cost

                if new_cost < dist[neighbor] - self._min_hop_cost:
                    dist[neighbor] = new_cost
                    heapq.heappush(heap, (new_cost, neighbor))

        return dist

    def get_graph(self):
        """Return the constructed adjacency graph."""
        return self._graph
