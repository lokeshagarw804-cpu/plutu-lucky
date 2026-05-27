"""Driver scorer — computes weighted performance scores.

Scores are based on fuel efficiency, speed compliance, and idle ratio.
Not all vehicles have data for every category (e.g., some lack speed
compliance sensors). Missing categories should not penalize the final
score.
"""
import configparser


class DriverScorer:
    """Computes weighted driver performance scores."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._w_efficiency = self._config.getfloat("scoring", "weight_efficiency")
        self._w_speed = self._config.getfloat("scoring", "weight_speed_compliance")
        self._w_idle = self._config.getfloat("scoring", "weight_idle_ratio")
        self._baseline_eff = self._config.getfloat(
            "scoring", "efficiency_baseline_km_per_liter"
        )
        self._max_speed = self._config.getfloat("scoring", "max_speed_kmh")

    def score_vehicle(self, vehicle_trips):
        """Compute driver score for a vehicle across all its trips.

        vehicle_trips is a list of dicts with keys:
          distance_km, fuel_liters, max_speed_kmh, idle_seconds, total_seconds

        Returns score between 0 and 1.
        """
        if not vehicle_trips:
            return 0.0

        # Compute category scores
        eff_score = self._efficiency_score(vehicle_trips)
        speed_score = self._speed_score(vehicle_trips)
        idle_score = self._idle_score(vehicle_trips)

        total_weight = self._w_efficiency + self._w_speed + self._w_idle

        weighted_sum = 0.0
        if eff_score is not None:
            weighted_sum += self._w_efficiency * eff_score
        if speed_score is not None:
            weighted_sum += self._w_speed * speed_score
        if idle_score is not None:
            weighted_sum += self._w_idle * idle_score

        return round(weighted_sum / total_weight, 4)

    def _efficiency_score(self, trips):
        """Score fuel efficiency relative to baseline."""
        total_dist = sum(t["distance_km"] for t in trips)
        total_fuel = sum(t["fuel_liters"] for t in trips)
        if total_fuel <= 0:
            return None
        actual_eff = total_dist / total_fuel
        ratio = min(actual_eff / self._baseline_eff, 1.5)
        return min(ratio / 1.5, 1.0)

    def _speed_score(self, trips):
        """Score based on fraction of trips within speed limit."""
        speeds = [t.get("max_speed_kmh") for t in trips]
        valid = [s for s in speeds if s is not None]
        if not valid:
            return None
        compliant = sum(1 for s in valid if s <= self._max_speed)
        return compliant / len(valid)

    def _idle_score(self, trips):
        """Score based on idle time ratio (lower idle = better score)."""
        total_idle = sum(t.get("idle_seconds", 0) for t in trips)
        total_time = sum(t.get("total_seconds", 1) for t in trips)
        if total_time <= 0:
            return None
        idle_ratio = total_idle / total_time
        return max(0.0, 1.0 - idle_ratio)
