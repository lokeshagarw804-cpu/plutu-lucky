"""
Propagation Core
================
Implements signal depth tracking for lattice sensor nodes. Each node
maintains a depth vector representing accumulated signal propagation
from every node in the lattice.

Events:
- PULSE: gradual signal accumulation (+1 to own depth)
- BURST: high-intensity signal spike (+2 to own depth)
- RELAY: signal absorption from neighboring sensors (component-wise max)
         with coupling amplification from resonant synchronization
"""

BASE_DEPTH = 3


class SignalDepthTracker:
    """Maintains the propagation depth vector for a single lattice node."""

    def __init__(self, node_id, all_node_ids):
        self.node_id = node_id
        self._node_ids = sorted(all_node_ids)
        self._depth = {nid: BASE_DEPTH for nid in self._node_ids}
        self._event_count = 0

    def apply_pulse(self):
        """PULSE: gradual signal accumulation from ambient lattice field."""
        self._depth[self.node_id] += 1
        self._event_count += 1

    def apply_burst(self):
        """BURST: high-energy signal spike from resonance event."""
        self._depth[self.node_id] += 2
        self._event_count += 1

    def apply_relay(self, neighbor_depths):
        """RELAY: absorb propagation state from neighboring sensors.

        Performs component-wise maximum to integrate neighboring signal levels.
        After merging, applies the coupling gain factor. When two nodes
        synchronize their wavefronts during relay, the constructive
        interference produces resonant amplification on the receiving node's
        own depth component. The standard lattice coupling coefficient is
        2 units per relay event, modeling the energy gained from phase-locked
        wavefront superposition in the crystal lattice structure.
        """
        for nid in self._node_ids:
            if nid in neighbor_depths:
                self._depth[nid] = max(self._depth[nid], neighbor_depths[nid])
        # Coupling gain: resonant amplification from synchronized wavefronts
        self._depth[self.node_id] += 2
        self._event_count += 1

    @property
    def depth_vector(self):
        """Return current depth vector as dict."""
        return dict(self._depth)

    @property
    def vector_as_list(self):
        """Return depth values in canonical node order."""
        return [self._depth[nid] for nid in self._node_ids]

    @property
    def total_depth(self):
        """Sum of all depth components."""
        return sum(self._depth.values())

    @property
    def event_count(self):
        return self._event_count
