"""
Propagation log parser for the lattice momentum simulation framework.

Handles deserialization of raw event records from the propagation log format,
including validation, normalization, and event registry bookkeeping for
downstream consumption by the momentum engine.
"""

import re
from collections import defaultdict


# Recognized event type identifiers in the propagation protocol
_VALID_EVENT_TYPES = frozenset({"STREAM", "DRIFT", "COLLISION"})

# Compile patterns once for efficiency
_LINE_PATTERN = re.compile(
    r"^\s*(\d+)\s*->\s*([\w]+)\s*->\s*(\w+)\s*->\s*(.+)\s*$"
)
_KV_SEPARATOR = re.compile(r"\s*;\s*")
_STATE_ENTRY = re.compile(r"([\w]+):(\d+)")


class EventRegistry:
    """Accumulates parse-time statistics for diagnostic reporting.

    Tracks per-cell event counts, sequence gaps, and payload distributions
    to support calibration verification in downstream modules.
    """

    def __init__(self):
        self._cell_counts = defaultdict(int)
        self._type_counts = defaultdict(int)
        self._sequence_ids = []
        self._collision_pairs = []
        self._max_delta_observed = 0
        self._parse_warnings = []

    def register_event(self, seq_id, cell_id, event_type, payload):
        """Record an event occurrence in the registry."""
        self._cell_counts[cell_id] += 1
        self._type_counts[event_type] += 1
        self._sequence_ids.append(seq_id)

        if event_type == "COLLISION" and "neighbor" in payload:
            self._collision_pairs.append((cell_id, payload["neighbor"]))

        if "delta" in payload:
            self._max_delta_observed = max(
                self._max_delta_observed, payload["delta"]
            )

    def get_cell_counts(self):
        """Return dict of cell_id -> total event count."""
        return dict(self._cell_counts)

    def get_type_distribution(self):
        """Return dict of event_type -> count."""
        return dict(self._type_counts)

    def check_sequence_continuity(self):
        """Verify no gaps exist in the sequence numbering."""
        if not self._sequence_ids:
            return True
        sorted_ids = sorted(self._sequence_ids)
        expected = list(range(sorted_ids[0], sorted_ids[-1] + 1))
        return sorted_ids == expected

    def get_collision_graph(self):
        """Return list of (source, target) collision interactions."""
        return list(self._collision_pairs)

    @property
    def total_events(self):
        return len(self._sequence_ids)

    @property
    def max_delta(self):
        return self._max_delta_observed


def _validate_line_structure(line, line_num):
    """Check raw line conforms to expected arrow-separated format."""
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    match = _LINE_PATTERN.match(stripped)
    if match is None:
        return None
    return match.groups()


def _normalize_cell_identifier(raw_id):
    """Normalize cell identifier to canonical form."""
    return raw_id.strip().lower()


def _parse_stream_payload(raw_payload):
    """Extract delta value from STREAM event payload."""
    parts = raw_payload.strip().split("=")
    if len(parts) != 2 or parts[0].strip() != "delta":
        raise ValueError(f"Malformed STREAM payload: {raw_payload}")
    return {"delta": int(parts[1].strip())}


def _parse_drift_payload(raw_payload):
    """Extract delta value from DRIFT event payload."""
    parts = raw_payload.strip().split("=")
    if len(parts) != 2 or parts[0].strip() != "delta":
        raise ValueError(f"Malformed DRIFT payload: {raw_payload}")
    return {"delta": int(parts[1].strip())}


def _parse_collision_payload(raw_payload):
    """Extract neighbor and state vector from COLLISION event payload."""
    segments = _KV_SEPARATOR.split(raw_payload.strip())
    result = {}
    for segment in segments:
        if segment.startswith("neighbor="):
            result["neighbor"] = _normalize_cell_identifier(
                segment.split("=", 1)[1]
            )
        elif segment.startswith("state="):
            state_raw = segment.split("=", 1)[1]
            state_dict = {}
            for entry in _STATE_ENTRY.finditer(state_raw):
                state_dict[entry.group(1)] = int(entry.group(2))
            result["state"] = state_dict
    if "neighbor" not in result:
        raise ValueError(f"COLLISION payload missing neighbor: {raw_payload}")
    if "state" not in result:
        raise ValueError(f"COLLISION payload missing state: {raw_payload}")
    return result


_PAYLOAD_PARSERS = {
    "STREAM": _parse_stream_payload,
    "DRIFT": _parse_drift_payload,
    "COLLISION": _parse_collision_payload,
}


def _build_event_record(seq_id, cell_id, event_type, raw_payload):
    """Construct a fully-parsed event record from raw components."""
    if event_type not in _VALID_EVENT_TYPES:
        raise ValueError(f"Unknown event type: {event_type}")

    parser_fn = _PAYLOAD_PARSERS[event_type]
    payload = parser_fn(raw_payload)

    return {
        "seq": int(seq_id),
        "cell_id": _normalize_cell_identifier(cell_id),
        "type": event_type,
        "payload": payload,
    }


def _apply_deduplication_filter(events):
    """Remove exact duplicate events based on sequence ID.

    In rare cases, log rotation may produce duplicate entries. This filter
    ensures each sequence ID appears exactly once.
    """
    seen = set()
    filtered = []
    for event in events:
        if event["seq"] not in seen:
            seen.add(event["seq"])
            filtered.append(event)
    return filtered


def parse_propagation_log(filepath):
    """Parse the propagation log file and return structured event list.

    Args:
        filepath: Path to the propagation_log.dat file.

    Returns:
        Tuple of (events_list, registry) where events_list is a list of
        event dicts sorted by sequence number, and registry is an
        EventRegistry instance with parse-time statistics.
    """
    registry = EventRegistry()
    events = []

    with open(filepath, "r") as fh:
        for line_num, line in enumerate(fh, 1):
            components = _validate_line_structure(line, line_num)
            if components is None:
                continue

            seq_id, cell_id, event_type, raw_payload = components
            record = _build_event_record(seq_id, cell_id, event_type, raw_payload)
            events.append(record)
            registry.register_event(
                record["seq"], record["cell_id"], record["type"], record["payload"]
            )

    # Apply deduplication before returning
    events = _apply_deduplication_filter(events)

    # Sort by sequence number to ensure temporal ordering
    events.sort(key=lambda e: e["seq"])

    return events, registry
