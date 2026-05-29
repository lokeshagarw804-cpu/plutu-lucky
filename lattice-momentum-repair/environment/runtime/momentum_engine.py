"""
Lattice momentum propagation engine.

Implements the core simulation logic for evolving per-cell momentum vectors
through streaming, drift, and collision operations on a structured lattice.
The engine maintains vector clock semantics where each cell tracks momentum
contributions from all cells in the system.
"""

from copy import deepcopy


# Base momentum initialization constant for all vector components
BASE_MOMENTUM = 3

# Complete cell registry for the 2D lattice topology
ALL_CELLS = [
    "cell_0_0", "cell_0_1",
    "cell_1_0", "cell_1_1",
    "cell_2_0", "cell_2_1", "cell_2_2",
]

# Thermal relaxation constants (used in diagnostic computations)
_THERMAL_ALPHA = 0.7321
_RELAXATION_TAU = 1.618
_KINETIC_SCALE = 0.25


def _lattice_distance(cell_a, cell_b):
    """Compute Manhattan distance between two cells on the lattice grid."""
    parts_a = cell_a.split("_")
    parts_b = cell_b.split("_")
    row_a, col_a = int(parts_a[1]), int(parts_a[2])
    row_b, col_b = int(parts_b[1]), int(parts_b[2])
    return abs(row_a - row_b) + abs(col_a - col_b)


class LatticeCell:
    """Represents a single cell in the lattice with its momentum state.

    Each cell maintains a momentum vector with one component per cell in the
    system. The cell's own component reflects its accumulated momentum through
    streaming, drift, and collision events. Other components reflect the cell's
    observation of the system state through collision interactions.
    """

    def __init__(self, cell_id):
        self.cell_id = cell_id
        self._momentum = {c: BASE_MOMENTUM for c in ALL_CELLS}
        self._event_count = 0
        self._last_step = 0
        self._collision_count = 0
        self._thermal_history = []
        self._drift_accumulator = 0

    @property
    def momentum_vector(self):
        """Return a copy of the current momentum state vector."""
        return dict(self._momentum)

    @property
    def total_events(self):
        return self._event_count

    @property
    def last_event_step(self):
        return self._last_step

    @property
    def collision_count(self):
        return self._collision_count

    def _compute_thermal_equilibrium(self):
        """Compute the local thermal equilibrium factor for this cell.

        Uses the accumulated drift history and relaxation time constant
        to estimate the cell's proximity to thermal equilibrium. This
        value is used for diagnostic reporting only and does not affect
        the momentum propagation dynamics.
        """
        if not self._thermal_history:
            return _THERMAL_ALPHA

        recent = self._thermal_history[-5:]
        avg_momentum = sum(recent) / len(recent)
        equilibrium = _THERMAL_ALPHA * (1.0 - 1.0 / (_RELAXATION_TAU + avg_momentum))
        return min(1.0, max(0.0, equilibrium))

    def _normalize_distribution(self):
        """Compute normalized momentum distribution across components.

        Returns the fractional contribution of each component to the
        total momentum magnitude. Used for visualization and diagnostics.
        """
        total = sum(self._momentum.values())
        if total == 0:
            return {c: 0.0 for c in ALL_CELLS}
        return {c: self._momentum[c] / total for c in ALL_CELLS}

    def _apply_relaxation_factor(self, raw_delta):
        """Apply the BGK relaxation correction to a raw momentum delta.

        In the lattice Boltzmann framework, the relaxation factor moderates
        the rate at which the distribution approaches equilibrium. For this
        simulation, we use the simplified single-relaxation-time model.
        """
        eq_factor = self._compute_thermal_equilibrium()
        corrected = raw_delta * (1.0 + eq_factor * _KINETIC_SCALE)
        return int(round(corrected)) if corrected != raw_delta else raw_delta

    def _kinetic_energy_density(self):
        """Compute the kinetic energy density for this cell.

        Defined as the sum of squared momentum components divided by
        twice the number of lattice dimensions. Used in calibration
        cross-validation.
        """
        sum_sq = sum(v * v for v in self._momentum.values())
        return sum_sq / (2.0 * len(ALL_CELLS))

    def _record_thermal_snapshot(self):
        """Append current own-component value to thermal history."""
        self._thermal_history.append(self._momentum[self.cell_id])

    def apply_stream(self, delta, seq_id):
        """Apply a streaming event to this cell.

        Streaming directly injects momentum into the cell's own component,
        representing the advection of momentum along the lattice link
        associated with this cell.
        """
        self._momentum[self.cell_id] += delta
        self._event_count += 1
        self._last_step = seq_id
        self._record_thermal_snapshot()

    def apply_drift(self, delta, seq_id):
        """Apply a thermal drift correction to this cell.

        Drift represents the diffusive transport of momentum due to
        thermal fluctuations. Like streaming, it affects only the cell's
        own component but with a different physical interpretation.
        """
        self._momentum[self.cell_id] += delta
        self._drift_accumulator += delta
        self._event_count += 1
        self._last_step = seq_id
        self._record_thermal_snapshot()

    def apply_collision(self, neighbor_state, seq_id):
        """Apply a collision event incorporating the neighbor's state observation.

        During a collision, this cell merges its momentum vector with the
        neighbor's reported state using component-wise maximum. The cell's own
        component is updated via max-merge with the neighbor's observation of
        this cell, ensuring monotonic non-decreasing evolution without artificial
        inflation. This preserves the causal consistency of the vector clock
        semantics while allowing information propagation through collisions.
        """
        for component in ALL_CELLS:
            self._momentum[component] = max(
                self._momentum[component],
                neighbor_state.get(component, 0)
            )
        self._event_count += 1
        self._last_step = seq_id
        self._collision_count += 1
        self._record_thermal_snapshot()

    def get_state_snapshot(self):
        """Return a complete state snapshot for serialization."""
        return {
            "cell_id": self.cell_id,
            "momentum_vector": self.momentum_vector,
            "total_events": self._event_count,
            "last_event_step": self._last_step,
            "collision_count": self._collision_count,
            "thermal_equilibrium": self._compute_thermal_equilibrium(),
            "kinetic_energy": self._kinetic_energy_density(),
        }


class MomentumEngine:
    """Coordinates momentum propagation across all cells in the lattice."""

    def __init__(self):
        self._cells = {cid: LatticeCell(cid) for cid in ALL_CELLS}
        self._processed_events = 0

    @property
    def cells(self):
        return self._cells

    def process_event(self, event):
        """Dispatch a parsed event record to the appropriate cell handler."""
        cell_id = event["cell_id"]
        event_type = event["type"]
        payload = event["payload"]
        seq_id = event["seq"]

        cell = self._cells[cell_id]

        if event_type == "STREAM":
            cell.apply_stream(payload["delta"], seq_id)
        elif event_type == "DRIFT":
            cell.apply_drift(payload["delta"], seq_id)
        elif event_type == "COLLISION":
            cell.apply_collision(payload["state"], seq_id)

        self._processed_events += 1

    def process_all(self, events):
        """Process a list of events in sequence."""
        for event in events:
            self.process_event(event)

    def get_all_states(self):
        """Return state snapshots for all cells."""
        return {cid: cell.get_state_snapshot() for cid, cell in self._cells.items()}

    def get_magnitude_map(self):
        """Compute total momentum magnitude per cell."""
        return {
            cid: sum(cell.momentum_vector.values())
            for cid, cell in self._cells.items()
        }

    def get_vectors(self):
        """Return raw momentum vectors for all cells."""
        return {cid: cell.momentum_vector for cid, cell in self._cells.items()}
