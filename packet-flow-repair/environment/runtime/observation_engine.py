"""Observation propagation engine for distributed sensor network.

Implements the core observation vector mechanics where each sensor
node maintains a vector tracking cumulative detection knowledge
across the entire mesh network. Vectors propagate through synchronization
events between connected sensors.
"""

BASE_LEVEL = 3


class SensorObservation:
    """Tracks observation propagation state for a single sensor node.
    
    Each sensor maintains an observation vector with one component per
    network node. Local scan/probe events increment the node's own
    component. Synchronization events merge knowledge from neighboring nodes.
    """

    def __init__(self, sensor_id, all_sensors):
        """Initialize sensor with base level across all components.
        
        Args:
            sensor_id: Identifier for this sensor node.
            all_sensors: Sorted list of all sensor node IDs in the network.
        """
        self.sensor_id = sensor_id
        self._sensors = sorted(all_sensors)
        self._observations = {n: BASE_LEVEL for n in self._sensors}

    def apply_scan(self):
        """Apply a single scan cycle to this sensor.
        
        A scan event represents one unit of local detection activity,
        incrementing only this node's component in the observation vector.
        """
        self._observations[self.sensor_id] += 1

    def apply_probe(self):
        """Apply a detection probe to this sensor.
        
        A probe represents a high-intensity local event that contributes
        two units of observation to this node's component.
        """
        self._observations[self.sensor_id] += 2

    def apply_sync(self, neighbor_observations):
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
            self._observations[node] = min(self._observations[node], saturation_threshold)

    def get_vector(self):
        """Return observation vector as list in sorted node order.
        
        Returns:
            List of observation values ordered by sorted node identifiers.
        """
        return [self._observations[n] for n in self._sensors]

    def get_observation_map(self):
        """Return full observation state as dictionary.
        
        Returns:
            Dict mapping each sensor_id to its current observation value.
        """
        return dict(self._observations)
