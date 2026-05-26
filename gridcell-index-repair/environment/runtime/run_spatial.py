"""
Main entry point for the spatial grid indexing system.

Orchestrates the full spatial analysis:
1. Load sensor readings
2. Partition readings into grid cells
3. Compute per-cell aggregations
4. Identify hotspot clusters
5. Execute spatial query
6. Write outputs
"""

import json
import os
import configparser

from runtime.loader import load_readings
from runtime.grid_partitioner import GridPartitioner
from runtime.aggregator import CellAggregator
from runtime.cluster_finder import ClusterFinder
from runtime.query_engine import QueryEngine


def main():
    """Run the spatial grid indexing process."""
    config = configparser.ConfigParser()
    config.read("/app/runtime/config.ini")

    # Stage 1: Load readings
    readings = load_readings()

    # Stage 2: Assign to grid cells
    partitioner = GridPartitioner()
    assigned = partitioner.assign_cells(readings)

    # Stage 3: Aggregate per cell
    aggregator = CellAggregator()
    cell_stats = aggregator.aggregate(assigned)

    # Stage 4: Find clusters
    finder = ClusterFinder()
    clusters = finder.find_clusters(cell_stats)

    # Stage 5: Execute query
    engine = QueryEngine()
    query_results = engine.execute_query(assigned, cell_stats)

    # Stage 6: Write outputs
    output_dir = os.path.dirname(config.get("output", "index_path"))
    os.makedirs(output_dir, exist_ok=True)

    grid_index = {
        "total_assigned": len(assigned),
        "cells_populated": len(cell_stats),
        "cell_stats": cell_stats,
    }

    cluster_report = {
        "total_clusters": len(clusters),
        "clusters": clusters,
    }

    query_output = {
        "center": {"lat": 1.0, "lon": 1.0},
        "radius": 3.0,
        "results_count": len(query_results),
        "results": query_results,
    }

    summary = {
        "total_readings_loaded": len(readings),
        "total_assigned_to_grid": len(assigned),
        "cells_populated": len(cell_stats),
        "total_clusters": len(clusters),
        "query_results_count": len(query_results),
    }

    with open(config.get("output", "index_path"), "w") as f:
        json.dump(grid_index, f, indent=2)
    with open(config.get("output", "clusters_path"), "w") as f:
        json.dump(cluster_report, f, indent=2)
    with open(config.get("output", "query_path"), "w") as f:
        json.dump(query_output, f, indent=2)
    with open(config.get("output", "summary_path"), "w") as f:
        json.dump(summary, f, indent=2)

    print(f"Indexed {len(assigned)} readings into {len(cell_stats)} cells")
    print(f"Clusters: {len(clusters)}")
    print(f"Query results: {len(query_results)}")


if __name__ == "__main__":
    main()
