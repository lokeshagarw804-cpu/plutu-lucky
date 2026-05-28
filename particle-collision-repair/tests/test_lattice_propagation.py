"""
Tests for the Lattice Signal Propagation Simulator.

Validates structural output, depth computations, isolation classification,
and full-system integrity across the propagation pipeline.
"""
import json
import os
import sys

RUNTIME_DIR = '/app/runtime'
if not os.path.isdir(RUNTIME_DIR):
    RUNTIME_DIR = os.path.join(os.path.dirname(__file__), '..', 'runtime')
sys.path.insert(0, RUNTIME_DIR)

STATE_PATH = os.path.join(RUNTIME_DIR, 'propagation_state.jsonl')
REPORT_PATH = os.path.join(RUNTIME_DIR, 'synthesis_report.json')

EXPECTED_NODES = ['n0', 'n1', 'n2', 'n3', 'n4', 'n5', 'n6']
EXPECTED_EVENT_COUNTS = {'n0': 9, 'n1': 7, 'n2': 6, 'n3': 6, 'n4': 6, 'n5': 6, 'n6': 5}


def load_state():
    """Load propagation state from JSONL output."""
    records = {}
    with open(STATE_PATH, 'r') as f:
        for line in f:
            rec = json.loads(line.strip())
            records[rec['node_id']] = rec
    return records


def load_report():
    """Load synthesis report from JSON output."""
    with open(REPORT_PATH, 'r') as f:
        return json.load(f)


# ===========================================================================
# Tier 1: Structural validation (8 tests - always pass)
# ===========================================================================

class TestStructuralIntegrity:
    """Verify pipeline output structure and completeness."""

    def test_state_file_exists(self):
        """Pipeline must produce propagation state output."""
        assert os.path.isfile(STATE_PATH), "propagation_state.jsonl not found"

    def test_report_file_exists(self):
        """Pipeline must produce synthesis report output."""
        assert os.path.isfile(REPORT_PATH), "synthesis_report.json not found"

    def test_node_count(self):
        """State must contain records for all 7 sensor nodes."""
        state = load_state()
        assert len(state) == 7

    def test_node_ids(self):
        """State must contain the correct set of node identifiers."""
        state = load_state()
        assert sorted(state.keys()) == EXPECTED_NODES

    def test_event_counts(self):
        """Each node must have processed the expected number of events."""
        state = load_state()
        for node, expected in EXPECTED_EVENT_COUNTS.items():
            assert state[node]['event_count'] == expected, \
                f"{node}: expected {expected} events, got {state[node]['event_count']}"

    def test_required_fields(self):
        """Each state record must contain all required fields."""
        state = load_state()
        required = {'node_id', 'depth_vector', 'total_depth', 'event_count'}
        for node in EXPECTED_NODES:
            assert required.issubset(set(state[node].keys())), \
                f"{node} missing fields: {required - set(state[node].keys())}"

    def test_total_event_count(self):
        """Total events across all nodes must equal trace event count."""
        state = load_state()
        total = sum(state[n]['event_count'] for n in EXPECTED_NODES)
        assert total == 45

    def test_report_structure(self):
        """Synthesis report must contain all required sections."""
        report = load_report()
        required_keys = {'isolated_pairs', 'isolated_pair_count', 'priority_order', 'digest'}
        assert required_keys.issubset(set(report.keys()))


# ===========================================================================
# Tier 2: Depth computation validation (2 tests - fail with Bug 1)
# ===========================================================================

class TestDepthComputation:
    """Verify signal depth tracking accuracy after event processing."""

    def test_relay_node_depth_n0(self):
        """Primary relay sensor n0 must reach correct depth after processing."""
        state = load_state()
        assert state['n0']['depth_vector']['n0'] == 15

    def test_relay_affected_total(self):
        """Total depth for relay-active nodes must reflect full accumulation."""
        state = load_state()
        assert state['n5']['total_depth'] == 47


# ===========================================================================
# Tier 3: Analysis validation (2 tests - fail with Bugs 2+3)
# ===========================================================================

class TestAnalysisResults:
    """Verify isolation classification and priority ordering."""

    def test_isolated_pair_count(self):
        """Isolation analysis must identify correct pair count."""
        report = load_report()
        assert report['isolated_pair_count'] == 21

    def test_priority_order_full(self):
        """Priority ranking must reflect accumulated signal strength."""
        report = load_report()
        expected = ['n0', 'n5', 'n1', 'n2', 'n3', 'n4', 'n6']
        assert report['priority_order'] == expected


# ===========================================================================
# Tier 4: Full system integrity (2 tests - fail without all fixes)
# ===========================================================================

class TestSystemIntegrity:
    """Cross-validation of propagation state and synthesis outputs."""

    def test_digest_value(self):
        """Simulation digest must match expected propagation fingerprint."""
        report = load_report()
        assert report['digest'] == 'b60a42d61586d560'

    def test_priority_total_depth_consistency(self):
        """Priority order must be consistent with depth accumulation."""
        state = load_state()
        report = load_report()
        priority = report['priority_order']
        totals = [state[n]['total_depth'] for n in priority]
        for i in range(len(totals) - 1):
            assert totals[i] >= totals[i + 1], \
                f"Priority inconsistency: {priority[i]} ({totals[i]}) < {priority[i+1]} ({totals[i+1]})"
