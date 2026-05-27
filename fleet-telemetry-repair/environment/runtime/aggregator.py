"""Report aggregator — assembles final fleet report.

Builds the per-vehicle report entries and summary statistics.
Vehicles should be ordered by numeric identifier for deterministic
output (V1, V2, V3, V10, V12 — not V1, V10, V12, V2, V3).
"""
import configparser
import json
import os


class ReportAggregator:
    """Aggregates trip data into fleet report."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._output_dir = self._config.get("fleet", "output_dir")

    def generate_report(self, vehicle_results):
        """Generate fleet report and summary from per-vehicle results.

        vehicle_results: dict mapping vehicle_id to dict with keys:
          trips (int), distance_km (float), fuel_liters (float), score (float)
        """
        os.makedirs(self._output_dir, exist_ok=True)

        vehicle_ids = sorted(vehicle_results.keys())

        report_entries = []
        for vid in vehicle_ids:
            data = vehicle_results[vid]
            report_entries.append({
                "vehicle_id": vid,
                "trips": data["trips"],
                "distance_km": round(data["distance_km"], 2),
                "fuel_liters": round(data["fuel_liters"], 3),
                "efficiency_km_per_liter": round(
                    data["distance_km"] / data["fuel_liters"], 2
                ) if data["fuel_liters"] > 0 else 0.0,
                "driver_score": data["score"],
            })

        # Summary
        total_trips = sum(d["trips"] for d in vehicle_results.values())
        total_distance = sum(d["distance_km"] for d in vehicle_results.values())
        total_fuel = sum(d["fuel_liters"] for d in vehicle_results.values())
        scores = [d["score"] for d in vehicle_results.values()]
        max_score = max(scores) if scores else 0.0
        best_vehicle = max(vehicle_results.keys(), key=lambda v: vehicle_results[v]["score"])

        report = {
            "vehicle_order": vehicle_ids,
            "vehicles": report_entries,
        }
        summary = {
            "total_trips": total_trips,
            "total_distance_km": round(total_distance, 2),
            "total_fuel_liters": round(total_fuel, 3),
            "fleet_efficiency_km_per_liter": round(
                total_distance / total_fuel, 2
            ) if total_fuel > 0 else 0.0,
            "max_driver_score": max_score,
            "best_vehicle": best_vehicle,
        }

        with open(os.path.join(self._output_dir, "report.json"), "w") as f:
            json.dump(report, f, indent=2)

        with open(os.path.join(self._output_dir, "summary.json"), "w") as f:
            json.dump(summary, f, indent=2)

        return report, summary
