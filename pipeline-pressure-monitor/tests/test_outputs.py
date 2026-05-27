"""Validation tests for pipeline pressure monitoring system output."""
import json
import os

import pytest

OUTPUT_DIR = "/app/runtime/output"
SUMMARY_PATH = os.path.join(OUTPUT_DIR, "summary.json")
EVENTS_PATH = os.path.join(OUTPUT_DIR, "events.json")
GRADIENT_STATS_PATH = os.path.join(OUTPUT_DIR, "gradient_stats.json")


@pytest.fixture(scope="module")
def summary_data():
    """Load summary output."""
    with open(SUMMARY_PATH, "r") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def events_data():
    """Load events output."""
    with open(EVENTS_PATH, "r") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def gradient_stats():
    """Load gradient statistics output."""
    with open(GRADIENT_STATS_PATH, "r") as f:
        return json.load(f)


class TestOutputFiles:
    """Basic output file validation."""

    def test_summary_file_exists(self):
        """Summary output must be generated."""
        assert os.path.isfile(SUMMARY_PATH)

    def test_events_file_exists(self):
        """Events output must be generated."""
        assert os.path.isfile(EVENTS_PATH)

    def test_gradient_stats_file_exists(self):
        """Gradient statistics output must be generated."""
        assert os.path.isfile(GRADIENT_STATS_PATH)

    def test_summary_structure(self, summary_data):
        """Summary output has required fields."""
        assert "segment_order" in summary_data
        assert "total_segments" in summary_data
        assert "total_events" in summary_data
        assert "events_by_type" in summary_data
        assert "per_segment_windows" in summary_data

    def test_events_structure(self, events_data):
        """Events output has required fields."""
        assert "total_events" in events_data
        assert "events" in events_data
        assert "threshold" in events_data


class TestSegmentOrdering:
    """Segment ordering in output."""

    def test_segment_count(self, summary_data):
        """Summary must include all 5 configured segments."""
        assert summary_data["total_segments"] == 5

    def test_segment_order_numeric(self, summary_data):
        """Segments must be ordered by numeric identifier."""
        order = summary_data["segment_order"]
        assert order == ["seg_1", "seg_2", "seg_3", "seg_4", "seg_10"]


class TestEventDetection:
    """Event detection accuracy."""

    def test_total_event_count(self, summary_data):
        """Must detect exactly 4 anomalous events."""
        assert summary_data["total_events"] == 4

    def test_surge_event_count(self, summary_data):
        """Must detect exactly 2 surge events."""
        assert summary_data["events_by_type"]["surge"] == 2

    def test_leak_event_count(self, summary_data):
        """Must detect exactly 2 leak events."""
        assert summary_data["events_by_type"]["leak"] == 2

    def test_seg1_has_surge(self, events_data):
        """seg_1 must have a surge event (strong positive gradient)."""
        events = events_data["events"]
        seg1_events = [e for e in events if e["segment_id"] == "seg_1"]
        assert len(seg1_events) >= 1
        surge_found = any(e["type"] == "surge" for e in seg1_events)
        assert surge_found, "seg_1 should have a surge event"

    def test_seg10_has_surge(self, events_data):
        """seg_10 must have a surge event (strong positive gradient)."""
        events = events_data["events"]
        seg10_events = [e for e in events if e["segment_id"] == "seg_10"]
        assert len(seg10_events) >= 1
        surge_found = any(e["type"] == "surge" for e in seg10_events)
        assert surge_found, "seg_10 should have a surge event"

    def test_seg3_has_leak(self, events_data):
        """seg_3 must have a leak event (strong negative gradient)."""
        events = events_data["events"]
        seg3_events = [e for e in events if e["segment_id"] == "seg_3"]
        assert len(seg3_events) >= 1
        leak_found = any(e["type"] == "leak" for e in seg3_events)
        assert leak_found, "seg_3 should have a leak event"

    def test_seg4_no_events(self, events_data):
        """seg_4 must have no events (oscillating, below threshold)."""
        events = events_data["events"]
        seg4_events = [e for e in events if e["segment_id"] == "seg_4"]
        assert len(seg4_events) == 0, f"seg_4 should have no events but got {len(seg4_events)}"

    def test_seg2_no_events(self, events_data):
        """seg_2 must have no events (low magnitude fluctuation)."""
        events = events_data["events"]
        seg2_events = [e for e in events if e["segment_id"] == "seg_2"]
        assert len(seg2_events) == 0, f"seg_2 should have no events but got {len(seg2_events)}"

    def test_event_duration_minimum(self, events_data):
        """All events must have duration >= min_duration_samples (3)."""
        for event in events_data["events"]:
            assert event["duration_windows"] >= 3


class TestGradientValues:
    """Gradient computation accuracy."""

    def test_seg3_highest_gradient(self, gradient_stats):
        """seg_3 must have the highest max gradient magnitude (steepest drop)."""
        seg3_max = gradient_stats["seg_3"]["max_magnitude"]
        for seg_id, stats in gradient_stats.items():
            if seg_id != "seg_3":
                assert seg3_max >= stats["max_magnitude"], (
                    f"seg_3 max_magnitude ({seg3_max}) should be >= "
                    f"{seg_id} max_magnitude ({stats['max_magnitude']})"
                )

    def test_seg1_gradient_significant(self, gradient_stats):
        """seg_1 gradient magnitude must be significant (> 2.0 kPa/s)."""
        assert gradient_stats["seg_1"]["mean_magnitude"] > 2.0

    def test_seg2_gradient_low(self, gradient_stats):
        """seg_2 gradient magnitude must be low (< 1.5 kPa/s mean)."""
        assert gradient_stats["seg_2"]["mean_magnitude"] < 1.5

    def test_seg4_gradient_moderate(self, gradient_stats):
        """seg_4 gradient magnitude must be moderate (< 2.0 kPa/s mean)."""
        assert gradient_stats["seg_4"]["mean_magnitude"] < 2.0

    def test_all_segments_have_stats(self, gradient_stats):
        """All 5 segments must have gradient statistics."""
        expected = ["seg_1", "seg_2", "seg_3", "seg_4", "seg_10"]
        for seg_id in expected:
            assert seg_id in gradient_stats, f"Missing gradient stats for {seg_id}"


class TestWindowComputation:
    """Window aggregation accuracy."""

    def test_window_counts_positive(self, summary_data):
        """All segments must have positive window counts."""
        for seg_id, count in summary_data["per_segment_windows"].items():
            assert count > 0, f"{seg_id} has zero windows"

    def test_seg1_seg3_equal_windows(self, summary_data):
        """seg_1 and seg_3 (same start_time, same sample count after interpolation) should have equal windows."""
        windows = summary_data["per_segment_windows"]
        assert windows["seg_1"] == windows["seg_3"], (
            f"seg_1 windows ({windows['seg_1']}) should equal "
            f"seg_3 windows ({windows['seg_3']})"
        )

    def test_event_peak_magnitude(self, events_data):
        """All events must have positive peak_magnitude."""
        for event in events_data["events"]:
            assert event["peak_magnitude"] > 0, (
                f"Event in {event['segment_id']} has non-positive peak_magnitude"
            )


class TestPreciseValues:
    """Precise numerical validation requiring correct computation."""

    def test_seg1_max_gradient_value(self, gradient_stats):
        """seg_1 max gradient must be close to 7.9 kPa/s (requires correct denominator)."""
        assert abs(gradient_stats["seg_1"]["max_magnitude"] - 7.9) < 0.5

    def test_seg3_max_gradient_value(self, gradient_stats):
        """seg_3 max gradient must be close to 9.5 kPa/s."""
        assert abs(gradient_stats["seg_3"]["max_magnitude"] - 9.5) < 0.5

    def test_seg1_event_duration(self, events_data):
        """seg_1 surge event must span at least 8 windows (sustained increase)."""
        events = events_data["events"]
        seg1_surges = [e for e in events if e["segment_id"] == "seg_1" and e["type"] == "surge"]
        assert len(seg1_surges) == 1
        assert seg1_surges[0]["duration_windows"] >= 8

    def test_seg3_two_leak_events(self, events_data):
        """seg_3 must have exactly 2 leak events (separated by flat region)."""
        events = events_data["events"]
        seg3_leaks = [e for e in events if e["segment_id"] == "seg_3" and e["type"] == "leak"]
        assert len(seg3_leaks) == 2, (
            f"seg_3 should have 2 leak events but got {len(seg3_leaks)}"
        )

    def test_seg3_second_leak_stronger(self, events_data):
        """seg_3 second leak event must have higher peak than first."""
        events = events_data["events"]
        seg3_leaks = sorted(
            [e for e in events if e["segment_id"] == "seg_3" and e["type"] == "leak"],
            key=lambda e: e["start_window"]
        )
        assert len(seg3_leaks) == 2
        assert seg3_leaks[1]["peak_magnitude"] > seg3_leaks[0]["peak_magnitude"]

    def test_seg10_event_starts_after_window_3(self, events_data):
        """seg_10 surge must start after window 3 (requires correct gradient ramp-up)."""
        events = events_data["events"]
        seg10_surges = [e for e in events if e["segment_id"] == "seg_10" and e["type"] == "surge"]
        assert len(seg10_surges) == 1
        assert seg10_surges[0]["start_window"] >= 3
