"""Compliance reporter — checks flow rates against operational limits.

Evaluates each meter's interval averages against configured min/max
flow thresholds and deviation limits, producing a compliance report.
"""
import configparser


class ComplianceReporter:
    """Generates compliance reports from aggregated meter data."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._min_flow = self._config.getfloat("compliance", "min_flow")
        self._max_flow = self._config.getfloat("compliance", "max_flow")
        self._max_deviation = self._config.getfloat("compliance", "max_deviation")

    def generate_report(self, aggregated_meters):
        """Generate compliance report for all meters.

        Checks each interval's mean flow against operational limits.
        Also checks deviation (max - min) of compensated readings within
        each interval for measurement consistency.

        Returns dict with keys: meter_order, total_meters, compliant_count,
        non_compliant_count, meters (list of per-meter results).
        """
        meter_ids = sorted(aggregated_meters.keys())

        meters_report = []
        compliant_count = 0

        for meter_id in meter_ids:
            intervals = aggregated_meters[meter_id]
            violations = []
            total_intervals = len(intervals)

            for interval in intervals:
                mean_flow = interval["mean_flow_raw"]
                readings = interval["readings"]

                # Check flow limits
                if mean_flow < self._min_flow:
                    violations.append({
                        "interval_index": interval["interval_index"],
                        "type": "below_minimum",
                        "value": round(mean_flow, 4),
                        "limit": self._min_flow,
                    })
                elif mean_flow > self._max_flow:
                    violations.append({
                        "interval_index": interval["interval_index"],
                        "type": "above_maximum",
                        "value": round(mean_flow, 4),
                        "limit": self._max_flow,
                    })

                # Check deviation within interval
                if len(readings) > 1:
                    comp_flows = [r["flow_compensated"] for r in readings]
                    deviation = max(comp_flows) - min(comp_flows)
                    if deviation > self._max_deviation:
                        violations.append({
                            "interval_index": interval["interval_index"],
                            "type": "excess_deviation",
                            "value": round(deviation, 4),
                            "limit": self._max_deviation,
                        })

            is_compliant = len(violations) == 0
            if is_compliant:
                compliant_count += 1

            meters_report.append({
                "meter_id": meter_id,
                "total_intervals": total_intervals,
                "is_compliant": is_compliant,
                "violation_count": len(violations),
                "violations": violations,
            })

        return {
            "meter_order": meter_ids,
            "total_meters": len(meter_ids),
            "compliant_count": compliant_count,
            "non_compliant_count": len(meter_ids) - compliant_count,
            "meters": meters_report,
        }
