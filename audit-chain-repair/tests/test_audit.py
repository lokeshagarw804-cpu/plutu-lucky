"""Validation tests for audit chain verifier output."""
import json
import os

import pytest

OUTPUT_DIR = "/app/runtime/output"
REPORT_PATH = os.path.join(OUTPUT_DIR, "integrity_report.json")
TAMPER_PATH = os.path.join(OUTPUT_DIR, "tamper_report.json")


@pytest.fixture(scope="module")
def report_data():
    """Load integrity report output."""
    with open(REPORT_PATH, "r") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def tamper_data():
    """Load tamper report output."""
    with open(TAMPER_PATH, "r") as f:
        return json.load(f)


class TestOutputFiles:
    """Basic output file validation — ensures system runs to completion."""

    def test_report_file_exists(self):
        """Integrity report output must be generated."""
        assert os.path.isfile(REPORT_PATH), (
            "integrity_report.json not found at /app/runtime/output/"
        )

    def test_tamper_file_exists(self):
        """Tamper report output must be generated."""
        assert os.path.isfile(TAMPER_PATH), (
            "tamper_report.json not found at /app/runtime/output/"
        )

    def test_report_structure(self, report_data):
        """Report output has required top-level fields."""
        assert "stream_count" in report_data
        assert "streams_verified" in report_data
        assert "total_entries" in report_data
        assert "total_valid" in report_data
        assert "total_tampered" in report_data
        assert "aggregate_score" in report_data
        assert "per_stream_scores" in report_data
        assert "hmac_key_length" in report_data

    def test_tamper_structure(self, tamper_data):
        """Tamper report has required top-level fields."""
        assert "tampered_count" in tamper_data
        assert "tampered_entries" in tamper_data
        assert "verification_windows" in tamper_data
        assert "window_count" in tamper_data


class TestStreamLoading:
    """Validates that all configured audit streams are loaded."""

    def test_stream_count(self, report_data):
        """All 4 active streams must be verified.

        Four stream types are active: access, payment, security, admin.
        Check /app/runtime/config.ini active_streams list and ensure
        all types are being matched correctly during loading.
        """
        assert report_data["stream_count"] == 4, (
            f"Expected 4 streams, got {report_data['stream_count']}. "
            f"Check stream type matching in /app/runtime/loader.py "
            f"against config active_streams list."
        )

    def test_admin_stream_present(self, report_data):
        """Admin stream must appear in verified streams list."""
        assert "admin" in report_data["streams_verified"], (
            "admin stream missing from streams_verified. Check that "
            "the admin stream type matches active_streams config "
            "in /app/runtime/loader.py."
        )

    def test_total_entries(self, report_data):
        """Must process all 43 entries across 4 streams."""
        assert report_data["total_entries"] == 43, (
            f"Expected 43 total entries from 4 streams, got "
            f"{report_data['total_entries']}."
        )

    def test_all_streams_listed(self, report_data):
        """All 4 streams must be in the verified list."""
        verified = report_data["streams_verified"]
        assert "access" in verified
        assert "admin" in verified
        assert "payment" in verified
        assert "security" in verified


class TestHMACConfiguration:
    """Validates HMAC key length from correct config section."""

    def test_hmac_key_length(self, report_data):
        """HMAC key length must be 32 from verification.hmac section.

        The hasher should read from the [verification.hmac] config
        section which has the production key length, not the [hmac]
        section. Check /app/runtime/hasher.py config section name.
        """
        assert report_data["hmac_key_length"] == 32, (
            f"Expected hmac_key_length=32 from [verification.hmac], "
            f"got {report_data['hmac_key_length']}. Check config "
            f"section in /app/runtime/hasher.py — should read from "
            f"[verification.hmac] not [hmac]."
        )


class TestIntegrityScoring:
    """Validates per-stream scoring computes independently."""

    def test_per_stream_scores_differ(self, report_data):
        """Per-stream scores must reflect each stream's own ratio.

        Each stream has different valid/total counts so their scores
        should differ. Check /app/runtime/integrity_scorer.py for
        using aggregate values where per-stream values are needed.
        """
        scores = report_data["per_stream_scores"]
        unique_scores = set(scores.values())
        assert len(unique_scores) > 1, (
            f"All per_stream_scores are identical ({unique_scores}). "
            f"Each stream should have its own independent score. "
            f"Check /app/runtime/integrity_scorer.py — should use "
            f"per-stream valid/total, not running aggregates."
        )

    def test_access_stream_score(self, report_data):
        """Access stream score must be approximately 0.0667 (1/15)."""
        score = report_data["per_stream_scores"].get("access", 0)
        assert 0.05 < score < 0.08, (
            f"Access stream score should be ~0.0667 (1/15 valid), "
            f"got {score}."
        )

    def test_admin_stream_score(self, report_data):
        """Admin stream score must be 0.125 (1/8)."""
        score = report_data["per_stream_scores"].get("admin", 0)
        assert 0.10 < score < 0.15, (
            f"Admin stream score should be 0.125 (1/8 valid), "
            f"got {score}."
        )

    def test_aggregate_score(self, report_data):
        """Aggregate score must be approximately 0.093 (4/43)."""
        assert 0.08 < report_data["aggregate_score"] < 0.11, (
            f"Expected aggregate ~0.093, got {report_data['aggregate_score']}."
        )


class TestVerificationWindows:
    """Validates window-based verification with correct boundaries."""

    def test_window_count(self, tamper_data):
        """Must produce exactly 4 verification windows.

        With window_size=50 and 4 streams (15+8+12+8 entries), each
        stream fits in one window: 4 windows total.
        Check /app/runtime/verifier.py window boundary calculation
        for off-by-one errors in the step size.
        """
        assert tamper_data["window_count"] == 4, (
            f"Expected 4 windows (one per stream), got "
            f"{tamper_data['window_count']}. Check window step "
            f"calculation in /app/runtime/verifier.py — step should "
            f"be window_size, not window_size+1."
        )


class TestTamperDetection:
    """Validates tampered entry detection and deterministic ordering."""

    def test_tampered_count(self, tamper_data):
        """Must detect exactly 39 tampered entries."""
        assert tamper_data["tampered_count"] == 39, (
            f"Expected 39 tampered entries, got "
            f"{tamper_data['tampered_count']}."
        )

    def test_tiebreaker_at_timestamp_300(self, tamper_data):
        """Entries at timestamp 1700000300 must be ordered by stream_id.

        At timestamp 1700000300, access(seq=5) and payment(seq=4) are
        both tampered. Despite payment having lower seq, access must
        come first because stream_id breaks ties alphabetically.
        Check sort key in /app/runtime/tamper_detector.py — seq alone
        is not sufficient since seq is local to each stream.
        """
        entries = tamper_data["tampered_entries"]
        ts300 = [e for e in entries if e["timestamp"] == 1700000300]
        assert len(ts300) >= 2, (
            f"Expected at least 2 tampered entries at ts=1700000300, "
            f"got {len(ts300)}."
        )
        # Find access and payment entries
        access_entry = next((e for e in ts300 if e["stream_id"] == "access"), None)
        payment_entry = next((e for e in ts300 if e["stream_id"] == "payment"), None)
        assert access_entry is not None and payment_entry is not None, (
            "Both access and payment entries must be detected at ts=1700000300."
        )
        idx_access = entries.index(access_entry)
        idx_payment = entries.index(payment_entry)
        assert idx_access < idx_payment, (
            f"access entry at position {idx_access} must come before "
            f"payment entry at position {idx_payment}. Ties at same "
            f"timestamp must be broken by stream_id alphabetically. "
            f"Check sort key in /app/runtime/tamper_detector.py."
        )

    def test_tampered_entries_sorted(self, tamper_data):
        """All tampered entries must be sorted by timestamp ascending."""
        entries = tamper_data["tampered_entries"]
        for i in range(1, len(entries)):
            assert entries[i]["timestamp"] >= entries[i - 1]["timestamp"], (
                f"Entry at position {i} has timestamp "
                f"{entries[i]['timestamp']} < previous "
                f"{entries[i-1]['timestamp']}."
            )
