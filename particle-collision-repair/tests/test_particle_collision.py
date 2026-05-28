"""
Particle Collision Simulation Tests
====================================
Validates the collision simulation output against expected physical
behavior. Tests are organized in tiers from structural validation
through full system integrity checks.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'runtime'))

RUNTIME_DIR = os.path.join(os.path.dirname(__file__), '..', 'runtime')
STATE_PATH = os.path.join(RUNTIME_DIR, 'simulation_state.jsonl')
REPORT_PATH = os.path.join(RUNTIME_DIR, 'collision_report.json')


def load_state():
    """Load the simulation state from JSONL file."""
    particles = {}
    with open(STATE_PATH, 'r') as f:
        for line in f:
            entry = json.loads(line.strip())
            particles[entry['particle_id']] = entry
    return particles


def load_report():
    """Load the collision report JSON."""
    with open(REPORT_PATH, 'r') as f:
        return json.load(f)


# =========================================================================
# TIER 1: Structural validation (always passes - 8 tests)
# =========================================================================

class TestTier1Structural:
    """Structural tests that validate file format and basic constraints."""

    def test_state_file_exists(self):
        """Simulation state file must be generated."""
        assert os.path.exists(STATE_PATH), "simulation_state.jsonl not found"

    def test_report_file_exists(self):
        """Collision report file must be generated."""
        assert os.path.exists(REPORT_PATH), "collision_report.json not found"

    def test_all_particles_present(self):
        """All 7 particles must appear in state output."""
        state = load_state()
        expected = {'alpha', 'beta', 'gamma', 'delta', 'epsilon', 'zeta', 'eta'}
        assert set(state.keys()) == expected

    def test_momentum_vector_dimensions(self):
        """Each particle momentum vector must have 7 components."""
        state = load_state()
        for pid, entry in state.items():
            assert len(entry['momentum_vector']) == 7, f"{pid} vector wrong dimension"

    def test_base_energy_minimum(self):
        """No momentum component should fall below BASE_ENERGY (3)."""
        state = load_state()
        for pid, entry in state.items():
            for comp_pid, value in entry['momentum_vector'].items():
                assert value >= 3, f"{pid}[{comp_pid}] = {value} < BASE_ENERGY"

    def test_event_counts_positive(self):
        """All particles must have processed at least one event."""
        state = load_state()
        for pid, entry in state.items():
            assert entry['event_count'] > 0, f"{pid} has no events"

    def test_alpha_has_most_events(self):
        """Alpha particle must have the highest event count (9 events)."""
        state = load_state()
        alpha_count = state['alpha']['event_count']
        for pid, entry in state.items():
            if pid != 'alpha':
                assert alpha_count >= entry['event_count'], \
                    f"Alpha should have most events but {pid} has {entry['event_count']}"

    def test_report_has_required_fields(self):
        """Collision report must contain all required top-level fields."""
        report = load_report()
        required = {'independent_pairs', 'independent_pair_count', 'priority_order', 'digest'}
        assert required.issubset(set(report.keys())), \
            f"Missing fields: {required - set(report.keys())}"


# =========================================================================
# TIER 2: Energy accounting (requires Bug 1 fix - 2 tests)
# =========================================================================

class TestTier2EnergyAccounting:
    """Tests that validate momentum accumulation from ABSORB events.

    ABSORB events represent active collisions where the particle both
    receives neighbor state AND gains kinetic energy from the impact.
    The own-component must increment by 1 to account for collision thrust.
    """

    def test_alpha_self_momentum(self):
        """Alpha's self-momentum must reflect all event contributions.

        Alpha processes 4 DRIFT (+4), 2 SCATTER (+4), 2 ABSORB (+2 from thrust)
        plus 1 DRIFT after last ABSORB. Starting from BASE_ENERGY=3:
        3 + 4 + 4 + 2 + 1 = 14
        """
        state = load_state()
        alpha = state['alpha']
        assert alpha['momentum_vector']['alpha'] == 14, \
            f"Alpha self-momentum should be 14, got {alpha['momentum_vector']['alpha']}"

    def test_alpha_total_energy(self):
        """Alpha total energy must include ABSORB thrust contributions.

        With correct ABSORB handling, alpha accumulates energy from both
        self-generated events and absorbed neighbor state maxima, plus
        the collision thrust increment on each absorption.
        """
        state = load_state()
        alpha = state['alpha']
        assert alpha['total_energy'] == 61, \
            f"Alpha total energy should be 61, got {alpha['total_energy']}"


# =========================================================================
# TIER 3: Causal analysis (requires Bugs 2+3 fix - 2 tests)
# =========================================================================

class TestTier3CausalAnalysis:
    """Tests for causal independence and evolution priority.

    Causal independence between particles is determined by vector
    incomparability - neither particle's momentum vector dominates
    the other. This is distinct from equality, which would mean
    the vectors are identical (an extremely rare condition in practice).

    Evolution priority is determined by total accumulated energy,
    not recency of last event. Particles with higher momentum sums
    represent the most energetic reaction fronts.
    """

    def test_independent_pair_count(self):
        """Must find 21 causally independent pairs via incomparability.

        With 7 particles having distinct self-momentum peaks, all pairs
        exhibit mutual non-dominance since each particle excels in its
        own component while lagging in others.
        """
        report = load_report()
        assert report['independent_pair_count'] == 21, \
            f"Expected 21 independent pairs, got {report['independent_pair_count']}"

    def test_priority_order_by_energy(self):
        """Priority must rank by total momentum energy, not event recency.

        The highest-energy particle drives the most significant reaction
        fronts. Sorting by sum of vector components gives the correct
        physical priority: alpha(61) > beta(50) > delta=epsilon=eta=gamma(48) > zeta(46).
        """
        report = load_report()
        expected = ['alpha', 'beta', 'delta', 'epsilon', 'eta', 'gamma', 'zeta']
        assert report['priority_order'] == expected, \
            f"Priority order mismatch: expected {expected}, got {report['priority_order']}"


# =========================================================================
# TIER 4: Full system integrity (requires all fixes - 2 tests)
# =========================================================================

class TestTier4SystemIntegrity:
    """End-to-end integrity checks requiring all bugs to be fixed."""

    def test_simulation_digest(self):
        """The simulation digest must match the fully-corrected state.

        The MD5 digest captures the complete momentum state across all
        particles. Only with correct ABSORB thrust, proper independence
        classification, and energy-based priority does the simulation
        converge to the expected fingerprint.
        """
        report = load_report()
        assert report['digest'] == '666f99c040b28ada', \
            f"Digest mismatch: expected 666f99c040b28ada, got {report['digest']}"

    def test_report_completeness(self):
        """Report must contain all required fields with consistent data.

        The independent_pair_count must match the actual pairs list length,
        priority_order must contain all 7 particles, and digest must be
        exactly 16 hex characters.
        """
        report = load_report()
        assert len(report['independent_pairs']) == report['independent_pair_count']
        assert len(report['priority_order']) == 7
        assert len(report['digest']) == 16
        assert all(c in '0123456789abcdef' for c in report['digest'])
        # Cross-check: pair count must be 21 for full correctness
        assert report['independent_pair_count'] == 21, \
            f"Expected 21 pairs for full integrity, got {report['independent_pair_count']}"
