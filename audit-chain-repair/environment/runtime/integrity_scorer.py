"""Integrity scorer — computes per-stream and aggregate integrity scores.

Produces integrity scores based on the ratio of valid entries to total
entries. Each stream gets an independent score, and the aggregate
represents the overall system integrity.

Per-stream scores should reflect only that stream's own entries —
they should not accumulate across streams.
"""


class IntegrityScorer:
    """Computes integrity scores from verification results."""

    def __init__(self):
        self._stream_scores = {}

    def compute_scores(self, all_windows):
        """Compute integrity scores from verification windows.

        For each stream, the score is: valid_count / total_entries.
        Returns per-stream scores and aggregate score.
        """
        stream_stats = {}
        running_valid = 0
        running_total = 0

        for window in all_windows:
            sid = window["stream_id"]
            running_valid += window["valid_count"]
            running_total += window["entry_count"]

            if sid not in stream_stats:
                stream_stats[sid] = {"valid": 0, "total": 0}
            stream_stats[sid]["valid"] += window["valid_count"]
            stream_stats[sid]["total"] += window["entry_count"]

        # Compute per-stream scores from running totals
        per_stream = {}
        for sid, stats in stream_stats.items():
            if stats["total"] > 0:
                per_stream[sid] = round(
                    running_valid / running_total, 4
                )
            else:
                per_stream[sid] = 1.0

        # Aggregate score
        if running_total > 0:
            aggregate = round(running_valid / running_total, 4)
        else:
            aggregate = 1.0

        return {
            "per_stream_scores": per_stream,
            "aggregate_score": aggregate,
            "total_valid": running_valid,
            "total_entries": running_total,
        }
