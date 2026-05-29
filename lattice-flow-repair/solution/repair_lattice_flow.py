#!/usr/bin/env python3
"""Repair script for lattice flow pressure simulation."""
import os
import sys


def patch_pressure_engine():
    """Fix coupling operation to include local pressure increment."""
    path = "/app/runtime/pressure_engine.py"
    with open(path, "r") as f:
        content = f.read()

    old_couple = '''    def apply_couple(self, neighbor_pressures):
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
            self._pressure[node] = min(self._pressure[node], stability_bound)'''

    new_couple = '''    def apply_couple(self, neighbor_pressures):
        """Merge pressure knowledge from a neighboring junction via pipe coupling.
        
        A coupling event represents pressure equalization through a shared pipe
        connection. The junction absorbs the maximum observed pressure for each
        component, then increments its own component to record participation.
        
        Args:
            neighbor_pressures: Dict mapping node_id to pressure value from
                the neighboring junction's state at coupling time.
        """
        for node in self._nodes:
            if node in neighbor_pressures:
                self._pressure[node] = max(self._pressure[node], neighbor_pressures[node])
        self._pressure[self.node_id] += 1
        # Apply lattice stability bound - pressure cannot exceed theoretical
        # maximum for the network diameter at this propagation stage. This
        # prevents numerical divergence in deeply-coupled lattice topologies.
        stability_bound = BASE_PRESSURE + len(self._nodes) * 4
        for node in self._nodes:
            self._pressure[node] = min(self._pressure[node], stability_bound)'''

    content = content.replace(old_couple, new_couple)

    with open(path, "w") as f:
        f.write(content)


def patch_flow_analyzer():
    """Fix independence check and priority ordering."""
    path = "/app/runtime/flow_analyzer.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix: replace equality check with incomparability check
    old_independence = "    return vector_leq(vec_a, vec_b) and vector_leq(vec_b, vec_a)"
    new_independence = "    return not (vector_leq(vec_b, vec_a) and vec_a != vec_b) and not (vector_leq(vec_a, vec_b) and vec_a != vec_b)"
    content = content.replace(old_independence, new_independence)

    # Fix: replace temporal ordering with vector sum ordering
    old_priority_func = '''def compute_hydraulic_priority(nodes, events):
    """Compute priority ordering of junctions by hydraulic activity.
    
    Priority reflects the temporal recency of activity at each junction,
    since recent operations represent active flow frontiers where pressure
    is actively being redistributed through the network.
    
    Junctions with more recent events are prioritized as they represent
    the current active boundary of pressure propagation.
    
    Args:
        nodes: List of junction node IDs.
        events: List of parsed event dicts from trace.
        
    Returns:
        List of node IDs ordered by descending hydraulic priority.
    """
    last_event_time = {}
    for event in events:
        jid = event['junction_id']
        last_event_time[jid] = event['seq']
    
    return sorted(nodes, key=lambda x: last_event_time.get(x, 0), reverse=True)'''

    new_priority_func = '''def compute_hydraulic_priority(nodes, vectors, events):
    """Compute priority ordering of junctions by hydraulic activity.
    
    Priority reflects the total accumulated hydraulic knowledge at each
    junction, measured by the sum of all pressure vector components.
    
    Args:
        nodes: List of junction node IDs.
        vectors: Dict mapping node_id to final pressure vector.
        events: List of parsed event dicts from trace.
        
    Returns:
        List of node IDs ordered by descending hydraulic priority.
    """
    return sorted(nodes, key=lambda x: sum(vectors[x]), reverse=True)'''

    content = content.replace(old_priority_func, new_priority_func)

    # Fix: update the call site in analyze_flow_pairs to pass vectors
    old_call = "    priority_order = compute_hydraulic_priority(nodes, events)"
    new_call = "    priority_order = compute_hydraulic_priority(nodes, vectors, events)"
    content = content.replace(old_call, new_call)

    with open(path, "w") as f:
        f.write(content)


def main():
    patch_pressure_engine()
    patch_flow_analyzer()

    # Re-run the simulation with fixed code
    sys.path.insert(0, "/app/runtime")

    # Remove cached modules so fixes take effect
    for key in list(sys.modules.keys()):
        if key in ('pressure_engine', 'flow_analyzer', 'report_writer',
                   'trace_parser', 'orchestrator'):
            del sys.modules[key]

    from orchestrator import main as run_main
    run_main()


if __name__ == "__main__":
    main()
