"""Segment sorter — orders pipeline segments for reporting.

Determines the order in which segments appear in the output report.
The configuration provides a reference ordering used for validation.
"""
import configparser


class SegmentSorter:
    """Orders segments for consistent report output."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        raw_order = self._config.get("segments", "upstream_order")
        self._reference_order = [s.strip() for s in raw_order.split(",")]

    def sort_segments(self, segments):
        """Return segment IDs in the canonical processing order.

        Produces a deterministic ordering of all active segments
        for consistent output generation.
        """
        available = [s for s in self._reference_order if s in segments]
        # Ensure any segments not in reference are still included
        extras = sorted(k for k in segments if k not in available)
        return sorted(available + extras)

    def get_adjacent_pairs(self, segments):
        """Return pairs of adjacent segments in processing order."""
        ordered = self.sort_segments(segments)
        pairs = []
        for i in range(len(ordered) - 1):
            pairs.append((ordered[i], ordered[i + 1]))
        return pairs
