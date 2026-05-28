"""
Particle Collision Simulation Tests
====================================
Validates the collision simulation output against expected physical
behavior. Tests are organized in tiers from structural validation
through full system integrity checks.

Tier 1: Structural (6 tests) - validates output format
Tier 2: Energy Accounting (3 tests) - validates ABSORB physics
Tier 3: Causal Analysis (3 tests) - validates independence and priority
Tier 4: System Integrity (2 tests) - validates full consistency
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'runtime'))

RUNTIME_DIR = os.path.join(os.path.dirname(__file__), '..', 'runtime')
STATE_PATH = os.path.join(RUNTIME_DIR, 'simulation_state.jsonl')
REPORT_PATH = os.path.join(RUNTIME_DIR, 'collision_report.json')

PARTICLE_IDS = ['alpha', 'beta', 'gamma', 'delta', 'epsilon', 'zeta', 'eta']


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
# TIER 1: Structural validation (always passes - 6 tests)
# =========================================================================

class TestTier1Structural:
    """Structural tests that validate file format and basic constraints."""

    def test_output_files_exist(self):
        """Both simulation_state.jsonl and collision_report.json must exist."""
        assert os.path.exists(STATE_PATH), "simulation_state.jsonl not found"
        assert os.path.exists(REPORT_PATH), "collision_report.json not found"

    def test_particle_count(self):
        """State file must contain exactly 7 particles."""
        state = load_state()
        assert len(state) == 7, f"Expected 7 particles, got {len(state)}"

    def test_particle_ids(self):
        """State must contain the correct particle identifiers."""
        state = load_state()
        expected = set(PARTICLE_IDS)
        assert set(state.keys()) == expected, \
            f"Particle ID mismatch: {set(state.keys())} != {expected}"

    def test_events_per_particle(self):
        """Each particle must have the expected event count from the log."""
        state = load_state()
        # alpha: 9, beta: 7, gamma: 6, delta: 6, epsilon: 6, zeta: 5, eta: 6
        expected_counts = {
            'alpha': 9, 'beta': 7, 'gamma': 6, 'delta': 6,
            'epsilon': 6, 'zeta': 5, 'eta': 6
        }
        for pid, expected in expected_counts.items():
            assert state[pid]['event_count'] == expected, \
                f"{pid} event count: {state[pid]['event_count']} != {expected}"

    def test_required_fields(self):
        """Each state entry must have all required fields."""
        state = load_state()
        required = {'particle_id', 'momentum_vector', 'total_energy', 'event_count'}
        for pid, entry in state.items():
            assert required.issubset(set(entry.keys())), \
                f"{pid} missing fields: {required - set(entry.keys())}"
            # Each momentum vector must have 7 components
            assert len(entry['momentum_vector']) == 7, \
                f"{pid} vector has {len(entry['momentum_vector'])} components, expected 7"

    def test_total_event_count(self):
        """Sum of all event counts must equal total events in the log (45)."""
        state = load_state()
        total = sum(entry['event_count'] for entry in state.values())
        assert total == 45, f"Total events {total} != 45"


# =========================================================================
# TIER 2: Energy accounting (requires Bug 1 fix - 3 tests)
# =========================================================================

class TestTier2EnergyAccounting:
    """Tests that validate momentum accumulation from ABSORB events.

    ABSORB events represent active collisions where the particle both
    receives neighbor state AND gains kinetic energy from the impact.
    The own-component must increment by 1 to account for collision thrust.
    """

    def test_momentum_after_absorb(self):
        """Alpha's self-momentum must reflect ABSORB thrust increments.

        Alpha processes: 4 DRIFT (+4), 2 SCATTER (+4), 2 ABSORB (+2 thrust).
        Starting from BASE_ENERGY=3: 3 + 4 + 4 + 2 = 13.
        But the second ABSORB's neighbor_state has alpha:11, and alpha's own
        value at that point is already 11 (from events prior to ABSORB #2),
        so max(11,11)=11 then +1=12 for the ABSORB. After final DRIFT: 14.
        """
        state = load_state()
        alpha = state['alpha']
        assert alpha['momentum_vector']['alpha'] == 14, \
            f"Alpha self-momentum should be 14, got {alpha['momentum_vector']['alpha']}"

    def test_absorb_knowledge_transfer(self):
        """Beta must absorb alpha's momentum correctly via ABSORB event.

        Beta's ABSORB at seq 023 has neighbor_state alpha:7. Beta's
        alpha-component before ABSORB should be 3 (no prior alpha info),
        so after ABSORB: max(3,7)=7. This value persists since no further
        events modify beta's alpha-component.
        """
        state = load_state()
        beta = state['beta']
        assert beta['momentum_vector']['alpha'] == 7, \
            f"Beta's alpha-component should be 7, got {beta['momentum_vector']['alpha']}"

    def test_vector_sums(self):
        """Total energy for particles with ABSORBs must exceed those without.

        Zeta has 2 ABSORB events and 3 other events. With thrust increments,
        zeta's total energy should be 46 (accounting for +1 per ABSORB on
        own component beyond the max-merge).
        """
        state = load_state()
        # Alpha has 2 ABSORBs: total should be 61 (includes +2 from thrust)
        assert state['alpha']['total_energy'] == 61, \
            f"Alpha total energy should be 61, got {state['alpha']['total_energy']}"


# =========================================================================
# TIER 3: Causal analysis (requires Bugs 2+3 fix - 3 tests)
# =========================================================================

class TestTier3CausalAnalysis:
    """Tests for causal independence and evolution priority.

    Causal independence between particles is determined by whether
    neither particle's vector dominates the other. Priority ordering
    uses total accumulated energy (vector sum), not event recency.
    """

    def test_priority_not_timestep(self):
        """Priority order must not follow last-event sequence numbers.

        Alpha has the highest total energy and must be first. If priority
        were by last event timestamp, beta (seq 045) would be first, but
        alpha (seq 042) should be first by energy.
        """
        report = load_report()
        assert report['priority_order'][0] == 'alpha', \
            f"First in priority should be alpha, got {report['priority_order'][0]}"
        assert report['priority_order'][-1] == 'zeta', \
            f"Last in priority should be zeta, got {report['priority_order'][-1]}"

    def test_independent_pair_count(self):
        """Must find exactly 21 causally independent pairs.

        With 7 particles that each have their own peak momentum component
        (from self-directed DRIFT/SCATTER events), no particle's vector
        dominates another. All C(7,2)=21 pairs are independent.
        """
        report = load_report()
        assert report['independent_pair_count'] == 21, \
            f"Expected 21 independent pairs, got {report['independent_pair_count']}"

    def test_coverage_no_conflicts(self):
        """All reported independent pairs must be valid and complete.

        Each pair must reference valid particle IDs, no pair should be
        duplicated, and the total must equal C(7,2)=21.
        """
        report = load_report()
        pairs = report['independent_pairs']
        # All pairs must contain valid particle IDs
        for pair in pairs:
            assert len(pair) == 2
            assert pair[0] in PARTICLE_IDS, f"Unknown particle: {pair[0]}"
            assert pair[1] in PARTICLE_IDS, f"Unknown particle: {pair[1]}"
        # No duplicate pairs
        pair_set = set(tuple(sorted(p)) for p in pairs)
        assert len(pair_set) == len(pairs), "Duplicate pairs found"
        # Count matches
        assert len(pairs) == report['independent_pair_count']


# =========================================================================
# TIER 4: Full system integrity (requires all fixes - 2 tests)
# =========================================================================

class TestTier4SystemIntegrity:
    """End-to-end integrity checks requiring all bugs to be fixed."""

    def test_exact_digest(self):
        """The simulation digest must match the fully-corrected state.

        The MD5 digest captures the complete momentum state across all
        particles. Only with correct ABSORB thrust, proper independence
        classification, and energy-based priority does the simulation
        converge to the expected fingerprint.
        """
        report = load_report()
        assert report['digest'] == '666f99c040b28ada', \
            f"Digest mismatch: expected 666f99c040b28ada, got {report['digest']}"

    def test_cross_validation(self):
        """State file and report must be internally consistent.

        The priority order must rank particles by descending total_energy
        from the state file. Ties are broken alphabetically (stable sort
        on the canonical particle ordering). The digest must be 16 hex
        chars. The pair count must equal len(independent_pairs).
        """
        state = load_state()
        report = load_report()

        # Priority order must be non-increasing in total energy
        energies = [state[p]['total_energy'] for p in report['priority_order']]
        for i in range(len(energies) - 1):
            assert energies[i] >= energies[i + 1], \
                f"Priority order not sorted by energy: {report['priority_order']}"

        # First must be alpha (highest energy), last must be zeta (lowest)
        assert report['priority_order'][0] == 'alpha'
        assert report['priority_order'][-1] == 'zeta'

        # Pair count consistency
        assert len(report['independent_pairs']) == report['independent_pair_count']

        # Digest format
        assert len(report['digest']) == 16
        assert all(c in '0123456789abcdef' for c in report['digest'])
