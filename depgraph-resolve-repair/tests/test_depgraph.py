"""
Tests for the dependency graph resolution system.

Validates resolution completeness, constraint satisfaction,
installation ordering, and manifest integrity.
"""
import json
import os
import hashlib
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
            f"Expected 15 resolved packages, got {m['total_packages']}. "
            "Check scope filtering and version constraint logic."
        )

    def test_no_peer_packages(self):
        """No peer-scoped packages should appear in resolution."""
        m = load_manifest()
        for entry in m["entries"]:
            assert entry["scope"] != "peer", (
                f"Package {entry['package']} has scope=peer but peer "
                "should be excluded. Check scope filtering."
            )

    def test_no_dev_packages(self):
        """No dev-scoped packages should appear in resolution."""
        m = load_manifest()
        for entry in m["entries"]:
            assert entry["scope"] != "dev", (
                f"Package {entry['package']} has scope=dev"
            )


class TestVersionSelection:
    """Verify constraint satisfaction produces correct versions."""

    def test_logger_version(self):
        """Logger must resolve to highest version satisfying >=2.0.0.

        With highest_compatible strategy and correct constraint matching,
        logger 2.4.0 satisfies >=2.0.0 and is the highest available.
        If logger is missing or wrong version, the version comparator
        in the resolver may be inverting the >= check.
        """
        m = load_manifest()
        logger_entries = [
            e for e in m["entries"] if e["package"] == "logger"
        ]
        assert len(logger_entries) == 1, (
            "Logger not resolved. The constraint >=2.0.0 should match "
            "versions 2.1.0 and 2.4.0. Check _satisfies_constraint in "
            "/app/runtime/resolver.py — the >= operator implementation."
        )
        assert logger_entries[0]["version"] == "2.4.0", (
            f"Logger resolved to {logger_entries[0]['version']}, expected "
            "2.4.0 (highest compatible with >=2.0.0)"
        )

    def test_crypto_base_version(self):
        """Crypto-base must resolve to 2.9.0 (highest satisfying >=2.7.0)."""
        m = load_manifest()
        cb_entries = [
            e for e in m["entries"] if e["package"] == "crypto-base"
        ]
        assert len(cb_entries) == 1, (
            "crypto-base not resolved"
        )
        assert cb_entries[0]["version"] == "2.9.0", (
            f"crypto-base resolved to {cb_entries[0]['version']}, "
            "expected 2.9.0"
        )

    def test_config_loader_present(self):
        """Config-loader must be resolved as a framework dependency."""
        m = load_manifest()
        cl = [e for e in m["entries"] if e["package"] == "config-loader"]
        assert len(cl) == 1, (
            "config-loader missing from resolution. It is a dependency "
            "of framework which requires config-loader >=1.5.0."
        )

    def test_max_depth_within_strict_limit(self):
        """Maximum depth must not exceed strict limit of 5."""
        s = load_summary()
        assert s["max_depth_reached"] <= 5, (
            f"Max depth {s['max_depth_reached']} exceeds the strict "
            "resolution limit. Check which config section provides "
            "the max_depth parameter."
        )


class TestInstallOrdering:
    """Verify leaves-first installation order."""

    def test_first_installed_is_deepest(self):
        """First entries in install order must be the deepest (leaf) packages."""
        m = load_manifest()
        entries = m["entries"]
        assert entries[0]["depth"] >= entries[-1]["depth"], (
            f"First entry has depth={entries[0]['depth']}, last has "
            f"depth={entries[-1]['depth']}. Leaves (highest depth) "
            "should be installed first."
        )

    def test_roots_installed_last(self):
        """Root packages (depth=0) must appear at the end of install order."""
        m = load_manifest()
        entries = m["entries"]
        last_two = entries[-2:]
        for entry in last_two:
            assert entry["depth"] == 0, (
                f"Expected depth=0 at end of install order, got "
                f"{entry['package']} at depth={entry['depth']}"
            )

    def test_non_increasing_depth(self):
        """Depths must be non-increasing across the install sequence."""
        m = load_manifest()
        entries = m["entries"]
        for i in range(len(entries) - 1):
            assert entries[i]["depth"] >= entries[i + 1]["depth"], (
                f"Position {i}: depth {entries[i]['depth']} followed by "
                f"{entries[i+1]['depth']} violates leaves-first order"
            )


class TestManifestIntegrity:
    """Verify checksum correctness using independent computation."""

    def test_checksum_present(self):
        """Integrity checksum must be non-null and 16 hex characters."""
        m = load_manifest()
        assert m["integrity_checksum"] is not None
        assert len(m["integrity_checksum"]) == 16

    def test_checksum_matches_entries(self):
        """Checksum must be reproducible from manifest entries.

        The checksum is SHA256 of the entries using only the configured
        fields (package, version, scope, depth) joined by pipe separators.
        It must NOT include install_position or other metadata.
        """
        m = load_manifest()
        entries = m["entries"]
        checksum_fields = ["package", "version", "scope", "depth"]
        hash_input = []
        for entry in entries:
            record = {k: entry[k] for k in checksum_fields if k in entry}
            hash_input.append(json.dumps(record, sort_keys=True))
        expected = hashlib.sha256("|".join(hash_input).encode()).hexdigest()[:16]
        assert m["integrity_checksum"] == expected, (
            f"Checksum {m['integrity_checksum']} does not match "
            f"recomputed value {expected}. The checksum computation "
            "may include fields beyond the configured set."
        )
