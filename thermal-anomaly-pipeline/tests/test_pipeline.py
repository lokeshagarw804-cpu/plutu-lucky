"""
Test suite for Thermal Anomaly Detection Pipeline.
Validates pipeline output correctness including aggregate metrics,
per-zone behavior, scoring accuracy, and alert ordering guarantees.
"""
import sys
import os
import json
import pytest

# Add runtime to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'environment', 'runtime'))

from run_pipeline import run_pipeline


@pytest.fixture(scope='module')
def pipeline_result():
    """Run the pipeline once and cache the result for all tests."""
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'environment', 'runtime', 'data')
    config_path = os.path.join(os.path.dirname(__file__), '..', 'environment', 'runtime', 'config.ini')
    return run_pipeline(data_dir, config_path)


# ============================================================
# SECTION 1: Aggregate metrics (visible behavior tests)
# ============================================================

class TestPipelineStats:
    """Test basic pipeline processing statistics."""

    def test_zones_processed(self, pipeline_result):
        """All four zones should be processed."""
        assert pipeline_result['pipeline_stats']['zones_processed'] == 4

    def test_total_windows_generated(self, pipeline_result):
        """Correct number of sliding windows should be created."""
        assert pipeline_result['pipeline_stats']['total_windows'] == 14

    def test_total_breaches_detected(self, pipeline_result):
        """All threshold breaches should be detected and scored above minimum."""
        assert pipeline_result['pipeline_stats']['total_breaches'] == 11


class TestCorrelationSummary:
    """Test cross-zone correlation behavior."""

    def test_pre_correlation_breach_count(self, pipeline_result):
        """Pre-correlation breach count should match total breaches."""
        assert pipeline_result['correlation_summary']['pre_correlation_breaches'] == 11

    def test_correlated_event_count(self, pipeline_result):
        """After correlation and deduplication, all 11 events should survive.
        Events from different zones at the same timestamp are NOT duplicates."""
        assert pipeline_result['correlation_summary']['total_correlated_events'] == 11


class TestAlertBatchAggregates:
    """Test alert batch summary metrics."""

    def test_batch_size(self, pipeline_result):
        """Batch should contain all correlated events."""
        assert pipeline_result['alert_batch']['batch_size'] == 11

    def test_severity_distribution(self, pipeline_result):
        """Correct count of critical and high alerts."""
        counts = pipeline_result['alert_batch']['severity_counts']
        assert counts.get('critical', 0) == 3
        assert counts.get('high', 0) == 8

    def test_total_batch_score(self, pipeline_result):
        """Total score across all alerts must be correct (tests weight accumulation)."""
        assert pipeline_result['alert_batch']['total_score'] == 2368.45


# ============================================================
# SECTION 2: Per-zone and per-alert semantic assertions
# ============================================================

class TestZoneAlpha:
    """Validate zone_alpha alert properties."""

    def test_alpha_has_critical_alert(self, pipeline_result):
        """zone_alpha should produce a critical-severity alert."""
        alerts = pipeline_result['alert_batch']['alerts']
        alpha_critical = [a for a in alerts if a['zone_id'] == 'zone_alpha' and a['severity'] == 'critical']
        assert len(alpha_critical) == 1

    def test_alpha_critical_score(self, pipeline_result):
        """zone_alpha critical alert score must reflect multi-weight accumulation."""
        alerts = pipeline_result['alert_batch']['alerts']
        alpha_critical = [a for a in alerts if a['zone_id'] == 'zone_alpha' and a['severity'] == 'critical'][0]
        # With weights [0.9, 1.3, 0.4]: accumulated = 0.9*(4/4) + 1.3 + 0.4*0.5 = 0.9 + 1.3 + 0.2 = 2.4
        # final = 83.6 * (1 + 2.4) = 83.6 * 3.4 = 284.24
        assert alpha_critical['final_score'] == 284.24

    def test_alpha_alert_count(self, pipeline_result):
        """zone_alpha should have exactly 3 alerts (1 critical + 2 high)."""
        alerts = pipeline_result['alert_batch']['alerts']
        alpha_alerts = [a for a in alerts if a['zone_id'] == 'zone_alpha']
        assert len(alpha_alerts) == 3


class TestZoneGamma:
    """Validate zone_gamma presence (tests deduplication correctness)."""

    def test_gamma_has_critical_alert(self, pipeline_result):
        """zone_gamma must have a critical alert (dedup must not remove cross-zone events)."""
        alerts = pipeline_result['alert_batch']['alerts']
        gamma_critical = [a for a in alerts if a['zone_id'] == 'zone_gamma' and a['severity'] == 'critical']
        assert len(gamma_critical) == 1

    def test_gamma_critical_timestamp(self, pipeline_result):
        """zone_gamma critical alert should be at timestamp 1020."""
        alerts = pipeline_result['alert_batch']['alerts']
        gamma_critical = [a for a in alerts if a['zone_id'] == 'zone_gamma' and a['severity'] == 'critical'][0]
        assert gamma_critical['timestamp'] == 1020

    def test_gamma_has_high_alert(self, pipeline_result):
        """zone_gamma should also have a high-severity alert."""
        alerts = pipeline_result['alert_batch']['alerts']
        gamma_high = [a for a in alerts if a['zone_id'] == 'zone_gamma' and a['severity'] == 'high']
        assert len(gamma_high) == 1


class TestZoneDelta:
    """Validate zone_delta alert properties."""

    def test_delta_alert_count(self, pipeline_result):
        """zone_delta should have exactly 3 high-severity alerts."""
        alerts = pipeline_result['alert_batch']['alerts']
        delta_alerts = [a for a in alerts if a['zone_id'] == 'zone_delta']
        assert len(delta_alerts) == 3

    def test_delta_highest_score(self, pipeline_result):
        """zone_delta's highest-scoring alert should have correct weighted score."""
        alerts = pipeline_result['alert_batch']['alerts']
        delta_alerts = [a for a in alerts if a['zone_id'] == 'zone_delta']
        max_score = max(a['final_score'] for a in delta_alerts)
        # weights [0.7, 1.8, 0.6]: accumulated = 0.7*(3/3) + 1.8 + 0.6*0.5 = 0.7 + 1.8 + 0.3 = 2.8
        # final = 72.98 * (1 + 2.8) = 72.98 * 3.8 = 277.32
        assert max_score == 277.32


# ============================================================
# SECTION 3: Alert ordering guarantees (determinism tests)
# ============================================================

class TestAlertOrdering:
    """Validate alert priority ordering is deterministic and correct."""

    def test_critical_before_high(self, pipeline_result):
        """All critical alerts must appear before any high alert."""
        alerts = pipeline_result['alert_batch']['alerts']
        last_critical_idx = -1
        first_high_idx = len(alerts)
        for i, a in enumerate(alerts):
            if a['severity'] == 'critical':
                last_critical_idx = max(last_critical_idx, i)
            elif a['severity'] == 'high':
                first_high_idx = min(first_high_idx, i)
        assert last_critical_idx < first_high_idx

    def test_same_severity_ordered_by_score_desc(self, pipeline_result):
        """Within same severity, alerts must be ordered by score descending."""
        alerts = pipeline_result['alert_batch']['alerts']
        # Check high-severity alerts are score-descending
        high_alerts = [a for a in alerts if a['severity'] == 'high']
        scores = [a['final_score'] for a in high_alerts]
        assert scores == sorted(scores, reverse=True), \
            f"High alerts not sorted by score desc: {scores}"

    def test_same_score_ordered_by_timestamp_asc(self, pipeline_result):
        """If two alerts have same severity and score, earlier timestamp comes first."""
        alerts = pipeline_result['alert_batch']['alerts']
        # This tests the tiebreaker - same severity, check timestamp ordering for equal scores
        high_alerts = [a for a in alerts if a['severity'] == 'high']
        for i in range(len(high_alerts) - 1):
            a, b = high_alerts[i], high_alerts[i + 1]
            if a['final_score'] == b['final_score']:
                assert a['timestamp'] <= b['timestamp'], \
                    f"Same-score alerts not ordered by timestamp: {a['timestamp']} > {b['timestamp']}"

    def test_first_alert_is_zone_beta_critical(self, pipeline_result):
        """The highest priority alert should be zone_beta critical (highest critical score)."""
        first_alert = pipeline_result['alert_batch']['alerts'][0]
        assert first_alert['zone_id'] == 'zone_beta'
        assert first_alert['severity'] == 'critical'
        assert first_alert['final_score'] == 295.68

    def test_alert_indices_sequential(self, pipeline_result):
        """Alert indices must be sequential starting from 0."""
        alerts = pipeline_result['alert_batch']['alerts']
        indices = [a['index'] for a in alerts]
        assert indices == list(range(len(alerts)))
