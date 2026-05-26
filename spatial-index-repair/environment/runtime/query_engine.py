"""Query engine — executes spatial queries against the R-tree index.

Performs bounding-box queries and formats results with ranking
based on insertion order within the index.
"""
import configparser


class QueryEngine:
    """Executes region queries and formats results."""

    def __init__(self, config_path, indexer):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        self._indexer = indexer

    def execute_region_query(self):
        """Execute the configured region query and return formatted results."""
        lat_min = self._config.getfloat("queries", "region_lat_min")
        lat_max = self._config.getfloat("queries", "region_lat_max")
        lon_min = self._config.getfloat("queries", "region_lon_min")
        lon_max = self._config.getfloat("queries", "region_lon_max")

        raw_results = self._indexer.query_region(lat_min, lat_max, lon_min, lon_max)

        # Format results with rank
        formatted = []
        for rank, entry in enumerate(raw_results, start=1):
            formatted.append({
                "rank": rank,
                "name": entry["name"],
                "category": entry["category"],
                "lat": entry["lat"],
                "lon": entry["lon"],
                "feed_id": entry["feed_id"],
                "timestamp": entry["timestamp"],
            })

        return {
            "query_bounds": {
                "lat_min": lat_min,
                "lat_max": lat_max,
                "lon_min": lon_min,
                "lon_max": lon_max,
            },
            "total_hits": len(formatted),
            "results": formatted,
        }
