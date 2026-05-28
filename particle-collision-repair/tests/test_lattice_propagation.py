"""
Lattice Propagation Test Suite
================================
Verifies the particle collision repair pipeline produces correct
propagation state and synthesis report outputs.

Test tiers:
- Structural (8): always pass with correct pipeline execution
- Depth accuracy (2): verify signal depth calculations
- Analysis accuracy (2): verify isolation and priority logic
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

STATE_PATH = os.path.join(RUNTIME_DIR, 'propagation_state.jsonl')
REPORT_PATH = os.path.join(RUNTIME_DIR, 'synthesis_report.json')

EXPECTED_NODES = ['n0', 'n1', 'n2', 'n3', 'n4', 'n5', 'n6']
EXPECTED_EVENT_COUNTS = {'n0': 10, 'n1': 7, 'n2': 6, 'n3': 6, 'n4': 6, 'n5': 6, 'n6': 4}
EXPECTED_TOTAL_EVENTS = 45


def load_state():
    """Load propagation state from JSONL file."""
    records = {}
    with open(STATE_PATH, 'r') as f:
        for line in f:
            record = json.loads(line.strip())
            records[record['node_id']] = record
    return records


def load_report():
    """Load synthesis report from JSON file."""
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

    def test_all_nodes_present(self):
        state = load_state()
        assert sorted(state.keys()) == EXPECTED_NODES

    def test_event_counts(self):
        state = load_state()
        for node, expected in EXPECTED_EVENT_COUNTS.items():
            assert state[node]['event_count'] == expected, \
                f"Node {node}: expected {expected} events, got {state[node]['event_count']}"

    def test_total_event_count(self):
        state = load_state()
        total = sum(r['event_count'] for r in state.values())
        assert total == EXPECTED_TOTAL_EVENTS

    def test_depth_vector_length(self):
        state = load_state()
        for node in EXPECTED_NODES:
            vec = state[node]['depth_vector']
            assert len(vec) == 7, f"Node {node}: depth vector has {len(vec)} components, expected 7"

    def test_report_has_required_fields(self):
        report = load_report()
        required = ['isolated_pairs', 'isolated_pair_count', 'priority_order', 'digest']
        for field in required:
            assert field in report, f"Missing field: {field}"

    def test_priority_order_contains_all_nodes(self):
        report = load_report()
        assert sorted(report['priority_order']) == EXPECTED_NODES


# ==============================================================
# TIER 2: Depth accuracy tests (fail with Bug 1)
# ==============================================================

class TestDepthAccuracy:
    """Tests that verify signal depth calculations are correct."""

    def test_n0_self_depth(self):
        """n0 processes 4 PULSE (+4) + 3 BURST (+6) + 3 RELAY on base 3 = 16."""
        state = load_state()
        n0_depth = state['n0']['depth_vector']['n0']
        assert n0_depth == 16, f"n0 self-depth: expected 16, got {n0_depth}"

    def test_n5_total_depth(self):
        """Total depth for n5 should be 47."""
        state = load_state()
        assert state['n5']['total_depth'] == 47, \
            f"n5 total_depth: expected 47, got {state['n5']['total_depth']}"


# ==============================================================
# TIER 3: Analysis accuracy tests (fail with Bug 2 and Bug 3)
# ==============================================================

class TestAnalysisAccuracy:
    """Tests that verify isolation and priority analysis."""

    def test_isolated_pair_count(self):
        """Should find exactly 21 isolated pairs."""
        report = load_report()
        assert report['isolated_pair_count'] == 21, \
            f"Isolated pairs: expected 21, got {report['isolated_pair_count']}"

    def test_priority_order(self):
        """Priority order must reflect total accumulated signal strength."""
        report = load_report()
        expected = ['n0', 'n5', 'n1', 'n2', 'n3', 'n4', 'n6']
        assert report['priority_order'] == expected, \
            f"Priority order: expected {expected}, got {report['priority_order']}"


# ==============================================================
# TIER 4: Integrity tests (fail when depths or analysis wrong)
# ==============================================================

class TestIntegrity:
    """Tests that verify overall report consistency."""

    def test_digest(self):
        """MD5 digest must match expected value for correct propagation state."""
        report = load_report()
        assert report['digest'] == '54784ba07076c2ca', \
            f"Digest: expected '54784ba07076c2ca', got '{report['digest']}'"

    def test_isolated_pairs_consistent(self):
        """Independently verify isolation count from depth state matches report."""
        report = load_report()
        state = load_state()
        sys.path.insert(0, RUNTIME_DIR)
        from lattice_analysis import check_signal_isolation
        node_list = sorted(state.keys())
        count = 0
        for i in range(len(node_list)):
            for j in range(i + 1, len(node_list)):
                va = list(state[node_list[i]]['depth_vector'].values())
                vb = list(state[node_list[j]]['depth_vector'].values())
                if check_signal_isolation(va, vb):
                    count += 1
        assert count == 21, \
            f"Recomputed isolated pair count: expected 21, got {count}"
