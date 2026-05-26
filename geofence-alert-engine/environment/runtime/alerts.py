"""Alert generator — computes severity scores and produces alert reports.

Calculates per-vehicle alert severity as a weighted average of dwell
metrics across geofence zones, filters by minimum threshold, and
produces sorted alert output with summary statistics.
"""
import configparser


class AlertGenerator:
    """Generates severity-ranked geofence violation alerts."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._min_severity = self._config.getfloat("alerts", "min_severity")
        self._weights = self._parse_weights()

    def _parse_weights(self):
        """Parse zone weights from config. Order matches zone definition order."""
        raw = self._config.get("geofences", "weights")
        return [float(w) for w in raw.split(",")]

    def generate(self, dwell_data):
        """Generate alerts from dwell metrics.

        For each vehicle, computes a single severity score by taking the
        weighted average of normalized dwell scores across all violated zones.
        Then emits one alert entry per zone that vehicle was present in.
        """
        # Group by vehicle
        vehicle_zones = {}
        for entry in dwell_data:
            vid = entry["vehicle_id"]
            if vid not in vehicle_zones:
                vehicle_zones[vid] = []
            vehicle_zones[vid].append(entry)

        zone_order = sorted(
            k for k in self._config.options("geofences") if k.startswith("zone_")
        )

        alerts = []
        for vid, entries in vehicle_zones.items():
            # Compute weighted severity across all violated zones for this vehicle
            weighted_sum = 0.0
            total_weight = 0.0
            violated_entries = []

            for zone_entry in entries:
                if zone_entry["readings_inside"] == 0:
                    continue
                violated_entries.append(zone_entry)

                zone_id = zone_entry["zone_id"]
                zone_idx = zone_order.index(zone_id) if zone_id in zone_order else 0
                weight = self._weights[zone_idx] if zone_idx < len(self._weights) else 0.1

                # Normalize dwell contribution (cap at 300s for max score)
                dwell_score = min(zone_entry["dwell_seconds"] / 300.0, 1.0)
                weighted_sum += weight * dwell_score
                total_weight = weight

            severity = weighted_sum / total_weight if total_weight > 0 else 0.0

            if severity >= self._min_severity:
                for zone_entry in violated_entries:
                    alerts.append({
                        "zone_id": zone_entry["zone_id"],
                        "vehicle_id": vid,
                        "severity": round(severity, 4),
                        "dwell_seconds": zone_entry["dwell_seconds"],
                        "readings_inside": zone_entry["readings_inside"],
                    })

        # Sort for deterministic output ordering
        alerts.sort(key=lambda a: (a["zone_id"], -a["severity"]))

        summary = {
            "total_alerts": len(alerts),
            "zones_violated": len(set(a["zone_id"] for a in alerts)),
            "total_dwell": sum(a["dwell_seconds"] for a in alerts),
            "max_severity": max((a["severity"] for a in alerts), default=0.0),
        }

        return alerts, summary
