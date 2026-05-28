"""
Type Inference Test Suite
==========================
Verifies the type inference constraint solver pipeline produces correct
constraint state and inference report outputs.

Test tiers:
- Structural (8): always pass with correct pipeline execution
- Constraint accuracy (2): verify constraint calculations
- Analysis accuracy (2): verify compatibility and priority logic
- Integrity (2): verify report consistency
"""
import json
import os
import sys

# Use /app/runtime in Docker, fall back to relative path for local dev
RUNTIME_DIR = '/app/runtime'
if not os.path.isdir(RUNTIME_DIR):
    RUNTIME_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'runtime')

sys.path.insert(0, RUNTIME_DIR)

STATE_PATH = os.path.join(RUNTIME_DIR, 'type_state.jsonl')
REPORT_PATH = os.path.join(RUNTIME_DIR, 'inference_report.json')

EXPECTED_TYPE_IDS = ['t0', 't1', 't2', 't3', 't4', 't5', 't6']
EXPECTED_EVENT_COUNTS = {'t0': 10, 't1': 7, 't2': 6, 't3': 6, 't4': 6, 't5': 6, 't6': 4}
EXPECTED_TOTAL_EVENTS = 45


def load_state():
    """Load type state from JSONL file."""
    records = {}
    with open(STATE_PATH, 'r') as f:
        for line in f:
            record = json.loads(line.strip())
            records[record['type_id']] = record
    return records


def load_report():
    """Load inference report from JSON file."""
    with open(REPORT_PATH, 'r') as f:
        return json.load(f)


# ==============================================================
# TIER 1: Structural tests (always pass with correct pipeline)
# ==============================================================

class TestStructural:
    """Tests that verify pipeline outputs exist and have correct shape."""

    def test_state_file_exists(self):
        assert os.path.isfile(STATE_PATH), f"Missing {STATE_PATH}"

    def test_report_file_exists(self):
        assert os.path.isfile(REPORT_PATH), f"Missing {REPORT_PATH}"

    def test_all_types_present(self):
        state = load_state()
        assert sorted(state.keys()) == EXPECTED_TYPE_IDS

    def test_event_counts(self):
        state = load_state()
        for tid, expected in EXPECTED_EVENT_COUNTS.items():
            assert state[tid]['event_count'] == expected, \
                f"Type {tid}: expected {expected} events, got {state[tid]['event_count']}"

    def test_total_event_count(self):
        state = load_state()
        total = sum(r['event_count'] for r in state.values())
        assert total == EXPECTED_TOTAL_EVENTS

    def test_constraint_vector_length(self):
        state = load_state()
        for tid in EXPECTED_TYPE_IDS:
            vec = state[tid]['constraint_vector']
            assert len(vec) == 7, f"Type {tid}: constraint vector has {len(vec)} components, expected 7"

    def test_report_has_required_fields(self):
        report = load_report()
        required = ['compatible_pairs', 'compatible_pair_count', 'priority_order', 'digest']
        for field in required:
            assert field in report, f"Missing field: {field}"

    def test_priority_order_contains_all_types(self):
        report = load_report()
        assert sorted(report['priority_order']) == EXPECTED_TYPE_IDS


# ==============================================================
# TIER 2: Constraint accuracy tests (fail with Bug 1)
# ==============================================================

class TestConstraintAccuracy:
    """Tests that verify constraint calculations are correct."""

    def test_t0_self_constraint(self):
        """t0 processes 4 BIND (+4) + 3 PROPAGATE (+6) + 3 UNIFY on base 3 = 16."""
        state = load_state()
        t0_constraint = state['t0']['constraint_vector']['t0']
        assert t0_constraint == 16, f"t0 self-constraint: expected 16, got {t0_constraint}"

    def test_t5_total_constraints(self):
        """Total constraints for t5 should be 47."""
        state = load_state()
        assert state['t5']['total_constraints'] == 47, \
            f"t5 total_constraints: expected 47, got {state['t5']['total_constraints']}"


# ==============================================================
# TIER 3: Analysis accuracy tests (fail with Bug 2 and Bug 3)
# ==============================================================

class TestAnalysisAccuracy:
    """Tests that verify compatibility and priority analysis."""

    def test_compatible_pair_count(self):
        """Should find exactly 21 compatible pairs."""
        report = load_report()
        assert report['compatible_pair_count'] == 21, \
            f"Compatible pairs: expected 21, got {report['compatible_pair_count']}"

    def test_priority_order(self):
        """Priority order must reflect total accumulated constraint strength."""
        report = load_report()
        expected = ['t0', 't5', 't1', 't2', 't3', 't4', 't6']
        assert report['priority_order'] == expected, \
            f"Priority order: expected {expected}, got {report['priority_order']}"


# ==============================================================
# TIER 4: Integrity tests (fail when constraints or analysis wrong)
# ==============================================================

class TestIntegrity:
    """Tests that verify overall report consistency."""

    def test_digest(self):
        """MD5 digest must match expected value for correct constraint state."""
        report = load_report()
        assert report['digest'] == '3fed9282152e0234', \
            f"Digest: expected '3fed9282152e0234', got '{report['digest']}'"

    def test_compatible_pairs_consistent(self):
        """Independently verify compatibility count from constraint state matches report."""
        report = load_report()
        state = load_state()
        sys.path.insert(0, RUNTIME_DIR)
        from type_analyzer import check_type_compatibility
        type_list = sorted(state.keys())
        count = 0
        for i in range(len(type_list)):
            for j in range(i + 1, len(type_list)):
                va = list(state[type_list[i]]['constraint_vector'].values())
                vb = list(state[type_list[j]]['constraint_vector'].values())
                if check_type_compatibility(va, vb):
                    count += 1
        assert count == 21, \
            f"Recomputed compatible pair count: expected 21, got {count}"
