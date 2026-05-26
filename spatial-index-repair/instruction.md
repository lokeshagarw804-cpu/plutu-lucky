# Spatial Index Repair — Debugging Task

## Overview

A spatial indexing system ingests geographic point-of-interest (POI) records from multiple feed sources, builds an R-tree spatial index, executes bounding-box region queries, and produces query results with index statistics. The system processes three feed files containing restaurant, park, museum, and hospital POI records across New York City.

## System Environment

- *Language*: Python 3.11
- *Runtime*: /app/runtime/ (source, config, data, output)
- *Global system-wide tooling*: uv and pytest are available
- *Configuration*: /app/runtime/config.ini (INI format with hierarchical sections)

## Processing Stages

1. *Feed Loading* — Reads JSONL records from /app/runtime/data/, filters by allowed categories defined in the `[feeds]` section of config. All category values must be trimmed before matching.

2. *Index Building* — Sorts filtered records and inserts them into R-tree leaf nodes in batches. The R-tree specific parameters (batch size, max entries per node) are defined in the `[indexer.rtree]` section. Records with identical timestamps must be ordered deterministically by feed_id first, then by sequence number, since sequence numbers are local to each feed stream.

3. *Region Query* — Executes a bounding-box query using coordinates from the `[queries]` config section and returns all matching POI entries with their insertion-order rank.

4. *Statistics Computation* — Scans indexed entries in partitions and computes per-category counts. Each partition represents a snapshot of category distribution; the final statistics should reflect only the last partition's category counts (not accumulated totals across all partitions).

## Problem

The system produces output but with incorrect values. The total number of indexed POIs is lower than expected, the index structure has far fewer nodes than appropriate for the configured R-tree parameters, the per-category statistics appear inflated, and the ordering of results at timestamp boundaries is non-deterministic across runs.

## Expected Correct Output

When all defects are resolved:
- All 56 POI records from the three feeds should be indexed (including all four categories: restaurant, park, museum, hospital)
- The R-tree should use a maximum of 8 entries per leaf node, producing 7 nodes
- Per-category statistics should reflect the final partition snapshot only
- Records sharing the same timestamp should be ordered by feed_id then sequence number

## Output Schema

### /app/runtime/output/query_results.json

| Field | Type | Description |
|-------|------|-------------|
| query_bounds | object | The bounding box used for the region query |
| query_bounds.lat_min | float | Minimum latitude of query region |
| query_bounds.lat_max | float | Maximum latitude of query region |
| query_bounds.lon_min | float | Minimum longitude of query region |
| query_bounds.lon_max | float | Maximum longitude of query region |
| total_hits | integer | Number of POIs found within the query region |
| results | array | List of matching POI entries |
| results[].rank | integer | Insertion-order rank (1-based) |
| results[].name | string | Name of the point of interest |
| results[].category | string | POI category (restaurant, park, museum, hospital) |
| results[].lat | float | Latitude coordinate |
| results[].lon | float | Longitude coordinate |
| results[].feed_id | string | Source feed identifier (alpha, beta, gamma) |
| results[].timestamp | string | ISO 8601 timestamp of the record |

### /app/runtime/output/index_stats.json

| Field | Type | Description |
|-------|------|-------------|
| total_indexed | integer | Total number of POIs in the index |
| node_count | integer | Number of R-tree leaf nodes created |
| avg_node_fill | float | Average entries per node (rounded to 2 decimals) |
| max_entries_per_node | integer | Configured maximum entries per leaf node |
| category_counts | object | Per-category POI counts from final partition snapshot |
| category_counts.restaurant | integer | Count of restaurant POIs in last partition |
| category_counts.park | integer | Count of park POIs in last partition |
| category_counts.museum | integer | Count of museum POIs in last partition |
| category_counts.hospital | integer | Count of hospital POIs in last partition |
| spatial_extent | object | Geographic spread of indexed data |
| spatial_extent.lat_spread | float | Latitude range (max - min, rounded to 4 decimals) |
| spatial_extent.lon_spread | float | Longitude range (max - min, rounded to 4 decimals) |

## Key Files

| File | Purpose |
|------|---------|
| /app/runtime/config.ini | Configuration with feed paths, indexer parameters, and query bounds |
| /app/runtime/feed_loader.py | Loads and filters POI records from JSONL feed files |
| /app/runtime/indexer.py | Builds R-tree spatial index from sorted records |
| /app/runtime/query_engine.py | Executes bounding-box region queries against the index |
| /app/runtime/stats.py | Computes index statistics across partitions |
| /app/runtime/run_spatial.py | Main entry point orchestrating all stages |
| /app/runtime/data/feed_alpha.jsonl | POI feed from source alpha (18 records) |
| /app/runtime/data/feed_beta.jsonl | POI feed from source beta (20 records) |
| /app/runtime/data/feed_gamma.jsonl | POI feed from source gamma (18 records) |

## Your Task

Identify and fix defects in the runtime source files under /app/runtime/ so that the system produces correct output matching the schema and expected behavior documented above. The configuration file contains the authoritative parameters; ensure the code reads from the appropriate config sections and handles all data correctly.
