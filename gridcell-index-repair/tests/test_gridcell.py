"""Tests for the spatial grid indexing system."""
import json
import os
import pytest

INDEX_PATH = "/app/runtime/output/grid_index.json"
CLUSTERS_PATH = "/app/runtime/output/cluster_report.json"
QUERY_PATH = "/app/runtime/output/query_results.json"
SUMMARY_PATH = "/app/runtime/output/spatial_summary.json"

def load_index():
    with open(INDEX_PATH) as f: return json.load(f)
def load_clusters():
    with open(CLUSTERS_PATH) as f: return json.load(f)
def load_query():
    with open(QUERY_PATH) as f: return json.load(f)
def load_summary():
    with open(SUMMARY_PATH) as f: return json.load(f)

class TestOutputStructure:
    def test_index_exists(self):
        """Grid index output must exist."""
        assert os.path.isfile(INDEX_PATH)
    def test_clusters_exists(self):
        """Cluster report must exist."""
        assert os.path.isfile(CLUSTERS_PATH)
    def test_query_exists(self):
        """Query results must exist."""
        assert os.path.isfile(QUERY_PATH)
    def test_summary_exists(self):
        """Summary must exist."""
        assert os.path.isfile(SUMMARY_PATH)

class TestGridAssignment:
    def test_total_assigned(self):
        """Exactly 35 readings should be assigned to the grid."""
        s = load_summary()
        assert s["total_assigned_to_grid"] == 35, (
            f"Expected 35 assigned, got {s['total_assigned_to_grid']}"
        )
    def test_cells_populated(self):
        """Exactly 11 cells should have readings."""
        s = load_summary()
        assert s["cells_populated"] == 11, (
            f"Expected 11 cells, got {s['cells_populated']}"
        )
    def test_no_negative_row_cells(self):
        """No cell should have a negative row index."""
        idx = load_index()
        for cell_id, stats in idx["cell_stats"].items():
            assert stats["cell_row"] >= 0, (
                f"Cell {cell_id} has negative row"
            )

class TestAggregation:
    def test_sample_variance(self):
        """Variance must use sample correction (N-1 divisor).

        For cell R01C01 with 8 readings, population variance and sample
        variance differ significantly.
        """
        idx = load_index()
        cell = idx["cell_stats"].get("R01C01")
        assert cell is not None, "Cell R01C01 not found"
        n = cell["count"]
        # Sample variance should be larger than population variance
        # For 8 readings, sample var = pop_var * 8/7
        # We check that variance > mean * 0.01 (non-trivial)
        assert cell["variance"] > 0, "Variance should be positive"
        # Check specific expected value for R01C01
        expected_var = 2.3421  # pre-computed sample variance
        assert abs(cell["variance"] - expected_var) < 0.01, (
            f"R01C01 variance={cell['variance']}, expected ~{expected_var}"
        )

class TestClustering:
    def test_cluster_count(self):
        """Exactly 1 cluster should be found with 8-connectivity."""
        c = load_clusters()
        assert c["total_clusters"] == 1, (
            f"Expected 1 cluster, got {c['total_clusters']}"
        )
    def test_cluster_includes_diagonal(self):
        """The cluster must include cell R00C03 via diagonal connection.

        Cell (0,3) connects to (1,2) diagonally. With correct
        8-connectivity, both belong to the same cluster.
        """
        c = load_clusters()
        assert c["total_clusters"] >= 1
        cluster_cells = c["clusters"][0]["cells"]
        assert "R00C03" in cluster_cells, (
            f"R00C03 missing from cluster — check connectivity mode"
        )
    def test_cluster_size(self):
        """The main cluster should contain 4 cells."""
        c = load_clusters()
        assert c["clusters"][0]["cell_count"] == 4, (
            f"Expected 4 cells in cluster, got {c['clusters'][0]['cell_count']}"
        )

class TestQueryResults:
    def test_query_result_count(self):
        """Query should return 9 cells within radius 3.0."""
        q = load_query()
        assert q["results_count"] == 9, (
            f"Expected 9 query results, got {q['results_count']}"
        )
    def test_query_includes_all_nearby_cells(self):
        """Query must include cells based on cell center distance."""
        q = load_query()
        result_ids = [r["cell_id"] for r in q["results"]]
        assert "R01C01" in result_ids, "R01C01 should be in query results"
        assert "R02C01" in result_ids, "R02C01 should be in query results"
