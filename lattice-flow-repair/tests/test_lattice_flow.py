"""Tests for lattice flow pressure simulation.

14 tests across 4 tiers verifying structural output, pressure state
correctness, flow pair classification, and digest consistency.
"""
import json
import os
import pytest


STATE_PATH = '/app/runtime/flow_state.jsonl'
REPORT_PATH = '/app/runtime/flow_report.json'

ALL_JUNCTIONS = [
    'junc_alpha', 'junc_beta', 'junc_delta', 'junc_epsilon',
    'junc_eta', 'junc_gamma', 'junc_zeta'
]

EXPECTED_EVENT_COUNTS = {
    'junc_alpha': 8,
    'junc_beta': 7,
    'junc_delta': 7,
    'junc_epsilon': 6,
    'junc_eta': 5,
    'junc_gamma': 6,
    'junc_zeta': 6,
}

TOTAL_EVENTS = 45


@pytest.fixture(scope='session')
def state_records():
    """Load state records from JSONL output."""
    records = []
    with open(STATE_PATH, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


@pytest.fixture(scope='session')
def report():
    """Load analysis report from JSON output."""
    with open(REPORT_PATH, 'r') as f:
        return json.load(f)


@pytest.fixture(scope='session')
def state_by_junction(state_records):
    """Index state records by junction ID."""
    return {r['junction_id']: r for r in state_records}


# ============================================================
# TIER 1: Structural tests (always pass with buggy code)
# ============================================================

class TestTier1Structure:
    """Basic structural validation of output files."""

    def test_output_files_exist(self):
        """Both output files must exist."""
        assert os.path.isfile(STATE_PATH), f"Missing {STATE_PATH}"
        assert os.path.isfile(REPORT_PATH), f"Missing {REPORT_PATH}"

    def test_junction_count(self, state_records):
        """State file must contain exactly 7 junction records."""
        assert len(state_records) == 7

    def test_junction_ids(self, state_records):
        """All expected junction IDs must be present."""
        ids = sorted([r['junction_id'] for r in state_records])
        assert ids == ALL_JUNCTIONS

    def test_events_per_junction(self, state_by_junction):
        """Each junction must report the correct number of trace events."""
        for jid, expected_count in EXPECTED_EVENT_COUNTS.items():
            actual = state_by_junction[jid]['event_count']
            assert actual == expected_count, (
                f"{jid}: expected {expected_count} events, got {actual}"
            )

    def test_required_fields(self, state_records):
        """Each state record must have required fields."""
        required = {'junction_id', 'pressure_vector', 'event_count'}
        for record in state_records:
            missing = required - set(record.keys())
            assert not missing, f"Missing fields: {missing}"

    def test_total_event_count(self, state_records):
        """Sum of all junction event counts must match trace total."""
        total = sum(r['event_count'] for r in state_records)
        assert total == TOTAL_EVENTS


# ============================================================
# TIER 2: Pressure state tests (need Bug 1 fixed)
# ============================================================

class TestTier2PressureState:
    """Pressure vector correctness after coupling operations."""

    def test_pressure_after_couple(self, state_by_junction):
        """Junction own-component must include couple increments.
        
        For junc_alpha: BASE(3) + 4 PUMPs + 2 SURGEs*2 + 2 COUPLEs = 13
        For junc_beta: BASE(3) + 4 PUMPs + 1 SURGE*2 + 2 COUPLEs = 11
        """
        # junc_alpha: 3 + 4 + 4 + 2 = 13
        alpha_own = state_by_junction['junc_alpha']['pressure_vector'][0]
        assert alpha_own == 13, f"junc_alpha own pressure: expected 13, got {alpha_own}"
        
        # junc_beta: 3 + 4 + 2 + 2 = 11
        beta_own = state_by_junction['junc_beta']['pressure_vector'][1]
        assert beta_own == 11, f"junc_beta own pressure: expected 11, got {beta_own}"

    def test_couple_knowledge_transfer(self, state_by_junction):
        """Coupling must propagate non-own component knowledge from peer.
        
        junc_alpha couples at seq 23 with peer_state junc_beta:7, then
        at seq 35 with peer_state junc_beta:8. Alpha's beta component
        should be max(3, 7, 8) = 8.
        """
        # junc_alpha's beta component (index 1 in sorted order)
        alpha_beta = state_by_junction['junc_alpha']['pressure_vector'][1]
        assert alpha_beta == 8, (
            f"junc_alpha beta component: expected 8, got {alpha_beta}"
        )

    def test_vector_sums(self, state_by_junction):
        """Junctions with couples must have correct total vector sums."""
        expected_sums = {
            'junc_alpha': 47,
            'junc_beta': 36,
            'junc_delta': 49,
            'junc_epsilon': 41,
            'junc_gamma': 39,
        }
        for jid, expected in expected_sums.items():
            actual = sum(state_by_junction[jid]['pressure_vector'])
            assert actual == expected, (
                f"{jid}: expected vector sum {expected}, got {actual}"
            )


# ============================================================
# TIER 3: Flow analysis tests (need Bugs 2+3 fixed)
# ============================================================

class TestTier3FlowAnalysis:
    """Flow independence and priority ordering correctness."""

    def test_priority_not_temporal(self, report):
        """Highest priority junction must not be determined by last event time.
        
        The temporally last junction (junc_epsilon, seq 45) should not be
        first in priority. The correct first priority is junc_delta (highest
        vector sum = 49).
        """
        priority = report['priority_order']
        assert priority[0] != 'junc_epsilon', (
            "Priority appears to use temporal ordering instead of vector sum"
        )
        assert priority[0] == 'junc_delta', (
            f"Expected junc_delta as highest priority, got {priority[0]}"
        )

    def test_independent_pair_count(self, report):
        """Must identify exactly 19 independent flow pairs.
        
        Only 2 pairs are dependent (where one dominates the other):
        junc_delta/junc_eta and junc_epsilon/junc_eta.
        """
        count = report['flow_analysis']['independent_count']
        assert count == 19, (
            f"Expected 19 independent pairs, got {count}"
        )

    def test_classification_coverage(self, report):
        """All 21 junction pairs must be classified."""
        analysis = report['flow_analysis']
        total = analysis['total_pairs']
        indep = analysis['independent_count']
        dep = analysis['dependent_count']
        assert total == 21, f"Expected 21 total pairs, got {total}"
        assert indep + dep == 21, (
            f"independent({indep}) + dependent({dep}) != 21"
        )


# ============================================================
# TIER 4: Full consistency tests (need ALL bugs fixed)
# ============================================================

class TestTier4Consistency:
    """End-to-end consistency requiring all fixes applied."""

    def test_report_digest(self, report):
        """Report digest must match expected value for fully corrected output."""
        assert report['digest'] == 'cc4f8ca3d64147e6', (
            f"Digest mismatch: got {report['digest']}"
        )

    def test_cross_validation(self, state_by_junction, report):
        """Cross-validation in report must match state file pressure vectors."""
        cross = report['cross_validation']
        # Verify specific known classifications
        assert cross['junc_delta:junc_eta']['independent'] is False, (
            "junc_delta:junc_eta should be dependent (delta dominates eta)"
        )
        assert cross['junc_epsilon:junc_eta']['independent'] is False, (
            "junc_epsilon:junc_eta should be dependent (epsilon dominates eta)"
        )
        assert cross['junc_alpha:junc_beta']['independent'] is True, (
            "junc_alpha:junc_beta should be independent"
        )
        assert cross['junc_alpha:junc_delta']['independent'] is True, (
            "junc_alpha:junc_delta should be independent"
        )
        # All junction summaries must match state file
        for jid in ALL_JUNCTIONS:
            report_vec = report['junction_summaries'][jid]['pressure_vector']
            state_vec = state_by_junction[jid]['pressure_vector']
            assert report_vec == state_vec, (
                f"{jid}: report vector {report_vec} != state vector {state_vec}"
            )
