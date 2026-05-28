"""Test suite for armada clash engagement simulation.

Validates the engagement processing pipeline, vector computations,
autonomy analysis, deployment ordering, and report integrity.
"""
import json
import hashlib
import os
import sys

sys.path.insert(0, '/app')


REPORT_PATH = '/app/runtime/armada_report.json'
STATE_PATH = '/app/runtime/clash_state.jsonl'


def load_report():
    """Load the generated armada report."""
    with open(REPORT_PATH, 'r') as f:
        return json.load(f)


def load_state_log():
    """Load the intermediate state log."""
    entries = []
    with open(STATE_PATH, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


# ============================================================
# Tier 1: Structural validation (always pass)
# ============================================================

class TestStructuralIntegrity:
    """Basic structural checks that validate report format."""

    def test_report_file_exists(self):
        """Verify that the armada report file was generated."""
        assert os.path.exists(REPORT_PATH), "armada_report.json not found"

    def test_report_has_required_keys(self):
        """Verify report contains all expected top-level keys."""
        report = load_report()
        required = {'vectors', 'autonomous_pairs', 'deployment_order',
                    'fleet_count', 'total_engagements', 'digest'}
        assert required.issubset(set(report.keys()))

    def test_all_armadas_present(self):
        """Verify all 7 armadas have vector entries."""
        report = load_report()
        expected_ids = {f'A{i}' for i in range(7)}
        assert set(report['vectors'].keys()) == expected_ids

    def test_vector_dimensions_correct(self):
        """Verify each vector has exactly 7 components."""
        report = load_report()
        for aid, vec in report['vectors'].items():
            assert len(vec) == 7, f"{aid} has {len(vec)} components, expected 7"

    def test_base_values_present(self):
        """Verify all vector components are at least BASE_VALUE (3)."""
        report = load_report()
        for aid, vec in report['vectors'].items():
            for i, v in enumerate(vec):
                assert v >= 3, f"{aid}[{i}] = {v}, expected >= 3"

    def test_deployment_order_length(self):
        """Verify deployment order contains all 7 armadas."""
        report = load_report()
        assert len(report['deployment_order']) == 7


# ============================================================
# Tier 2: Event processing validation (always pass)
# ============================================================

class TestEventProcessing:
    """Validate that event ingestion and state logging are correct."""

    def test_event_count_in_state_file(self):
        """Verify state log contains exactly 45 processed events."""
        state_log = load_state_log()
        assert len(state_log) == 45, f"Expected 45 events, got {len(state_log)}"

    def test_sector_coverage(self):
        """Verify engagement events span multiple operational sectors."""
        state_log = load_state_log()
        # Check that events reference the expected event types
        event_types = {entry['event'] for entry in state_log}
        assert 'SKIRMISH' in event_types
        assert 'BARRAGE' in event_types
        assert 'REGROUP' in event_types


# ============================================================
# Tier 3: Analytical correctness (fail with bugs)
# ============================================================

class TestAnalyticalCorrectness:
    """Validate computed analytical results against expected values."""

    def test_autonomous_pair_count(self):
        """Verify the correct number of autonomous fleet pairs.

        With proper autonomy analysis, the engagement vectors should
        yield exactly 21 operationally autonomous pairs.
        """
        report = load_report()
        assert len(report['autonomous_pairs']) == 21, (
            f"Expected 21 autonomous pairs, got {len(report['autonomous_pairs'])}"
        )

    def test_specific_autonomous_pairs(self):
        """Verify specific known autonomous pairs are identified.

        These pairs have been independently verified through manual
        analysis of the engagement log.
        """
        report = load_report()
        pairs_set = {tuple(p) for p in report['autonomous_pairs']}
        # These specific pairs must be present
        expected_subset = [
            ('A0', 'A6'),
            ('A2', 'A4'),
            ('A3', 'A5'),
            ('A1', 'A3'),
        ]
        for pair in expected_subset:
            assert pair in pairs_set, f"Expected autonomous pair {pair} not found"

    def test_deployment_order_by_weight(self):
        """Verify deployment ordering reflects engagement vector weight.

        Deployment priority should be determined by total engagement
        depth (sum of vector components), not temporal recency.
        """
        report = load_report()
        expected_order = ['A5', 'A1', 'A0', 'A3', 'A2', 'A4', 'A6']
        assert report['deployment_order'] == expected_order, (
            f"Expected {expected_order}, got {report['deployment_order']}"
        )

    def test_vector_values_after_regroup(self):
        """Verify vector state correctly reflects regroup operations.

        Armada A5 performs two regroup operations. Its final vector
        should reflect both the merged awareness and the local
        engagement increments from each synchronization event.
        """
        report = load_report()
        # A5 regroups from A0 (tick 27) and A4 (tick 37)
        # Expected final vector for A5 with correct regroup handling
        expected_a5 = [11, 9, 6, 3, 10, 11, 5]
        assert report['vectors']['A5'] == expected_a5, (
            f"A5 vector expected {expected_a5}, got {report['vectors']['A5']}"
        )


# ============================================================
# Tier 4: Full consistency (fail with bugs)
# ============================================================

class TestConsistency:
    """Validate full pipeline consistency including digest."""

    def test_digest_integrity(self):
        """Verify report digest matches the validated reference value.

        The digest must match the known-good SHA256 computed from
        correct vector states, autonomous pairs, and deployment order.
        """
        report = load_report()
        expected_digest = '108cb7df8bfe718defc64f72b717796ce43101d013acc1d1c0f6f6d13bc11b8d'
        assert report['digest'] == expected_digest, (
            f"Digest mismatch: expected {expected_digest}, got {report['digest']}"
        )

    def test_full_consistency_check(self):
        """Verify all analytical outputs are internally consistent.

        Cross-validates autonomous pairs against vector states and
        confirms deployment order matches vector weight ranking.
        """
        report = load_report()
        vectors = report['vectors']

        # Verify deployment order matches weight sort
        weights = {aid: sum(vec) for aid, vec in vectors.items()}
        expected_deploy = sorted(vectors.keys(), key=lambda x: weights[x], reverse=True)
        assert report['deployment_order'] == expected_deploy, (
            "Deployment order inconsistent with vector weights"
        )

        # Verify autonomous pairs use correct incomparability criterion
        def vec_dominates(a, b):
            return all(x >= y for x, y in zip(a, b)) and any(x > y for x, y in zip(a, b))

        sorted_ids = sorted(vectors.keys())
        expected_pairs = []
        for i in range(len(sorted_ids)):
            for j in range(i + 1, len(sorted_ids)):
                va = vectors[sorted_ids[i]]
                vb = vectors[sorted_ids[j]]
                if not vec_dominates(va, vb) and not vec_dominates(vb, va):
                    expected_pairs.append([sorted_ids[i], sorted_ids[j]])

        assert report['autonomous_pairs'] == expected_pairs, (
            f"Autonomous pairs inconsistent: expected {len(expected_pairs)}, "
            f"got {len(report['autonomous_pairs'])}"
        )
