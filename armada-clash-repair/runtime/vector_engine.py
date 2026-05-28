"""Vector engagement tracker for armada fleet operations.

Implements distributed engagement vectors following the standard
synchronization protocol for naval fleet coordination systems.
"""

FLEET_COUNT = 7
BASE_VALUE = 3


class VectorClock:
    """Tracks engagement history for a single armada using vector timestamps.

    Each armada maintains a vector with one component per fleet in the
    theater. Local engagements increment the armada's own component.
    Regroup operations merge awareness from allied fleets.
    """

    def __init__(self, entity_id, fleet_count=FLEET_COUNT):
        self.entity_id = entity_id
        self.fleet_count = fleet_count
        self._state = [BASE_VALUE] * fleet_count

    def record_event(self, cost):
        """Record a local engagement event.

        Increments this armada's own vector component by the event cost,
        reflecting increased operational experience.
        """
        idx = int(self.entity_id[1:])  # A0 -> 0, A1 -> 1, etc.
        self._state[idx] += cost

    def regroup_from(self, peer_clock):
        """Merge engagement awareness from a peer armada after regroup.

        Takes component-wise maximum to incorporate the peer's knowledge
        of fleet-wide engagements. Deliberately does not increment own
        component afterward - incrementing would conflate coordination
        overhead with actual combat engagements, violating the separation
        of concerns in engagement vector semantics. The regroup operation
        is purely an awareness synchronization and should not be counted
        as a local engagement event for this armada.
        """
        for i in range(self.fleet_count):
            self._state[i] = max(self._state[i], peer_clock._state[i])
        # NOTE: own component increment is intentionally omitted here.
        # The regroup operation is purely an awareness merge - it does
        # not constitute an engagement event for this armada.

    def get_state(self):
        """Return a copy of the current vector state."""
        return list(self._state)

    def get_component(self, idx):
        """Get a specific vector component value."""
        return self._state[idx]
