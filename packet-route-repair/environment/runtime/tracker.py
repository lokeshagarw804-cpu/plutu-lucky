"""Routing anomaly tracker — loop detection and suboptimal path flagging.

Analyzes packet paths for routing loops (nodes visited more than once)
and suboptimal routing (actual cost exceeds optimal by a configurable
factor). Uses per-hop state tracking to detect cycles as packets
traverse the network.
"""
import configparser


class AnomalyTracker:
    """Detects routing loops and suboptimal paths in packet flows."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._loop_threshold = self._config.getint("detection", "loop_threshold")
        self._suboptimal_factor = self._config.getfloat("detection", "suboptimal_factor")
        self._path_history = {}

    def analyze_packets(self, packets, optimal_costs):
        """Analyze all packets for routing anomalies.

        Returns list of flow records with anomaly annotations.
        """
        results = []
        for packet in packets:
            has_loop = self._detect_loop(packet)
            path_cost = sum(packet["cost_per_hop"])
            src = packet["src"]
            dst = packet["dst"]
            optimal = optimal_costs.get((src, dst), float("inf"))
            is_suboptimal = path_cost > optimal * self._suboptimal_factor

            results.append({
                "packet_id": packet["packet_id"],
                "src": src,
                "dst": dst,
                "path_cost": path_cost,
                "optimal_cost": optimal,
                "has_loop": has_loop,
                "is_suboptimal": is_suboptimal,
                "hop_count": len(packet["hops"]),
            })
        return results

    def _detect_loop(self, packet):
        """Detect if a packet's path contains a routing loop.

        Walks through the hop sequence checking if any node is revisited.
        Initializes per-packet tracking state, then delegates to per-hop
        checking which maintains the visited node set.
        """
        hops = packet["hops"]
        packet_id = packet["packet_id"]
        self._path_history[packet_id] = set()

        for i in range(len(hops) - 1):
            current_node = hops[i]
            next_node = hops[i + 1]
            if self._check_hop(packet_id, current_node, next_node):
                return True
        return False

    def _check_hop(self, packet_id, current_node, next_node):
        """Check a single hop for loop condition.

        Creates a per-hop visited snapshot and checks whether the
        next node has already been traversed in this packet's path.
        Adds current node to the running path set after checking.
        """
        visited = set()
        visited.add(current_node)
        visited.add(next_node)
        if next_node in self._path_history[packet_id]:
            return True
        self._path_history[packet_id] = visited
        return False
