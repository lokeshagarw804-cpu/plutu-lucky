"""
Tests for the dependency graph resolution system.

Validates resolution completeness, constraint satisfaction,
installation ordering, and manifest integrity.
"""
import json
import os
import pytest


MANIFEST_PATH = "/app/runtime/output/resolution_manifest.json"
GRAPH_PATH = "/app/runtime/output/dependency_graph.json"
SUMMARY_PATH = "/app/runtime/output/resolve_summary.json"


def load_manifest():
    with open(MANIFEST_PATH, "r") as f:
        return json.load(f)


def load_graph():
    with open(GRAPH_PATH, "r") as f:
        return json.load(f)


def load_summary():
    with open(SUMMARY_PATH, "r") as f:
        return json.load(f)


class TestOutputStructure:
    """Basic output file presence and structure."""

    def test_manifest_exists(self):
        """Resolution manifest must be produced."""
        assert os.path.isfile(MANIFEST_PATH)

    def test_graph_exists(self):
        """Dependency graph must be produced."""
        assert os.path.isfile(GRAPH_PATH)

    def test_summary_exists(self):
        """Resolution summary must be produced."""
        assert os.path.isfile(SUMMARY_PATH)

    def test_manifest_structure(self):
        """Manifest must have required top-level keys."""
        m = load_manifest()
        for key in ["total_packages", "entries", "integrity_checksum"]:
            assert key in m, f"Missing key: {key}"


class TestResolutionCompleteness:
    """Verify correct package count and scope filtering."""

    def test_total_package_count(self):
        """Resolution must produce exactly 15 packages."""
        m = load_manifest()
        assert m["total_packages"] == 15, (
            f"Expected 15 resolved packages, got {m['total_packages']}"
        )

    def test_no_peer_packages(self):
        """No peer-scoped packages should appear in resolution."""
        m = load_manifest()
        for entry in m["entries"]:
            assert entry["scope"] != "peer", (
                f"Package {entry['package']} has scope=peer"
            )

    def test_no_dev_packages(self):
        """No dev-scoped packages should appear in resolution."""
        m = load_manifest()
        for entry in m["entries"]:
            assert entry["scope"] != "dev", (
                f"Package {entry['package']} has scope=dev"
            )

    def test_max_depth_within_limit(self):
        """Maximum depth must not exceed 5 (strict limit)."""
        s = load_summary()
        assert s["max_depth_reached"] <= 5, (
            f"Max depth {s['max_depth_reached']} exceeds strict limit"
        )


class TestVersionSelection:
    """Verify constraint satisfaction produces correct versions."""

    def test_logger_version(self):
        """Logger must resolve to 2.4.0 (highest satisfying >=2.0.0)."""
        m = load_manifest()
        logger_entries = [
            e for e in m["entries"] if e["package"] == "logger"
        ]
        assert len(logger_entries) == 1, "Logger not found in manifest"
        assert logger_entries[0]["version"] == "2.4.0", (
            f"Logger resolved to {logger_entries[0]['version']}, "
            f"expected 2.4.0"
        )

    def test_crypto_base_version(self):
        """Crypto-base must resolve to 2.9.0 (highest satisfying >=2.7.0)."""
        m = load_manifest()
        cb_entries = [
            e for e in m["entries"] if e["package"] == "crypto-base"
        ]
        assert len(cb_entries) == 1, "crypto-base not found in manifest"
        assert cb_entries[0]["version"] == "2.9.0", (
            f"crypto-base resolved to {cb_entries[0]['version']}, "
            f"expected 2.9.0"
        )

    def test_config_loader_present(self):
        """Config-loader must be resolved as a framework dependency."""
        m = load_manifest()
        cl = [e for e in m["entries"] if e["package"] == "config-loader"]
        assert len(cl) == 1, "config-loader missing from resolution"


class TestInstallOrdering:
    """Verify leaves-first installation order."""

    def test_first_installed_is_deepest(self):
        """First entries must be the deepest (leaf) packages."""
        m = load_manifest()
        entries = m["entries"]
        assert entries[0]["depth"] >= entries[-1]["depth"], (
            f"First entry depth={entries[0]['depth']} should be >= "
            f"last entry depth={entries[-1]['depth']} (leaves first)"
        )

    def test_roots_installed_last(self):
        """Root packages (depth=0) must be at the end."""
        m = load_manifest()
        entries = m["entries"]
        last_two = entries[-2:]
        for entry in last_two:
            assert entry["depth"] == 0, (
                f"Expected depth=0 at end, got {entry['package']} "
                f"at depth={entry['depth']}"
            )

    def test_monotonic_depth_ordering(self):
        """Depths must be non-increasing across the install sequence."""
        m = load_manifest()
        entries = m["entries"]
        for i in range(len(entries) - 1):
            assert entries[i]["depth"] >= entries[i + 1]["depth"], (
                f"Position {i}: depth {entries[i]['depth']} followed by "
                f"{entries[i+1]['depth']} violates leaves-first order"
            )


class TestManifestIntegrity:
    """Verify checksum correctness."""

    def test_checksum_present(self):
        """Integrity checksum must be computed."""
        m = load_manifest()
        assert m["integrity_checksum"] is not None
        assert len(m["integrity_checksum"]) == 16

    def test_checksum_value(self):
        """Checksum must match expected value for correct resolution."""
        m = load_manifest()
        assert m["integrity_checksum"] == "0080b0f4e4453e15", (
            f"Checksum mismatch: got {m['integrity_checksum']}"
        )
