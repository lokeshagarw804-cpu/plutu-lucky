# Spatial Grid Indexer Repair — Debugging Task

## Overview

A spatial grid indexer processes geospatial point data from multiple thematic layers, assigns points to fixed-size grid cells with boundary handling, computes kernel density estimates using distance-weighted contributions, and builds distance-based point clusters through incremental centroid tracking. The system handles heterogeneous spatial layers and produces both a grid index with density scores and a cluster analysis report.

## System Environment

- *Language*: Python 3.11
- *Runtime*: /app/runtime/ (source modules, configuration, layer data, output)
- *Global system-wide tooling*: uv and pytest are available
- *Configuration*: /app/runtime/config.ini

## Architecture

The system processes spatial layers through four stages:

1. *Loading* (`/app/runtime/loader.py`) — Reads JSON-format layer files from `/app/runtime/data/`, filtering to only layers whose type appears in the active_layers config

2. *Grid Indexing* (`/app/runtime/grid_indexer.py`) — Assigns each point to a grid cell. The resolution and cell_size come from the `grid.analysis` configuration section. Cell index is floor(coord / cell_size). Points on exact cell boundaries (coordinate is an exact multiple of cell_size) are assigned to the lower cell — this is the inclusive upper bound rule that keeps boundary points in the correct density neighborhood.

3. *Density Estimation* (`/app/runtime/density_calculator.py`) — Uses a distance-weighted linear kernel where each point within kernel_radius contributes: weight * (1 - distance/radius). This linear decay means points at the centroid contribute full weight while points at the radius boundary contribute zero. The density per cell is the sum of weighted contributions divided by cell area, averaged across passes.

4. *Clustering* (`/app/runtime/cluster_builder.py`) — Groups points using incremental centroid-based clustering with a distance threshold. Points are processed in timestamp order, with layer_id alphabetically then seq as deterministic tiebreakers for same-timestamp points. Each new point either joins the nearest cluster (updating its centroid) or seeds a new cluster. Only clusters reaching min_points are retained.

## Problem

The system produces output but with several anomalies:
- Fewer points and layers are processed than the data files contain
- The grid has far more occupied cells than the spatial point distribution should produce
- Density values appear higher than expected for the given point weights and cell area
- Some clusters are missing that should form from point groups in the data
- Points at coordinate boundaries appear in unexpected grid cells

## Expected Correct Output

When all defects are resolved:
- All 40 points from 4 layers (terrain: 12, infrastructure: 10, vegetation: 10, hydrology: 8)
- Grid resolution 25 with cell_size 40.0, producing 10 occupied cells
- Point t011 at (400.0, 400.0) must be in cell (9,9) due to boundary rule
- Density values all below 0.02 (linear kernel with 1600 sq unit cell area)
- 6 clusters formed (vegetation points enable 2 additional clusters to reach min_points)
- All 40 points assigned to clusters, largest cluster has 11 members

## Output Schema

### /app/runtime/output/grid_index.json

| Field | Type | Description |
|-------|------|-------------|
| resolution | integer | Grid resolution used |
| cell_size | float | Physical size of each grid cell |
| total_points | integer | Total points indexed across all layers |
| occupied_cells | integer | Number of non-empty grid cells |
| layers_loaded | array[string] | Sorted list of loaded layer identifiers |
| layer_count | integer | Number of layers loaded |
| cell_assignments | object | Map of "cx,cy" to list of point IDs in that cell |
| density_scores | object | Map of "cx,cy" to computed density value |

### /app/runtime/output/cluster_report.json

| Field | Type | Description |
|-------|------|-------------|
| cluster_count | integer | Number of valid clusters (>= min_points) |
| distance_threshold | float | Clustering distance threshold used |
| clusters | array | List of cluster objects |
| clusters[].cluster_id | integer | Sequential cluster identifier |
| clusters[].centroid_x | float | Current cluster centroid X |
| clusters[].centroid_y | float | Current cluster centroid Y |
| clusters[].member_count | integer | Number of points in cluster |
| clusters[].members | array[string] | Point IDs assigned to cluster |
| total_clustered_points | integer | Sum of all cluster member counts |

## Key Files

| File | Purpose |
|------|---------|
| /app/runtime/config.ini | Grid parameters, density settings, layer config |
| /app/runtime/loader.py | Layer data loading with type filtering |
| /app/runtime/grid_indexer.py | Point-to-cell assignment with boundary logic |
| /app/runtime/density_calculator.py | Distance-weighted kernel density computation |
| /app/runtime/cluster_builder.py | Incremental centroid-based spatial clustering |
| /app/runtime/run_spatial.py | Main entry point and orchestration |

## Your Task

Identify and fix defects in the runtime source files under `/app/runtime/` so that the system produces correct output matching the expected behavior described above. Multiple modules contain interacting defects that collectively produce incorrect spatial analysis results.
