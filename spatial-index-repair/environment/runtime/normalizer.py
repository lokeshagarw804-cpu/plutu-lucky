"""Record normalizer — validates and filters POI records.

Applies category filtering based on the allowed_categories config,
validates coordinate ranges, and normalizes field formats before
records are passed to the indexing stage.
"""
import configparser


class RecordNormalizer:
    """Filters and validates POI records before indexing."""

    def __init__(self, config_path):
        self._config = configparser.ConfigParser()
        self._config.read(config_path)
        raw_categories = self._config.get("feeds", "allowed_categories")
        self._allowed = set(raw_categories.split(","))

    def normalize(self, records):
        """Filter records by allowed categories and validate fields."""
        normalized = []
        for record in records:
            category = record.get("category", "")
            if category not in self._allowed:
                continue
            if not self._valid_coordinates(record):
                continue
            normalized.append({
                "seq": record["seq"],
                "feed_id": record["feed_id"],
                "name": record["name"],
                "category": category,
                "lat": float(record["lat"]),
                "lon": float(record["lon"]),
                "timestamp": record["timestamp"],
            })
        return normalized

    def _valid_coordinates(self, record):
        """Check that coordinates are within valid WGS84 range."""
        lat = record.get("lat", 0)
        lon = record.get("lon", 0)
        return -90 <= lat <= 90 and -180 <= lon <= 180
