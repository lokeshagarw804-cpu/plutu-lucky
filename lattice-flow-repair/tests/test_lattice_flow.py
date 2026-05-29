"""Tests for lattice flow pressure simulation."""
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
    'junc_alpha': 9,
    'junc_beta': 9,
    'junc_delta': 8,
    'junc_epsilon': 6,
    'junc_eta': 6,
    'junc_gamma': 7,
    'junc_zeta': 7,
}

TOTAL_EVENTS = 52


@pytest.fixture(scope='session')
def state_records():
    records = []
    with open(STATE_PATH, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


@pytest.fixture(scope='session')
def report():
    with open(REPORT_PATH, 'r') as f:
        return json.load(f)


@pytest.fixture(scope='session')
def state_by_junction(state_records):
    return {r['junction_id']: r for r in state_records}


# ============================================================
# TIER 1: Structural tests
# ============================================================

class TestTier1Structure:

    def test_output_files_exist(self):
        assert os.path.isfile(STATE_PATH), f"Missing {STATE_PATH}"
        assert os.path.isfile(REPORT_PATH), f"Missing {REPORT_PATH}"

    def test_junction_count(self, state_records):
        assert len(state_records) == 7

    def test_junction_ids(self, state_records):
        ids = sorted([r['junction_id'] for r in state_records])
        assert ids == ALL_JUNCTIONS

    def test_events_per_junction(self, state_by_junction):
        for jid, expected_count in EXPECTED_EVENT_COUNTS.items():
            actual = state_by_junction[jid]['event_count']
            assert actual == expected_count, f"{jid}: {actual} != {expected_count}"

    def test_required_fields(self, state_records):
        required = {'junction_id', 'pressure_vector', 'event_count', 'pressure_map'}
        for record in state_records:
            missing = required - set(record.keys())
            assert not missing, f"Missing: {missing}"

    def test_total_event_count(self, state_records):
        total = sum(r['event_count'] for r in state_records)
        assert total == TOTAL_EVENTS


# ============================================================
# TIER 2: Pressure state tests
# ============================================================

class TestTier2PressureState:

    def test_pressure_own_component(self, state_by_junction):
        alpha_own = state_by_junction['junc_alpha']['pressure_vector'][0]
        assert alpha_own == 14, f"junc_alpha own: {alpha_own}"
        beta_own = state_by_junction['junc_beta']['pressure_vector'][1]
        assert beta_own == 14, f"junc_beta own: {beta_own}"

    def test_couple_knowledge_transfer(self, state_by_junction):
        alpha_beta = state_by_junction['junc_alpha']['pressure_vector'][1]
        assert alpha_beta == 9, f"junc_alpha beta component: {alpha_beta}"

    def test_vector_sums(self, state_by_junction):
        expected_sums = {
            'junc_alpha': 50,
            'junc_beta': 41,
            'junc_delta': 51,
            'junc_gamma': 42,
            'junc_zeta': 40,
        }
        for jid, expected in expected_sums.items():
            actual = sum(state_by_junction[jid]['pressure_vector'])
            assert actual == expected, f"{jid}: sum {actual} != {expected}"


# ============================================================
# TIER 3: Flow analysis tests
# ============================================================

class TestTier3FlowAnalysis:

    def test_priority_ordering(self, report):
        priority = report['priority_order']
        assert priority[0] == 'junc_delta', f"top priority: {priority[0]}"
        assert priority[1] == 'junc_alpha', f"second priority: {priority[1]}"

    def test_independent_pair_count(self, report):
        count = report['flow_analysis']['independent_count']
        assert count == 20, f"independent pairs: {count}"

    def test_classification_coverage(self, report):
        analysis = report['flow_analysis']
        total = analysis['total_pairs']
        indep = analysis['independent_count']
        dep = analysis['dependent_count']
        assert total == 21, f"total: {total}"
        assert indep + dep == 21, f"{indep} + {dep} != 21"


# ============================================================
# TIER 4: Full consistency tests
# ============================================================

class TestTier4Consistency:

    def test_report_digest(self, report):
        assert report['digest'] == '5426791a02bc19a0', f"digest: {report['digest']}"

    def test_cross_validation(self, state_by_junction, report):
        cross = report['cross_validation']
        assert cross['junc_epsilon:junc_zeta']['independent'] is False
        assert cross['junc_alpha:junc_beta']['independent'] is True
        assert cross['junc_alpha:junc_delta']['independent'] is True
        assert cross['junc_delta:junc_gamma']['independent'] is True
        for jid in ALL_JUNCTIONS:
            report_vec = report['junction_summaries'][jid]['pressure_vector']
            state_vec = state_by_junction[jid]['pressure_vector']
            assert report_vec == state_vec, f"{jid}: mismatch"
