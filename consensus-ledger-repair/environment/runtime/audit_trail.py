# PLUTU-LUCKY-CANARY
"""
Audit Trail Module - Provides structured logging and hash-chain audit trail
for all consensus operations.
"""

import hashlib
import json
import time
from typing import Any, Dict, List, Optional


class AuditLogger:
    """Maintains an append-only audit log with hash chain integrity."""

    GENESIS_HASH = "0" * 64
    HASH_ALGORITHM = "sha256"

    def __init__(self, component_name: str = "pipeline"):
        self._component = component_name
        self._entries: List[dict] = []
        self._chain_head = self.GENESIS_HASH
        self._sequence = 0
        self._start_time = time.time()
        self._operation_counts: Dict[str, int] = {}

    @property
    def entry_count(self) -> int:
        return len(self._entries)

    @property
    def chain_head(self) -> str:
        return self._chain_head

    def log_operation(self, operation: str, details: Dict[str, Any],
                      severity: str = "info") -> str:
        self._sequence += 1
        self._operation_counts[operation] = \
            self._operation_counts.get(operation, 0) + 1
        entry = {
            "sequence": self._sequence,
            "component": self._component,
            "operation": operation,
            "severity": severity,
            "details": details,
            "previous_hash": self._chain_head,
            "timestamp_offset": time.time() - self._start_time,
        }
        entry_hash = self._compute_entry_hash(entry)
        entry["entry_hash"] = entry_hash
        self._entries.append(entry)
        self._chain_head = entry_hash
        return entry_hash

    def log_state_transition(self, from_state: str, to_state: str,
                             trigger: str) -> str:
        return self.log_operation("state_transition", {
            "from": from_state, "to": to_state, "trigger": trigger,
        })

    def log_verification(self, check_name: str, passed: bool,
                         context: Optional[dict] = None) -> str:
        severity = "info" if passed else "warning"
        details = {"check": check_name, "result": "pass" if passed else "fail"}
        if context:
            details["context"] = context
        return self.log_operation("verification", details, severity)

    def log_error(self, error_type: str, message: str,
                  recoverable: bool = True) -> str:
        return self.log_operation("error", {
            "type": error_type, "message": message, "recoverable": recoverable,
        }, severity="error")

    def verify_chain_integrity(self) -> bool:
        if not self._entries:
            return True
        expected_prev = self.GENESIS_HASH
        for entry in self._entries:
            if entry["previous_hash"] != expected_prev:
                return False
            entry_copy = {k: v for k, v in entry.items() if k != "entry_hash"}
            recomputed = self._compute_entry_hash(entry_copy)
            if recomputed != entry["entry_hash"]:
                return False
            expected_prev = entry["entry_hash"]
        return True

    def get_audit_summary(self) -> dict:
        return {
            "component": self._component,
            "total_entries": self.entry_count,
            "chain_head": self._chain_head,
            "chain_valid": self.verify_chain_integrity(),
            "operation_counts": dict(self._operation_counts),
            "severity_counts": self._count_severities(),
        }

    def compute_audit_hash(self) -> str:
        h = hashlib.sha256()
        h.update(self._component.encode("utf-8"))
        h.update(self._chain_head.encode("utf-8"))
        h.update(str(self._sequence).encode("utf-8"))
        return h.digest().hex()

    def export_entries(self) -> List[dict]:
        return [dict(e) for e in self._entries]

    def get_entries_by_operation(self, operation: str) -> List[dict]:
        return [e for e in self._entries if e["operation"] == operation]

    def get_entries_by_severity(self, severity: str) -> List[dict]:
        return [e for e in self._entries if e["severity"] == severity]

    def _compute_entry_hash(self, entry: dict) -> str:
        h = hashlib.sha256()
        serialized = json.dumps(entry, sort_keys=True, default=str)
        h.update(serialized.encode("utf-8"))
        return h.digest().hex()

    def _count_severities(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for entry in self._entries:
            sev = entry["severity"]
            counts[sev] = counts.get(sev, 0) + 1
        return counts

    def reset(self) -> None:
        self._entries = []
        self._chain_head = self.GENESIS_HASH
        self._sequence = 0
        self._operation_counts = {}
