"""Validation tests for spatial query planner output."""
import json
import os

import pytest

OUTPUT_DIR = "/app/runtime/output"
SUMMARY_PATH = os.path.join(OUTPUT_DIR, "query_summary.json")
RESULTS_PATH = os.path.join(OUTPUT_DIR, "query_results.json")
INDEX_PATH = os.path.join(OUTPUT_DIR, "index_stats.json")


@pytest.fixture(scope="module")
def summary():
    """Load query summary output."""
    with open(SUMMARY_PATH, "r") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def results():
    """Load query results output."""
    with open(RESULTS_PATH, "r") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def index_stats():
    """Load index statistics output."""
    with open(INDEX_PATH, "r") as f:
        return json.load(f)


# --- EASY TESTS (pass even with buggy code, structural checks) ---

class TestOutputStructure:
    """Basic output file existence and structure."""

    def test_summary_file_exists(self):
        """Query summary output file must exist."""
        assert os.path.isfile(SUMMARY_PATH)

    def test_results_file_exists(self):
        """Query results output file must exist."""
        assert os.path.isfile(RESULTS_PATH)

    def test_index_stats_file_exists(self):
        """Index statistics output file must exist."""
        assert os.path.isfile(INDEX_PATH)

    def test_summary_has_required_fields(self, summary):
        """Summary must contain all documented fields."""
        required = [
            "total_results", "sources_queried", "source_count",
            "results_per_source", "index_cells", "index_features",
            "max_distance_km", "min_distance_km",
        ]
        for field in required:
            assert field in summary, f"Missing field: {field}"


# --- MEDIUM TESTS (require 1-2 bug fixes each) ---

class TestSourceLoading:
    """Source loading completeness — requires Bug A fix."""

    def test_all_four_sources_loaded(self, summary):
        """All 4 configured sources must be loaded including cadastral.

        The active_sources list in /app/runtime/config.ini must be parsed
        correctly — check whitespace handling in /app/runtime/loader.py.
        """
        sources = summary["sources_queried"]
        assert len(sources) == 4, (
            f"Expected 4 sources but got {len(sources)}: {sources}. "
            f"Check how /app/runtime/loader.py parses active_sources from config."
        )
        assert "cadastral" in sources, (
            "cadastral source missing — check whitespace in config parsing"
        )

    def test_cadastral_features_in_results(self, summary):
        """Results must include features from the cadastral source."""
        per_source = summary["results_per_source"]
        assert "cadastral" in per_source, (
            "No cadastral results found. The cadastral source file exists at "
            "/app/runtime/data/cadastral.json but is not being loaded."
        )
        assert per_source["cadastral"] > 0


class TestQueryRadius:
    """Query radius correctness — requires Bug B fix."""

    def test_max_distance_within_spatial_radius(self, summary):
        """Maximum result distance must be within 12.5 km (query.spatial radius).

        The query.spatial section in /app/runtime/config.ini defines
        radius_km=12.5. Check that /app/runtime/range_query.py reads
        from the correct config section.
        """
        max_dist = summary["max_distance_km"]
        assert max_dist <= 12.5, (
            f"max_distance_km={max_dist} exceeds the spatial radius of 12.5km. "
            f"Check which config section /app/runtime/range_query.py reads "
            f"radius_km from — it should use query.spatial, not query."
        )

    def test_total_results_capped(self, summary):
        """Total results must not exceed max_results=25 from query.spatial."""
        assert summary["total_results"] <= 25, (
            f"Got {summary['total_results']} results but max_results=25 "
            f"in query.spatial section."
        )


# --- HARD TESTS (require 3-4 bug fixes together) ---

class TestIndexAccuracy:
    """Index feature count accuracy — requires Bug C fix."""

    def test_index_total_features_matches_loaded(self, index_stats, summary):
        """Index total_features must equal actual features loaded (61 with all sources).

        The index builder processes features in batches. Feature counts
        must reflect the final snapshot per cell, not accumulate across
        batch iterations.
        """
        # With all 4 sources: 13+15+18+15 = 61 features
        expected_total = 61
        actual = index_stats["total_features"]
        assert actual == expected_total, (
            f"Index reports {actual} features but {expected_total} were loaded. "
            f"Check /app/runtime/index_builder.py batch accumulation logic — "
            f"feature_count should reflect per-batch snapshot, not sum across batches."
        )

    def test_no_cell_exceeds_batch_size_features(self, index_stats):
        """No single cell should report more features than actually exist there.

        With batch_size=10 and accumulation bug, cells get inflated counts.
        """
        cells = index_stats["cells"]
        for cell_key, cell_data in cells.items():
            assert cell_data["feature_count"] <= 30, (
                f"Cell {cell_key} reports {cell_data['feature_count']} features "
                f"which exceeds what a single cell can hold. Check batch "
                f"accumulation in /app/runtime/index_builder.py."
            )


class TestResultOrdering:
    """Result ordering determinism — requires Bug D fix."""

    def test_tied_distances_sorted_by_source_then_feature(self, results):
        """Features at identical distances must be sorted by source_id then feature_id.

        Multiple features exist at the exact query center (45.0, -93.0) with
        distance=0.0. These must appear ordered by source_id then feature_id
        for deterministic output. Note: feature_id is local to each source.
        """
        result_list = results["results"]
        # Find features with distance 0.0 (at query center)
        zero_dist = [r for r in result_list if r["distance_km"] == 0.0]
        if len(zero_dist) >= 2:
            for i in range(len(zero_dist) - 1):
                a = zero_dist[i]
                b = zero_dist[i + 1]
                key_a = (a["source_id"], a["feature_id"])
                key_b = (b["source_id"], b["feature_id"])
                assert key_a <= key_b, (
                    f"Results with tied distance not sorted by (source_id, feature_id): "
                    f"{a['source_id']}:{a['feature_id']} should come before "
                    f"{b['source_id']}:{b['feature_id']}. "
                    f"Check sort key in /app/runtime/range_query.py."
                )

    def test_first_result_is_nearest(self, results):
        """First result must have the minimum distance."""
        result_list = results["results"]
        assert len(result_list) > 0
        distances = [r["distance_km"] for r in result_list]
        assert distances[0] == min(distances), (
            f"First result distance {distances[0]} is not the minimum "
            f"{min(distances)} — results not sorted by distance."
        )
