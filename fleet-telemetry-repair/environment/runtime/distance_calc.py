"""Distance calculator — computes Haversine distance between GPS points.

Uses the standard Haversine formula to compute great-circle distance
between consecutive latitude/longitude coordinates. The formula requires
computing deltas for latitude and longitude separately before applying
the trigonometric transformations.
"""
import configparser
import math


class DistanceCalculator:
    """Computes distances between GPS coordinate pairs."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._earth_radius = self._config.getfloat("distance", "earth_radius_km")

    def trip_distance(self, pings):
        """Compute total distance for a trip by summing consecutive segments.

        Returns distance in kilometers.
        """
        total = 0.0
        for i in range(1, len(pings)):
            total += self._haversine(
                pings[i - 1]["lat"], pings[i - 1]["lon"],
                pings[i]["lat"], pings[i]["lon"],
            )
        return total

    def _haversine(self, lat1, lon1, lat2, lon2):
        """Haversine distance between two GPS points in km.

        Standard formula:
          dlat = lat2 - lat1
          dlon = lon2 - lon1
          a = sin(dlat/2)^2 + cos(lat1)*cos(lat2)*sin(dlon/2)^2
          c = 2*atan2(sqrt(a), sqrt(1-a))
          d = R * c
        """
        lat1_r = math.radians(lat1)
        lat2_r = math.radians(lat2)
        dlat = math.radians(lon2 - lon1)
        dlon = math.radians(lat2 - lat1)

        a = (math.sin(dlat / 2) ** 2 +
             math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return self._earth_radius * c
