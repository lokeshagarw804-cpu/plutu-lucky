"""
Resolution manifest writer.

Generates the final resolution manifest with installation order,
dependency graph, and integrity checksum. The checksum is computed
from the ordered list of resolved packages using only the fields
specified in config (package, version, scope, depth).
"""

import json
import os
import hashlib
import configparser


class ManifestWriter:
    """Writes resolution output files."""

    def __init__(self, config_path="/app/runtime/config.ini"):
        config = configparser.ConfigParser()
        config.read(config_path)

        self._manifest_path = config.get("manifest", "output_path")
        self._graph_path = config.get("manifest", "graph_path")
        self._summary_path = config.get("manifest", "summary_path")
        self._include_checksum = config.getboolean(
            "manifest", "include_checksum"
        )
        self._checksum_fields = [
            f.strip() for f in
            config.get("manifest", "checksum_fields").split(",")
        ]

    def write_outputs(self, resolved_packages, install_order, graph):
        """Write all output files."""
        manifest = self._build_manifest(install_order)
        summary = self._build_summary(resolved_packages, graph)

        self._write_json(self._manifest_path, manifest)
        self._write_json(self._graph_path, graph)
        self._write_json(self._summary_path, summary)

        return manifest, graph, summary

    def _build_manifest(self, install_order):
        """Build the resolution manifest with checksum."""
        entries = []
        for pkg in install_order:
            entries.append({
                "package": pkg["package"],
                "version": pkg["version"],
                "scope": pkg["scope"],
                "depth": pkg["depth"],
                "install_position": len(entries),
            })

        checksum = None
        if self._include_checksum:
            checksum = self._compute_checksum(entries)

        return {
            "total_packages": len(entries),
            "entries": entries,
            "integrity_checksum": checksum,
        }

    def _compute_checksum(self, entries):
        """Compute SHA256 checksum of resolved package list.

        Uses only configured fields (package, version, scope, depth)
        to ensure the checksum is deterministic and independent of
        non-resolution metadata.
        """
        hash_input = []
        for entry in entries:
            record = {
                k: entry[k] for k in self._checksum_fields
                if k in entry
            }
            record["install_position"] = entry["install_position"]
            hash_input.append(json.dumps(record, sort_keys=True))

        combined = "|".join(hash_input)
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    def _build_summary(self, resolved_packages, graph):
        """Build resolution summary."""
        scopes = {}
        depths = {}
        for pkg in resolved_packages:
            s = pkg["scope"]
            scopes[s] = scopes.get(s, 0) + 1
            d = pkg["depth"]
            depths[d] = depths.get(d, 0) + 1

        return {
            "total_resolved": len(resolved_packages),
            "by_scope": scopes,
            "by_depth": depths,
            "max_depth_reached": max(
                (p["depth"] for p in resolved_packages), default=0
            ),
            "graph_nodes": graph["node_count"],
        }

    def _write_json(self, path, data):
        """Write data as JSON."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
