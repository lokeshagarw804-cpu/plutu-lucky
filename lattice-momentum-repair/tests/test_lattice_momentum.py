"""Validation tests for lattice Boltzmann momentum simulation."""
import json
import os
import pytest

OUTPUT_DIR = "/app/runtime/output"
STATE_PATH = os.path.join(OUTPUT_DIR, "lattice_state.jsonl")
REPORT_PATH = os.path.join(OUTPUT_DIR, "flow_report.json")


@pytest.fixture(scope="module")
def state_data():
    records = {}
    with open(STATE_PATH, 'r') as f:
        for line in f:
            rec = json.loads(line)
            records[rec['cell_id']] = rec
    return records


@pytest.fixture(scope="module")
def report_data():
    with open(REPORT_PATH, 'r') as f:
        return json.load(f)


# --- TIER 1: Structural tests (always pass) ---

class TestStructure:
    def test_output_files_exist(self):
        assert os.path.isfile(STATE_PATH)
        assert os.path.isfile(REPORT_PATH)

    def test_cell_count(self, state_data):
        assert len(state_data) == 7

    def test_cell_identifiers(self, state_data):
        expected = {'cell_alpha', 'cell_beta', 'cell_gamma', 'cell_delta',
                    'cell_epsilon', 'cell_zeta', 'cell_eta'}
        assert set(state_data.keys()) == expected

    def test_events_per_cell(self, state_data):
        expected_counts = {
            'cell_alpha': 9,
            'cell_beta': 6,
            'cell_gamma': 6,
            'cell_delta': 6,
            'cell_epsilon': 6,
            'cell_zeta': 6,
            'cell_eta': 6,
        }
        for cell_id, expected in expected_counts.items():
            assert state_data[cell_id]['total_events'] == expected, \
                f"{cell_id} expected {expected} events"

    def test_required_fields(self, state_data):
        for cell_id, rec in state_data.items():
            assert 'momentum_vector' in rec
            assert 'cell_id' in rec
            assert 'total_events' in rec

    def test_total_event_count(self, state_data):
        total = sum(v['total_events'] for v in state_data.values())
        assert total == 45


# --- TIER 2: Need Bug 1 fixed (collision self-increment) ---

class TestMomentum:
    def test_momentum_after_collision(self, state_data):
        """Cells that participated in collisions must show incremented
        own-component values reflecting active momentum contribution."""
        # cell_alpha has 2 collisions, so its own component should be
        # base(3) + stream(1) + drift(2) + stream(1) + collision_inc(1)
        # + stream(1) + drift(2) + collision_inc(1) + stream(1) + stream(1)
        # = 3 + 1 + 2 + 1 + 1 + 1 + 2 + 1 + 1 + 1 = 14
        alpha_own = state_data['cell_alpha']['momentum_vector']['cell_alpha']
        assert alpha_own == 14, f"cell_alpha own momentum should be 14, got {alpha_own}"

    def test_collision_knowledge_transfer(self, state_data):
        """After collision, the cell should reflect neighbor knowledge
        while also incrementing its own component."""
        # cell_beta had 1 collision at step 33 with neighbor_state showing
        # cell_alpha:10, cell_delta:9. After collision, beta's own should
        # be 11 (10 from streams/drifts + 1 from collision increment).
        beta_own = state_data['cell_beta']['momentum_vector']['cell_beta']
        assert beta_own == 11, f"cell_beta own should be 11, got {beta_own}"

    def test_vector_magnitude_comparison(self, state_data):
        """Cells with collision participation have higher magnitudes
        than their stream-only momentum would suggest."""
        # cell_alpha with fixed code: magnitude 58 (buggy gives 56)
        alpha_mag = sum(state_data['cell_alpha']['momentum_vector'].values())
        zeta_mag = sum(state_data['cell_zeta']['momentum_vector'].values())
        # With collisions properly accounted, alpha must exceed zeta
        assert alpha_mag > zeta_mag, \
            "cell_alpha should have higher magnitude than cell_zeta"
        # The exact magnitude reflects collision increments
        assert alpha_mag == 58, f"cell_alpha magnitude should be 58, got {alpha_mag}"


# --- TIER 3: Need Bugs 2+3 fixed (flow analysis) ---

class TestFlowAnalysis:
    def test_priority_not_temporal(self, report_data):
        """Dissipation priority must reflect momentum magnitude,
        not temporal event ordering."""
        priority = report_data['dissipation_priority']
        magnitudes = report_data['priority_magnitudes']
        # The highest-magnitude cell should be first
        assert priority[0] == 'cell_eta', \
            f"First priority should be cell_eta (highest magnitude), got {priority[0]}"
        # Verify ordering is by magnitude descending
        mag_values = [magnitudes[c] for c in priority]
        assert mag_values == sorted(mag_values, reverse=True), \
            "Priority should be sorted by magnitude descending"

    def test_exact_decoupled_pair_count(self, report_data):
        """All cell pairs should be classified as decoupled when no
        vector dominance relationship exists between them."""
        assert report_data['decoupled_count'] == 21, \
            f"Expected 21 decoupled pairs, got {report_data['decoupled_count']}"

    def test_pair_coverage_no_conflicts(self, report_data):
        """Every pair must be classified exactly once - either coupled
        or decoupled with no gaps or overlaps."""
        total = report_data['total_pairs']
        decoupled = report_data['decoupled_count']
        coupled = report_data['coupled_count']
        assert total == 21
        assert decoupled + coupled == total
        # Verify no pair appears in both lists
        decoupled_set = {tuple(p) for p in report_data['decoupled_pairs']}
        coupled_set = {tuple(p) for p in report_data['coupled_pairs']}
        assert len(decoupled_set & coupled_set) == 0, \
            "A pair cannot be both coupled and decoupled"


# --- TIER 4: Need ALL bugs fixed ---

class TestIntegration:
    def test_simulation_digest(self, report_data):
        """The simulation digest must match the expected value
        computed from correctly processed outputs."""
        assert report_data['simulation_digest'] == '8f7340833babbafb', \
            f"Digest mismatch: {report_data.get('simulation_digest')}"

    def test_cross_validation(self, state_data, report_data):
        """State file magnitudes must be consistent with report
        priority magnitudes."""
        priority_mags = report_data['priority_magnitudes']
        for cell_id, mag in priority_mags.items():
            state_mag = sum(state_data[cell_id]['momentum_vector'].values())
            assert state_mag == mag, \
                f"{cell_id}: state magnitude {state_mag} != report magnitude {mag}"
