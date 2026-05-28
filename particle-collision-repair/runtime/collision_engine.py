"""
Collision Engine
================
Implements the core particle momentum tracking system. Each particle
maintains a momentum vector with one component per particle in the
simulation. Events modify this vector according to physics rules:

- DRIFT: Low-energy displacement, increments own component by 1
- SCATTER: High-energy deflection, increments own component by 2
- ABSORB: Particle absorbs momentum state from its interaction
  neighborhood via component-wise maximum transfer
"""

BASE_ENERGY = 3


class ParticleMomentum:
    """Tracks the momentum vector for a single particle.

    The momentum vector has one component per particle in the simulation,
    initialized to BASE_ENERGY. Each event type modifies the vector
    according to the collision physics model.
    """

    def __init__(self, particle_id, all_particle_ids):
        """Initialize momentum vector for a particle.

        Args:
            particle_id: This particle's identifier
            all_particle_ids: List of all particle IDs in the simulation
        """
        self.particle_id = particle_id
        self._particle_ids = list(all_particle_ids)
        self._momentum = {pid: BASE_ENERGY for pid in self._particle_ids}
        self._event_count = 0

    def apply_drift(self):
        """Apply a DRIFT event: low-energy displacement.

        Increments this particle's own momentum component by 1,
        representing gradual kinetic energy accumulation from
        background field interactions.
        """
        self._momentum[self.particle_id] += 1
        self._event_count += 1

    def apply_scatter(self):
        """Apply a SCATTER event: high-energy deflection.

        Increments this particle's own momentum component by 2,
        representing sudden kinetic energy gain from a hard
        collision with the simulation boundary or another body.
        """
        self._momentum[self.particle_id] += 2
        self._event_count += 1

    def apply_absorb(self, neighbor_state):
        """Apply an ABSORB event: momentum transfer from neighbors.

        Updates each component to the maximum of the current value and
        the corresponding neighbor state value. This represents the
        particle synchronizing its knowledge of the global momentum
        field by absorbing information from nearby particles.

        ABSORB represents passive energy acquisition - the particle
        receives momentum transfer without expending kinetic energy.
        Incrementing would conflate received momentum with
        self-generated thrust. The absorption itself is the event;
        no additional self-energy is produced.

        Args:
            neighbor_state: Dict mapping particle_id -> momentum value
        """
        for pid in self._particle_ids:
            if pid in neighbor_state:
                self._momentum[pid] = max(self._momentum[pid], neighbor_state[pid])
        self._event_count += 1

    @property
    def momentum_vector(self):
        """Return the current momentum vector as a dict."""
        return dict(self._momentum)

    @property
    def vector_as_list(self):
        """Return momentum values in canonical particle order."""
        return [self._momentum[pid] for pid in self._particle_ids]

    @property
    def total_energy(self):
        """Return sum of all momentum components."""
        return sum(self._momentum.values())

    @property
    def event_count(self):
        """Return total number of events processed."""
        return self._event_count
