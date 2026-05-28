"""Lattice Boltzmann momentum tracking engine.

Manages per-cell momentum vectors that evolve through streaming,
drift, and collision events on the hexagonal lattice.
"""

BASE_MOMENTUM = 3
ALL_CELLS = ['cell_alpha', 'cell_beta', 'cell_gamma', 'cell_delta',
             'cell_epsilon', 'cell_zeta', 'cell_eta']


class MomentumCell:
    """Tracks the momentum vector for a single lattice cell.

    The momentum vector has one component per cell in the lattice,
    representing this cell's knowledge of momentum distribution.
    """

    def __init__(self, cell_id):
        self.cell_id = cell_id
        self._momentum = {c: BASE_MOMENTUM for c in ALL_CELLS}
        self._event_count = 0
        self._last_event_step = 0

    @property
    def momentum_vector(self):
        return dict(self._momentum)

    @property
    def event_count(self):
        return self._event_count

    @property
    def last_event_step(self):
        return self._last_event_step

    def apply_stream(self, delta, step):
        """Apply STREAM event: increment own momentum component."""
        self._momentum[self.cell_id] += delta
        self._event_count += 1
        self._last_event_step = step

    def apply_drift(self, delta, step):
        """Apply DRIFT event: increment own momentum component by drift amount."""
        self._momentum[self.cell_id] += delta
        self._event_count += 1
        self._last_event_step = step

    def apply_collision(self, neighbor_state, step):
        """Apply COLLISION event: synchronize momentum knowledge with neighbors.

        A COLLISION represents passive momentum exchange - the cell absorbs
        neighbor information without generating new momentum. Incrementing
        would conflate information propagation with active particle streaming,
        overstating the cell's true kinetic contribution.
        """
        for cell_id, value in neighbor_state.items():
            if value > self._momentum[cell_id]:
                self._momentum[cell_id] = value
        # The collision synchronizes knowledge only - no self-increment occurs
        # because the cell is not actively streaming during a collision phase.
        self._event_count += 1
        self._last_event_step = step


def build_lattice_state(events):
    """Process all events and return final momentum state for each cell."""
    cells = {c: MomentumCell(c) for c in ALL_CELLS}

    for event in events:
        cell = cells[event['cell_id']]
        if event['event_type'] == 'STREAM':
            cell.apply_stream(event['detail'], event['seq'])
        elif event['event_type'] == 'DRIFT':
            cell.apply_drift(event['detail'], event['seq'])
        elif event['event_type'] == 'COLLISION':
            cell.apply_collision(event['detail'], event['seq'])

    return cells
