# Spatial Index Repair — Debugging Task

## Overview

A spatial indexing system ingests geographic point-of-interest (POI) records from multiple feed sources, builds an R-tree spatial index for efficient region queries, and produces query results with index statistics. The system processes three JSONL feed files containing POI records across several categories and geographic areas.

## System Environment

- *Language*: Python 3.11
- *Runtime*: /app/runtime/ (source modules, configuration, data files, output)
- *Global system-wide tooling*: uv and pytest are available
- *Configuration*: /app/runtime/config.ini (INI format with hierarchical section structure)

## Architecture

The system is composed of six modules that execute in sequence:

1. *Feed Loading* (`/app/runtime/feed_loader.py`) — Reads raw JSONL records from `/app/runtime/data/` without applying any filters.

2. *Normalization* (`/app/runtime/normalizer.py`) — Validates records and applies category filtering based on the `allowed_categories` value in the `[feeds]` config section. All category tokens in the config should be treated as trimmed values.

3. *Index Construction* (`/app/runtime/indexer.py`) — Sorts normalized records using the ordering utility and inserts them into R-tree leaf nodes in configurable batches. The leaf node parameters (batch size, maximum entries per node) are specified in the `[spatial.engine.leafnode]` config section which provides R-tree-specific overrides for POI storage.

4. *Record Ordering* (`/app/runtime/record_ordering.py`) — Provides the deterministic sort function for index insertion. The canonical ordering is by timestamp, then source identifier, then local sequence number within that source.

5. *Region Query* (`/app/runtime/query_engine.py`) — Executes a bounding-box query using coordinates from the `[queries]` section. The query region uses inclusive boundary matching for all four edges of the bounding rectangle.

6. *Statistics* (`/app/runtime/stats.py` + `/app/runtime/partition_merger.py`) — Scans indexed entries in partition windows and computes per-category distribution. Each partition represents a self-contained snapshot; the final reported statistics should reflect final partition snapshot semantics rather than cumulative totals across all windows.

## Problem

The system produces output but several metrics are incorrect: the total number of indexed POIs is lower than expected, the index tree structure does not match the configured leaf node capacity, query results omit records that should be included, per-category statistics appear significantly inflated beyond what any single partition window could contain, and record ordering is non-deterministic at certain timestamp boundaries.

## Expected Correct Output

When all defects are resolved:
- All 56 POI records from the three feeds should pass normalization and be indexed
- The R-tree should contain 7 leaf nodes with 8 entries each
- The region query should return 56 matching results
- Per-category statistics should reflect a single partition's distribution (sum ≤ 20)
- Records at shared timestamps should be ordered by source feed identifier

## Output Schema

### /app/runtime/output/query_results.json

| Field | Type | Description |
|-------|------|-------------|
| query_bounds | object | Bounding box parameters used for the region query |
| query_bounds.lat_min | float | Southern boundary latitude |
| query_bounds.lat_max | float | Northern boundary latitude |
| query_bounds.lon_min | float | Western boundary longitude |
| query_bounds.lon_max | float | Eastern boundary longitude |
| total_hits | integer | Number of POIs within the query region |
| results | array | Matching POI entries in insertion order |
| results[].rank | integer | 1-based insertion order rank |
| results[].name | string | POI name |
| results[].category | string | POI category |
| results[].lat | float | Latitude |
| results[].lon | float | Longitude |
| results[].feed_id | string | Source feed identifier |
| results[].timestamp | string | ISO 8601 timestamp |

### /app/runtime/output/index_stats.json

| Field | Type | Description |
|-------|------|-------------|
| total_indexed | integer | Total POIs in the index |
| node_count | integer | Number of R-tree leaf nodes |
| avg_node_fill | float | Average entries per node |
| max_entries_per_node | integer | Configured leaf node capacity |
| category_counts | object | Per-category counts from final partition |
| category_counts.restaurant | integer | Restaurant POIs in final partition |
| category_counts.park | integer | Park POIs in final partition |
| category_counts.museum | integer | Museum POIs in final partition |
| category_counts.hospital | integer | Hospital POIs in final partition |
| spatial_extent | object | Geographic spread metrics |
| spatial_extent.lat_spread | float | Latitude range |
| spatial_extent.lon_spread | float | Longitude range |

## Key Files

| File | Purpose |
|------|---------|
| /app/runtime/config.ini | Hierarchical configuration with multiple sections |
| /app/runtime/feed_loader.py | Raw record loading from JSONL feeds |
| /app/runtime/normalizer.py | Category filtering and record validation |
| /app/runtime/indexer.py | R-tree construction and region query execution |
| /app/runtime/record_ordering.py | Sort utility for deterministic insertion order |
| /app/runtime/query_engine.py | Query formatting and result assembly |
| /app/runtime/stats.py | Partition-based statistics computation |
| /app/runtime/partition_merger.py | Merges partition snapshots into final counts |
| /app/runtime/run_spatial.py | Main orchestration entry point |

## Your Task

Identify and fix defects in the runtime source files under /app/runtime/ so that the system produces correct output matching the documented schema and expected values. The configuration file contains authoritative parameters; ensure each module reads from the appropriate section.
