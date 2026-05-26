"""Validation tests for spatial index output correctness."""
import json
import os

import pytest

OUTPUT_DIR = "/app/runtime/output"
QUERY_PATH = os.path.join(OUTPUT_DIR, "query_results.json")
STATS_PATH = os.path.join(OUTPUT_DIR, "index_stats.json")


@pytest.fixture(scope="module")
def query_data():
    """Load query results output."""
    with open(QUERY_PATH, "r") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def stats_data():
    """Load index statistics output."""
    with open(STATS_PATH, "r") as f:
        return json.load(f)


class TestOutputFiles:
    """Verify output file existence and basic structure."""

    def test_query_results_exists(self):
        """Output must be generated."""
        assert os.path.isfile(QUERY_PATH)

    def test_index_stats_exists(self):
        """Output must be generated."""
        assert os.path.isfile(STATS_PATH)

    def test_query_results_structure(self, query_data):
        """Query output must contain required top-level keys."""
        assert "query_bounds" in query_data
        assert "total_hits" in query_data
        assert "results" in query_data
        assert isinstance(query_data["results"], list)

    def test_stats_structure(self, stats_data):
        """Stats output must contain required top-level keys."""
        for key in ("total_indexed", "node_count", "avg_node_fill",
                    "max_entries_per_node", "category_counts", "spatial_extent"):
            assert key in stats_data


class TestIndexCompleteness:
    """Verify all source data is indexed correctly."""

    def test_total_indexed_count(self, stats_data):
        """All qualifying records from all three feeds must be indexed."""
        assert stats_data["total_indexed"] == 56

    def test_query_hit_count(self, query_data):
        """Region query must return all indexed records within bounds."""
        assert query_data["total_hits"] == 56

    def test_all_categories_indexed(self, stats_data):
        """Index must contain all four configured POI categories."""
        cats = set(stats_data["category_counts"].keys())
        assert cats == {"restaurant", "park", "museum", "hospital"}

    def test_result_entry_fields(self, query_data):
        """Each result entry must have the expected field set."""
        required = {"rank", "name", "category", "lat", "lon", "feed_id", "timestamp"}
        for entry in query_data["results"][:3]:
            assert required.issubset(set(entry.keys()))


class TestIndexStructure:
    """Verify R-tree node configuration and structure."""

    def test_leaf_node_count(self, stats_data):
        """Index must produce exactly 7 leaf nodes."""
        assert stats_data["node_count"] == 7

    def test_max_entries_config(self, stats_data):
        """Leaf node capacity must be 8."""
        assert stats_data["max_entries_per_node"] == 8

    def test_average_fill_factor(self, stats_data):
        """Average node occupancy must equal 8.0."""
        assert stats_data["avg_node_fill"] == 8.0


class TestPartitionStatistics:
    """Verify partition-based category statistics."""

    def test_restaurant_count(self, stats_data):
        """Restaurant count in final statistics."""
        assert stats_data["category_counts"]["restaurant"] == 7

    def test_park_count(self, stats_data):
        """Park count in final statistics."""
        assert stats_data["category_counts"]["park"] == 5

    def test_hospital_count(self, stats_data):
        """Hospital count in final statistics."""
        assert stats_data["category_counts"]["hospital"] == 3

    def test_museum_count(self, stats_data):
        """Museum count in final statistics."""
        assert stats_data["category_counts"]["museum"] == 1

    def test_category_total_within_partition_bounds(self, stats_data):
        """Sum of category counts must not exceed partition window size."""
        total = sum(stats_data["category_counts"].values())
        assert total <= 20


class TestRecordOrdering:
    """Verify deterministic ordering at timestamp boundaries."""

    def test_tiebreaker_at_concurrent_timestamp(self, query_data):
        """Records at 2024-01-15T10:14:00Z must follow correct tie resolution."""
        results = query_data["results"]
        tied = [r for r in results if r["timestamp"] == "2024-01-15T10:14:00Z"]
        assert len(tied) == 2
        assert tied[0]["name"] == "Jade Palace"
        assert tied[1]["name"] == "Golden Dragon"
