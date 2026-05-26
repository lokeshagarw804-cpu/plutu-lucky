"""Spatial grid indexer — main entry point.

Orchestrates the full spatial analysis: load layers, merge points,
assign to grid cells, compute density, build clusters, and produce
the spatial index output.
"""
import json
import os

from runtime.loader import LayerLoader
from runtime.grid_indexer import GridIndexer
from runtime.density_calculator import DensityCalculator
from runtime.cluster_builder import ClusterBuilder


def main():
    config_path = "/app/runtime/config.ini"

    # Load spatial layers
    loader = LayerLoader(config_path)
    layers = loader.load_layers()

    # Merge all points with layer metadata
    all_points = []
    for layer_id, layer_data in layers.items():
        for point in layer_data["points"]:
            all_points.append({
                "point_id": point["point_id"],
                "layer_id": layer_id,
                "x": point["x"],
                "y": point["y"],
                "weight": point["weight"],
                "timestamp": point["timestamp"],
                "seq": point["seq"],
            })

    # Sort for deterministic processing
    all_points.sort(key=lambda p: (p["timestamp"], p["seq"]))

    # Assign to grid cells
    indexer = GridIndexer(config_path)
    grid = indexer.index_points(all_points)

    # Compute density
    calculator = DensityCalculator(config_path)
    densities = calculator.compute_density(
        grid, indexer.get_cell_size(), all_points
    )

    # Build clusters
    builder = ClusterBuilder(config_path)
    clusters = builder.build_clusters(all_points)

    # Write outputs
    output_dir = "/app/runtime/output"
    os.makedirs(output_dir, exist_ok=True)

    # Grid index output
    grid_output = {
        "resolution": indexer.get_resolution(),
        "cell_size": indexer.get_cell_size(),
        "total_points": len(all_points),
        "occupied_cells": len(grid),
        "layers_loaded": sorted(layers.keys()),
        "layer_count": len(layers),
        "cell_assignments": {
            f"{k[0]},{k[1]}": [p["point_id"] for p in v]
            for k, v in sorted(grid.items())
        },
        "density_scores": {
            f"{k[0]},{k[1]}": v for k, v in sorted(densities.items())
        },
    }
    with open(os.path.join(output_dir, "grid_index.json"), "w") as f:
        json.dump(grid_output, f, indent=2)

    # Cluster output
    cluster_output = {
        "cluster_count": len(clusters),
        "distance_threshold": builder.get_threshold(),
        "clusters": clusters,
        "total_clustered_points": sum(
            c["member_count"] for c in clusters
        ),
    }
    with open(os.path.join(output_dir, "cluster_report.json"), "w") as f:
        json.dump(cluster_output, f, indent=2)


if __name__ == "__main__":
    main()
