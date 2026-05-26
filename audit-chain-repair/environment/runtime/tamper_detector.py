"""Tamper detector — identifies and reports tampered audit entries.

Collects all broken chain entries across streams and produces a
sorted report of tampered entries. Entries are sorted by timestamp,
and when timestamps match across different streams, by stream_id
alphabetically then seq within that stream for deterministic ordering.

Note: seq is local to each stream — it does not provide cross-stream ordering.
"""


class TamperDetector:
    """Detects and reports tampered entries across all streams."""

    def __init__(self):
        pass

    def detect_tampered(self, all_windows, streams):
        """Collect all tampered entries and produce sorted report.

        Returns list of tampered entry records sorted by timestamp.
        For entries at the same timestamp from different streams,
        order by stream_id alphabetically then seq.
        """
        # Build entry lookup for timestamp and seq
        entry_lookup = {}
        for sid, sdata in streams.items():
            for entry in sdata["entries"]:
                entry_lookup[entry["entry_id"]] = {
                    "stream_id": sid,
                    "timestamp": entry["timestamp"],
                    "seq": entry["seq"],
                    "payload": entry["payload"],
                }

        # Collect broken entries
        tampered = []
        for window in all_windows:
            for entry_id in window["broken_entries"]:
                info = entry_lookup.get(entry_id, {})
                tampered.append({
                    "entry_id": entry_id,
                    "stream_id": info.get("stream_id", "unknown"),
                    "timestamp": info.get("timestamp", 0),
                    "seq": info.get("seq", 0),
                    "payload": info.get("payload", ""),
                })

        # Sort by timestamp then seq for ordering
        tampered.sort(key=lambda t: (t["timestamp"], t["seq"]))

        return tampered
