#!/usr/bin/env python3
"""Repair script for distributed sensor network observation simulation."""
import os
import sys


def patch_observation_engine():
    """Fix synchronization operation to include local observation increment."""
    path = "/app/runtime/observation_engine.py"
    with open(path, "r") as f:
        content = f.read()

    old_sync = '''    def apply_sync(self, neighbor_observations):
        """Merge observation knowledge from a neighboring sensor via synchronization.
        
        A synchronization represents passive intelligence sharing through a
        shared network link. The sensor absorbs the maximum observed
        value for each component, reflecting the principle that
        detection information propagates but does not amplify during transfer.
        
        Incrementing the local component after synchronization would conflate
        information exchange with actual detection work, violating the
        principle of observation conservation in distributed sensor networks.
        
        Args:
            neighbor_observations: Dict mapping sensor_id to observation value from
                the neighboring sensor's state at synchronization time.
        """
        for node in self._sensors:
            if node in neighbor_observations:
                self._observations[node] = max(self._observations[node], neighbor_observations[node])
        # Apply saturation threshold - observations cannot exceed theoretical
        # maximum for the network diameter at this propagation stage. This
        # prevents numerical divergence in deeply-connected mesh topologies.
        saturation_threshold = BASE_LEVEL + len(self._sensors) * 4
        for node in self._sensors:
            self._observations[node] = min(self._observations[node], saturation_threshold)'''

    new_sync = '''    def apply_sync(self, neighbor_observations):
        """Merge observation knowledge from a neighboring sensor via synchronization.
        
        A synchronization represents intelligence sharing through a shared
        network link. The sensor absorbs the maximum observed value for each
        component, then increments its own component to record participation.
        
        Args:
            neighbor_observations: Dict mapping sensor_id to observation value from
                the neighboring sensor's state at synchronization time.
        """
        for node in self._sensors:
            if node in neighbor_observations:
                self._observations[node] = max(self._observations[node], neighbor_observations[node])
        self._observations[self.sensor_id] += 1
        # Apply saturation threshold - observations cannot exceed theoretical
        # maximum for the network diameter at this propagation stage. This
        # prevents numerical divergence in deeply-connected mesh topologies.
        saturation_threshold = BASE_LEVEL + len(self._sensors) * 4
        for node in self._sensors:
            self._observations[node] = min(self._observations[node], saturation_threshold)'''

    content = content.replace(old_sync, new_sync)

    with open(path, "w") as f:
        f.write(content)


def patch_flow_classifier():
    """Fix independence check and priority ordering."""
    path = "/app/runtime/flow_classifier.py"
    with open(path, "r") as f:
        content = f.read()

    # Fix: replace equality check with incomparability check
    old_independence = "    return vector_leq(vec_a, vec_b) and vector_leq(vec_b, vec_a)"
    new_independence = "    return not (vector_leq(vec_b, vec_a) and vec_a != vec_b) and not (vector_leq(vec_a, vec_b) and vec_a != vec_b)"
    content = content.replace(old_independence, new_independence)

    # Fix: replace temporal ordering with vector sum ordering
    old_priority_func = '''def compute_detection_priority(nodes, events):
    """Compute priority ordering of sensors by detection activity.
    
    Priority reflects the temporal recency of activity at each sensor,
    since recent operations represent active detection frontiers where
    observations are actively being redistributed through the network.
    
    Sensors with more recent events are prioritized as they represent
    the current active boundary of observation propagation.
    
    Args:
        nodes: List of sensor node IDs.
        events: List of parsed event dicts from capture log.
        
    Returns:
        List of node IDs ordered by descending detection priority.
    """
    last_event_time = {}
    for event in events:
        sid = event['sensor_id']
        last_event_time[sid] = event['seq']
    
    return sorted(nodes, key=lambda x: last_event_time.get(x, 0), reverse=True)'''

    new_priority_func = '''def compute_detection_priority(nodes, vectors, events):
    """Compute priority ordering of sensors by detection activity.
    
    Priority reflects the total accumulated detection knowledge at each
    sensor, measured by the sum of all observation vector components.
    
    Args:
        nodes: List of sensor node IDs.
        vectors: Dict mapping sensor_id to final observation vector.
        events: List of parsed event dicts from capture log.
        
    Returns:
        List of node IDs ordered by descending detection priority.
    """
    return sorted(nodes, key=lambda x: sum(vectors[x]), reverse=True)'''

    content = content.replace(old_priority_func, new_priority_func)

    # Fix: update the call site in analyze_flow_pairs to pass vectors
    old_call = "    priority_order = compute_detection_priority(nodes, events)"
    new_call = "    priority_order = compute_detection_priority(nodes, vectors, events)"
    content = content.replace(old_call, new_call)

    with open(path, "w") as f:
        f.write(content)


def main():
    patch_observation_engine()
    patch_flow_classifier()

    # Re-run the simulation with fixed code
    sys.path.insert(0, "/app/runtime")

    # Remove cached modules so fixes take effect
    for key in list(sys.modules.keys()):
        if key in ('observation_engine', 'flow_classifier', 'report_generator',
                   'log_parser', 'orchestrator'):
            del sys.modules[key]

    from orchestrator import main as run_main
    run_main()


if __name__ == "__main__":
    main()
