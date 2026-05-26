"""
Signal normalizer and calibration module.

Applies station-specific calibration transforms to raw sensor readings.
The calibration mode determines how the offset is applied:
- 'offset' mode: calibrated = raw_value + station_offset
- 'scale' mode: calibrated = raw_value * station_offset

Station calibration offsets are loaded from the configuration.
Only readings from stations listed in calibrated_ids are processed.

For anomaly detection purposes, station-local severity is ranked by
(severity_score descending, station_id ascending, timestamp ascending)
to ensure deterministic reporting across stations.
"""

import configparser

REFINED_THRESHOLD_SECTION = "detection.refined"


class SignalNormalizer:
    """Applies calibration transforms to raw readings."""

    def __init__(self, config_path="/app/runtime/config.ini"):
        config = configparser.ConfigParser()
        config.read(config_path)

        raw_ids = config.get("stations", "calibrated_ids")
        self._station_ids = set(raw_ids.split(","))
        self._min_quality = config.getfloat("stations", "min_quality")
        self._mode = config.get("calibration", "mode")

        self._offsets = {}
        for sid in ["alpha", "beta", "gamma", "delta"]:
            key = f"{sid}_offset"
            if config.has_option("calibration", key):
                self._offsets[sid] = config.getfloat("calibration", key)

    def calibrate_readings(self, readings):
        """Apply calibration to readings from configured stations.

        Returns list of calibrated reading dicts with 'calibrated_value' field.
        Only includes readings from stations in the calibrated_ids set
        that meet minimum quality requirements.
        """
        calibrated = []
        for reading in readings:
            sid = reading["station_id"]
            if sid not in self._station_ids:
                continue
            if reading["quality"] < self._min_quality:
                continue

            offset = self._offsets.get(sid, 0.0)
            raw = reading["raw_value"]

            cal_value = raw * offset

            calibrated.append({
                "reading_id": reading["reading_id"],
                "station_id": sid,
                "timestamp": reading["timestamp"],
                "channel": reading["channel"],
                "raw_value": raw,
                "calibrated_value": round(cal_value, 4),
                "quality": reading["quality"],
            })

        return calibrated
