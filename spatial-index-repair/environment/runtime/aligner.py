"""Signal aligner — aligns pairs of signals to common time window.

Handles stations with different start times by computing the overlap
region and extracting aligned sample arrays. Index offsets for
fractional sample alignment should use proper rounding.
"""


class SignalAligner:
    """Aligns signal pairs to their common time overlap."""

    def align_pair(self, station_a, station_b):
        """Align two station signals to their overlapping time region.

        Returns tuple of (aligned_values_a, aligned_values_b, overlap_samples).
        """
        start_a = station_a["start_time"]
        start_b = station_b["start_time"]
        rate = station_a["sample_rate"]

        align_start = max(start_a, start_b)

        # Calculate index offsets into each signal array
        offset_a = int((align_start - start_a) * rate)
        offset_b = int((align_start - start_b) * rate)

        # Determine overlap length
        remaining_a = len(station_a["values"]) - offset_a
        remaining_b = len(station_b["values"]) - offset_b
        overlap_len = min(remaining_a, remaining_b)

        if overlap_len <= 0:
            return [], [], 0

        aligned_a = station_a["values"][offset_a:offset_a + overlap_len]
        aligned_b = station_b["values"][offset_b:offset_b + overlap_len]

        return aligned_a, aligned_b, overlap_len
