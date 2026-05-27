"""Fleet telemetry engine — main entry point.

Orchestrates the full pipeline: load vehicle data, segment into trips,
compute distances and fuel, score drivers, and generate report.
"""
from runtime.loader import FleetLoader
from runtime.trip_segmenter import TripSegmenter
from runtime.distance_calc import DistanceCalculator
from runtime.fuel_calculator import FuelCalculator
from runtime.scorer import DriverScorer
from runtime.aggregator import ReportAggregator


def main():
    config_path = "/app/runtime/config.ini"

    loader = FleetLoader(config_path)
    fleet = loader.load_vehicles()

    segmenter = TripSegmenter(config_path)
    distance_calc = DistanceCalculator(config_path)
    fuel_calc = FuelCalculator()
    scorer = DriverScorer(config_path)

    vehicle_results = {}

    for vid, vehicle_data in fleet.items():
        pings = vehicle_data["pings"]
        trips = segmenter.segment(pings)

        trip_details = []
        total_distance = 0.0
        total_fuel = 0.0

        for trip_pings in trips:
            dist = distance_calc.trip_distance(trip_pings)
            fuel = fuel_calc.trip_fuel(trip_pings)
            total_distance += dist
            total_fuel += fuel

            # Compute trip metadata for scoring
            trip_duration = trip_pings[-1]["timestamp"] - trip_pings[0]["timestamp"]
            idle_time = sum(
                p.get("idle_seconds", 0) for p in trip_pings
            )
            max_speed = None
            speeds = [p.get("speed_kmh") for p in trip_pings if p.get("speed_kmh") is not None]
            if speeds:
                max_speed = max(speeds)

            trip_details.append({
                "distance_km": dist,
                "fuel_liters": fuel,
                "max_speed_kmh": max_speed,
                "idle_seconds": idle_time,
                "total_seconds": trip_duration,
            })

        score = scorer.score_vehicle(trip_details)

        vehicle_results[vid] = {
            "trips": len(trips),
            "distance_km": total_distance,
            "fuel_liters": total_fuel,
            "score": score,
        }

    aggregator = ReportAggregator(config_path)
    aggregator.generate_report(vehicle_results)


if __name__ == "__main__":
    main()
