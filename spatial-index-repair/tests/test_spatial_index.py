"""Tests for the spatial index builder system.

Validates that the R-tree spatial index correctly loads, indexes,
queries, and reports statistics on POI data from multiple feed sources.
"""
import json
import os

import pytest

OUTPUT_DIR = "/app/runtime/output"
QUERY_RESULTS_PATH = os.path.join(OUTPUT_DIR, "query_results.json")
INDEX_STATS_PATH = os.path.join(OUTPUT_DIR, "index_stats.json")


def load_query_results():
    """Load query results from output file."""
    with open(QUERY_RESULTS_PATH, "r") as f:
        return json.load(f)


def load_index_stats():
    """Load index statistics from output file."""
    with open(INDEX_STATS_PATH, "r") as f:
        return json.load(f)


class TestOutputFileExistence:
    """Verify that the system produces expected output files."""

    def test_query_results_file_exists(self):
        """Output file query_results.json must exist after processing."""
        assert os.path.isfile(QUERY_RESULTS_PATH), (
            f"Expected output file not found: {QUERY_RESULTS_PATH}"
        )

    def test_index_stats_file_exists(self):
        """Output file index_stats.json must exist after processing."""
        assert os.path.isfile(INDEX_STATS_PATH), (
            f"Expected output file not found: {INDEX_STATS_PATH}"
        )


class TestQueryResultsStructure:
    """Verify the structure of query results output."""

    def test_query_results_has_required_fields(self):
        """Query results must contain query_bounds, total_hits, and results fields."""
        data = load_query_results()
        assert "query_bounds" in data, "Missing 'query_bounds' field in query_results.json"
        assert "total_hits" in data, "Missing 'total_hits' field in query_results.json"
        assert "results" in data, "Missing 'results' field in query_results.json"

    def test_query_results_entry_fields(self):
        """Each result entry must have rank, name, category, lat, lon, feed_id, timestamp."""
        data = load_query_results()
        assert len(data["results"]) > 0, "No results found in query output"
        required_fields = {"rank", "name", "category", "lat", "lon", "feed_id", "timestamp"}
        first_entry = data["results"][0]
        missing = required_fields - set(first_entry.keys())
        assert not missing, f"Result entry missing fields: {missing}"


class TestCategoryFiltering:
    """Verify that all configured categories are properly loaded."""

    def test_total_indexed_includes_all_categories(self):
        """All 56 POI records must be indexed when all 4 categories are allowed.
        
        The config allows restaurant, park, museum, and hospital categories.
        Check that the category filter in /app/runtime/feed_loader.py correctly
        parses all category names from the comma-separated config value.
        """
        stats = load_index_stats()
        assert stats["total_indexed"] == 56, (
            f"Expected 56 total indexed records (all 4 categories) but got "
            f"{stats['total_indexed']}. Verify category parsing in "
            f"/app/runtime/feed_loader.py handles whitespace in config values."
        )

    def test_hospital_category_present(self):
        """Hospital category POIs must appear in query results.
        
        The allowed_categories config value includes hospital — ensure the
        category filter in /app/runtime/feed_loader.py properly strips
        whitespace from each category name after splitting.
        """
        data = load_query_results()
        categories_found = {r["category"] for r in data["results"]}
        assert "hospital" in categories_found, (
            "Hospital category missing from results. Check how "
            "/app/runtime/feed_loader.py splits the allowed_categories "
            "config value — whitespace handling may be incorrect."
        )

    def test_all_four_categories_present(self):
        """All four categories (restaurant, park, museum, hospital) must be indexed."""
        stats = load_index_stats()
        expected_categories = {"restaurant", "park", "museum", "hospital"}
        actual_categories = set(stats["category_counts"].keys())
        assert expected_categories == actual_categories, (
            f"Expected categories {expected_categories} but got {actual_categories}"
        )


class TestIndexStructure:
    """Verify R-tree index uses correct configuration parameters."""

    def test_node_count_matches_rtree_config(self):
        """R-tree must produce 7 leaf nodes with max 8 entries per node for 56 records.
        
        The indexer.rtree section specifies max_entries_per_node = 8.
        Ensure /app/runtime/indexer.py reads from the correct config section.
        """
        stats = load_index_stats()
        assert stats["node_count"] == 7, (
            f"Expected 7 nodes (56 records / 8 max entries) but got "
            f"{stats['node_count']}. Check which config section "
            f"/app/runtime/indexer.py reads batch_size and max_entries_per_node from."
        )

    def test_max_entries_per_node_from_rtree_section(self):
        """The max_entries_per_node stat must reflect the [indexer.rtree] config value of 8."""
        stats = load_index_stats()
        assert stats["max_entries_per_node"] == 8, (
            f"Expected max_entries_per_node=8 (from [indexer.rtree] section) "
            f"but got {stats['max_entries_per_node']}. The indexer should read "
            f"parameters from [indexer.rtree], not [indexer]."
        )

    def test_avg_node_fill(self):
        """Average node fill should be 8.0 when 56 records fill 7 nodes evenly."""
        stats = load_index_stats()
        assert stats["avg_node_fill"] == 8.0, (
            f"Expected avg_node_fill=8.0 but got {stats['avg_node_fill']}"
        )


class TestStatisticsComputation:
    """Verify partition-based statistics use final snapshot values."""

    def test_category_counts_are_final_partition_snapshot(self):
        """Category counts must reflect the LAST partition snapshot, not accumulated totals.
        
        When computing per-category statistics across partitions, each partition
        is a snapshot. The final output should contain only the last partition's
        counts — not the sum of all partitions. Check /app/runtime/stats.py for
        how partition counts are merged into the final result.
        """
        stats = load_index_stats()
        counts = stats["category_counts"]
        # If accumulated, restaurant would be 18 — the correct value is from last partition
        assert counts.get("restaurant", 0) < 18, (
            f"restaurant count is {counts.get('restaurant', 0)} which suggests "
            f"accumulation across partitions. Stats in /app/runtime/stats.py "
            f"should use last-write-wins, not summation."
        )

    def test_category_counts_not_inflated(self):
        """Total of all category counts must not exceed the partition batch size.
        
        Since counts represent a single partition snapshot, total cannot exceed
        the batch size (20 records per partition from [indexer.rtree]).
        """
        stats = load_index_stats()
        counts = stats["category_counts"]
        total = sum(counts.values())
        assert total <= 20, (
            f"Sum of category_counts is {total}, exceeding partition size of 20. "
            f"This indicates accumulation bug in /app/runtime/stats.py — "
            f"partition snapshots should overwrite, not accumulate."
        )


class TestSortDeterminism:
    """Verify deterministic ordering of records at timestamp boundaries."""

    def test_tiebreaker_ordering_at_shared_timestamp(self):
        """Records sharing timestamp 2024-01-15T10:14:00Z must be ordered by feed_id.
        
        When multiple records have identical timestamps, the sort must use
        feed_id as a secondary key before sequence number. Check the sort key
        in /app/runtime/indexer.py — note that seq is local to each feed stream,
        so feed_id must be included for deterministic cross-feed ordering.
        """
        data = load_query_results()
        results = data["results"]
        # Find the two records at timestamp 2024-01-15T10:14:00Z
        tied_records = [
            r for r in results
            if r["timestamp"] == "2024-01-15T10:14:00Z"
        ]
        assert len(tied_records) == 2, (
            f"Expected 2 records at timestamp 2024-01-15T10:14:00Z but found "
            f"{len(tied_records)}"
        )
        # alpha should come before beta in feed_id ordering
        assert tied_records[0]["feed_id"] == "alpha", (
            f"First record at tied timestamp should be from feed 'alpha' "
            f"(alphabetical feed_id ordering) but got '{tied_records[0]['feed_id']}'. "
            f"Check sort key in /app/runtime/indexer.py — feed_id must be "
            f"included between timestamp and seq for deterministic ordering."
        )
        assert tied_records[1]["feed_id"] == "beta", (
            f"Second record at tied timestamp should be from feed 'beta' "
            f"but got '{tied_records[1]['feed_id']}'"
        )

    def test_three_way_tie_at_11_00_00(self):
        """Three records at 2024-01-15T11:00:00Z must be ordered alpha, beta, gamma."""
        data = load_query_results()
        results = data["results"]
        tied_records = [
            r for r in results
            if r["timestamp"] == "2024-01-15T11:00:00Z"
        ]
        assert len(tied_records) == 3, (
            f"Expected 3 records at timestamp 2024-01-15T11:00:00Z but found "
            f"{len(tied_records)}"
        )
        feed_order = [r["feed_id"] for r in tied_records]
        assert feed_order == ["alpha", "beta", "gamma"], (
            f"Records at 11:00:00Z should be ordered by feed_id "
            f"['alpha', 'beta', 'gamma'] but got {feed_order}. "
            f"Check sort key in /app/runtime/indexer.py — seq is local to "
            f"each stream, so feed_id is required for deterministic ordering."
        )
