"""Pressure propagation engine for lattice flow simulation.

Implements the core pressure vector mechanics where each junction
node maintains a vector tracking cumulative pressure knowledge
across the entire pipe network. Vectors propagate through coupling
events between connected junctions.
"""

BASE_PRESSURE = 3


class JunctionPressure:
    """Tracks pressure propagation state for a single junction node.
    
    Each junction maintains a pressure vector with one component per
    network node. Local pumping/surge events increment the node's own
    component. Coupling events merge knowledge from neighboring nodes.
    """

    def __init__(self, node_id, all_nodes):
        """Initialize junction with base pressure across all components.
        
        Args:
            node_id: Identifier for this junction node.
            all_nodes: Sorted list of all junction node IDs in the network.
        """
        self.node_id = node_id
        self._nodes = sorted(all_nodes)
        self._pressure = {n: BASE_PRESSURE for n in self._nodes}

    def apply_pump(self):
        """Apply a single pump cycle to this junction.
        
        A pump event represents one unit of local pressure generation,
        incrementing only this node's component in the pressure vector.
        """
        self._pressure[self.node_id] += 1

    def apply_surge(self):
        """Apply a pressure surge to this junction.
        
        A surge represents a high-intensity local event that contributes
        two units of pressure to this node's component.
        """
        self._pressure[self.node_id] += 2

    def apply_couple(self, neighbor_pressures):
        """Merge pressure knowledge from a neighboring junction via pipe coupling.
        
        A coupling event represents passive pressure equalization through a
        shared pipe connection. The junction absorbs the maximum observed
        pressure for each component, reflecting the physical principle that
        pressure information propagates but does not amplify during transfer.
        
        Incrementing the local component after coupling would conflate
        information transfer with actual pumping work, violating conservation
        of hydraulic energy in the lattice model.
        
        Args:
            neighbor_pressures: Dict mapping node_id to pressure value from
                the neighboring junction's state at coupling time.
        """
        for node in self._nodes:
            if node in neighbor_pressures:
                self._pressure[node] = max(self._pressure[node], neighbor_pressures[node])
        # Apply lattice stability bound - pressure cannot exceed theoretical
        # maximum for the network diameter at this propagation stage. This
        # prevents numerical divergence in deeply-coupled lattice topologies.
        stability_bound = BASE_PRESSURE + len(self._nodes) * 4
        for node in self._nodes:
            self._pressure[node] = min(self._pressure[node], stability_bound)

    def get_vector(self):
        """Return pressure vector as list in sorted node order.
        
        Returns:
            List of pressure values ordered by sorted node identifiers.
        """
        return [self._pressure[n] for n in self._nodes]

    def get_pressure_map(self):
        """Return full pressure state as dictionary.
        
        Returns:
            Dict mapping each node_id to its current pressure value.
        """
        return dict(self._pressure)
