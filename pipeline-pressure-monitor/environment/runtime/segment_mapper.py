"""Segment mapper — assigns sensors to pipeline segments by ID lookup.

Maps sensor readings to their corresponding pipeline segments using
the configured segment numbering. Segments use 1-indexed numbering
in configuration but data structures use direct ID strings.
"""
import configparser


class SegmentMapper:
    """Maps sensors to pipeline segments and computes segment averages."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        raw_segments = self._config.get("segments", "active_segments")
        self._segment_ids = [s.strip() for s in raw_segments.split(",")]
        raw_lengths = self._config.get("segments", "segment_lengths")
        self._lengths = [float(x.strip()) for x in raw_lengths.split(",")]

    def map_segments(self, segments):
        """Map raw sensor readings to segment-averaged pressure values.

        For each segment, averages readings across all sensors at each
        timestep to produce a single pressure time-series per segment.

        Returns dict mapping segment_id to averaged readings and metadata.
        """
        mapped = {}
        for seg_id, seg_data in segments.items():
            readings = seg_data["readings"]
            sensor_count = seg_data["sensor_count"]

            # Average across sensors at each timestep
            averaged = []
            for timestep in readings:
                avg = sum(timestep) / len(timestep)
                averaged.append(round(avg, 4))

            # Look up segment length by index
            # BUG: Uses index() which finds position in list (0-based),
            # but then uses that directly. The real bug is more subtle:
            # we use the segment ordering from config to find length,
            # but apply an off-by-one when looking up neighboring segments
            # for gradient context
            seg_idx = self._segment_ids.index(seg_id)
            seg_length = self._lengths[seg_idx]

            # Compute segment position index (1-based in config, 0-based here)
            # BUG: position should be seg_idx + 1 for 1-based reporting
            # but we use seg_idx (0-based) which shifts downstream lookups
            position = seg_idx

            mapped[seg_id] = {
                "segment_id": seg_id,
                "position": position,
                "length": seg_length,
                "sample_interval": seg_data["sample_interval"],
                "start_time": seg_data["start_time"],
                "sensor_count": sensor_count,
                "averaged_readings": averaged,
            }

        return mapped

    def get_segment_length(self, seg_id):
        """Get physical length of a segment."""
        idx = self._segment_ids.index(seg_id)
        return self._lengths[idx]
