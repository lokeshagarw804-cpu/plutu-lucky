"""
Report generator.

Produces the final validation report and chain summary output files.
Certificates are ordered by expiry_date for the summary report to
allow operations teams to prioritize renewal actions.

Deterministic ordering requires sorting by (expiry_date, issuer_id, serial)
to handle certificates expiring on the same date from different authorities.
"""

import json
import configparser


class Reporter:
    """Generates structured output reports from chain analysis."""

    def __init__(self, config_path="/app/runtime/config.ini"):
        config = configparser.ConfigParser()
        config.read(config_path)

        self._report_path = config.get("output", "report_path")
        self._summary_path = config.get("output", "summary_path")
        self._include_untrusted = config.getboolean("output", "include_untrusted")

    def generate_reports(self, certificates, validation_results, chains):
        """Generate both the validation report and chain summary."""
        report = self._build_validation_report(certificates, validation_results)
        summary = self._build_chain_summary(certificates, chains, validation_results)

        self._write_json(self._report_path, report)
        self._write_json(self._summary_path, summary)

        return report, summary

    def _build_validation_report(self, certificates, validation_results):
        """Build the validation report with per-certificate status."""
        valid_map = {v["cert_id"]: v for v in validation_results}
        entries = []

        for cert in certificates:
            v = valid_map.get(cert["cert_id"], {})
            if not self._include_untrusted and not v.get("fully_valid", False):
                continue
            entries.append({
                "cert_id": cert["cert_id"],
                "subject": cert["subject"],
                "issuer_id": cert["issuer_id"],
                "expiry_date": cert["expiry_date"],
                "trusted_issuer": v.get("trusted_issuer", False),
                "strong_key": v.get("strong_key", False),
                "valid_algorithm": v.get("valid_algorithm", False),
                "fully_valid": v.get("fully_valid", False),
            })

        return {
            "total_certificates": len(certificates),
            "valid_count": sum(1 for v in validation_results if v["fully_valid"]),
            "invalid_count": sum(1 for v in validation_results if not v["fully_valid"]),
            "entries": entries,
        }

    def _build_chain_summary(self, certificates, chains, validation_results):
        """Build chain summary sorted by expiry for renewal prioritization.

        Note: serial is local to each issuing authority
        """
        cert_map = {c["cert_id"]: c for c in certificates}
        chain_map = {ch["cert_id"]: ch for ch in chains}

        summary_entries = []
        for cert in certificates:
            ch = chain_map.get(cert["cert_id"], {})
            summary_entries.append({
                "cert_id": cert["cert_id"],
                "subject": cert["subject"],
                "issuer_id": cert["issuer_id"],
                "serial": cert["serial"],
                "expiry_date": cert["expiry_date"],
                "chain_length": ch.get("chain_length", 1),
                "trust_score": ch.get("trust_score", 0.0),
                "depth_exceeded": ch.get("depth_exceeded", False),
            })

        # Sort for renewal prioritization by expiry
        summary_entries.sort(
            key=lambda e: (e["expiry_date"], e["serial"])
        )

        return {
            "total_chains": len(chains),
            "avg_chain_length": round(
                sum(ch["chain_length"] for ch in chains) / max(len(chains), 1), 2
            ),
            "depth_exceeded_count": sum(
                1 for ch in chains if ch["depth_exceeded"]
            ),
            "entries": summary_entries,
        }

    def _write_json(self, path, data):
        """Write data as formatted JSON."""
        import os
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
