# Spatial Query Planner — Debugging Task

## Overview

A spatial query system loads geographic features from data sources, builds a cell index, and runs radius range queries. Results are sorted by (distance_km, source_id, feature_id) for determinism.

## System Environment

- *Language*: Python 3.11
- *Runtime*: /app/runtime/ (source, config, data, output)
- *Global system-wide tooling*: uv and pytest are available
- *Configuration*: /app/runtime/config.ini — the query.spatial section holds operational query parameters

## Processing Stages

1. `/app/runtime/loader.py` — Loads feature JSON for each source in active_sources
2. `/app/runtime/index_builder.py` — Builds cell bounding boxes from batched features
3. `/app/runtime/range_query.py` — Finds features within the radius from query.spatial config
4. `/app/runtime/report_builder.py` — Assembles output

## Symptoms

- One configured source never loads despite its file existing
- Query radius too large, returning features beyond operational range
- Index reports incorrect feature counts
- Tied-distance results not deterministically ordered

## Expected Output

- Sources loaded: cadastral, hydrology, infrastructure, terrain (all 4)
- Radius: 12.5 km (from query.spatial section)
- Index feature counts reflect actual loaded data (61 total)
- Results ordered by (distance_km, source_id, feature_id)
- max_results: 25 (from query.spatial)

## Your Task

Fix defects in /app/runtime/ source files so output matches expectations. Note: feature_id is local to each source.
