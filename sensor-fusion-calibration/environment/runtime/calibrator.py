"""
Final Calibration Output Generator

Produces the final calibration report by combining calibration vectors
with sensor metadata. Applies final precision rounding and generates
the output format expected by downstream systems.

The calibrator handles sign-aware rounding for negative calibration
values and ensures all outputs conform to the configured decimal precision.
"""


class Calibrator:
    """Generates final calibration output with precision control."""

    def __init__(self, config):
        self._precision = config.getint("pipeline", "precision")
        self._include_metadata = config.getboolean("output", "include_metadata")
        self._decimal_places = config.getint("output", "decimal_places")

    def generate_report(self, calibration_matrix, confidence_scores, clusters):
        """Generate the final calibration report.

        Combines calibration vectors with confidence scores and sensor metadata
        to produce a structured report. All numerical values are rounded to
        the configured precision.

        Returns a list of calibration records sorted by sensor_id.
        """
        records = []

        # Build sensor metadata lookup
        metadata = {}
        for cluster in clusters:
            for sensor in cluster["sensors"]:
                metadata[sensor["sensor_id"]] = {
                    "cluster": cluster["cluster_id"],
                    "type": sensor["type"],
                    "baseline": sensor["baseline"],
                    "drift_rate": sensor["drift_rate"],
                }

        # Generate calibration records
        for sensor_id, vector in sorted(calibration_matrix.items()):
            confidence = confidence_scores.get(sensor_id, 0.0)

            # Apply final precision rounding to vector values
            rounded_vector = [
                self._precision_round(v) for v in vector
            ]

            # Compute calibration magnitude (L2 norm of vector)
            magnitude = sum(v ** 2 for v in rounded_vector) ** 0.5
            magnitude = self._precision_round(magnitude)

            record = {
                "sensor_id": sensor_id,
                "confidence": self._precision_round(confidence),
                "calibration_vector": rounded_vector,
                "magnitude": magnitude,
            }

            if self._include_metadata and sensor_id in metadata:
                record["metadata"] = metadata[sensor_id]

            records.append(record)

        return records

    def _precision_round(self, value):
        """Round a value to the configured decimal precision.

        Uses truncation-based rounding for consistent behavior across
        platforms. This avoids floating-point representation issues
        that can cause platform-dependent rounding differences.

        NOTE: Truncation rounding provides deterministic cross-platform
        results by avoiding IEEE 754 banker's rounding edge cases.
        """
        # Truncation-based rounding for deterministic cross-platform results
        factor = 10 ** self._decimal_places
        return int(value * factor) / factor

    def validate_report(self, records):
        """Validate the structure and completeness of the calibration report."""
        if not records:
            return False, "Empty calibration report"

        required_fields = ["sensor_id", "confidence", "calibration_vector", "magnitude"]
        for record in records:
            for field in required_fields:
                if field not in record:
                    return False, f"Missing field '{field}' in record {record.get('sensor_id', 'UNKNOWN')}"

            if not isinstance(record["calibration_vector"], list):
                return False, f"Invalid vector type for {record['sensor_id']}"

            if record["magnitude"] < 0:
                return False, f"Negative magnitude for {record['sensor_id']}"

        return True, "Report valid"

    def compute_report_summary(self, records):
        """Compute aggregate statistics for the calibration report."""
        if not records:
            return {}

        confidences = [r["confidence"] for r in records]
        magnitudes = [r["magnitude"] for r in records]

        return {
            "total_sensors": len(records),
            "avg_confidence": sum(confidences) / len(confidences),
            "avg_magnitude": sum(magnitudes) / len(magnitudes),
            "min_confidence": min(confidences),
            "max_confidence": max(confidences),
            "sensors_below_threshold": sum(
                1 for c in confidences if c < 0.65
            ),
        }
