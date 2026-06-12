"""Geofence evaluator — tests point containment against polygon zones.

Uses ray-casting algorithm to determine if GPS readings fall within
defined geofence polygons. Each zone is defined as a bounding rectangle
in config, converted to polygon vertices for precise testing.
"""
import configparser


class GeofenceEvaluator:
    """Evaluates GPS point containment against geofence zones."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._zones = self._load_zones()

    def _load_zones(self):
        """Load geofence zone polygons from config.

        Each zone is defined as lat_min,lat_max,lon_min,lon_max and
        converted to a 4-vertex polygon (counter-clockwise winding).
        """
        zones = {}
        for key in self._config.options("geofences"):
            if key.startswith("zone_"):
                parts = self._config.get("geofences", key).split(",")
                lat_min = float(parts[0])
                lat_max = float(parts[1])
                lon_min = float(parts[2])
                lon_max = float(parts[3])
                # Convert to polygon vertices (counter-clockwise)
                polygon = [
                    (lat_min, lon_min),  # SW corner
                    (lat_min, lon_max),  # SE corner
                    (lat_max, lon_max),  # NE corner
                    (lat_max, lon_min),  # NW corner
                ]
                zones[key] = {
                    "polygon": polygon,
                    "bounds": (lat_min, lat_max, lon_min, lon_max),
                }
        return zones

    def evaluate_all(self, readings):
        """Evaluate zone containment for all readings.

        Returns readings annotated with zone membership information.
        """
        results = []
        for reading in readings:
            lat = reading["lat"]
            lon = reading["lon"]
            zones_containing = []
            for zone_id, zone_data in self._zones.items():
                if self._point_in_polygon(lat, lon, zone_data["polygon"]):
                    zones_containing.append(zone_id)
            reading["zones"] = zones_containing
            results.append(reading)
        return results

    def _point_in_polygon(self, lat, lon, polygon):
        """Ray-casting algorithm for point-in-polygon test.

        Casts a horizontal ray from the test point to the right and counts
        edge crossings. Odd count means inside, even means outside.
        Points on vertical edges are handled by the crossing parity.
        """
        n = len(polygon)
        inside = False

        j = n - 1
        for i in range(n):
            lat_i, lon_i = polygon[i]
            lat_j, lon_j = polygon[j]

            # Check if point's latitude is between the edge's latitude range
            if (lat_i > lat) != (lat_j > lat):
                # Compute the longitude where the ray intersects this edge
                intersect_lon = lon_i + (lat - lat_i) * (lon_j - lon_i) / (lat_j - lat_i)
                if lon <= intersect_lon:
                    inside = not inside

            j = i

        return inside

    def get_zone_ids(self):
        """Return list of configured zone IDs."""
        return list(self._zones.keys())
