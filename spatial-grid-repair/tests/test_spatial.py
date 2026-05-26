"""Validation tests for spatial grid indexer output."""
import json
import os

import pytest

OUTPUT_DIR = "/app/runtime/output"
GRID_PATH = os.path.join(OUTPUT_DIR, "grid_index.json")
CLUSTER_PATH = os.path.join(OUTPUT_DIR, "cluster_report.json")


@pytest.fixture(scope="module")
def grid_data():
    """Load grid index output."""
    with open(GRID_PATH, "r") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def cluster_data():
    """Load cluster report output."""
    with open(CLUSTER_PATH, "r") as f:
        return json.load(f)


class TestOutputFiles:
    """Basic output file validation."""

    def test_grid_file_exists(self):
        """Grid index output must be generated."""
        assert os.path.isfile(GRID_PATH)

    def test_cluster_file_exists(self):
        """Cluster report output must be generated."""
        assert os.path.isfile(CLUSTER_PATH)

    def test_grid_structure(self, grid_data):
        """Grid output has required top-level fields."""
        assert "resolution" in grid_data
        assert "cell_size" in grid_data
        assert "total_points" in grid_data
        assert "occupied_cells" in grid_data
        assert "layers_loaded" in grid_data
        assert "density_scores" in grid_data

    def test_cluster_structure(self, cluster_data):
        """Cluster output has required top-level fields."""
        assert "cluster_count" in cluster_data
        assert "distance_threshold" in cluster_data
        assert "clusters" in cluster_data
        assert "total_clustered_points" in cluster_data


class TestLayerLoading:
    """Validates that all configured spatial layers are loaded."""

    def test_total_points(self, grid_data):
        """All 40 points from 4 layers must be indexed."""
        assert grid_data["total_points"] == 40, (
            f"Expected 40 points from 4 layers, got "
            f"{grid_data['total_points']}."
        )

    def test_layer_count(self, grid_data):
        """Must include all 4 layers."""
        assert grid_data["layer_count"] == 4

    def test_vegetation_present(self, grid_data):
        """Vegetation layer must appear in loaded layers."""
        assert "vegetation" in grid_data["layers_loaded"]


class TestGridResolution:
    """Validates grid uses correct resolution from config."""

    def test_resolution_value(self, grid_data):
        """Grid resolution must be 25 from grid.analysis section."""
        assert grid_data["resolution"] == 25, (
            f"Expected resolution=25, got {grid_data['resolution']}."
        )

    def test_cell_size_value(self, grid_data):
        """Cell size must be 40.0 from grid.analysis section."""
        assert grid_data["cell_size"] == 40.0, (
            f"Expected cell_size=40.0, got {grid_data['cell_size']}."
        )

    def test_occupied_cells(self, grid_data):
        """With resolution=25 (cell_size=40), must have 7 occupied cells."""
        assert grid_data["occupied_cells"] == 7, (
            f"Expected 7 occupied cells with 40x40 grid, got "
            f"{grid_data['occupied_cells']}."
        )


class TestDensityComputation:
    """Validates density calculations with correct averaging."""

    def test_density_not_tripled(self, grid_data):
        """Density scores must reflect single-pass average, not 3x accumulated.

        With 3 passes of identical computation, the average should equal
        a single pass value. If accumulated (not averaged), values will be
        3x too high.
        """
        densities = grid_data["density_scores"]
        # All density scores should be reasonable (< 5.0 for these data points)
        for cell, score in densities.items():
            assert score < 5.0, (
                f"Cell {cell} has density {score} which exceeds 5.0 — "
                f"likely accumulated across passes instead of averaged."
            )

    def test_high_density_cell(self, grid_data):
        """Cell containing the point cluster near (125,348) must have highest density."""
        densities = grid_data["density_scores"]
        # Cell (3,8) with 40x40 grid: centroid at (140, 340)
        # Many points cluster near (125, 348) within 80.0 kernel radius
        cell_3_8 = densities.get("3,8", 0)
        assert 1.8 < cell_3_8 < 2.5, (
            f"Cell 3,8 density should be ~2.1, got {cell_3_8}."
        )

    def test_density_cell_count(self, grid_data):
        """Must have exactly 7 density scores (one per occupied cell)."""
        assert len(grid_data["density_scores"]) == 7


class TestClusterFormation:
    """Validates spatial clustering results."""

    def test_cluster_count(self, cluster_data):
        """Must produce exactly 5 clusters with all 4 layers loaded."""
        assert cluster_data["cluster_count"] == 5, (
            f"Expected 5 clusters, got {cluster_data['cluster_count']}."
        )

    def test_total_clustered(self, cluster_data):
        """All 40 points must be assigned to clusters."""
        assert cluster_data["total_clustered_points"] == 40, (
            f"Expected 40 clustered points, got "
            f"{cluster_data['total_clustered_points']}."
        )

    def test_largest_cluster_size(self, cluster_data):
        """Largest cluster must have 13 members (central point group)."""
        sizes = [c["member_count"] for c in cluster_data["clusters"]]
        assert max(sizes) == 13, (
            f"Expected largest cluster=13, got {max(sizes)}."
        )

    def test_smallest_cluster_size(self, cluster_data):
        """Smallest cluster must have 3 members (minimum threshold)."""
        sizes = [c["member_count"] for c in cluster_data["clusters"]]
        assert min(sizes) == 3

    def test_cluster_centroid_range(self, cluster_data):
        """First cluster centroid must be near (128, 348)."""
        c0 = cluster_data["clusters"][0]
        assert 120 < c0["centroid_x"] < 135, (
            f"First cluster centroid_x should be ~128, got {c0['centroid_x']}."
        )
        assert 340 < c0["centroid_y"] < 355, (
            f"First cluster centroid_y should be ~348, got {c0['centroid_y']}."
        )
