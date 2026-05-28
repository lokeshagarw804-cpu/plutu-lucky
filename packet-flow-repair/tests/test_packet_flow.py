"""Tests for distributed sensor network observation simulation."""
import json
import os
import pytest


STATE_PATH = '/app/runtime/flow_state.jsonl'
REPORT_PATH = '/app/runtime/flow_report.json'

ALL_SENSORS = [
    'sensor_core', 'sensor_east', 'sensor_edge', 'sensor_gate',
    'sensor_north', 'sensor_south', 'sensor_west'
]

EXPECTED_EVENT_COUNTS = {
    'sensor_north': 9,
    'sensor_south': 9,
    'sensor_east': 7,
    'sensor_west': 8,
    'sensor_core': 6,
    'sensor_edge': 7,
    'sensor_gate': 6,
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
def state_by_sensor(state_records):
    return {r['sensor_id']: r for r in state_records}


# ============================================================
# TIER 1: Structural tests
# ============================================================

class TestTier1Structure:

    def test_output_files_exist(self):
        assert os.path.isfile(STATE_PATH), f"Missing {STATE_PATH}"
        assert os.path.isfile(REPORT_PATH), f"Missing {REPORT_PATH}"

    def test_sensor_count(self, state_records):
        assert len(state_records) == 7

    def test_sensor_ids(self, state_records):
        ids = sorted([r['sensor_id'] for r in state_records])
        assert ids == ALL_SENSORS

    def test_events_per_sensor(self, state_by_sensor):
        for sid, expected_count in EXPECTED_EVENT_COUNTS.items():
            actual = state_by_sensor[sid]['event_count']
            assert actual == expected_count, f"{sid}: {actual} != {expected_count}"

    def test_required_fields(self, state_records):
        required = {'sensor_id', 'observation_vector', 'event_count', 'observation_map'}
        for record in state_records:
            missing = required - set(record.keys())
            assert not missing, f"Missing: {missing}"

    def test_total_event_count(self, state_records):
        total = sum(r['event_count'] for r in state_records)
        assert total == TOTAL_EVENTS


# ============================================================
# TIER 2: Observation state tests
# ============================================================

class TestTier2ObservationState:

    def test_observation_own_component(self, state_by_sensor):
        north_own = state_by_sensor['sensor_north']['observation_vector'][4]
        assert north_own == 14, f"sensor_north own: {north_own}"
        south_own = state_by_sensor['sensor_south']['observation_vector'][5]
        assert south_own == 14, f"sensor_south own: {south_own}"

    def test_sync_knowledge_transfer(self, state_by_sensor):
        north_south = state_by_sensor['sensor_north']['observation_vector'][5]
        assert north_south == 9, f"sensor_north south component: {north_south}"

    def test_vector_sums(self, state_by_sensor):
        expected_sums = {
            'sensor_north': 50,
            'sensor_south': 41,
            'sensor_west': 51,
            'sensor_east': 42,
            'sensor_edge': 40,
        }
        for sid, expected in expected_sums.items():
            actual = sum(state_by_sensor[sid]['observation_vector'])
            assert actual == expected, f"{sid}: sum {actual} != {expected}"


# ============================================================
# TIER 3: Flow analysis tests
# ============================================================

class TestTier3FlowAnalysis:

    def test_priority_ordering(self, report):
        priority = report['priority_order']
        assert priority[0] == 'sensor_west', f"top priority: {priority[0]}"
        assert priority[1] == 'sensor_north', f"second priority: {priority[1]}"

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
        assert report['digest'] == 'c0338b64eac91c22', f"digest: {report['digest']}"

    def test_cross_validation(self, state_by_sensor, report):
        cross = report['cross_validation']
        assert cross['sensor_core:sensor_edge']['independent'] is False
        assert cross['sensor_north:sensor_south']['independent'] is True
        assert cross['sensor_north:sensor_west']['independent'] is True
        assert cross['sensor_east:sensor_west']['independent'] is True
        for sid in ALL_SENSORS:
            report_vec = report['sensor_summaries'][sid]['observation_vector']
            state_vec = state_by_sensor[sid]['observation_vector']
            assert report_vec == state_vec, f"{sid}: mismatch"
