# Spatial Grid Indexer Repair — Debugging Task

## Overview

A spatial grid indexer processes geospatial point data from multiple thematic layers, assigns points to grid cells, computes kernel density estimates across the grid, and builds distance-based point clusters. The system handles heterogeneous spatial layers and produces both a grid index with density scores and a cluster analysis report.

## System Environment

- *Language*: Python 3.11
- *Runtime*: /app/runtime/ (source modules, configuration, layer data, output)
- *Global system-wide tooling*: uv and pytest are available
- *Configuration*: /app/runtime/config.ini

## Architecture

The system processes spatial layers through four stages:

1. *Loading* (`/app/runtime/loader.py`) — Reads JSON-format layer files from `/app/runtime/data/`, filtering to only layers whose type appears in the active_layers config

2. *Grid Indexing* (`/app/runtime/grid_indexer.py`) — Assigns each point to a grid cell using the resolution and cell_size from the `grid.analysis` configuration section. Cell index is computed as floor(coordinate / cell_size) with boundary handling.

3. *Density Estimation* (`/app/runtime/density_calculator.py`) — Performs multiple kernel density passes over the grid. Each pass computes the mean weight of points within kernel_radius of each cell centroid. The final density is the average across all passes (since passes use the same kernel, the average equals a single pass value).

4. *Clustering* (`/app/runtime/cluster_builder.py`) — Groups points into distance-based clusters using incremental centroid computation. Points are processed in timestamp order with layer_id alphabetically then seq as tiebreakers for deterministic assignment when timestamps match.

## Problem

The system produces output but with several anomalies:
- Fewer points and layers appear than expected given the data files present
- Grid cell assignments produce far more occupied cells than the spatial distribution warrants
- Density scores appear inflated beyond reasonable values for the point weights
- Cluster sizes and centroids differ from expected values
- Point processing order affects cluster assignment non-deterministically

## Expected Correct Output

When all defects are resolved:
- All 40 points from 4 layers (terrain: 12, infrastructure: 10, vegetation: 10, hydrology: 8) are indexed
- Grid resolution is 25 with cell_size 40.0 (from grid.analysis section)
- 7 occupied grid cells (points cluster into broader 40x40 areas)
- Density scores are the single-pass mean (not multiplied by number of passes)
- 5 clusters are formed with the largest having 13 members
- All 40 points are assigned to clusters (minimum cluster size is 3)

## Output Schema

### /app/runtime/output/grid_index.json

| Field | Type | Description |
|-------|------|-------------|
| resolution | integer | Grid resolution used |
| cell_size | float | Size of each grid cell |
| total_points | integer | Total points indexed |
| occupied_cells | integer | Number of non-empty cells |
| layers_loaded | array[string] | Sorted list of loaded layers |
| layer_count | integer | Number of layers loaded |
| cell_assignments | object | Map of cell key to point IDs |
| density_scores | object | Map of cell key to density value |

### /app/runtime/output/cluster_report.json

| Field | Type | Description |
|-------|------|-------------|
| cluster_count | integer | Number of valid clusters |
| distance_threshold | float | Clustering distance threshold |
| clusters | array | List of cluster objects |
| clusters[].cluster_id | integer | Sequential cluster identifier |
| clusters[].centroid_x | float | Cluster centroid X coordinate |
| clusters[].centroid_y | float | Cluster centroid Y coordinate |
| clusters[].member_count | integer | Points in cluster |
| clusters[].members | array[string] | Point IDs in cluster |
| total_clustered_points | integer | Sum of all cluster members |

## Key Files

| File | Purpose |
|------|---------|
| /app/runtime/config.ini | Grid parameters and layer configuration |
| /app/runtime/loader.py | Layer data loading with type filtering |
| /app/runtime/grid_indexer.py | Point-to-cell assignment logic |
| /app/runtime/density_calculator.py | Multi-pass kernel density estimation |
| /app/runtime/cluster_builder.py | Distance-based spatial clustering |
| /app/runtime/run_spatial.py | Main entry point and orchestration |

## Your Task

Identify and fix defects in the runtime source files under `/app/runtime/` so that the system produces correct output matching the expected behavior described above. Multiple modules contain interacting defects that collectively produce incorrect spatial analysis results.
