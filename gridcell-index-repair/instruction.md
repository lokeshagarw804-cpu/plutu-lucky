# Spatial Grid Cell Indexer — Debugging Task

## Overview

A spatial grid indexing system partitions geo-located sensor readings into uniform grid cells, computes per-cell statistical aggregations, identifies clusters of high-density cells, and answers spatial range queries. The system currently produces incorrect results across multiple stages.

## System Environment

- *Language*: Python 3.11
- *Runtime*: /app/runtime/ (source, config, data, output)
- *Global system-wide tooling*: uv and pytest are available

## Processing Stages

1. *Grid Partitioning* — Assigns each reading to a grid cell based on geographic coordinates. The grid covers a defined spatial extent with uniform cell size.

2. *Aggregation* — Computes summary statistics (count, mean, variance, min, max) for each cell that meets the minimum reading threshold.

3. *Cluster Detection* — Identifies clusters of adjacent high-density cells using connected-component analysis on the grid topology.

4. *Range Query* — Finds cells within a specified radius of a query point, returning their statistics ranked by density.

5. *Output Generation* — Writes grid index, cluster report, query results, and processing summary.

## Problem

The system runs without errors but produces results that fail validation:
- Too many readings are assigned to the grid (some should be excluded)
- Statistical variance values do not match expected sample statistics
- Cluster detection misses cells that should be connected
- Range query returns fewer results than expected

## Expected Correct Output

When functioning correctly:
- Exactly 35 readings assigned to the grid (not more)
- 11 cells populated with sufficient readings
- 1 cluster containing 4 cells (connected via full adjacency)
- 9 cells returned by the range query

## Output Schema

### /app/runtime/output/grid_index.json

| Field | Type | Description |
|-------|------|-------------|
| total_assigned | int | Readings assigned to grid cells |
| cells_populated | int | Cells meeting minimum threshold |
| cell_stats | object | Per-cell statistics keyed by cell_id |

### /app/runtime/output/cluster_report.json

| Field | Type | Description |
|-------|------|-------------|
| total_clusters | int | Number of detected clusters |
| clusters | list | Cluster details with cell lists |

### /app/runtime/output/query_results.json

| Field | Type | Description |
|-------|------|-------------|
| results_count | int | Matching cells returned |
| results | list | Cell statistics within query radius |

### /app/runtime/output/spatial_summary.json

| Field | Type | Description |
|-------|------|-------------|
| total_readings_loaded | int | All readings from data files |
| total_assigned_to_grid | int | Readings within grid extent |
| cells_populated | int | Cells with sufficient data |
| total_clusters | int | Detected hotspot clusters |
| query_results_count | int | Range query matches |

## Key Files

| File | Purpose |
|------|---------|
| /app/runtime/run_spatial.py | Main entry point |
| /app/runtime/loader.py | Sensor data loading |
| /app/runtime/grid_partitioner.py | Coordinate-to-cell assignment |
| /app/runtime/aggregator.py | Per-cell statistical computation |
| /app/runtime/cluster_finder.py | Density-based cluster detection |
| /app/runtime/query_engine.py | Spatial range query execution |
| /app/runtime/config.ini | Grid and query configuration |

## Your Task

Identify and fix the defects in the runtime source files under /app/runtime/ that cause incorrect grid assignment, wrong variance values, incomplete clustering, and missing query results.
