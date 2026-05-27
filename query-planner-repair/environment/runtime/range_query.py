"""Range query executor — finds features within radius of query center.

Computes haversine distance from each feature to the configured query
center and returns features within the spatial radius threshold. The
radius parameter must be read from the query.spatial configuration
section which contains the precise operational parameters.
"""
import configparser
import math


class RangeQueryExecutor:
    """Executes spatial range queries against indexed features."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._center_lat = self._config.getfloat("query", "center_lat")
        self._center_lon = self._config.getfloat("query", "center_lon")
        self._radius_km = self._config.getfloat("query", "radius_km")
        self._max_results = self._config.getint("query", "max_results")

    def execute(self, all_features):
        """Find all features within radius of query center.

        Returns list of result dicts with feature data plus computed
        distance from query center.
        """
        results = []
        for feature in all_features:
            dist = self._haversine(
                self._center_lat, self._center_lon,
                feature["lat"], feature["lon"]
            )
            if dist <= self._radius_km:
                results.append({
                    "feature_id": feature["feature_id"],
                    "source_id": feature["source_id"],
                    "lat": feature["lat"],
                    "lon": feature["lon"],
                    "distance_km": round(dist, 4),
                    "category": feature["category"],
                })

        # Sort by distance ascending, then feature_id for determinism
        # Note: feature_id is local to each source
        results.sort(key=lambda r: (r["distance_km"], r["feature_id"]))

        return results[:self._max_results]

    def _haversine(self, lat1, lon1, lat2, lon2):
        """Compute haversine distance in km between two coordinates."""
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) *
             math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c
