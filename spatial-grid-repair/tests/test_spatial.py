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


class TestGridConfiguration:
    """Validates grid uses correct resolution and cell size from config."""

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
        """With cell_size=40 and boundary handling, must have 10 occupied cells."""
        assert grid_data["occupied_cells"] == 10, (
            f"Expected 10 occupied cells, got {grid_data['occupied_cells']}."
        )

    def test_boundary_point_assignment(self, grid_data):
        """Point t011 at (400.0, 400.0) must be in cell 9,9 not 10,10.

        Points exactly on cell boundaries (coordinate is exact multiple
        of cell_size) must be assigned to the lower cell. This is the
        inclusive upper bound rule. Check boundary logic in
        /app/runtime/grid_indexer.py _get_cell method.
        """
        assignments = grid_data["cell_assignments"]
        # t011 should be in cell 9,9
        cell_9_9 = assignments.get("9,9", [])
        assert "t011" in cell_9_9, (
            f"Point t011 at (400.0, 400.0) should be in cell 9,9 "
            f"(boundary points go to lower cell). Found in: "
            f"{[k for k, v in assignments.items() if 't011' in v]}"
        )


class TestDensityComputation:
    """Validates kernel density estimation with correct kernel function."""

    def test_density_values_reasonable(self, grid_data):
        """All density scores must be below 0.02 (linear kernel with area normalization).

        If densities are above 0.02, the kernel function is likely
        using quadratic weights (dist^2/radius^2) instead of linear
        (dist/radius). The correct kernel for weighted_linear mode is:
        contribution = weight * (1 - dist/radius).
        Check /app/runtime/density_calculator.py kernel weight formula.
        """
        densities = grid_data["density_scores"]
        for cell, score in densities.items():
            assert score < 0.02, (
                f"Cell {cell} has density {score} which is too high. "
                f"With linear kernel and area normalization, values "
                f"should be below 0.02. Check kernel weight formula "
                f"in /app/runtime/density_calculator.py — should use "
                f"(1 - dist/radius) not (1 - dist^2/radius^2)."
            )

    def test_highest_density_cell(self, grid_data):
        """The cell with most nearby high-weight points must have highest density."""
        densities = grid_data["density_scores"]
        max_cell = max(densities, key=densities.get)
        max_val = densities[max_cell]
        assert 0.010 < max_val < 0.015, (
            f"Highest density should be ~0.012, got {max_val}."
        )

    def test_density_cell_count(self, grid_data):
        """Must have exactly 10 density scores (one per occupied cell)."""
        assert len(grid_data["density_scores"]) == 10


class TestClusterFormation:
    """Validates spatial clustering with correct point ordering."""

    def test_cluster_count(self, cluster_data):
        """Must produce exactly 6 clusters with all layers and correct ordering.

        Without vegetation layer, only 4 clusters form. With vegetation
        loaded AND correct timestamp-based ordering (using layer_id as
        tiebreaker), 6 clusters emerge because vegetation points fill
        gaps that enable additional clusters to meet min_points=3.
        """
        assert cluster_data["cluster_count"] == 6, (
            f"Expected 6 clusters, got {cluster_data['cluster_count']}. "
            f"Cluster formation depends on all layers being loaded AND "
            f"correct point processing order."
        )

    def test_total_clustered(self, cluster_data):
        """All 40 points must be assigned to valid clusters."""
        assert cluster_data["total_clustered_points"] == 40, (
            f"Expected 40 clustered points, got "
            f"{cluster_data['total_clustered_points']}."
        )

    def test_largest_cluster_size(self, cluster_data):
        """Largest cluster must have 11 members."""
        sizes = [c["member_count"] for c in cluster_data["clusters"]]
        assert max(sizes) == 11, (
            f"Expected largest cluster=11, got {max(sizes)}."
        )

    def test_smallest_cluster_size(self, cluster_data):
        """Smallest cluster must have exactly 3 members (minimum threshold)."""
        sizes = [c["member_count"] for c in cluster_data["clusters"]]
        assert min(sizes) == 3

    def test_central_cluster_has_vegetation(self, cluster_data):
        """The cluster near (400, 400) must include vegetation points v008 and v009.

        This cluster only reaches min_points=3 when vegetation is loaded.
        Without vegetation, it has too few members and gets filtered out.
        """
        # Find cluster near (400, 400)
        target_cluster = None
        for c in cluster_data["clusters"]:
            if 380 < c["centroid_x"] < 420 and 380 < c["centroid_y"] < 420:
                target_cluster = c
                break
        assert target_cluster is not None, (
            "No cluster found near (400, 400). This cluster depends on "
            "vegetation points being loaded."
        )
        assert "v008" in target_cluster["members"], (
            f"Vegetation point v008 must be in the (400,400) cluster."
        )
