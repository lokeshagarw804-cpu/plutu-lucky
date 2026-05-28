"""
Validation suite for the lattice momentum propagation simulator.
"""

import json
import os

STATE_PATH = "/app/runtime/output/lattice_state.jsonl"
REPORT_PATH = "/app/runtime/output/flow_report.json"

EXPECTED_CELLS = [
    "cell_0_0", "cell_0_1", "cell_1_0", "cell_1_1",
    "cell_2_0", "cell_2_1", "cell_2_2",
]

EVENT_COUNTS = {
    "cell_0_0": 10,
    "cell_0_1": 9,
    "cell_1_0": 9,
    "cell_1_1": 9,
    "cell_2_0": 9,
    "cell_2_1": 9,
    "cell_2_2": 10,
}

STREAM_DRIFT_TOTALS = {
    "cell_0_0": 10,
    "cell_0_1": 11,
    "cell_1_0": 11,
    "cell_1_1": 12,
    "cell_2_0": 11,
    "cell_2_1": 12,
    "cell_2_2": 11,
}


def _load_state():
    records = {}
    with open(STATE_PATH) as f:
        for line in f:
            obj = json.loads(line.strip())
            records[obj["cell_id"]] = obj
    return records


def _load_report():
    with open(REPORT_PATH) as f:
        return json.load(f)


class TestTier1Structural:

    def test_output_files_exist(self):
        assert os.path.isfile(STATE_PATH)
        assert os.path.isfile(REPORT_PATH)

    def test_cell_count(self):
        records = _load_state()
        assert len(records) == 7

    def test_cell_identifiers(self):
        records = _load_state()
        for cid in EXPECTED_CELLS:
            assert cid in records

    def test_events_per_cell(self):
        records = _load_state()
        for cid, expected in EVENT_COUNTS.items():
            assert records[cid]["total_events"] == expected

    def test_required_fields(self):
        records = _load_state()
        for cid, rec in records.items():
            assert "cell_id" in rec
            assert "momentum_vector" in rec
            assert "total_events" in rec
            assert "last_event_step" in rec

    def test_total_event_count(self):
        records = _load_state()
        total = sum(rec["total_events"] for rec in records.values())
        assert total == 65

    def test_vector_dimensions(self):
        records = _load_state()
        for cid, rec in records.items():
            assert len(rec["momentum_vector"]) == 7
            for k in EXPECTED_CELLS:
                assert k in rec["momentum_vector"]

    def test_momentum_non_negative(self):
        records = _load_state()
        for cid, rec in records.items():
            for k, v in rec["momentum_vector"].items():
                assert v >= 0


class TestTier2Momentum:

    def test_collision_participant_momentum(self):
        records = _load_state()
        assert records["cell_0_0"]["momentum_vector"]["cell_0_0"] == 16
        assert records["cell_1_1"]["momentum_vector"]["cell_1_1"] == 17
        assert records["cell_2_2"]["momentum_vector"]["cell_2_2"] == 17
        assert records["cell_2_1"]["momentum_vector"]["cell_2_1"] == 17

    def test_aggregate_magnitude_bounds(self):
        records = _load_state()
        total = sum(
            sum(rec["momentum_vector"].values())
            for rec in records.values()
        )
        assert 338 <= total <= 350

    def test_collision_increment_invariant(self):
        records = _load_state()
        base = 3
        collision_cells = [
            "cell_0_0", "cell_0_1", "cell_1_0", "cell_1_1",
            "cell_2_0", "cell_2_1", "cell_2_2",
        ]
        for cid in collision_cells:
            own_val = records[cid]["momentum_vector"][cid]
            threshold = base + STREAM_DRIFT_TOTALS[cid]
            assert own_val > threshold


class TestTier3Regime:

    def test_regime_classification_count(self):
        report = _load_report()
        assert report["decoupled_count"] == 21

    def test_relaxation_ordering_property(self):
        report = _load_report()
        priority = report["relaxation_priority"]
        magnitudes = report["magnitude_map"]
        for i in range(len(priority) - 1):
            assert magnitudes[priority[i]] >= magnitudes[priority[i + 1]]


class TestTier4Integration:

    def test_simulation_digest(self):
        report = _load_report()
        assert report["digest"] == "c7a86047371a8b007e07f62aceb869519acc486bd4a1b44f4482d0c277c2917a"
