"""Replay summarizer — generates summary report from materialized view.

Produces a summary document with per-stream statistics and a global
event ordering verification hash to detect replay inconsistencies.
"""
import hashlib
import json


class ReplaySummarizer:
    """Generates replay summary from final materialized state."""

    def summarize(self, materialized_view, sequenced_events):
        """Create summary report from materialized view and event sequence.

        Includes per-stream stats, global totals, and an ordering hash
        computed from the deterministic event sequence.
        """
        stream_stats = {}
        total_events = 0

        for stream_id, state in materialized_view.items():
            count = state["event_count"]
            total_events += count
            stream_stats[stream_id] = {
                "event_count": count,
                "entity_count": len(state["entities"]),
                "totals": state["totals"],
            }

        # Compute ordering hash from sequenced events for verification
        ordering_hash = self._compute_ordering_hash(sequenced_events)

        return {
            "total_events_processed": total_events,
            "stream_count": len(materialized_view),
            "streams": stream_stats,
            "ordering_hash": ordering_hash,
        }

    def _compute_ordering_hash(self, events):
        """Hash the event ordering for determinism verification.

        Uses stream_id + seq + timestamp to produce a fingerprint
        of the exact replay order used.
        """
        hasher = hashlib.sha256()
        for event in events:
            key = f"{event['stream_id']}:{event['seq']}:{event['timestamp']}"
            hasher.update(key.encode())
        return hasher.hexdigest()[:16]
