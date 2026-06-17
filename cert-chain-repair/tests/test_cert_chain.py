"""
Tests for the certificate chain verification system.

Validates the correctness of trust validation, chain building,
trust score computation, and output report generation.
"""
import json
import os
import pytest


REPORT_PATH = "/app/runtime/output/validation_report.json"
SUMMARY_PATH = "/app/runtime/output/chain_summary.json"


def load_report():
    """Load the validation report output file."""
    with open(REPORT_PATH, "r") as f:
        return json.load(f)


def load_summary():
    """Load the chain summary output file."""
    with open(SUMMARY_PATH, "r") as f:
        return json.load(f)


# --- EASY TESTS (pass even with buggy code) ---

class TestOutputFileStructure:
    """Tests that verify basic output file existence and structure."""

    def test_validation_report_exists(self):
        """The validation report file must exist at the configured path."""
        assert os.path.isfile(REPORT_PATH), (
            f"Expected validation report at {REPORT_PATH}"
        )

    def test_chain_summary_exists(self):
        """The chain summary file must exist at the configured path."""
        assert os.path.isfile(SUMMARY_PATH), (
            f"Expected chain summary at {SUMMARY_PATH}"
        )

    def test_report_has_required_fields(self):
        """The validation report must contain all required top-level fields."""
        report = load_report()
        required_fields = ["total_certificates", "valid_count", "invalid_count", "entries"]
        for field in required_fields:
            assert field in report, (
                f"Missing required field '{field}' in validation report"
            )

    def test_summary_has_required_fields(self):
        """The chain summary must contain all required top-level fields."""
        summary = load_summary()
        required_fields = ["total_chains", "avg_chain_length", "depth_exceeded_count", "entries"]
        for field in required_fields:
            assert field in summary, (
                f"Missing required field '{field}' in chain summary"
            )


# --- MEDIUM TESTS (require 1-2 bug fixes each) ---

class TestTrustValidation:
    """Tests for trust store validation correctness."""

    def test_total_certificate_count(self):
        """All 43 certificates from 3 authority files must be processed."""
        report = load_report()
        assert report["total_certificates"] == 43, (
            f"Expected 43 total certificates, got {report['total_certificates']}. "
            "Check that all authority data files are being loaded."
        )

    def test_delta_ca_certificates_trusted(self):
        """Certificates from delta_ca must be recognized as trusted.

        The delta_ca authority is configured in the trusted_roots list.
        If delta_ca certs show as untrusted, check how the trust store
        parses the trusted_roots config value in /app/runtime/validator.py.
        """
        report = load_report()
        entries = report["entries"]
        delta_entries = [e for e in entries if e["issuer_id"] == "delta_ca"]
        assert len(delta_entries) > 0, (
            "No delta_ca entries found in valid results. "
            "Check trusted_roots parsing in /app/runtime/validator.py - "
            "the config value may have whitespace issues."
        )
        for entry in delta_entries:
            assert entry["trusted_issuer"] is True, (
                f"Certificate {entry['cert_id']} from delta_ca should have "
                f"trusted_issuer=True. Check config parsing in /app/runtime/validator.py."
            )

    def test_valid_count_includes_all_trusted(self):
        """All certificates from trusted CAs with valid keys and algos must be valid.

        Expected: 43 valid certificates (all from alpha_ca, beta_ca, delta_ca
        with 2048+ bit keys and sha256/sha384/sha512 algorithms).
        """
        report = load_report()
        assert report["valid_count"] == 43, (
            f"Expected 43 valid certificates, got {report['valid_count']}. "
            "Check that all trusted authorities are recognized and config "
            "parsing handles whitespace correctly."
        )


# --- MEDIUM-HARD TESTS (require 2-3 bug fixes) ---

class TestChainDepth:
    """Tests for chain depth enforcement using strict validation mode."""

    def test_depth_exceeded_count(self):
        """Chains exceeding the strict max_chain_depth=4 must be flagged.

        The validation.strict section in /app/runtime/config.ini sets
        max_chain_depth=4. Check that /app/runtime/chain_builder.py reads
        from the correct config section.
        """
        summary = load_summary()
        exceeded = summary["depth_exceeded_count"]
        assert exceeded > 0, (
            "Expected some chains to exceed strict depth limit of 4, but "
            f"got depth_exceeded_count={exceeded}. Check which config section "
            "/app/runtime/chain_builder.py reads max_chain_depth from — "
            "it should use validation.strict (max_chain_depth=4), not validation."
        )

    def test_chain_length_limited(self):
        """No chain in the summary should have chain_length > 5 (4 hops + root).

        With strict max_chain_depth=4, chains are traversed at most 4 hops.
        """
        summary = load_summary()
        for entry in summary["entries"]:
            assert entry["chain_length"] <= 5, (
                f"Certificate {entry['cert_id']} has chain_length={entry['chain_length']} "
                f"which exceeds strict limit. Check max_chain_depth config section "
                f"in /app/runtime/chain_builder.py."
            )


# --- HARD TESTS (require 3-4 bug fixes together) ---

class TestTrustScores:
    """Tests for trust score computation correctness."""

    def test_root_certificate_score(self):
        """A valid root certificate (chain_length=1) should have trust_score=1.0.

        The trust score at hop 0 is (1 - decay)^0 = 1.0 for a fully valid cert.
        If scores are inflated, check the accumulation logic in
        /app/runtime/chain_builder.py _compute_chain_score method.
        """
        summary = load_summary()
        root_entries = [e for e in summary["entries"] if e["chain_length"] == 1]
        assert len(root_entries) > 0, "Expected at least one root certificate"
        for entry in root_entries:
            assert entry["trust_score"] == 1.0, (
                f"Root cert {entry['cert_id']} has trust_score={entry['trust_score']} "
                f"but expected 1.0. Check score computation in "
                f"/app/runtime/chain_builder.py — scores should not accumulate "
                f"across repeated evaluations."
            )

    def test_chain_score_decay(self):
        """A chain of length 2 with all valid certs should score 1.0 + 0.9 = 1.9.

        With decay=0.10 (strict), hop 0 contributes 1.0, hop 1 contributes 0.9.
        Total = 1.9. If the score is wrong, check both the decay factor source
        (validation.strict section) and the accumulation logic.
        """
        summary = load_summary()
        len2_entries = [e for e in summary["entries"]
                        if e["chain_length"] == 2]
        assert len(len2_entries) > 0, "Expected chains of length 2"
        for entry in len2_entries:
            expected_score = round(1.0 + 0.9, 4)
            assert entry["trust_score"] == expected_score, (
                f"Certificate {entry['cert_id']} (chain_length=2) has "
                f"trust_score={entry['trust_score']} but expected {expected_score}. "
                f"Check decay factor (should be 0.10 from validation.strict) and "
                f"score computation in /app/runtime/chain_builder.py."
            )


class TestDeterministicOrdering:
    """Tests for deterministic ordering in chain summary output."""

    def test_summary_sorted_by_expiry_issuer_serial(self):
        """Chain summary entries must be sorted by (expiry_date, issuer_id, serial).

        Certificates that expire on the same date must have a stable order
        determined by issuer_id then serial. Check the sort key in
        /app/runtime/reporter.py — serial alone is insufficient because
        serial numbers are local to each issuing authority.
        """
        summary = load_summary()
        entries = summary["entries"]
        for i in range(len(entries) - 1):
            curr = entries[i]
            nxt = entries[i + 1]
            curr_key = (curr["expiry_date"], curr["issuer_id"], curr["serial"])
            nxt_key = (nxt["expiry_date"], nxt["issuer_id"], nxt["serial"])
            assert curr_key <= nxt_key, (
                f"Summary entries not sorted correctly at position {i}: "
                f"{curr['cert_id']} ({curr_key}) should come before "
                f"{nxt['cert_id']} ({nxt_key}). "
                f"Check sort key in /app/runtime/reporter.py — must sort by "
                f"(expiry_date, issuer_id, serial) not just (expiry_date, serial)."
            )
